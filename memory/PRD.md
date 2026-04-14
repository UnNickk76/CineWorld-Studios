# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Architettura
- **Frontend**: React + TailwindCSS + Shadcn/UI, porta 3000
- **Backend**: FastAPI + MongoDB + APScheduler, porta 8001
- **DB**: MongoDB (collections: film_projects, films, users, city_tastes, challenges, npc_agencies, etc.)

## Stato Pipeline V2 (State Machine)
draft → idea → proposed → hype_setup → hype_live → casting_live → prep → shooting → postproduction → sponsorship → marketing → (premiere_setup | release_pending) → released → completed

## Funzionalita Implementate

### Core Pipeline V2
- 14 step completi: IDEA, HYPE, CAST, PREP, CIAK, FINAL CUT, MARKETING, LA PRIMA, USCITA
- Poster AI (GPT Image 1) + Sceneggiatura AI (GPT-4o-mini)
- Cast system con 23K+ NPC, chimiche attori, agenzie
- Durata film dinamica per genere
- Quality Score calcolato progressivamente

### Fix Definitivo Pipeline (Aprile 2026)
- **Marketing Non-Bloccante**: try/except con fallback narrativo, mai blocca la pipeline
- **Separazione Rilascio**: release_type salvato indipendentemente dal marketing
- **Step Finale Forzato**: Nuovo componente StepFinale con riepilogo (poster, cast, hype, produzione, marketing) + quality preview + CONFERMA USCITA / SCARTA FILM
- **Ricalcolo Completo**: endpoint confirm-final-release ricalcola quality da tutti i metrics
- **Fix Uscita**: Film salvato correttamente come released con completed=True, mai return vuoto
- **Progresso 0-100**: ProgressCircle SVG per locandina/sceneggiatura (frontend only)

### Motori Backend Autonomi (APScheduler)
- theater_life.py — Affluenza, uscite, prolungamenti cinema
- city_tastes.py — 25 citta con gusti dinamici
- ri_cinema.py — Eventi rerun film ritirati

### Altre Feature
- Parco Studio 3D (mappa, LED sign, perspective text)
- Tutorial Guest (Velion) allineato a Pipeline V2
- Sfide Minigiochi (18 giochi, tempo reale)
- Admin Panel con Reset Gioco
- Serie TV / Anime con episodi e stagioni

## Endpoint Chiave
- POST /api/pipeline-v2/films/{pid}/confirm-final-release — Ricalcolo + release
- POST /api/pipeline-v2/films/{pid}/discard-final — Scarta dallo step finale
- POST /api/pipeline-v2/films/{pid}/save-marketing — Non-bloccante
- POST /api/pipeline-v2/films/{pid}/schedule-release — Date + zone distribuzione
- GET /api/city-tastes/tips/{pid} — Consigli Velion citta

## Backlog
- (P1) Fase 3 Mercato: vendita serie/anime
- (P1) CinemaStatsModal + ProducerProfileModal (dati reali)
- (P2) Sfida della Settimana
- (P3) Previsioni Festival, Marketplace diritti TV/Anime

## Refactoring Necessari
- PipelineV2.jsx (~4000 righe) → separare in componenti per fase
- ContentTemplate.jsx → semplificazione logica legacy

## Integrazioni 3rd Party
- Emergent LLM Key (AI Avatar, Poster, Screenplay)
- Stripe (Payments - richiede API Key utente)
