# CineWorld Studio's - PRD

## Original Problem Statement
A cinematic empire game where users produce films, manage TV stations, compete in challenges, and build a Hollywood-style business empire.

## Architecture
- **Frontend**: React (CRA) with Tailwind + Shadcn UI
- **Backend**: FastAPI + MongoDB (Motor async driver)
- **Scheduler**: APScheduler for background tasks
- **AI**: OpenAI GPT-4o-mini (text) + GPT-Image-1 (posters) via Emergent LLM Key

## Completed Features

### Core Game
- Full film/sequel/TV series/anime production pipelines
- TV station management, Cinema Journal, CineBoard, Hall of Fame, Festivals
- Infrastructure, Acting school, Friend system, chat, challenges, leaderboards

### Dynamic Release Events System (Film + Serie TV + Anime)
- **Film**: 19 eventi narrativi (scandalo, successo virale, fenomeno culturale, ecc.)
- **Serie TV**: 16 eventi tematici (Binge Watching Virale, Record Streaming, Spoiler Diffusi, ecc.)
- **Anime**: 15 eventi tematici (Fandom Esplosivo, Sakuga Leggendario, Sensazione Globale, ecc.)
- Tre tipi: positivo/negativo/neutro, 3 livelli rarità
- Modifica qualità e incassi, bias qualità, varianza ±20%
- **Cinematic reveal a 3 fasi** su tutti i contenuti: titolo → evento → risultati
- Animazioni: fadeIn, slideUp, scaleIn, eventReveal, shakeIn (rari), shimmer, countUp

### Poster Management
- Generate/regenerate poster for Film, Series, Anime
- AI Automatica + AI + Prompt personalizzato
- Automatic background generation at release with polling

### Talent Scout System
- Talent Scout Attori + Sceneggiatori
- Purchased screenplays usable in Film Pipeline

### Persistent Release Results (2026-03-21)
- Film Detail page (/films/:id) now displays persistent release results visible to ALL authenticated users
- Shows: Film Tier badge, Key Stats (Quality, Opening Revenue, IMDb, Total Revenue), Quality Modifiers (advanced_factors), Critic Reviews
- Release Event detail (name, description, rarity, type) shows for pipeline-released films
- Color-coded positive/negative modifiers, tier-specific badge styling

### Bug Fixes
- TV Dashboard legacy emittente_tv, Infrastructure unique_types, Scout tabs rendering

## Backlog
- (P1) Readable AI Screenplay (scrollable, accessible post-generation)
- (P1) Free Visual Trailer System (storyboard-style, 3-5 key scenes as images)
- (P1) Guest Star per puntate singole Serie TV
- (P1) Marketplace diritti TV/Anime
- (P2) Fix layout mobile Contest Page
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial
