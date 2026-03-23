# CineWorld Studio's - Product Requirements Document

## Original Problem Statement
Full-stack cinematic empire game where players create, produce, and release films, TV series, and anime.

## Core Architecture
- **Frontend**: React + Shadcn UI + framer-motion (port 3000)
- **Backend**: FastAPI + MongoDB (port 8001)
- **Integrations**: OpenAI GPT-4o-mini (text), GPT-Image-1 (poster), APScheduler

## Pipeline Flow (Updated March 23 2026)
```
[Idea] → [Trama] → [Location] → [Poster] → [Hype] → [Casting] → [Script] → [Produzione] → [Uscita]
```

### Visual Step Bar (Game Feel)
- 9 animated steps with gold glow, breathing effects, animated connectors
- Completed: green check + gold glow pop animation
- Current: colored breathing glow (CSS custom property --step-glow-color)
- Future: dimmed grey
- Locked (Coming Soon): lock icon + blur + pulse
- Coming Soon active: rotating icon + progress bar animation
- Haptic feedback (navigator.vibrate) on mobile
- Reduced motion support (@media prefers-reduced-motion)

### Film Card Effects
- Mini step bar (7 steps, 3px height) at top of each card
- Hover/tap: translateY(-2px) + gold shadow glow
- film-card-hover class applied to all pipeline cards

### Cinematic Error Handling
- Main ErrorBoundary: film glitch effect with scanlines + grain
  - "La pellicola si è inceppata!" + actual error message
  - "Riprendi la scena" button (pill-shaped)
- TabErrorBoundary: "Scena interrotta" with film icon

### Enhanced Notifications
- Slide from top (framer-motion spring: damping 22, stiffness 350)
- Gradient backgrounds per severity (critical/important/positive)
- Glow shadow matching severity color
- Vibration patterns: critical [50,50,50], normal [25]

### Coming Soon Flow (Fixed)
- Films NO LONGER go backwards to `coming_soon` after shooting
- `choose-release-strategy` → `completed` + `release_pending: true`
- Scheduler auto-releases when timer expires

## CSS Animations (index.css)
- step-complete-pop, step-glow-gold, check-appear
- step-breathe, step-glow-current
- connector-wave (light wave between steps)
- step-locked-pulse
- cs-icon-rotate, cs-countdown-pulse, cs-progress-fill
- card-glow, film-card-hover
- glitch-1, glitch-scanlines, film-grain (error effects)
- notif-slide-in, notif-exit

## Bug Fixes
- Flame icon missing import (March 23)
- expandedScreenplay state missing in ScreenplayTab (March 23)
- f.screenplay as object crash (March 23)
- Coming Soon backwards flow (March 23)

## Known Issues
- (P2) Contest Page mobile layout broken

## Backlog
- P1: Chat Evolution Step 6, Marketplace TV/Anime rights
- P2: RBAC, CinePass + Stripe, PWA, Tutorial, Contest Page fix
- P3: Scommesse Coming Soon, Eventi globali, Push notifications
