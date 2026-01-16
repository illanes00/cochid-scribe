# Scribe Implementation Guide

> Step-by-step instructions for implementing remaining features.
> This guide is designed for AI coding assistants (Claude, Codex, etc.)

---

## Prerequisites

Before implementing any feature:

1. **Read the codebase context:**
   ```bash
   cat PROJECT_HANDOVER.md
   cat ARCHITECTURE.md
   cat BACKLOG.json
   ```

2. **Understand the file structure:**
   ```bash
   tree backend/app -I __pycache__
   tree frontend/components
   ```

3. **Check current database state:**
   ```bash
   sqlite3 backend/scribe.db ".schema"
   ```

4. **Run the project locally:**
   ```bash
   # Terminal 1: Backend
   cd backend && source .venv/bin/activate && python run.py

   # Terminal 2: Frontend
   cd frontend && npm run dev
   ```

---

## Feature 1: Auto Claim Extraction on Document Save

### Goal
When a document is saved, automatically extract claims using the LLM and store them.

### Files to Modify

**1. backend/app/api/v1/documents.py**

Find the `update_document` function and add claim extraction:

```python
# Add import at top
from app.api.v1.llm import extract_claims_from_text

@router.put("/{slug}", response_model=DocumentResponse)
async def update_document(
    slug: str,
    data: DocumentUpdate,
    db: Session = Depends(get_db)
):
    # ... existing code to update document ...

    # After saving, extract claims if content changed significantly
    if data.content and data.markdown:
        try:
            # Extract claims using LLM
            claims_response = await extract_claims_from_text(
                text=data.markdown,
                doc_type=document.doc_type
            )

            # Create claim records
            for claim_data in claims_response.get("claims", []):
                claim_id = f"C-{uuid.uuid4().hex[:10]}"
                existing = db.query(Claim).filter(
                    Claim.document_id == document.id,
                    Claim.claim_text == claim_data["text"][:200]
                ).first()

                if not existing:
                    claim = Claim(
                        id=str(uuid.uuid4()),
                        claim_id=claim_id,
                        document_id=document.id,
                        claim_text=claim_data["text"],
                        claim_type=claim_data.get("type", "MIXED"),
                        section=claim_data.get("section"),
                        status="draft"
                    )
                    db.add(claim)

            db.commit()
        except Exception as e:
            # Log but don't fail the save
            print(f"Claim extraction failed: {e}")

    return document
```

### Acceptance Test

```bash
# 1. Update a document via API
curl -X PUT http://localhost:8000/api/v1/documents/test-doc \
  -H "Content-Type: application/json" \
  -d '{"markdown": "El gasto aumentó 23% en 2024. Según datos del BID, Chile invierte 1,43% del PIB."}'

# 2. Check claims were created
curl http://localhost:8000/api/v1/claims/document/test-doc

# Should return claims for the percentages and data
```

---

## Feature 2: Visual Claim Highlighting in Editor

### Goal
Display claim-marked text with a blue highlight in the TipTap editor.

### Files to Modify

**1. frontend/components/editor/TiptapEditor.tsx**

The claim extension is already registered. Ensure CSS is applied:

```tsx
// In the Editor configuration, ensure claim extension is included
import { Claim } from './extensions/claim'

const editor = useEditor({
  extensions: [
    // ... other extensions
    Claim,
  ],
  // ...
})
```

**2. frontend/styles/globals.css**

Add or verify claim highlight styles:

```css
/* Claim highlighting */
.ProseMirror span[data-claim-id] {
  background-color: rgba(59, 130, 246, 0.15);
  border-bottom: 2px solid #3b82f6;
  padding: 2px 0;
  cursor: pointer;
  transition: background-color 0.2s;
}

.ProseMirror span[data-claim-id]:hover {
  background-color: rgba(59, 130, 246, 0.3);
}

.ProseMirror span[data-claim-id].active {
  background-color: rgba(59, 130, 246, 0.4);
}
```

**3. frontend/components/editor/extensions/claim.ts**

Verify the extension renders correctly:

```typescript
import { Mark } from '@tiptap/core'

export const Claim = Mark.create({
  name: 'claim',

  addAttributes() {
    return {
      claimId: {
        default: null,
        parseHTML: element => element.getAttribute('data-claim-id'),
        renderHTML: attributes => {
          if (!attributes.claimId) return {}
          return { 'data-claim-id': attributes.claimId }
        }
      }
    }
  },

  parseHTML() {
    return [{ tag: 'span[data-claim-id]' }]
  },

  renderHTML({ HTMLAttributes }) {
    return ['span', HTMLAttributes, 0]
  }
})
```

### Acceptance Test

1. Open editor at http://localhost:3000/editor/bid-seguridad-resumen
2. Claims should appear with blue highlighting
3. Hovering should increase opacity
4. Clicking should show claim in panel

---

## Feature 3: Asset Model for Images

### Goal
Create database model and API for storing document assets (images).

### Files to Create

**1. backend/app/models/asset.py**

```python
"""Asset model for document images and files."""

from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.session import Base


class Asset(Base):
    """Asset model for storing document images and files."""

    __tablename__ = "assets"

    id = Column(String(36), primary_key=True)
    document_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    size_bytes = Column(Integer, default=0)
    url = Column(String(500), nullable=False)  # Local path or CDN URL
    source_url = Column(String(500), nullable=True)  # Original source (e.g., Google)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Asset {self.filename}>"
```

**2. backend/app/schemas/asset.py**

```python
"""Asset schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class AssetCreate(BaseModel):
    """Schema for creating an asset."""
    filename: str
    mime_type: str
    document_id: str | None = None


class AssetResponse(BaseModel):
    """Schema for asset response."""
    id: UUID
    document_id: UUID | None
    filename: str
    mime_type: str
    size_bytes: int
    url: str
    source_url: str | None
    created_at: datetime

    class Config:
        from_attributes = True
```

**3. backend/app/api/v1/assets.py**

```python
"""Asset API endpoints."""

import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.asset import Asset
from app.schemas.asset import AssetResponse

router = APIRouter(prefix="/assets", tags=["assets"])

UPLOAD_DIR = "uploads/assets"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=AssetResponse)
async def upload_asset(
    file: UploadFile = File(...),
    document_id: str | None = None,
    db: Session = Depends(get_db)
):
    """Upload a new asset."""
    asset_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    filename = f"{asset_id}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    # Save file
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Create record
    asset = Asset(
        id=asset_id,
        document_id=document_id,
        filename=file.filename,
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
        url=f"/uploads/assets/{filename}",
        created_at=datetime.utcnow()
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)

    return asset


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(asset_id: str, db: Session = Depends(get_db)):
    """Get asset by ID."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
    return asset


@router.delete("/{asset_id}")
async def delete_asset(asset_id: str, db: Session = Depends(get_db)):
    """Delete an asset."""
    asset = db.query(Asset).filter(Asset.id == asset_id).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Delete file
    filepath = os.path.join(UPLOAD_DIR, os.path.basename(asset.url))
    if os.path.exists(filepath):
        os.remove(filepath)

    db.delete(asset)
    db.commit()
    return {"status": "deleted"}
```

**4. Update backend/app/models/__init__.py**

```python
from app.models.asset import Asset
from app.models.bibliography import BibliographyEntry
from app.models.claim import Claim
from app.models.comment import Comment
from app.models.dataset import Dataset
from app.models.document import Document
from app.models.document_version import DocumentVersion
from app.models.export import ExportJob
from app.models.integration import Integration
from app.models.note import Note
```

**5. Update backend/app/main.py to include router**

```python
from app.api.v1 import assets
# ... other imports

app.include_router(assets.router, prefix="/api/v1")
```

### Database Migration

```bash
# Run this SQL to create the table
sqlite3 backend/scribe.db <<EOF
CREATE TABLE IF NOT EXISTS assets (
    id VARCHAR(36) PRIMARY KEY,
    document_id VARCHAR(36) REFERENCES documents(id),
    filename VARCHAR(255) NOT NULL,
    mime_type VARCHAR(100) NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    url VARCHAR(500) NOT NULL,
    source_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
```

### Acceptance Test

```bash
# Upload an image
curl -X POST http://localhost:8000/api/v1/assets/upload \
  -F "file=@test-image.png" \
  -F "document_id=your-doc-id"

# Get asset
curl http://localhost:8000/api/v1/assets/{returned-id}
```

---

## Feature 4: Professional PPTX Export with python-pptx

### Goal
Generate high-quality PPTX files with Espacio Público branding.

### Files to Create

**1. backend/app/services/slides_export.py**

```python
"""Professional PPTX export using python-pptx."""

from io import BytesIO
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RgbColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# Espacio Público colors
PRIMARY_COLOR = RgbColor(0x1a, 0x36, 0x5d)    # Dark blue
SECONDARY_COLOR = RgbColor(0xc5, 0x30, 0x30)  # Red
ACCENT_COLOR = RgbColor(0x2b, 0x6c, 0xb0)     # Medium blue


def create_presentation(slides_data: dict) -> BytesIO:
    """
    Create a professional PPTX from slides data.

    Args:
        slides_data: Dict with 'slides' list and 'theme' dict

    Returns:
        BytesIO buffer containing the PPTX file
    """
    prs = Presentation()
    prs.slide_width = Inches(13.333)  # 16:9 aspect
    prs.slide_height = Inches(7.5)

    slides = slides_data.get("slides", [])
    theme = slides_data.get("theme", {})

    for slide_data in slides:
        layout = slide_data.get("layout", "content")

        if layout == "title":
            slide = add_title_slide(prs, slide_data, theme)
        else:
            slide = add_content_slide(prs, slide_data, theme)

    # Save to buffer
    buffer = BytesIO()
    prs.save(buffer)
    buffer.seek(0)
    return buffer


def add_title_slide(prs: Presentation, slide_data: dict, theme: dict):
    """Add a title slide."""
    blank_layout = prs.slide_layouts[6]  # Blank
    slide = prs.slides.add_slide(blank_layout)

    # Background
    background = slide.shapes.add_shape(
        1, 0, 0, prs.slide_width, prs.slide_height
    )
    background.fill.solid()
    background.fill.fore_color.rgb = PRIMARY_COLOR
    background.line.fill.background()

    # Title
    title = slide_data.get("title", "")
    title_box = slide.shapes.add_textbox(
        Inches(1), Inches(2.5), Inches(11.333), Inches(2)
    )
    title_frame = title_box.text_frame
    title_frame.paragraphs[0].text = title
    title_frame.paragraphs[0].font.size = Pt(44)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RgbColor(255, 255, 255)
    title_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    return slide


def add_content_slide(prs: Presentation, slide_data: dict, theme: dict):
    """Add a content slide."""
    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # Header bar
    header = slide.shapes.add_shape(
        1, 0, 0, prs.slide_width, Inches(1)
    )
    header.fill.solid()
    header.fill.fore_color.rgb = PRIMARY_COLOR
    header.line.fill.background()

    # Title
    title = slide_data.get("title", "")
    title_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(0.2), Inches(12), Inches(0.6)
    )
    title_frame = title_box.text_frame
    title_frame.paragraphs[0].text = title
    title_frame.paragraphs[0].font.size = Pt(28)
    title_frame.paragraphs[0].font.bold = True
    title_frame.paragraphs[0].font.color.rgb = RgbColor(255, 255, 255)

    # Content
    content = slide_data.get("content", "")
    content_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(1.3), Inches(12.333), Inches(5.5)
    )
    content_frame = content_box.text_frame
    content_frame.word_wrap = True

    # Parse markdown-like content
    lines = content.split('\n')
    first_para = True

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if first_para:
            p = content_frame.paragraphs[0]
            first_para = False
        else:
            p = content_frame.add_paragraph()

        # Handle bullets
        if line.startswith('- ') or line.startswith('* '):
            p.text = '• ' + line[2:]
            p.level = 0
        elif line.startswith('  - ') or line.startswith('  * '):
            p.text = '  • ' + line[4:]
            p.level = 1
        else:
            p.text = line

        p.font.size = Pt(18)
        p.font.color.rgb = RgbColor(0x1a, 0x20, 0x2c)

    # Footer
    footer_box = slide.shapes.add_textbox(
        Inches(0.5), Inches(7), Inches(4), Inches(0.3)
    )
    footer_frame = footer_box.text_frame
    footer_frame.paragraphs[0].text = "Espacio Público"
    footer_frame.paragraphs[0].font.size = Pt(10)
    footer_frame.paragraphs[0].font.color.rgb = RgbColor(128, 128, 128)

    # Slide number
    num_box = slide.shapes.add_textbox(
        Inches(12), Inches(7), Inches(1), Inches(0.3)
    )
    num_frame = num_box.text_frame
    num_frame.paragraphs[0].text = str(slide_data.get("slideNumber", ""))
    num_frame.paragraphs[0].font.size = Pt(10)
    num_frame.paragraphs[0].font.color.rgb = RgbColor(128, 128, 128)
    num_frame.paragraphs[0].alignment = PP_ALIGN.RIGHT

    return slide
```

**2. Update backend/app/api/v1/exports.py**

Add the python-pptx export option:

```python
from app.services.slides_export import create_presentation

@router.post("/{slug}/export-pptx")
async def export_to_pptx(slug: str, db: Session = Depends(get_db)):
    """Export document as professional PPTX."""
    document = db.query(Document).filter(Document.slug == slug).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Get slides data from front_matter
    front_matter = document.front_matter or {}
    slides_data = front_matter.get("slides_data", {
        "slides": [],
        "theme": {}
    })

    # If no slides, create from content
    if not slides_data.get("slides"):
        # Fallback: convert markdown to basic slides
        slides_data = markdown_to_slides(document.markdown or "")

    # Generate PPTX
    pptx_buffer = create_presentation(slides_data)

    return StreamingResponse(
        pptx_buffer,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f'attachment; filename="{slug}.pptx"'
        }
    )
```

### Install Dependency

```bash
cd backend
pip install python-pptx>=0.6.21
echo "python-pptx>=0.6.21" >> requirements.txt
```

### Acceptance Test

```bash
# Export a presentation
curl -X POST http://localhost:8000/api/v1/exports/bid-seguridad-presentacion/export-pptx \
  -o output.pptx

# Open in PowerPoint or Google Slides
```

---

## Feature 5: TipTap in SlideEditor

### Goal
Replace the textarea in SlideEditor with TipTap for rich content editing.

### Files to Modify

**1. frontend/components/editor/SlideEditor.tsx**

```tsx
'use client'

import { useEditor, EditorContent } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { useEffect } from 'react'

interface Slide {
  id: string
  slideNumber: number
  layout: string
  title: string
  content: string
  notes: string
}

interface SlideEditorProps {
  slide: Slide
  onUpdate: (slide: Slide) => void
}

export default function SlideEditor({ slide, onUpdate }: SlideEditorProps) {
  // TipTap editor for content
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [1, 2, 3] }
      })
    ],
    content: slide.content,
    onUpdate: ({ editor }) => {
      const markdown = editor.storage.markdown?.getMarkdown()
        || editor.getText()
      onUpdate({ ...slide, content: markdown })
    }
  })

  // Update editor when slide changes
  useEffect(() => {
    if (editor && slide.content !== editor.getText()) {
      editor.commands.setContent(slide.content)
    }
  }, [slide.id])

  const layouts = [
    { value: 'title', label: 'Title Slide' },
    { value: 'content', label: 'Content' },
    { value: 'two-column', label: 'Two Column' },
    { value: 'image-full', label: 'Full Image' },
    { value: 'blank', label: 'Blank' }
  ]

  return (
    <div className="flex flex-col h-full p-4 bg-white">
      {/* Slide number and layout */}
      <div className="flex items-center gap-4 mb-4">
        <span className="text-sm text-gray-500">
          Slide {slide.slideNumber}
        </span>
        <select
          value={slide.layout}
          onChange={(e) => onUpdate({ ...slide, layout: e.target.value })}
          className="text-sm border rounded px-2 py-1"
        >
          {layouts.map(l => (
            <option key={l.value} value={l.value}>{l.label}</option>
          ))}
        </select>
      </div>

      {/* Title input */}
      <input
        type="text"
        value={slide.title}
        onChange={(e) => onUpdate({ ...slide, title: e.target.value })}
        placeholder="Slide title..."
        className="text-2xl font-bold mb-4 p-2 border-b focus:outline-none focus:border-blue-500"
      />

      {/* Content editor (TipTap) */}
      <div className="flex-1 border rounded-lg p-4 overflow-auto">
        <EditorContent
          editor={editor}
          className="prose max-w-none min-h-[200px]"
        />
      </div>

      {/* Notes */}
      <div className="mt-4">
        <label className="text-sm text-gray-500 mb-1 block">
          Speaker Notes
        </label>
        <textarea
          value={slide.notes}
          onChange={(e) => onUpdate({ ...slide, notes: e.target.value })}
          placeholder="Notes for this slide..."
          className="w-full h-20 p-2 border rounded text-sm resize-none"
        />
      </div>
    </div>
  )
}
```

### Acceptance Test

1. Open presentation at http://localhost:3000/editor/bid-seguridad-presentacion
2. Click on a slide
3. Edit content with rich formatting
4. Verify changes persist

---

## Running Tests

### Backend Tests

```bash
cd backend
source .venv/bin/activate

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_documents.py -v

# Run with coverage
pytest --cov=app --cov-report=html
```

### Manual API Testing

```bash
# Documents
curl http://localhost:8000/api/v1/documents
curl http://localhost:8000/api/v1/documents/bid-seguridad-resumen

# Claims
curl http://localhost:8000/api/v1/claims/document/bid-seguridad-resumen

# LLM (requires ANTHROPIC_API_KEY)
curl -X POST http://localhost:8000/api/v1/llm/rewrite \
  -H "Content-Type: application/json" \
  -d '{"text": "This is a test.", "style": "academic"}'
```

---

## Deployment

### Local Development

```bash
# Backend
cd backend
python run.py  # http://localhost:8000

# Frontend
cd frontend
npm run dev    # http://localhost:3000
```

### Production Build

```bash
# Backend (already running with systemd)
sudo systemctl restart scribe-backend

# Frontend
cd frontend
npm run build
npm start  # or systemctl restart scribe-frontend
```

### Environment Check

```bash
# Verify backend env
cd backend
cat .env | grep -v "KEY\|SECRET"

# Verify frontend env
cd frontend
cat .env.local
```

---

## Troubleshooting

### Common Issues

1. **"No such table" error**
   - Run database migrations
   - Check scribe.db exists in backend/

2. **CORS errors**
   - Verify CORS_ORIGINS in backend .env
   - Check frontend URL matches

3. **LLM errors**
   - Verify ANTHROPIC_API_KEY is set
   - Check API credits

4. **Google OAuth fails**
   - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
   - Check redirect URI matches exactly

### Debug Commands

```bash
# Check backend logs
journalctl -u scribe-backend -f

# Check frontend logs
journalctl -u scribe-frontend -f

# Test database
sqlite3 backend/scribe.db "SELECT COUNT(*) FROM documents;"

# Test API health
curl http://localhost:8000/api/v1/health
```
