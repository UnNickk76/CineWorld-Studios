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

### Festival System Overhaul v3.0
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

### Velion AI Assistant (v5.0 - Smart Advisor)
- **Pannello con 2 Tab**: Tutorial (16 step immersivi) + "Chiedi a Velion" (chat AI)
- **Chat AI**: GPT-4o-mini, personalita misterioso/cifrato, metafore cinematografiche, 2-3 frasi
- **Quick Ask Chips**: 5 domande rapide + "Lo sapevi?" tips button
- **ADVISOR SINGOLO (v5)**: Un solo suggerimento alla volta, il piu importante, secondo priorita
- **Login Greeting**: saluto + advisor combinati, 1x per sessione
- **Controllo ON/OFF (v6)**: Toggle nel menu hamburger

### Rivivi il Rilascio (2026-03-25) - NEW
- **Backend**: `GET /api/films/{film_id}/release-cinematic` ritorna dati cinematici salvati o ricostruiti da fallback
- **Frontend**: `ReleaseCinematic.jsx` componente condiviso con supporto `inline` (per FilmPopup) e overlay (per FilmDetail)
- **FilmDetail.jsx**: Card "Rivivi il Rilascio" visibile per film rilasciati, click carica dati e mostra overlay cinematica
- **FilmPopup.jsx**: Refactorizzato per usare `<ReleaseCinematic inline>` invece del codice duplicato (~300 righe rimosse)
- **Test**: Backend 100% (11/11), Frontend 100%

## Architettura
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion
- Backend: FastAPI + MongoDB + APScheduler
- Integrazioni: OpenAI GPT-4o-mini + GPT-Image-1 via Emergent LLM Key

## Test
- Iter 127-152: Vedi changelog
- Iter 153: 100% Rivivi il Rilascio (Backend 11/11 + Frontend verified)

## Backlog

### P0 -- Completato
1. ~~Locandina non generata~~ -- Risolto
2. ~~Presentazione dopo Ciak assente~~ -- Risolto
3. ~~Rimozione sezione Like obsoleta~~ -- Risolto
4. ~~Recupero film scomparsi + sistema Bozze~~ -- Risolto
5. ~~Rivivi il rilascio~~ -- Risolto

### P1
- Sistema "Previsioni Festival" (scommesse sui vincitori)
- Marketplace per diritti TV/Anime
- Velion Mood Indicator (indicatore visivo stato giocatore)
- Chat Evolution (mobile + social)

### P2
- Velion Levels (Base, Advanced, OFF)
- RBAC, CinePass + Stripe, PWA
- Contest Page Mobile Layout Fix (ricorrente)
- ESLint / Python linting cleanup

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
- Velion AI Memory (memoria sessione per conversazioni contestuali)
