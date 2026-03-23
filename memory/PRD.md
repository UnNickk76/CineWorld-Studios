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

### CRITICAL BUG FIX: Coming Soon Film Disappearing (v3.1)
- **Root Cause 1**: `/film-pipeline/all` excluded `completed` status, but `choose-release-strategy` sets film to `completed` + `release_pending: True` → film disappeared from pipeline
- **Root Cause 2**: `/films/{id}` only checked `films` collection, not `film_projects` → auto-released films showed "non disponibile"
- **Root Cause 3**: Scheduler notifications linked to `/films/{id}` instead of `/create-film?film={id}` → wrong collection lookup
- **Root Cause 4**: Count endpoint didn't match film list filter → count/list mismatch (18 films shown in counter, 0 in list)
- **Root Cause 5**: No auto-advance mechanism when Coming Soon timer expired on frontend → film stuck until scheduler ran
- **Fixes**: Pipeline includes completed+release_pending, `/films/{id}` fallback to film_projects, fixed notification links, auto-advance endpoint + frontend integration, card shows "Pronto per il Casting!" on expired timer

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

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime

### P2
- RBAC, CinePass + Stripe, PWA
- Contest Page Mobile Layout Fix

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
- Tutorial interattivo con personaggio (attesa input utente)
