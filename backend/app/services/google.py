"""Google integration helpers."""

from __future__ import annotations

import random
import time
from functools import wraps
from typing import TypeVar, Callable

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
import structlog

from app.config import get_settings
from app.models.integration import Integration

logger = structlog.get_logger()

T = TypeVar("T")


def with_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_codes: tuple[int, ...] = (429, 500, 502, 503, 504),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator that adds exponential backoff retry logic for Google API calls.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exponential_base: Base for exponential backoff (default: 2.0)
        jitter: Add random jitter to delays to avoid thundering herd (default: True)
        retryable_codes: HTTP status codes that should trigger a retry

    Returns:
        Decorated function with retry logic
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except HttpError as e:
                    last_exception = e
                    status_code = e.resp.status if e.resp else 0

                    if status_code not in retryable_codes or attempt >= max_retries:
                        logger.warning(
                            "google.api.error",
                            function=func.__name__,
                            status_code=status_code,
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            retryable=status_code in retryable_codes,
                        )
                        raise

                    # Calculate delay with exponential backoff
                    delay = min(
                        initial_delay * (exponential_base**attempt),
                        max_delay,
                    )

                    # Add jitter (±25% of delay)
                    if jitter:
                        delay = delay * (0.75 + random.random() * 0.5)

                    logger.info(
                        "google.api.retry",
                        function=func.__name__,
                        status_code=status_code,
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        delay_seconds=round(delay, 2),
                    )

                    time.sleep(delay)

            # Should not reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


def execute_with_retry(
    request,
    max_retries: int = 3,
    initial_delay: float = 1.0,
    operation_name: str = "google_api_call",
):
    """Execute a Google API request with exponential backoff retry.

    Use this for individual API calls when the decorator approach isn't suitable.

    Args:
        request: A Google API request object (returned by .get(), .list(), etc.)
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        operation_name: Name of the operation for logging

    Returns:
        The API response

    Raises:
        HttpError: If all retries fail or error is not retryable
    """
    retryable_codes = (429, 500, 502, 503, 504)
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return request.execute()
        except HttpError as e:
            last_exception = e
            status_code = e.resp.status if e.resp else 0

            if status_code not in retryable_codes or attempt >= max_retries:
                logger.warning(
                    "google.api.error",
                    operation=operation_name,
                    status_code=status_code,
                    attempt=attempt + 1,
                    max_retries=max_retries,
                )
                raise

            delay = min(initial_delay * (2**attempt), 60.0)
            delay = delay * (0.75 + random.random() * 0.5)  # Add jitter

            logger.info(
                "google.api.retry",
                operation=operation_name,
                status_code=status_code,
                attempt=attempt + 1,
                delay_seconds=round(delay, 2),
            )

            time.sleep(delay)

    if last_exception:
        raise last_exception

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/presentations",
]


def get_client_config():
    settings = get_settings()
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uris": [settings.google_redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def ensure_integration(db: Session, provider: str) -> Integration:
    integration = db.query(Integration).filter(Integration.provider == provider).first()
    if integration:
        return integration
    integration = Integration(provider=provider)
    db.add(integration)
    db.commit()
    db.refresh(integration)
    return integration


def build_oauth_flow(state: str | None = None) -> Flow:
    settings = get_settings()
    flow = Flow.from_client_config(
        get_client_config(),
        scopes=SCOPES,
        redirect_uri=settings.google_redirect_uri,
        state=state,
    )
    return flow


def get_auth_url(state: str | None = None) -> str:
    flow = build_oauth_flow(state=state)
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code_for_tokens(code: str) -> Credentials:
    flow = build_oauth_flow()
    flow.fetch_token(code=code)
    return flow.credentials


def save_credentials(db: Session, provider: str, credentials: Credentials) -> Integration:
    integration = ensure_integration(db, provider)
    integration.access_token = credentials.token
    integration.refresh_token = credentials.refresh_token or integration.refresh_token
    integration.token_type = "Bearer"
    integration.scope = " ".join(credentials.scopes or [])
    integration.expires_at = credentials.expiry
    db.commit()
    db.refresh(integration)
    return integration


def get_google_credentials(db: Session) -> Credentials | None:
    integration = db.query(Integration).filter(Integration.provider == "google").first()
    if not integration or not integration.access_token:
        return None

    creds = Credentials(
        token=integration.access_token,
        refresh_token=integration.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=get_settings().google_client_id,
        client_secret=get_settings().google_client_secret,
        scopes=SCOPES,
        expiry=integration.expires_at,
    )

    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(Request())
            integration.access_token = creds.token
            integration.expires_at = creds.expiry
            # Persist refreshed tokens and sync the object
            db.commit()
            db.refresh(integration)
        except Exception:
            # If refresh fails, return None to trigger re-authentication
            db.rollback()
            return None

    return creds


def build_drive_service(db: Session):
    creds = get_google_credentials(db)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds)


def build_docs_service(db: Session):
    creds = get_google_credentials(db)
    if not creds:
        return None
    return build("docs", "v1", credentials=creds)


def build_slides_service(db: Session):
    """Build Google Slides API service."""
    creds = get_google_credentials(db)
    if not creds:
        return None
    return build("slides", "v1", credentials=creds)
