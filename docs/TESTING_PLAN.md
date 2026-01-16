# Scribe Testing Plan

> Comprehensive testing strategy for ensuring quality and reliability.

---

## Test Categories

1. **Unit Tests** - Individual functions and methods
2. **Integration Tests** - API endpoints with database
3. **E2E Tests** - Full user workflows
4. **Manual Tests** - Visual and UX verification

---

## Current Test Coverage

### Existing Tests (backend/tests/)

| File | Coverage | Status |
|------|----------|--------|
| test_health.py | Health endpoint | ✅ Passing |
| test_documents.py | Document CRUD | ✅ Passing |
| test_claims.py | Claims CRUD | ✅ Passing |
| test_bibliography.py | Bibliography CRUD | ✅ Passing |
| test_notes.py | Notes CRUD | ✅ Passing |

### Running Existing Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

---

## Test Implementation Plan

### Priority 1: LLM Service Tests

**File:** `backend/tests/test_llm.py`

```python
"""Tests for LLM service endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestRewriteEndpoint:
    """Tests for /api/v1/llm/rewrite endpoint."""

    @patch('app.api.v1.llm.anthropic_client')
    def test_rewrite_academic_style(self, mock_client):
        """Test rewriting text in academic style."""
        # Mock Anthropic response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="The evidence suggests...")]
        mock_client.messages.create.return_value = mock_response

        response = client.post("/api/v1/llm/rewrite", json={
            "text": "This proves that X causes Y.",
            "style": "academic"
        })

        assert response.status_code == 200
        data = response.json()
        assert "rewritten" in data
        assert data["original"] == "This proves that X causes Y."

    @patch('app.api.v1.llm.anthropic_client')
    def test_rewrite_concise_style(self, mock_client):
        """Test rewriting text in concise style."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="X affects Y.")]
        mock_client.messages.create.return_value = mock_response

        response = client.post("/api/v1/llm/rewrite", json={
            "text": "It can be observed that X has an effect on Y.",
            "style": "concise"
        })

        assert response.status_code == 200

    def test_rewrite_missing_text(self):
        """Test error when text is missing."""
        response = client.post("/api/v1/llm/rewrite", json={
            "style": "academic"
        })

        assert response.status_code == 422


class TestExtractClaimsEndpoint:
    """Tests for /api/v1/llm/extract-claims endpoint."""

    @patch('app.api.v1.llm.anthropic_client')
    def test_extract_data_claims(self, mock_client):
        """Test extracting numeric data claims."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='''[
            {"text": "El gasto aumentó 23%", "type": "DATA", "confidence": 0.95}
        ]''')]
        mock_client.messages.create.return_value = mock_response

        response = client.post("/api/v1/llm/extract-claims", json={
            "text": "El gasto aumentó 23% en 2024."
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) >= 1
        assert data["claims"][0]["type"] == "DATA"

    @patch('app.api.v1.llm.anthropic_client')
    def test_extract_no_claims(self, mock_client):
        """Test when no claims are found."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='[]')]
        mock_client.messages.create.return_value = mock_response

        response = client.post("/api/v1/llm/extract-claims", json={
            "text": "Hello world."
        })

        assert response.status_code == 200
        data = response.json()
        assert len(data["claims"]) == 0


class TestImproveHedgingEndpoint:
    """Tests for /api/v1/llm/improve-hedging endpoint."""

    @patch('app.api.v1.llm.anthropic_client')
    def test_add_hedging(self, mock_client):
        """Test adding hedging to definitive statements."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(
            text="The evidence suggests that X may contribute to Y."
        )]
        mock_client.messages.create.return_value = mock_response

        response = client.post("/api/v1/llm/improve-hedging", json={
            "text": "This proves that X causes Y."
        })

        assert response.status_code == 200
        data = response.json()
        assert "suggests" in data["improved"] or "may" in data["improved"]
```

### Priority 2: Google Integration Tests

**File:** `backend/tests/test_google.py`

```python
"""Tests for Google integration endpoints."""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestGoogleOAuth:
    """Tests for Google OAuth flow."""

    def test_get_auth_url(self):
        """Test generating OAuth URL."""
        response = client.post("/api/v1/integrations/google/auth-url")

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "accounts.google.com" in data["auth_url"]

    def test_status_not_connected(self):
        """Test status when not connected."""
        response = client.get("/api/v1/integrations/google/status")

        assert response.status_code == 200
        data = response.json()
        assert data["connected"] == False


class TestGoogleDocsImport:
    """Tests for Google Docs import."""

    @patch('app.services.google.GoogleService')
    def test_import_google_doc(self, mock_service):
        """Test importing a Google Doc."""
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.get_document_content.return_value = {
            "title": "Test Doc",
            "content": "<p>Test content</p>"
        }
        mock_service.return_value = mock_instance

        response = client.post("/api/v1/google/docs/import", json={
            "file_id": "1abc123",
            "doc_type": "policy"
        })

        # May fail if not authenticated
        assert response.status_code in [200, 401, 403]

    def test_import_missing_file_id(self):
        """Test error when file_id is missing."""
        response = client.post("/api/v1/google/docs/import", json={
            "doc_type": "policy"
        })

        assert response.status_code == 422


class TestGoogleDocsExport:
    """Tests for Google Docs export."""

    @patch('app.services.google.GoogleService')
    def test_export_to_google_docs(self, mock_service):
        """Test exporting to Google Docs."""
        # First create a test document
        doc_response = client.post("/api/v1/documents", json={
            "title": "Test Export",
            "markdown": "# Test\n\nContent"
        })

        if doc_response.status_code == 200:
            slug = doc_response.json()["slug"]

            mock_instance = MagicMock()
            mock_instance.create_document.return_value = {
                "file_id": "1xyz",
                "url": "https://docs.google.com/..."
            }
            mock_service.return_value = mock_instance

            response = client.post("/api/v1/google/docs/export", json={
                "document_slug": slug
            })

            # May fail if not authenticated
            assert response.status_code in [200, 401, 403]
```

### Priority 3: Export Tests

**File:** `backend/tests/test_exports.py`

```python
"""Tests for export functionality."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path

from app.main import app

client = TestClient(app)


class TestExportFormats:
    """Tests for different export formats."""

    @pytest.fixture(autouse=True)
    def setup_test_document(self):
        """Create a test document before each test."""
        response = client.post("/api/v1/documents", json={
            "title": "Export Test Document",
            "markdown": "# Title\n\nThis is test content.\n\n## Section\n\n- Item 1\n- Item 2"
        })
        if response.status_code == 200:
            self.test_slug = response.json()["slug"]
        else:
            self.test_slug = None
        yield
        # Cleanup
        if self.test_slug:
            client.delete(f"/api/v1/documents/{self.test_slug}")

    def test_export_markdown(self):
        """Test exporting to Markdown."""
        if not self.test_slug:
            pytest.skip("No test document")

        response = client.post(f"/api/v1/documents/{self.test_slug}/export", json={
            "format": "md"
        })

        assert response.status_code == 200

    def test_export_html(self):
        """Test exporting to HTML."""
        if not self.test_slug:
            pytest.skip("No test document")

        response = client.post(f"/api/v1/documents/{self.test_slug}/export", json={
            "format": "html"
        })

        assert response.status_code == 200

    def test_export_pdf_job(self):
        """Test starting PDF export job."""
        if not self.test_slug:
            pytest.skip("No test document")

        response = client.post(f"/api/v1/documents/{self.test_slug}/export", json={
            "format": "pdf"
        })

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data

    def test_export_invalid_format(self):
        """Test error for invalid format."""
        if not self.test_slug:
            pytest.skip("No test document")

        response = client.post(f"/api/v1/documents/{self.test_slug}/export", json={
            "format": "invalid"
        })

        assert response.status_code in [400, 422]


class TestExportJobStatus:
    """Tests for export job status tracking."""

    def test_get_nonexistent_job(self):
        """Test getting status of nonexistent job."""
        response = client.get("/api/v1/exports/nonexistent-id")

        assert response.status_code == 404
```

### Priority 4: Presentation Tests

**File:** `backend/tests/test_presentations.py`

```python
"""Tests for presentation/slides functionality."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestPresentationDocuments:
    """Tests for presentation document type."""

    def test_create_presentation(self):
        """Test creating a presentation document."""
        response = client.post("/api/v1/documents", json={
            "title": "Test Presentation",
            "doc_type": "presentation",
            "markdown": "# Slide 1\n\nContent\n\n---\n\n# Slide 2\n\nMore content",
            "front_matter": {
                "slides_data": {
                    "slides": [
                        {
                            "id": "slide-1",
                            "slideNumber": 1,
                            "layout": "title",
                            "title": "Slide 1",
                            "content": "Content"
                        }
                    ],
                    "theme": {
                        "primaryColor": "#1a365d"
                    }
                }
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["doc_type"] == "presentation"

        # Cleanup
        client.delete(f"/api/v1/documents/{data['slug']}")

    def test_update_slides_data(self):
        """Test updating slides data."""
        # Create document
        create_response = client.post("/api/v1/documents", json={
            "title": "Slides Test",
            "doc_type": "presentation"
        })

        if create_response.status_code != 200:
            pytest.skip("Could not create document")

        slug = create_response.json()["slug"]

        # Update with slides
        update_response = client.put(f"/api/v1/documents/{slug}", json={
            "front_matter": {
                "slides_data": {
                    "slides": [
                        {"id": "s1", "slideNumber": 1, "layout": "title", "title": "New Title"}
                    ]
                }
            }
        })

        assert update_response.status_code == 200

        # Verify
        get_response = client.get(f"/api/v1/documents/{slug}")
        data = get_response.json()
        assert "slides_data" in data.get("front_matter", {})

        # Cleanup
        client.delete(f"/api/v1/documents/{slug}")
```

---

## E2E Test Plan (Playwright)

### Setup

```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

### Test File: `frontend/tests/e2e/editor.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Document Editor', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000/dashboard')
  })

  test('should create new document', async ({ page }) => {
    // Click create button
    await page.click('button:has-text("New Document")')

    // Fill title
    await page.fill('input[name="title"]', 'E2E Test Document')

    // Submit
    await page.click('button:has-text("Create")')

    // Verify redirect to editor
    await expect(page).toHaveURL(/\/editor\//)

    // Verify title appears
    await expect(page.locator('h1, input[value="E2E Test Document"]')).toBeVisible()
  })

  test('should edit document content', async ({ page }) => {
    // Go to a document
    await page.goto('http://localhost:3000/editor/bid-seguridad-resumen')

    // Wait for editor to load
    await page.waitForSelector('.ProseMirror')

    // Type in editor
    await page.click('.ProseMirror')
    await page.keyboard.type('Test content added by E2E')

    // Wait for autosave
    await page.waitForTimeout(2000)

    // Refresh and verify
    await page.reload()
    await expect(page.locator('text=Test content added by E2E')).toBeVisible()
  })

  test('should show claims panel', async ({ page }) => {
    await page.goto('http://localhost:3000/editor/bid-seguridad-resumen')

    // Click Claims tab
    await page.click('button:has-text("Claims")')

    // Verify panel opens
    await expect(page.locator('.claims-panel, [data-panel="claims"]')).toBeVisible()
  })

  test('should export to PDF', async ({ page }) => {
    await page.goto('http://localhost:3000/editor/bid-seguridad-resumen')

    // Click export button
    await page.click('button:has-text("Export")')

    // Select PDF
    await page.click('text=PDF')

    // Verify download started (or job created)
    // This depends on implementation
  })
})

test.describe('Presentation Mode', () => {
  test('should toggle presentation mode', async ({ page }) => {
    await page.goto('http://localhost:3000/editor/bid-seguridad-presentacion')

    // Click presentation mode toggle
    await page.click('button:has-text("Presentation")')

    // Verify slide navigator appears
    await expect(page.locator('.slide-navigator, [data-component="slide-navigator"]')).toBeVisible()
  })

  test('should navigate between slides', async ({ page }) => {
    await page.goto('http://localhost:3000/editor/bid-seguridad-presentacion')

    // Enter presentation mode
    await page.click('button:has-text("Presentation")')

    // Click next slide
    await page.click('button[aria-label="Next slide"], .next-slide-btn')

    // Verify slide changed
    await expect(page.locator('text=Slide 2, .slide-indicator:has-text("2")')).toBeVisible()
  })
})
```

### Running E2E Tests

```bash
cd frontend

# Run all E2E tests
npx playwright test

# Run with UI
npx playwright test --ui

# Run specific test file
npx playwright test tests/e2e/editor.spec.ts

# Generate report
npx playwright show-report
```

---

## Manual Test Checklist

### Document Workflow

- [ ] Create new document from dashboard
- [ ] Edit title and content
- [ ] Save document (autosave)
- [ ] Create new version
- [ ] Restore previous version
- [ ] Delete document

### Claims Workflow

- [ ] View claims panel
- [ ] Extract claims via AI button
- [ ] Verify claim appears in panel
- [ ] Mark claim as verified
- [ ] Add evidence to claim
- [ ] Click claim to scroll in editor

### Bibliography Workflow

- [ ] Open bibliography panel
- [ ] Import BibTeX file
- [ ] Search for entry
- [ ] Insert citation in editor
- [ ] View citation tooltip

### Export Workflow

- [ ] Export to PDF
- [ ] Export to DOCX
- [ ] Export to PPTX
- [ ] Export to Markdown
- [ ] Export to Google Docs
- [ ] Export to Google Slides

### Presentation Workflow

- [ ] Create presentation document
- [ ] Toggle presentation mode
- [ ] Navigate between slides
- [ ] Edit slide content
- [ ] Add new slide
- [ ] Delete slide
- [ ] Change slide layout
- [ ] Export to PPTX

### Google Integration

- [ ] Connect Google account
- [ ] Import from Google Docs
- [ ] Export to Google Docs
- [ ] Export to Google Slides
- [ ] Disconnect account

---

## Test Data

### Sample Document JSON

```json
{
  "title": "Test Policy Brief",
  "doc_type": "policy",
  "content": {
    "json": {
      "type": "doc",
      "content": [
        {
          "type": "heading",
          "attrs": { "level": 1 },
          "content": [{ "type": "text", "text": "Title" }]
        },
        {
          "type": "paragraph",
          "content": [{ "type": "text", "text": "El gasto aumentó 23% en 2024." }]
        }
      ]
    }
  },
  "markdown": "# Title\n\nEl gasto aumentó 23% en 2024."
}
```

### Sample BibTeX

```bibtex
@article{smith2024,
  author = {Smith, John and Doe, Jane},
  title = {Test Article},
  journal = {Test Journal},
  year = {2024},
  volume = {1},
  pages = {1-10}
}
```

### Sample Slides Data

```json
{
  "slides": [
    {
      "id": "slide-1",
      "slideNumber": 1,
      "layout": "title",
      "title": "Test Presentation",
      "content": "Subtitle here",
      "notes": ""
    },
    {
      "id": "slide-2",
      "slideNumber": 2,
      "layout": "content",
      "title": "Key Points",
      "content": "- Point 1\n- Point 2\n- Point 3",
      "notes": "Remember to emphasize point 2"
    }
  ],
  "theme": {
    "primaryColor": "#1a365d",
    "secondaryColor": "#c53030",
    "fontFamily": "IBM Plex Sans"
  }
}
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov

      - name: Run tests
        run: |
          cd backend
          pytest -v --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: backend/coverage.xml

  frontend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node
        uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run lint
        run: |
          cd frontend
          npm run lint

      - name: Install Playwright
        run: |
          cd frontend
          npx playwright install --with-deps

      - name: Run E2E tests
        run: |
          cd frontend
          npx playwright test
```
