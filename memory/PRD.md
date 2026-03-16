# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), sfide 1v1, gestione infrastrutture e distribuzione film.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), Emergent LLM Key

## FASE 1 COMPLETATA: Sistema Distribuzione Film (16 Mar 2026)

### Nuovo Flusso Film
1. **Crea Film** → Paghi solo costi produzione (attori, location, ecc.) in CineCoins
2. **Film va in "Attesa di Rilascio"** → Sezione dedicata in Dashboard con badge contatore
3. **Rilascio Film** → Popup distribuzione con 3 zone:
   - Nazionale (solo paese studio): ~$500K + 3 CinePass, 0.4x ricavi
   - Continentale (selezione continente): ~$1.5M + 5 CinePass, 1.0x ricavi
   - Mondiale: ~$4M + 8 CinePass, 2.5x ricavi
4. **CinePass detratti solo al rilascio**, non alla creazione

### Nuovi Endpoint Backend
- `GET /api/films/pending` — Film in attesa di rilascio
- `GET /api/distribution/config` — Zone, paesi, continenti
- `POST /api/films/{id}/release` — Rilascio con zona distribuzione

### Campo Profilo
- `studio_country` (default: IT) — Paese dello studio di produzione (50 paesi)
- Aggiornabile via `PUT /api/auth/profile`

## FASE 2 DA IMPLEMENTARE: Studio di Produzione

### 3 Pannelli nell'Infrastruttura:
1. **Pre-Produzione** — Storyboard, Casting Interno, Scouting Location
2. **Post-Produzione** — Remaster, Director's Cut, Re-editing
3. **Agenzia Casting** — Audizioni settimanali, talenti esclusivi, contratti

## Bug Fix (16 Mar 2026)
- FIX CRITICO: Premio CinePass sfide 1v1 (xp → total_xp)
- FIX: Pareggi falsi skill battle (draw_chance ridotta)
- FIX: Route CinemaJournal /film/ → /films/
- FIX: CinePass update ottimistico
- FIX: Locandine duplicate + nome studio UI
- Trailer generation: "Coming Soon" (FFmpeg non disponibile in prod)

## Task Prossimi
- **FASE 2:** Studio di Produzione (3 pannelli infrastruttura)
- **FASE 3:** Profilo - selezione città studio con dropdown
- Sistema ruoli Admin (RBAC)
- Tutorial popup nuovi utenti

## Backlog
- Runware Integration (trailer premium)
- CineCoins Purchase System (Stripe)
- Conversione PWA

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
