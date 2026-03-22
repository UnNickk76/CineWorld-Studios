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

### Admin Panel - User & Film Management (2026-03-22)
- Tabbed admin panel with "Gestione Utenti" and "Gestione Film" sections
- **User Management**: List all users, search by username, select user to view/edit funds/CinePass, delete user with cascade (all associated data: films, series, infrastructure, friendships, follows, likes, ratings, notifications, poster files)
- **Film Management**: Ultra-compact grid (16/row desktop, 12 tablet, 8 mobile) with mini poster thumbnails, title, studio name, quality % badge. Search by title. Delete with trash icon + confirmation modal
- Confirmation modal before any deletion ("Confermi eliminazione definitiva?")
- Admin self-deletion prevention
- Backend endpoints: DELETE /api/admin/delete-user/{user_id}, GET /api/admin/all-films, DELETE /api/admin/delete-film/{film_id}
- Also includes automated cleanup endpoints: GET/POST /api/admin/cleanup-test-data/preview|execute
- Testing: 19/19 backend tests + all frontend UI tests PASSED (iteration 112)

### CineBoard Social + Like System (2026-03-22)
- **Social Feed** (`/social?view=social-feed`): Compact grid of ALL released films (responsive: ~9/row mobile, ~19/row desktop via CSS `min(85px, 11vw)`)
- Each card: mini poster, studio name overlay, like counter with heart icon, quality %, clickable to film detail
- **Like System**: One like per user per film (toggle). DB: `likes` collection with unique index `(film_id, user_id)`. Prevents self-like. Tracks `total_likes_given` and `total_likes_received` on users
- **Gameplay Bonuses**: Film attendance bonus `log(avg_likes + 1) / 100` in cinema revenue calculation. Player bonus `log(likes_given + 1)` for global engagement
- **Top Liked Leaderboard** (`/social?view=top-liked`): Films ranked by likes_count (top 50), shows rank badges, like bonus %
- **My Bonuses**: `GET /api/social/my-bonuses` returns like stats and bonus percentages
- **CineBoard Menu**: Added "Social" and "Top Liked" entries in the navbar popup under new "Social" section
- **Dashboard micro-copy**: Pink CTA card "Interagisci con altri player: metti like ai film per supportarli e ottenere piccoli bonus!"
- Testing: 100% backend + 100% frontend PASSED (iteration 113). Bug fixed: KeyError on films without user_id

### Chat Social System Evolution (2026-03-22)
**Step 1 - Stanze Pubbliche + Lista Utenti:**
- 4 stanze tematiche: Generale, Produzioni, Strategie, Off-topic (con icone e descrizioni)
- Nuovo endpoint `GET /api/users/presence` con stato 3 livelli (online/recent/offline)
- Lista utenti laterale scrollabile con indicatori presenza (verde/giallo/rosso)
- Layout mobile-first con pannelli slide-in (breakpoint md: 768px)

**Step 2 - Profilo Social Rapido:**
- Nuovo endpoint leggero `GET /api/users/{user_id}/social-card` (user info + 12 film + friend status)
- Modal con avatar, studio, livello, presenza, 3 action buttons (Messaggio/Profilo/Amicizia)
- Griglia 6 colonne mini locandine con cuoricino Like funzionale
- Testing: 100% PASSED (iteration 114)

**Step 3 - Chat Privata 1:1:**
- DM system (pre-existing) migliorato: sort per ultimo messaggio, timestamp visibili
- Tab Private con badge contatore, anteprima messaggi, avatar + presenza
- Creazione DM idempotente, messaggi persistenti e recuperabili
- Testing: 100% PASSED (iteration 115)

**Step 4 - Invio Immagini in Chat:**
- `POST /api/chat/upload-image`: upload JPG/PNG/WEBP, max 5MB, validazione MIME
- Storage: disk + MongoDB per persistenza cross-deployment
- `GET /api/chat-images/{filename}`: serving con cache 7 giorni
- Frontend: pulsante upload immagine nella input area, preview in chat, click → fullscreen viewer
- Validazione client-side + server-side (tipo file + dimensione)

**Bug Fix - Chat Mobile:**
- Breakpoint cambiato da lg (1024px) a md (768px)
- Pannelli laterali come overlay slide-in su mobile (max 75vw, 220px)
- overflow-x-hidden sul container, overflow-hidden sull'area principale
- Chat fullwidth su mobile, input sempre visibile

### Moderation/Reporting System (2026-03-22)
- **Backend**: POST /api/reports (create report for message/image/user), GET /api/admin/reports (admin-only, filter by status), POST /api/admin/reports/{id}/resolve (dismiss or delete_content)
- Duplicate report prevention (same reporter + target type + target_id)
- Snapshot of reported content stored in report document
- Soft deletion: moderated messages get content replaced + image_url nulled
- **Frontend ChatPage**: "Segnala" button on hover for other users' messages/images, ReportModal with reason textarea
- **Frontend UserProfileModal**: "Segnala Utente" button for reporting users
- **Frontend AdminPage**: New "Segnalazioni" tab with filter buttons (In attesa/Risolte/Archiviate/Tutte), report cards with type/status badges, snapshot preview, "Rimuovi Contenuto" and "Archivia" action buttons
- Testing: 16/16 backend + 13/13 frontend tests PASSED (iteration 116)

### Notification System - Like & DM (2026-03-22)
- **Like notifications**: When a user likes another's film, owner gets notified ("X ha messo like al tuo film") with link to film detail page
- **Private message notifications**: When a DM is sent, recipient gets notified ("Messaggio da X") with content preview and link to /chat
- **Throttling**: Only 1 unread DM notification per sender (no spam for multiple messages)
- **New NOTIFICATION_TYPES**: Added `like` (heart/red) and `private_message` (message-square/blue) to social_system.py
- **NotificationsPage**: Added icons and smart navigation for `like` → `/films/{id}` and `private_message` → `/chat`
- **Existing infra reused**: Bell icon + badge count + read/unread states + delete all already functional

### Bug Fixes
- TV Dashboard legacy emittente_tv, Infrastructure unique_types, Scout tabs rendering
- Like endpoint: safe handling of films without user_id (orphan films)
- Chat mobile: pannelli laterali fuori schermo su mobile (breakpoint fix)

## Backlog
- (P0) Chat Evolution Step 6: Rifinitura mobile e qualita social
- (P1) Readable AI Screenplay (scrollable, accessible post-generation)
- (P1) Marketplace diritti TV/Anime
- (P2) Fix layout mobile Contest Page
- (P2) RBAC, CinePass, Stripe, PWA, Tutorial
