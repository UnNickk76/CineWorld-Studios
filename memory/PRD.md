# CineWorld Studio's - PRD

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Funzionalità Completate

### Sistema Distribuzione Film (FASE 1)
- Film dopo creazione -> status `pending_release` -> sezione Dashboard sempre visibile
- Popup rilascio: Nazionale ($500K+3CP), Continentale ($1.5M+5CP), Mondiale ($4M+8CP)
- CinePass detratti solo al rilascio

### Studio di Produzione (FASE 2)
- 3 pannelli: Pre-Produzione, Post-Produzione, Agenzia Casting
- Pre-Produzione: bonus film pending + Genera Bozze Sceneggiatura AI
- Post-Produzione: remaster film rilasciati
- Agenzia Casting: pool settimanale talenti scontati + leggendari
- Auto-scroll pannelli su mobile

### Integrazione Studio nel Film Wizard (FASE 3)
- Bozze disponibili in Step 1 Film Wizard
- CinePass gratis + bonus qualità (+4 a +13%)
- Pre-compila titolo, genere, sottogeneri, sceneggiatura
- Collection DB: `studio_drafts`

### Tutorial (16 step)
- Step 2: tutti i 12 passaggi creazione film
- Step 12: Studio di Produzione
- Step 3: Distribuzione Film dettagliata

### Note di Sistema
- 3 note pubblicate: Studio, Bozze, Tutorial
- Pagina `/system-notes` con categorie

### Bug Fix (Sessione corrente)
- Dashboard "Film in Attesa" sempre visibile (anche vuota)
- Studio tabs auto-scroll su mobile

### Bug Fix (Sessioni precedenti)
- Premio CinePass 1v1 (xp -> total_xp)
- Pareggi falsi skill battle
- Route /film/ -> /films/ in CinemaJournal
- CinePass update ottimistico
- Locandine duplicate + nome studio UI
- Trailer: "Coming Soon"

## Task Prossimi
- **Layout mobile pagina Contest** (`/games`) - Issue ricorrente
- **Sistema ruoli Admin** (RBAC)

## Backlog
- Runware Integration (trailer premium)
- CineCoins Purchase (Stripe)
- Conversione PWA
- Tutorial popup per nuovi utenti

## Dominio
- cineworld-studios.it -> Cloudflare DNS -> Emergent Host
