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
- Contenuto completo: Proposta → Distribuzione → PvP → Social

### Copy Login
- Sottotitolo coinvolgente sotto CINEWORLD STUDIO'S
- Marketplace label "Prossimamente" (non "In pausa")

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

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime

### P2
- RBAC, CinePass + Stripe, PWA
- Contest Page Mobile Layout Fix

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
