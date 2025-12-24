# Patent Editor Client

## TL;DR

- Run the frontend: `npm install && npm run dev`
- Features:
  - Load, edit, save, and create document versions.
  - AI-powered rephrase for selected text.
  - AI analysis of the document with quality score and issues.
  - Real-time AI suggestions via WebSocket.
- Ensure backend runs at `http://localhost:8000`.

---

## Overview

React-based UI for managing patent documents with AI support. Key functionality includes version control, document editing, AI-assisted rewriting, analysis, and live suggestions.

---

## Project Layout
```
src
├── App.tsx                 # Main app logic & AI integration
├── Document.tsx            # Editor with WebSocket AI suggestions
├── internal
│ ├── Editor.tsx            # Rich text editor
│ ├── LoadingOverlay.tsx
├── assets                  # Images
├── utils                   # Utilities (e.g., showToast)
└── main.tsx                # Entry point
```
---

## Setup

1. Install dependencies:
    > npm install

1. Run the frontend:

    > npm run dev

Ensure the backend is running at http://localhost:8000.

## Features

- **Document Management:** Load patents, switch versions, save edits, create new versions.

- **AI Rephrase:** Highlight text to request AI rewriting; approve/reject changes.

- **AI Analysis:** Analyze full document for quality score and problem areas.

- **Real-time Suggestions:** Live AI feedback via WebSocket.

- **UI:** Collapsible panels for AI features and loading overlays during operations.