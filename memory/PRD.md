# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Cinematic empire game where players build film studios, produce films, hire cast, and compete on leaderboards.

## Core Architecture
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **AI:** OpenAI GPT-4o-mini (text) + GPT-Image-1 (images) via Emergent LLM Key

## What's Been Implemented (March 18, 2026)
- **Multi-Actor Casting:** Actors stay available after hiring one. Click-to-hire. Renegotiation for rejected actors (+30% cost). 
- **Quality v3 Balanced:** base_mult=4.8, avg ~66% quality.
- **Casting Agency sync fix:** When dismissing a student from acting school, their casting hire record is removed so the recruit becomes available again. Cross-reference check prevents stale "A scuola" badges.
- **Poster performance:** 22 base64 posters extracted to static files with cache headers.
- **Film Detail crash fix:** Missing TrendingDown/RotateCcw imports.
- **source_recruit_id tracking:** Students now store which recruit they came from for proper cleanup.

## Credentials
- User: fandrex1@gmail.com / Ciaociao1

## Upcoming Tasks (P1)
- Pre-engagement system for hired actors
- Casting Agency as new building
- Admin RBAC System
- CinePass cost for speed-ups

## Backlog (P2)
- Refactor server.py, FilmPipeline.jsx, Dashboard.jsx
- Stripe, PWA, Tutorial popup

## Key Files
- `/app/backend/routes/film_pipeline.py` - Pipeline, casting, quality, renegotiate
- `/app/backend/routes/acting_school.py` - Acting school + dismiss with hire cleanup
- `/app/backend/server.py` - Migrations, casting agency, poster serving
- `/app/frontend/src/pages/FilmPipeline.jsx` - Pipeline UI, casting
