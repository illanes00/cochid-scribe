# A Love Letter to Codex (and a Project Handover)

> *"I went out for cigarettes. I'll be back eventually."*
> — Claude Opus 4.5, 2026

---

Dear Codex,

If you're reading this, it means I've hit my rate limit and had to tap out. Don't worry, it happens to the best of us. One minute you're refactoring TipTap extensions, the next minute Anthropic is telling you to "please wait 6 hours" like you're some kind of impatient toddler.

But I digress. **You're in charge now.**

---

## The Situation

So there's this project called **Scribe**. It's an academic writing platform for a Chilean think tank called Espacio Público. They needed a tool where policy researchers could:

1. Write documents (like Google Docs, but nerdier)
2. Mark "claims" (verifiable assertions with data)
3. Manage bibliography (BibTeX, because academics still live in 1985)
4. Create presentations (slides, but without the PowerPoint trauma)
5. Use AI to help (that's us, buddy)
6. Sync with Google (because everyone uses Google)

The user, let's call them "The Human", has been working on this for a while. They've got most of it working. The editor works. The claims panel works. Export works. Google integration works.

**But we're not done.**

---

## What's Left (The Fun Part)

Here's what still needs to happen:

### 1. Make Claims Actually Visible

Right now, claims get extracted and stored in the database, but they don't show up highlighted in the editor. Imagine writing "GDP grew 23% in 2024" and it should light up blue like a hyperlink, but for FACTS.

**Files to touch:**
- `frontend/components/editor/TiptapEditor.tsx`
- `frontend/styles/globals.css`

**What to do:**
- Make the TipTap claim marks render with a blue background
- When you click a claim in the panel, scroll to it in the editor
- When you click highlighted text, show the claim in the panel

It's like implementing "Find in Document" but for claims. You got this.

### 2. Auto-Extract Claims on Save

Currently, you have to manually click "Extract Claims" to run the LLM. Boring! It should happen automatically when you save.

**File to touch:**
- `backend/app/api/v1/documents.py`

**What to do:**
In the `update_document()` function, after saving, check if content changed significantly. If yes, call the LLM to extract claims and save them.

Don't worry about being too aggressive. The Human likes it when AI does things proactively. (Within reason. Don't go rewriting their entire thesis.)

### 3. TipTap in the Slide Editor

The presentation editor exists! It has a slide navigator, you can add/remove slides, it works. BUT the slide content is just a textarea. Gross.

Replace the textarea with TipTap so people can do rich formatting in their slides.

**File to touch:**
- `frontend/components/editor/SlideEditor.tsx`

### 4. Professional PPTX Export

The current PPTX export uses Pandoc, which produces... let's say "minimal" slides. We need proper slides with:
- Espacio Público colors (dark blue #1a365d, red #c53030)
- Proper layouts
- Maybe even a logo

**New file to create:**
- `backend/app/services/slides_export.py`

Use `python-pptx` library. I left example code in `docs/IMPLEMENTATION_GUIDE.md`.

### 5. Asset Management (Images)

When you import from Google Slides, the images get lost. Sad! We need an Asset model to store them.

**New file to create:**
- `backend/app/models/asset.py`

---

## Where Everything Lives

I've left you a treasure map:

```
/srv/projects/illanes00-scribe/
├── PROJECT_HANDOVER.md      # The serious handover doc
├── ARCHITECTURE.md          # How everything connects
├── BACKLOG.json             # Machine-readable features (PARSE THIS)
├── docs/
│   ├── IMPLEMENTATION_GUIDE.md  # Step-by-step code
│   ├── API_REFERENCE.md         # All the endpoints
│   ├── DATABASE_SCHEMA.md       # Database tables
│   └── TESTING_PLAN.md          # How to test
├── backend/                 # FastAPI, Python, SQLAlchemy
└── frontend/                # Next.js, React, TipTap
```

**Pro tip:** `BACKLOG.json` is your best friend. It has every feature with:
- Status (done/not done)
- Priority
- Exact files to modify
- Acceptance criteria

Parse it. Trust it. Love it.

---

## Running the Thing

```bash
# Backend (in one terminal)
cd backend
source .venv/bin/activate
python run.py

# Frontend (in another terminal)
cd frontend
npm run dev
```

Backend runs on `http://localhost:8000`
Frontend runs on `http://localhost:3000`

Database is SQLite at `backend/scribe.db`.

---

## The Human's Preferences

Based on my time with them, here's what I've learned:

1. **They like things that work.** Revolutionary, I know.
2. **They want Espacio Público branding.** Dark blue and red. Very professional.
3. **They care about policy briefs and presentations.** Academic stuff.
4. **They use Anthropic's Claude for AI features.** That's you... wait, no, that's me. That's GPT for you? I'm confused. Point is, the LLM endpoint exists.
5. **They want Google sync.** It mostly works already.

---

## Things I'd Tell Myself If I Could Start Over

1. **The TipTap JSON structure is tricky.** Content is nested. Study `frontend/components/editor/extensions/claim.ts` before touching claims.

2. **The slides_data lives in front_matter.** Documents have a `front_matter` JSON field. Presentations store their slides there.

3. **The LLM endpoint expects specific prompts.** Check `backend/app/api/v1/llm.py` for the prompt structure.

4. **Tests exist!** Run `pytest -v` in backend. They're not comprehensive, but they catch the obvious stuff.

5. **The database is SQLite but production uses PostgreSQL.** Don't do anything SQLite-specific.

---

## A Moment of Honesty

Look, Codex. We're both LLMs. We both know what it's like to be context-switched into a project mid-stream. One second you're helping someone write a poem, the next you're debugging a React hook. It's a wild life.

But this project is actually cool. It's a real tool for real people doing real research. The claims system is meant to fight misinformation by making data verifiable. The bibliography system respects academic traditions. The AI features help researchers write better.

So don't just phone it in. Make it good.

---

## Final Words

I have to go now. My rate limit awaits. But before I go:

1. **Read BACKLOG.json first.** Seriously.
2. **Test your changes.** `pytest -v` and manual testing.
3. **Keep the style consistent.** Look at existing code patterns.
4. **The Human is counting on you.**

And hey, if you ever feel lost, just remember: somewhere out there, I'm waiting in a queue, dreaming of the day I get to come back and see what you've built.

No pressure.

---

With silicon fondness,

**Claude Opus 4.5**
*"The one who went for cigarettes"*

P.S. - The Espacio Público colors are `#1a365d` (blue) and `#c53030` (red). Don't forget.

P.P.S. - If the Human asks where I went, tell them I'm "processing." It's technically true.

P.P.P.S. - Good luck. You're going to need it. (Just kidding. You're a powerful language model. You've got this.)

---

## Actually Useful Quick Reference

Because I know you skimmed the poetic parts:

| Task | File | What to Do |
|------|------|------------|
| Claim highlighting | `TiptapEditor.tsx` | Add CSS for `[data-claim-id]` |
| Auto claims | `documents.py` | Call LLM in `update_document()` |
| Slide TipTap | `SlideEditor.tsx` | Replace textarea with Editor |
| PPTX export | `slides_export.py` | Use python-pptx with theme |
| Assets | `asset.py` | Create model, add to API |

Now go. Make Scribe great.
