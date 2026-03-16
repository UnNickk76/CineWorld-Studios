# CineWorld Studio's - PRD

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Sessione 16 Mar 2026

### Sistema Distribuzione Film (FASE 1 - Completata)
- Film dopo creazione → status `pending_release` → sezione Dashboard "Film in Attesa"
- Popup rilascio: Nazionale ($500K+3CP), Continentale ($1.5M+5CP), Mondiale ($4M+8CP)
- Endpoint: GET /films/pending, GET /distribution/config, POST /films/{id}/release
- CinePass detratti solo al rilascio

### Tutorial Aggiornato
- Aggiunto step 3 "Distribuzione Film" con spiegazione zone
- Rinumerati step successivi (6-15)

### Note di Sistema (Nuovo)
- Pagina `/system-notes` con patch notes/changelog
- Categorie: update, feature, bugfix, event, maintenance
- Priorità: low, normal, high (alta evidenziata)
- Badge unread nel menu laterale
- Admin (NeoMorpheus) può creare/eliminare note
- Endpoint: GET /system-notes, POST /system-notes/mark-read, POST /admin/system-notes

### Bug Fix
- Premio CinePass 1v1 (xp → total_xp)
- Pareggi falsi skill battle
- Route /film/ → /films/ in CinemaJournal
- CinePass update ottimistico
- Locandine duplicate + nome studio UI
- Trailer: "Coming Soon"

## Task Prossimi
- **FASE 2:** Studio di Produzione (3 pannelli: Pre-Produzione, Post-Produzione, Agenzia Casting)
- Profilo: dropdown selezione paese studio (50 paesi)
- Sistema ruoli Admin (RBAC)

## Backlog
- Runware Integration (trailer premium)
- CineCoins Purchase (Stripe)
- Conversione PWA
- Layout Android Chrome

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
