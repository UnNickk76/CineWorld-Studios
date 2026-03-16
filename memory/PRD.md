# CineWorld Studio's - PRD

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o, GPT-Image-1, Emergent LLM Key

## Funzionalità Completate

### Sistema Distribuzione Film (FASE 1)
- Film dopo creazione -> status `pending_release` -> sezione Dashboard SEMPRE visibile
- Popup rilascio: Nazionale ($500K+3CP), Continentale ($1.5M+5CP), Mondiale ($4M+8CP)
- CinePass detratti solo al rilascio

### Studio di Produzione (FASE 2) - VERIFICATO E FUNZIONANTE
- 3 pannelli: Pre-Produzione, Post-Produzione, Agenzia Casting
- Pre-Produzione: bonus film pending + Genera Bozze Sceneggiatura AI
- Post-Produzione: remaster film rilasciati
- Agenzia Casting: pool settimanale talenti scontati + leggendari
- Auto-scroll pannelli su mobile
- **Bug fix critico**: query usavano `user_id` invece di `owner_id` (5 occorrenze corrette)

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

### Bug Fix (Sessione corrente - 16 Mar 2026)
- **CRITICO**: Production Studio `owner_id` fix (5 query backend corrette)
- Dashboard "Film in Attesa" sempre visibile (anche vuota)
- Studio tabs auto-scroll su mobile
- Tutorial aggiornato a 16 step + 3 note di sistema

## Task Prossimi
- **Sistema ruoli Admin (RBAC)** - Sostituire check hardcoded `nickname === 'NeoMorpheus'`
- **Layout mobile pagina Contest** (`/games`) - Issue ricorrente

## Backlog
- Runware Integration (trailer premium)
- CineCoins Purchase (Stripe)
- Conversione PWA
- Tutorial popup per nuovi utenti

## Key DB Schema Note
- **infrastructure collection**: usa `owner_id` (NON `user_id`)
- **films collection**: usa `user_id`
- **studio_drafts collection**: usa `user_id`

## Dominio
- cineworld-studios.it -> Cloudflare DNS -> Emergent Host
