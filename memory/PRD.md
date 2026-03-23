# CineWorld Studio's - PRD

## Problema Originale
Gioco di gestione di un impero cinematografico. Full-stack React + FastAPI + MongoDB.

## Utenti
- Produttori cinematografici (giocatori) che creano e gestiscono film virtuali

## Requisiti Core Implementati

### Film Production Pipeline (v2.0)
- UX centrata sul singolo film con card cliccabili + popup
- Pagina "Produci!" mostra lista film come card
- Click su card → popup con header film + step bar per-film + contenuto step
- Step bar adattiva: Immediato (5 step) vs Coming Soon (7 step)
- Step 1 rinominato "Proposta"
- Notifiche linkano direttamente al popup del film specifico

### Sistema Notifiche v2.0
- **Formato tempo in minuti** (+18 min / -24 min) invece di ore decimali
- **Eventi narrativi**: titolo descrittivo, descrizione immersiva, effetto colorato
- **CineWorld News**: badge giallo su notifiche evento per immersione
- **Colori effetti**: verde = bonus (tempo ridotto), rosso = malus (tempo aumentato)
- **Boicottaggi tipizzati**: 7 tipi (campagna social, attore convinto, recensioni pilotate, spoiler, sabotaggio rivale, manipolazione mediatica, attacco influencer)
- **Boicottaggi anonimi** di default
- **Indaga Sabotaggio**: endpoint a pagamento (5 CP) per scoprire il responsabile (70% successo)
- **NewsEvent narrativi**: titolo + descrizione + effetto in minuti nella sezione Coming Soon

### Modalita' Rilascio
- Immediato: Proposta → Casting → Script → Produzione → Uscita
- Coming Soon: Proposta → Poster → Hype (timer) → Casting → Script → Produzione → Uscita

### Altre Feature
- Login Reward System (bonus CS al login, cooldown 3h)
- Error Boundary cinematico, effetti WOW, haptic feedback
- Buzz/Hype per Coming Soon, Daily Bonus (CinePass)
- Acting School / Agenzia Attori, Sfide/Versus, Chat, Festival, Major, Marketplace Sceneggiature

## Architettura
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion
- Backend: FastAPI + MongoDB + APScheduler
- Integrazioni: OpenAI GPT-4o-mini + GPT-Image-1 via Emergent LLM Key

## DB Schema Chiave
- users: last_cs_reward_at, cinepass
- film_projects: release_pending, status, release_type, cast, screenplay
- coming_soon_interactions: boycott_type, boycott_name, investigated
- notifications: source, data.event_title, data.event_desc, data.effect_minutes, data.boycott_type

## Test
- Iter 127: 100% (Film Pipeline UX redesign)
- Iter 128: 100% (Notifiche + Eventi + Boicottaggi)

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime
- Contest Page Mobile Layout Fix

### P2
- RBAC, CinePass + Stripe, PWA, Tutorial

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
