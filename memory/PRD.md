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

### TV Station System Refactor (2026-03-21)
- Auto-provisions tv_station from emittente_tv infrastructure using infrastructure custom_name
- Infrastructure level determines schedule capacity (Lv.1: 3 film, 2 serie, 2 anime = 7 total)
- Dashboard "Le Mie TV" navigates directly to station page (no popup for single station)
- /my-tv route redirects to new TV station system
- Station page shows level, capacity, content counts per category
- Eliminated legacy_stations system

### Series/Anime Release & Poster Bug Fixes (2026-03-22)
- Fixed poster generation: n=1 → number_of_images=1, b64_json → raw bytes (both series and film)
- Consolidated series release to single DB update (was two, causing inconsistency on failure)
- Aligned series/anime release pattern with film release (immediate response, poster in background)
- Added 60s timeout on frontend release call
- Verified: Series release returns complete data (quality, episodes, audience, revenue, release_event, poster_generating)
- Verified: Poster generated in background and accessible via /api/posters/series_{id}.png

### Dynamic Release Images (2026-03-22)
- 3 static images: cinema_flop.jpg, cinema_normal.jpg, cinema_success.jpg
- Backend returns release_outcome and release_image based on quality score (<55=flop, 55-75=normal, >75=success)
- Full-width image at top of release modal with overlay text
- Visual effects: success=zoom+glow+warm, flop=fade+desaturated+cold, normal=static
- Mobile-optimized with scrollable modal

### Cinematic Release Experience (2026-03-22)
- 5-phase cinematic release: Intro → Trailer → Event → Animated Numbers → Final Result
- Phase 1 (Intro): Cinema image + "Il tuo film sta uscendo nelle sale..." with slow animation
- Phase 2 (Visual Trailer): Slideshow of screenplay scenes (3-5 key excerpts) with fade transitions
- Phase 3 (Event Reveal): Dynamic release event card with animations
- Phase 4 (Animated Numbers): Quality, IMDb, Opening Revenue counting up progressively + tier badge
- Phase 5 (Final Result): Outcome message + modifiers + costs + action buttons
- Hype system: hype_level derived from buzz + soundtrack + sponsors, displayed during intro
- Backend returns screenplay_scenes and hype_level in release response

### Series/Anime Detail Page + Posters (2026-03-22)
- New /series/:id detail page reusing FilmDetail structure
- GET /api/series/{series_id} endpoint returns full series data + owner info
- Shows: poster, title, genre, stats (quality/rating/revenue/audience), tier badge, release event, cast, quality breakdown, audience comments, production info
- Poster pre-release: "Genera Locandina" button during production phase
- Poster post-release: "Rigenera Locandina" button on detail page
- Series cards in pipeline are now clickable → navigate to /series/:id
- Route added in App.js for /series/:id

### Production Speed-Up for Series/Anime (2026-03-22)
- POST /api/series-pipeline/{id}/speed-up-production reduces remaining time by 30%
- Stackable (multiple clicks allowed)
- CinePass cost: 15 CP (<=8 ep), 20 CP (<=16 ep), 25 CP (>16 ep)
- UI: "Accelera Produzione" button with cost during active production phase
- Reuses existing series production_duration_minutes system

### Bug Fixes
- TV Dashboard legacy emittente_tv, Infrastructure unique_types, Scout tabs rendering

## Backlog
- (P1) Readable AI Screenplay (scrollable, accessible post-generation)
- (P1) Free Visual Trailer System (storyboard-style, 3-5 key scenes as images)
- (P1) Guest Star per puntate singole Serie TV
- (P1) Marketplace diritti TV/Anime
- (P2) Fix layout mobile Contest Page
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial
