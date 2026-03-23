# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime.

## Core Architecture
- **Frontend**: React + Shadcn UI (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster gen), APScheduler (background jobs)

## Implemented Features

### Production Pipelines - Flow
**Film**: Creazione > Locandina > Coming Soon > `ready_for_casting` > Casting > Sceneggiatura > Pre-produzione > Shooting > Release
**Serie TV/Anime**: Concept > Locandina > Coming Soon > `ready_for_casting` > Casting > Sceneggiatura > Produzione > Release

### Coming Soon Interactive System
- Pre-Casting Phase with dynamic timer (Short/Medium/Long tiers)
- Dynamic Events via scheduler, Support/Boycott, Speed-Up (credit-based)
- Auto News, Scheduler auto-releases to `ready_for_casting`

### Release Strategy System
- Automatica (+3% guaranteed) vs Manuale (perfect timing = +8%)

### Dynamic Notification System (March 22 2026)
- Notification Engine, Severity Levels, Popup Priority System, Anti-spam, Click Navigation

### Admin Maintenance Tool (March 23 2026)
- **Repair Database**: Logical flow validation + data cleanup (admin only)
- **Diagnose Screenplay**: Shows data types and fields for all screenplay films (debug tool)
- Tab "Manutenzione" in Admin Panel

### Dashboard "Prossimamente"
- Always visible with Coming Soon content, countdown, hype, interactive support/boycott

### Other Systems
- Box office, cinema/infrastructure revenue, cast system
- Social hub: chat, private messages, notifications
- Moderation, leaderboard, contests, challenges

## Critical Bug Fixes (March 23 2026)

### BUG 1: `expandedScreenplay` state missing (ROOT CAUSE of "Qualcosa è andato storto")
- **Problem**: `expandedScreenplay` state was declared in CastingTab but NOT in ScreenplayTab. When rendering film with screenplay text, accessing `expandedScreenplay[f.id]` on undefined caused crash.
- **Fix**: Added `const [expandedScreenplay, setExpandedScreenplay] = useState({})` to ScreenplayTab

### BUG 2: `f.screenplay` might be an object instead of string  
- **Problem**: If screenplay stored as `{text: "...", generated_at: "..."}` (like series format), React throws "Objects are not valid as a React child"
- **Fix**: Defensive rendering: `typeof f.screenplay === 'string' ? f.screenplay : f.screenplay?.text || JSON.stringify(f.screenplay)`

### BUG 3: One bad film crashes entire list
- **Problem**: A single film with corrupt data in the map() crashes the entire ScreenplayTab
- **Fix**: try/catch around each film rendering, with fallback Card showing error + "Scarta" button

### Improved ErrorBoundary
- Now shows actual error message (not just "Qualcosa è andato storto")
- TabErrorBoundary also shows error details

## Known Issues
- (P2) Contest Page mobile layout broken (recurring)

## Backlog
- P1: Chat Evolution - Step 6 (mobile refinement + social quality)
- P1: Marketplace for TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse sui Coming Soon, Eventi globali
- Future: Push notifications (mobile), guerre tra Major
