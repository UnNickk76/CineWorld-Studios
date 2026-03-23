# CineWorld Studio's - PRD

## Problema Originale
Gioco di gestione di un impero cinematografico. Full-stack React + FastAPI + MongoDB.

## Requisiti Core Implementati

### Film Production Pipeline (v2.0)
- UX centrata sul singolo film con card cliccabili + popup
- Step bar adattiva: Immediato (5 step) vs Coming Soon (7 step)
- Fix: ready_for_casting gestito correttamente anche senza release_type

### Sistema Notifiche v2.0
- Formato tempo in minuti, eventi narrativi, CineWorld News
- Routing PvP: notifiche legali e contro-attacchi puntano a /hq

### Sistema PvP Infrastrutture (v2.0)
- **Acquisto**: Dalla board Infrastrutture (non da HQ)
  - Divisione Operativa: Lv.2, $300K, 3 CP
  - Divisione Investigativa: Lv.3, $500K, 5 CP
  - Divisione Legale: Lv.5, Fame 60, $1M, 10 CP (richiede Investigativa)
- **Gestione/Upgrade**: Dal Quartier Generale (/hq)
  - Lv.0 mostra "Acquista da Infrastrutture" (redirect)
  - Lv.1+ mostra upgrade a livelli successivi
- **Azioni PvP in Coming Soon**: Indaga, Difesa, Attacca, Causa
- **Bottom Navbar**: Icona "Sfide" (Target, rossa) distinta da top nav (Swords)
- **Storico cause legali** con dettagli vittoria/sconfitta

### Fame System
- Valori sempre interi (int), mai decimali
- Auto-fix per fame=0 su giocatori con film completati
- Endpoint /player/recalculate-fame per ricalcolo manuale

### Cast Skills UI (Ripristinata)
- Stelle, badge fama, eta, film count, agenzia, nazionalita
- Toggle "Mostra Skill" con griglia skill colorate (verde/giallo/rosso)

### Tutorial V2.0
- TutorialPopup.jsx riutilizzabile con 16 step
- Bottone "Come si gioca?" nella pagina login/registrazione
- Contenuto completo: Proposta > Distribuzione > PvP > Social

### Copy Login
- Sottotitolo coinvolgente sotto CINEWORLD STUDIO'S
- Marketplace label "Prossimamente" (non "In pausa")

### Festival System Overhaul v3.0 (NEW)
**Backend:**
- Nuove categorie: Miglior Produzione, Miglior Sorpresa (Best Surprise)
- Nomination automatica multi-fattore: qualita 35%, soddisfazione 25%, revenue 15%, likes 15%, cast skills 10%
- "Best Surprise" score: qualita effettiva vs attesa (film sorprendenti)
- Voto pesato per livello/fama del giocatore (1 + level*0.1 + fame*0.005)
- Limite giornaliero voti: 3 base + 1 ogni 5 livelli (max 15)
- Premio Palma d'Oro CineWorld: assegnato a Best Film al Golden Stars
  - Bonus permanente: +2% qualita futuri film, +1% hype
  - Salvato in collection iconic_prizes
- CinePass nei premi: Golden Stars +5 CP, Spotlight +2 CP, Excellence +2 CP
- Endpoint /api/festivals/countdown: countdown con nomination preview e Palma d'Oro flag
- Endpoint /api/festivals/history: storico edizioni con vincitori
- Endpoint /api/player/iconic-prizes: premi iconici e bonus permanenti
- Endpoint /api/player/{id}/badges: badge per profilo (premi + iconici)
- Festival custom: richiede denaro + 3 CinePass per la creazione

**Frontend:**
- Countdown banners pre-evento con timer real-time (G/O/M/S)
- Golden Stars evidenziato con bordo dorato e label Palma d'Oro
- Nomination preview nei countdown
- CinePass visibile nei premi (+5 CP, +2 CP)
- Tab "Storico" per consultare edizioni passate
- Voto pesato: messaggio "Voto pesato per livello e fama"
- Voti rimanenti giornalieri visibili
- Envelope Reveal animation per cerimonia live
- Festival custom mostra costo CinePass nella creazione

### CRITICAL BUG FIX: Coming Soon Film Disappearing (v3.1 + v3.2)
- **Root Cause 1**: `/film-pipeline/all` excluded `completed` status → film spariva dopo auto-completion scheduler
- **Root Cause 2**: `/films/{id}` solo collection `films`, non `film_projects` → "non disponibile"
- **Root Cause 3**: Notification links errati → `/films/{id}` invece di `/create-film?film={id}`
- **Root Cause 4**: Count/list mismatch
- **Root Cause 5**: Scheduler impostava `completed` senza passare dal casting (no flag `coming_soon_type`)
- **Fixes v3.1**: Pipeline query include tutto tranne discarded/abandoned, `/films/{id}` fallback, fix notifiche, auto-advance endpoint
- **Fixes v3.2**: 
  - `/film-pipeline/all` ora mostra TUTTI i film (anche `completed`)
  - Rescue aggressivo: scansiona TUTTI i film e recupera quelli persi
  - Auto-rescue: se pipeline vuota, chiama rescue automaticamente
  - **Admin Panel**: sezione "Recupero Film Persi" per nickname specifico
  - `/admin/repair-database`: aggiunto case "completed senza produzione"
  - Scheduler riconosce pre-casting anche senza flag (controlla assenza cast/shooting)
- **Fixes v3.4 (DEFINITIVO)**:
  - Logica rescue riscritta: condizione chiave = `completed SENZA shooting_started_at` (non piu basata su director)
  - Cattura anche `auto_released: True` (scheduler) indipendentemente dalla presenza cast
  - Pulizia dati fake: `$unset` di quality_score, total_revenue, audience_rating, auto_released, release_pending
  - Auto-rescue su OGNI caricamento di "Produci" (non solo quando lista vuota)
  - Testato E2E: film con director MA senza shooting → correttamente recuperato
  - Film legittimi con shooting → correttamente ignorati

### Velion AI Assistant (v5.0 - Smart Advisor)
- **Pannello con 2 Tab**: Tutorial (16 step immersivi) + "Chiedi a Velion" (chat AI)
- **Chat AI**: GPT-4o-mini, personalita misterioso/cifrato, metafore cinematografiche, 2-3 frasi
- **Quick Ask Chips**: 5 domande rapide + "Lo sapevi?" tips button
- **ADVISOR SINGOLO (v5)**: Un solo suggerimento alla volta, il piu importante, secondo priorita:
  1. Film bloccati/incompleti (stuck_film)
  2. Coming Soon imminente < 10 min (countdown_imminent)
  3. Coming Soon < 60 min (countdown)
  4. Incassi da riscuotere (revenue)
  5. Nessun film attivo (no_films)
  6. Upgrade infrastrutture disponibile (infrastructure_upgrade)
  7. Eventi PvP (pvp_event)
  8. Social hint (social_hint)
  9. Qualita bassa (low_quality)
  10. Idle player (idle)
- **Login Greeting**: `GET /api/velion/login-greeting` saluto + advisor combinati, 1x per sessione (sessionStorage)
- **Infrastructure Upgrade Detection**: Controlla fondi vs costo upgrade, suggerisce se disponibile
- **Trigger Automatici**: Login, cambio pagina (2s), polling 60s, idle detection 3+ min
- **Messaggi Dinamici**: 4+ varianti per tipo (32+ totali), mai ripetitivi
- **Suggerimenti Contestuali**: 9 pagine con messaggi per livello
- **Bubble Non-Invasiva**: Styling per priorita, auto-hide 8-12s, cliccabile per navigazione
- **Controllo Utente ON/OFF (v6)**: Toggle nel menu hamburger ("Assistente Velion")
  - ON: Tutorial + suggerimenti + interventi automatici + bubble + login greeting
  - OFF: Nessun popup automatico, icona visibile ma desaturata, tooltip "Velion (OFF)", click apre panel manualmente
  - Persistenza in DB (collection `velion_prefs`: user_id, mode, last_autonomy_prompt)
  - Comunicazione TopNavbar↔ProtectedRoute via window events
  - Hint "Riattiva Velion per suggerimenti automatici" quando OFF
  - Visual feedback: glow grigio, saturazione 0.5, no notification dot
  - Autonomy Prompt: dopo 5 giorni, soft popup "Ti senti pronto a gestire in autonomia?" con 2 CTA
- **Preparato per livelli futuri**: Velion Base / Velion Avanzato / Velion OFF

## Architettura
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion
- Backend: FastAPI + MongoDB + APScheduler
- Integrazioni: OpenAI GPT-4o-mini + GPT-Image-1 via Emergent LLM Key

## Test
- Iter 127: 100% (Film Pipeline UX)
- Iter 128: 100% (Notifiche + Eventi)
- Iter 129: 100% (PvP Backend + HQ - 21/21)
- Iter 130: 100% (PvP Coming Soon Integration - 12/12)
- Iter 131: 100% (PvP Infra UX Revision - 11/11)
- Iter 132: 100% (Festival Overhaul Phase 1+2 - 18/18)
- Iter 133: 100% (Velion Tutorial System Interactive - 12/12)
- Iter 134: 100% (Velion AI Assistant - Backend 13/13 + Frontend all verified)
- Iter 135: 100% (Velion Phase 2 - Dynamic variants, Page-context, Priority styling - Backend 14/14 + Frontend all)
- Iter 136: 100% (Velion Phase 3 - Enhanced personality, Idle detection, Tips, Quick asks - Backend 16/16 + Frontend all)
- Iter 137: 100% (Velion Advisor Evolution - Priority system, Login greeting, Infra upgrade - Backend 15/15 + Frontend all)
- Iter 138: 100% (Velion ON/OFF Control - Toggle, Persistence, Visual feedback, Autonomy prompt - Backend 15/15 + Frontend all)

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime

### P2
- RBAC, CinePass + Stripe, PWA
- Contest Page Mobile Layout Fix

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
