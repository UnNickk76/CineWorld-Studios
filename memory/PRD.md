# CineWorld Studio's - PRD

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Funzionalità Completate

### Sistema Distribuzione Film (FASE 1)
- Film dopo creazione -> status `pending_release` -> sezione Dashboard SEMPRE visibile (max 6)
- Popup rilascio: Nazionale/Continentale/Mondiale con pulsante "Porta in Studio di Produzione"
- Pulsante rapido "IN ATTESA" nella griglia Dashboard con pallino rosso conteggio

### Studio di Produzione (FASE 2) - VERIFICATO
- 3 pannelli: Pre-Produzione, Post-Produzione, Agenzia Casting
- **Bug fix critico**: query `owner_id` invece di `user_id` (5 occorrenze)
- Auto-scroll pannelli su mobile

### Agenzia Casting - MIGLIORATA (16 Mar 2026)
- **Bug fix**: Nomi "Unknown" → nomi reali per nazionalità (Marco Esposito, Julia Pereira, etc.)
- **Nuovo**: Click su talento → popup con due opzioni:
  - "Usa Subito" → aggiunge al cast personale
  - "Invia alla Scuola di Recitazione" → studente con skill pre-esistenti
- Protezione doppio ingaggio settimanale (`casting_hires` collection)

### Cast Filtrato per Livello/Fama (16 Mar 2026)
- `max_stars = min(5, 1 + level // 10)` — Lv1→1 stella, Lv10→2, Lv20→3, Lv30→4, Lv40→5
- `max_fame = min(100, fame + 30)` — Limita accesso ai talenti più famosi
- Applicato a `/cast/search-advanced` e `/cast/available/{type}`

### Integrazione Studio nel Film Wizard (FASE 3)
- Bozze Sceneggiatura AI con CinePass gratis + bonus qualità
- Collection DB: `studio_drafts`

### Tutorial (16 step) + Note di Sistema (3 note)

## Key DB Schema
- **infrastructure**: usa `owner_id` (NON `user_id`)
- **cast_pool**: attori personali con `is_personal_cast: true`, `owner_id`
- **casting_hires**: traccia ingaggi settimanali `{user_id, recruit_id, week, action}`
- **studio_drafts**: bozze sceneggiatura `{user_id, title, genre, quality_bonus, used}`

## Task Prossimi
- Sistema ruoli Admin (RBAC)
- Layout mobile pagina Contest

## Backlog
- Runware Integration, CineCoins Purchase (Stripe), Conversione PWA
- Tutorial popup nuovi utenti
- Refactoring server.py in router separati
