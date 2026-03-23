# CineWorld Studio's - PRD

## Problema Originale
Gioco di gestione di un impero cinematografico. Full-stack React + FastAPI + MongoDB.

## Utenti
- Produttori cinematografici (giocatori) che creano e gestiscono film virtuali

## Requisiti Core Implementati

### Film Production Pipeline (Completato - v2.0)
- **Vecchia UI (rimossa):** Navigazione a schede (Creation, Proposals, Casting, etc.)
- **Nuova UI (v2.0):** UX centrata sul singolo film con card cliccabili + popup
  - Pagina "Produci!" mostra lista film in produzione come card
  - Click su card → popup con header film + step bar per-film + contenuto step corrente
  - Step bar adattiva: Immediato (5 step) vs Coming Soon (7 step)
  - Step 1 rinominato "Proposta"
  - Notifiche linkano direttamente al popup del film specifico (?film=id)
  
### Modalita' Rilascio
- **Immediato:** Proposta → Casting → Script → Produzione → Uscita
- **Coming Soon:** Proposta → Poster → Hype (timer) → Casting → Script → Produzione → Uscita

### Altre Feature Completate
- Login Reward System (bonus Coming Soon al login, cooldown 3h)
- Error Boundary cinematico con effetto glitch
- Effetti WOW (animazioni, glow, haptic feedback)
- Sistema Buzz/Hype per film Coming Soon
- Daily Bonus (CinePass giornaliero)
- Acting School / Agenzia Attori
- Sistema Sfide/Versus
- Chat Privata
- Festival del Cinema
- Sistema Major
- Marketplace Sceneggiature Emergenti

## Architettura

### Frontend
- React + Tailwind CSS + Shadcn/UI
- Framer Motion per animazioni
- Componenti chiave:
  - `/pages/FilmPipeline.jsx` - Pagina principale produzione (refactored v2.0)
  - `/components/FilmPopup.jsx` - Popup film con step bar e contenuti
  - `/components/FilmProductionCard.jsx` - Card film per la lista

### Backend
- FastAPI + MongoDB + APScheduler
- Route principali in `/backend/routes/`
- Scheduler in `/backend/scheduler_tasks.py`

### Integrazioni
- OpenAI GPT-4o-mini (generazione testo) via Emergent LLM Key
- OpenAI GPT-Image-1 (generazione locandine) via Emergent LLM Key

## DB Schema Chiave
- `users`: last_cs_reward_at (timestamp cooldown login reward)
- `film_projects`: release_pending (boolean), status, release_type, cast, screenplay, etc.

## Stato Test
- Testing Agent Iter 127: 100% backend (16/16), 100% frontend
- Test account: test@test.com / test1234

## Backlog Prioritizzato

### P0 - Nessuno (tutto funzionante)

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime
- Contest Page Mobile Layout Fix (bug ricorrente)

### P2
- RBAC (Role Based Access Control)
- CinePass + Stripe (monetizzazione)
- PWA (Progressive Web App)
- Tutorial interattivo

### P3
- Scommesse sui Coming Soon
- Eventi globali
- Push notifications
- Guerre tra Major
