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
- Iter 139: 100% (Velion Mobile Bubble Fix + Login Welcome Bubble - 8/8 features verified)
- Iter 140: 100% (Festival Rework Step 1-3: Dynamic Nominations + 4-State System + UI - Backend 25/25 + Frontend all)
- Iter 141: 100% (Festival Rework Step 4-5-6: AI Unpredictable + Cinematic Ceremony + Player Festivals - Backend 21/21 + Frontend all)
- Iter 143: 100% (Bug Fix "Scegli" Button - Casting actor selection verified working - Backend 5/5 + Frontend 9/9)
- Iter 144: 100% (Fail-Safe Cast System - 4 livelli sicurezza - Backend 8/8 + Frontend all verified)
- Iter 145: 100% (Fix Regressione Rilascio Film + Produci - 4 fix: colonna sonora, animazione, velocita, filtro)
- Iter 146: Profile Page crash (React Error #31) - Root cause: fame_tier object rendered as React child. Fixed + Error Boundary added.
- Iter 147: Preload Pages - Background prefetch di 5 endpoint chiave al login, pagine usano cachedGet con TTL 2min e deduplication.
- Iter 148: 100% Draft/Autosave System - 7 fix: salvataggio step-by-step, autosave 4s, recupero bozza, draft in Produci, cleanup su create, no count limit.
- Iter 149: 100% Step Navigation + Release Balancing - Step bar cliccabili per tornare indietro, rilascio immediato -2 qualita/-10% incassi, Coming Soon +3~11 qualita/+15~40% incassi.
- Iter 150: Auth Fix - Login robusto con safe field defaults, Pydantic validation fallback, messaggio errore italiano, auto-logout su 401, password admin resettata.

### Festival Rework Step 1-3 (2026-03-23)
- **Step 1 - Nomination Dinamiche:** Solo film ultimi 14 giorni, max 5 candidati, mix top 3 + 2 random
- **Step 2 - Sistema 4 Stati:** UPCOMING (>3gg) → VOTING (0-3gg) → LIVE (cerimonia) → ENDED. Auto-transizione
- **Step 3 - UI Migliorata:** Countdown banner, state badges, voting type badges, card con premi, timer live

### Festival Rework Step 4-5-6 (2026-03-23)
- **Step 4 - AI Non Prevedibile:** 3 sistemi winner: player (50% voti + 50% audience), algorithm (qualita' tecnica pura), AI (fattori nascosti: hype, viral, rumor, critic bias, eventi random)
- **Step 5 - Diretta Cinematica:** CinematicCeremony.jsx con 9 fasi animate (intro, presentazione, categoria, nomination, suspense, reveal, premio, transizione, finale), particelle, heartbeat, chat live, skip
- **Step 6 - Festival Player Migliorato:** max_participants (5-50), badge vincitore (festival_badges collection), leaderboard custom festivals (top creators + top winners)

### Fail-Safe Cast System (2026-03-24)
- **Livello 1 - Fallback Automatico:** Endpoint `POST /api/film-pipeline/{id}/auto-complete-cast` riempie ruoli mancanti da proposte disponibili o genera nuovi membri, 50% costo ridotto
- **Livello 2 - Auto-Complete in advance-to-screenplay:** Se cast incompleto, auto-fill prima di avanzare (MAI blocca con errore 400)
- **Livello 3 - Cast Minimo Garantito:** Regista + Sceneggiatore + Compositore + 2-5 attori adatti al genere del film
- **Livello 4 - Safe Mode Frontend:** Retry automatico su errore selectCast, fallback auto-complete, pulsante "Completa Cast Automaticamente" dopo 5s, messaggio Velion purple banner
- **Emergency Mode:** Se tutto fallisce, genera cast d'emergenza minimo (2 attori) senza costo

### Fix Regressione Rilascio Film + Produci (2026-03-24)
- **Colonna Sonora:** Aggiunto `soundtrack_rating` e `modifiers.soundtrack` nella response del rilascio. UI mostra punteggio con highlight viola in Phase 5
- **Animazione Cinematica Rilascio:** Portata animazione completa a 5 fasi da FilmPipeline.jsx a FilmPopup.jsx (intro cinema, trailer sceneggiatura, evento, numeri animati, risultato finale)
- **Velocita Rilascio:** Loading immediato con fasi animate sequenziali, nessun blocco UI
- **Filtro Produci:** Frontend ora esclude film con status `completed` e `released` dalla sezione Produci
- **Recensioni Critici:** Aggiunte 3 recensioni nella response rilascio, mostrate in Phase 5 con punteggi
- **Soddisfazione Pubblico:** Aggiunta barra soddisfazione pubblico nella Phase 5

### Ottimizzazione Performance - Navigazione Istantanea (2026-03-24)
- **GameStore SWR:** `contexts/GameStore.jsx` - Store globale con stale-while-revalidate (30s stale, 5min max). Dati persistenti tra navigazioni, aggiornamento background senza blocco UI.
- **Prefetch intelligente:** Wave-based dopo login (wave1: dashboard+pipeline, wave2: films+arena, wave3: level+genres). Prefetch on-hover sui link della bottom navbar.
- **Pagine migrate:** Dashboard (`useSWR('/dashboard/batch')`), FilmPipeline (`useSWR('/film-pipeline/all')`), PvPArena (`useSWR('/pvp-cinema/arena')`), MyFilms (`useSWR('/films/my')`)
- **Riduzione API:** Cache elimina fetch duplicati, SWR mostra dati cached istantaneamente + revalidazione background
- **Mobile performance:** Zero blocchi UI, dati visibili subito su ogni pagina
- **Test:** Iter 149 - 100% frontend, 0 errori console, navigazione istantanea verificata

### Bug Fix UX Mobile Chat (2026-03-24)
- **Banner donazione:** Nascosto su `/chat` (`location.pathname !== '/chat'`)
- **Velion avatar:** Nascosto su `/chat` (rimosso VelionOverlay quando chat attiva)
- **Input sticky z-50:** Input chat con `sticky bottom-0 z-50`, sempre visibile sopra tutto
- **Keyboard mobile:** `visualViewport` API per adattare altezza dinamicamente quando tastiera aperta
- **100dvh:** Sostituito `h-screen` con `h-[100dvh]` per gestione corretta viewport mobile iOS/Android
- **Auto-scroll:** `onFocus` dell'input scrolla messaggi in basso quando tastiera si apre

### Arena PvP Cinematografica - Rework Completo (2026-03-24)
- **Arena Film per Genere:** 5 sezioni (Azione&Thriller, Dramma&Romance, Commedia&Animazione, Fantasy&SciFi, Horror&Mistero) con mini locandine portrait, badge status (In Sala/Coming Soon/Anteprima), stella film propri
- **Azioni Supporto (4):** Campagna Social (+2-5%), Influencer (+3-6%), Evento Promo (+4-7%), Premi Pilotati (+5-8%). Sempre positive per i propri film.
- **Azioni Boicottaggio (4):** Scandalo Mediatico (-3-8%, 55% base), Critica Negativa (-4-10%, 50%), Leak Produzione (-5-10%, 45%), Sabotaggio Evento (-6-10%, 40%). Possono fallire e ritorcersi.
- **Calcolo successo:** random + livello infrastrutture + fama + livello strategico
- **Cooldown:** 30-90 min per azione, max 5 azioni/ora
- **Difesa:** Recupera 40-70% danni da boicottaggio (2 CP)
- **Report:** Storico azioni, successo/fallimento, stats aggregate
- **Navbar:** "Arena" (Swords) aggiunta alla bottom navbar, sostituisce "Sfide"
- **Backend:** `routes/pvp_cinema.py` - 8 endpoint (arena, film detail, support, boycott, defend, history, stats, marketing)
- **Frontend:** `pages/PvPArenaPage.jsx` - 2 tab (Arena, Report), popup film con azioni
- **Test:** Backend 8/8 API verificate via curl (support, boycott, defend, history, stats tutti OK)

### Sistema "Migliora Film" + Velion UI (2026-03-24)
- **Bug Fix P0:** Aggiunto `'proposed'` alla lista stati applicabili di `cast_upgrade` in IMPROVEMENT_OPTIONS
- **Improvement Suggestions:** GET `/api/film-pipeline/{id}/suggestions` ritorna suggerimenti dinamici basati su stato film, cast, hype
- **Apply Improvement:** POST `/api/film-pipeline/{id}/improve` applica miglioramento con costo fondi+CP, bonus qualita random
- **ImprovementPanel:** Componente in FilmPopup.jsx con suggerimenti prioritizzati, Velion message, pulsante "Migliora"
- **Swipe-to-Dismiss:** VelionOverlay.jsx con Framer Motion drag gesture per eliminare notifiche
- **Smart Badges:** Badge conteggi nella pagina Produci per categorie film
- **Test:** Iter 148 - 100% backend (13/13) + 100% frontend

### Sistema PvP Cinematografico (2026-03-24)
- **Guerra al Box Office:** Auto-trigger quando film dello stesso genere escono nello stesso periodo (48h). Marketing boost (4 tipi: Social, Premiere, Critici, Billboard). Premi: fondi, fama, revenue bonus al vincitore. Penalita revenue al perdente.
- **Testa a Testa:** Sfide manuali tra film in sala. 24h durata, score basato su qualita, audience, revenue, IMDb, likes + fattore fortuna. Premi: $250K + 5 fama + 5 CP. Costo: $100K + 3 CP.
- **Classifica PvP:** Leaderboard basata su vittorie totali nelle sfide.
- **Scheduler:** `resolve_pvp_cinema_events` ogni 10min risolve guerre e sfide scadute.
- **Integrazione rilascio:** Al rilascio di un film, auto-check per guerre al box office con film dello stesso genere.
- **Navigazione:** Icona Target rossa nella top bar + route `/pvp-arena`
- **Backend:** `routes/pvp_cinema.py` con 8 endpoint
- **Frontend:** `pages/PvPArenaPage.jsx` con 3 tab (Box Office, Testa a Testa, Classifica)
- **Test:** Backend 8/8 API verificate via curl + risoluzione challenge/war manuale + frontend verificato via screenshot

### Fix UI Mobile + Migliorie Dashboard (2026-03-24)
- **Navbar Safe Area:** Aggiunto `paddingTop: env(safe-area-inset-top)` al navbar e wrapper contenuto in ProtectedRoute per evitare sovrapposizione titoli pagina su mobile (specialmente iOS con notch/dynamic island)
- **Bottom Nav Safe Area:** Aggiunto `paddingBottom: env(safe-area-inset-bottom)` al bottom mobile nav per dispositivi con home indicator
- **Sezione "Ciak!" sostituita con "Arena":** Card "shooting-shortcut" rimossa dal Dashboard, sostituita con card "arena-shortcut" che mostra statistiche PvP e linka a /pvp-arena. Usa hook useSWR('/pvp-cinema/stats') dal GameStore.
- **Bilancio Finanziario Collassabile:** Sezione resa collapsabile con Framer Motion AnimatePresence. Mostra Profitto/Perdita nel header quando chiuso. Default chiuso (financeOpen=false).
- **Test:** Iter 150 - 100% frontend (6/6)

## Backlog

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
