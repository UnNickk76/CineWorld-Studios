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

### Sistema PvP Infrastrutture (v1.0) - NUOVO
- **Quartier Generale (HQ)**: Pagina dedicata /hq per gestire le 3 divisioni PvP
- **Divisione Investigativa**: Indaga sui boicottaggi ricevuti (Lv1: 55%, Lv2: 70%, Lv3: 85% successo)
- **Divisione Operativa**: Boicottaggi difensivi (riduce danni) e offensivi mirati
- **Divisione Legale**: Azioni legali contro sabotatori identificati (richiede Investigativa + fame alta)
- **Upgrade ibridi**: Costi in $ + CinePass con requisiti di livello/fama
- **Daily limits**: Azioni giornaliere basate sul livello della divisione
- **Storico cause legali**: Visualizzazione storico azioni legali
- **Probabilita' causa**: 40 + legal*10 + level*2 + fame*0.3 - opp_legal*8 (15%-85%)
- **Penalita' vittoria**: Avversario perde fondi (max 15%), rallentamento produzione, PvP block 48h
- **Penalita' sconfitta**: Attaccante perde fondi + 2 fama

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
- users: last_cs_reward_at, cinepass, pvp_divisions (investigative/operative/legal con level, daily_used, last_reset)
- film_projects: release_pending, status, release_type, cast, screenplay
- coming_soon_interactions: boycott_type, boycott_name, investigated, revealed_to
- notifications: source, data.event_title, data.event_desc, data.effect_minutes, data.boycott_type
- pvp_actions: attacker_id, target_id, type, target_content_id, effects
- pvp_legal_actions: attacker_id, target_id, content_id, success, probability, penalties
- pvp_blocks: blocked_user, blocked_from_attacking, expires_at

## API Endpoints PvP
- GET /api/pvp/status - Stato divisioni, livelli, limiti, costi upgrade
- POST /api/pvp/upgrade - Migliora divisione (division: investigative|operative|legal)
- POST /api/pvp/investigate - Indaga boicottaggio (content_id)
- POST /api/pvp/counter-boycott - Contro-boicottaggio (content_id, mode: defense|targeted, target_user_id)
- POST /api/pvp/legal-action - Azione legale (target_user_id, content_id)
- GET /api/pvp/legal-history - Storico azioni legali

## Test
- Iter 127: 100% (Film Pipeline UX redesign)
- Iter 128: 100% (Notifiche + Eventi + Boicottaggi)
- Iter 129: 100% (PvP Infrastructure System - Backend 21/21, Frontend 100%)

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime
- Contest Page Mobile Layout Fix (ricorrente)

### P2
- RBAC, CinePass + Stripe, PWA, Tutorial

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
