# CineWorld Studio's - PRD

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Sessione 16 Mar 2026

### Sistema Distribuzione Film (FASE 1 - Completata)
- Film dopo creazione -> status `pending_release` -> sezione Dashboard "Film in Attesa"
- Popup rilascio: Nazionale ($500K+3CP), Continentale ($1.5M+5CP), Mondiale ($4M+8CP)
- Endpoint: GET /films/pending, GET /distribution/config, POST /films/{id}/release
- CinePass detratti solo al rilascio

### Tutorial Aggiornato
- Aggiunto step 3 "Distribuzione Film" con spiegazione zone
- Rinumerati step successivi (6-15)

### Note di Sistema (Nuovo)
- Pagina `/system-notes` con patch notes/changelog
- Categorie: update, feature, bugfix, event, maintenance
- Badge unread nel menu laterale
- Admin (NeoMorpheus) può creare/eliminare note

### Bug Fix (Sessione precedente)
- Premio CinePass 1v1 (xp -> total_xp)
- Pareggi falsi skill battle
- Route /film/ -> /films/ in CinemaJournal
- CinePass update ottimistico
- Locandine duplicate + nome studio UI
- Trailer: "Coming Soon"

### Studio di Produzione - FASE 2 (Completata)
- 3 pannelli in `ProductionStudioPanel.jsx`: Pre-Produzione, Post-Produzione, Agenzia Casting
- **Pre-Produzione:** Applica bonus (storyboard +qualità, casting -costi attori, scouting -costi location) a film pending
- **Post-Produzione:** Remaster film rilasciati (+qualità, +IMDb rating)
- **Agenzia Casting:** Pool settimanale di talenti con sconti, possibilità di leggendari
- Backend: GET /production-studio/status, POST /pre-production/{id}, POST /remaster/{id}, GET /casting
- Upgrade: livelli 1-10, ogni livello migliora bonus e sblocca più funzionalità

### Integrazione Studio nel Film Wizard - FASE 3 (Completata)
- **Bozze Sceneggiatura:** Genera bozze AI dal Pre-produzione ($280K-$1M)
- **Backend:** POST /production-studio/generate-draft, GET /production-studio/drafts, DELETE /production-studio/drafts/{id}
- **Film Creation:** POST /films accetta `studio_draft_id` -> CinePass gratis + bonus qualità (+4 a +13%)
- **Frontend:** FilmWizard Step 1 mostra bozze disponibili con selezione interattiva
- Bozze pre-compilano titolo, genere, sottogeneri, sceneggiatura
- Limite bozze: 3 + livello studio
- Collection DB: `studio_drafts` (id, user_id, title, genre, synopsis, quality_bonus, used, created_at)

## Profilo
- Dropdown selezione paese studio (50 paesi) - Completato

## Task Prossimi
- **Layout mobile pagina Contest** (`/games`) - Issue ricorrente da fork precedenti
- Sistema ruoli Admin (RBAC)

## Backlog
- Runware Integration (trailer premium)
- CineCoins Purchase (Stripe)
- Conversione PWA
- Layout Android Chrome
- Tutorial popup per nuovi utenti

## Dominio
- cineworld-studios.it -> Cloudflare DNS -> Emergent Host
