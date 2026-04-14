# CineWorld Studio's — PRD

## Prodotto
Browser game gestionale cinematografico Full-Stack (FastAPI + React + MongoDB).

## Architettura
- **Frontend**: React + TailwindCSS + Shadcn/UI, porta 3000
- **Backend**: FastAPI + MongoDB + APScheduler, porta 8001
- **DB**: MongoDB (collections: film_projects, films, users, city_tastes, challenges, npc_agencies, etc.)

## Pipeline V2 — State Machine (11 Step)
```
draft → idea → proposed → hype_setup → hype_live → casting_live → prep → shooting → postproduction → sponsorship → marketing → release_choice → distribution → release_pending → released → completed
```

### UI Step Map (0-10):
0: IDEA | 1: HYPE | 2: CAST | 3: PREP | 4: CIAK | 5: FINAL CUT | 6: MARKETING | 7: RILASCIO | 8: DISTRIBUZIONE | 9: CONFERMA | 10: AL CINEMA

### Step SEMPRE visibili:
- completed = verde con check
- active = evidenziato  
- locked = visibile ma opaco, non cliccabile
- MAI nascondere step, MAI rimuovere step

## Flusso Obbligatorio (Post-Marketing)
1. marketing (anche fallito) → 2. release_choice (SEMPRE) → 3. distribution (SEMPRE) → 4. release_pending (StepFinale) → 5. released

## Quality Score
- **Preview (frontend only)**: `safeAverage([cast, hype, produzione, marketing])` — MAI salvata, MAI usata per classifiche
- **Calcolo reale**: SOLO in `confirm-final-release` endpoint — formula: `(cast*0.4 + hype*0.2 + production*0.2 + marketing*0.2) / 20 + random(-1,1)`
- **Invisibile fino all'uscita**: prima mostrato solo preview, dopo uscita il valore reale

## Funzionalita Implementate

### Core Pipeline V2
- 11 step con stepper SEMPRE visibile (completed/active/locked)
- Marketing non-bloccante con fallback narrativo
- Separazione rilascio (release_type indipendente)
- Step Finale forzato con CONFERMA USCITA / SCARTA FILM
- Ricalcolo quality SOLO a uscita (mai prima)
- Anti-NaN globale con safeAverage
- Fallback anti-bug per dati mancanti
- ProgressCircle SVG per locandina/sceneggiatura
- Poster AI (GPT Image 1) + Sceneggiatura AI (GPT-4o-mini)
- Cast system con 23K+ NPC, chimiche attori
- Durata film dinamica per genere

### Componenti Frontend Nuovi
- `ProgressCircle` — SVG cerchio 0-100%
- `ReleaseChoicePhase` — Scelta La Prima / Diretto
- `DistributionPhase` — Zone e date distribuzione
- `StepFinale` — Riepilogo + Conferma Uscita

### Motori Backend Autonomi (APScheduler)
- theater_life.py — Affluenza, uscite, prolungamenti cinema
- city_tastes.py — 25 citta con gusti dinamici
- ri_cinema.py — Eventi rerun film ritirati

### Endpoint Chiave
- POST /api/pipeline-v2/films/{pid}/confirm-final-release — Ricalcolo reale + release
- POST /api/pipeline-v2/films/{pid}/discard-final — Scarta film
- POST /api/pipeline-v2/films/{pid}/save-marketing — Non-bloccante, auto-avanza a release_choice
- POST /api/pipeline-v2/films/{pid}/choose-premiere — release_choice → distribution
- POST /api/pipeline-v2/films/{pid}/choose-direct-release — release_choice → distribution
- POST /api/pipeline-v2/films/{pid}/schedule-release — distribution → release_pending

## Backlog
- (P1) Fase 3 Mercato: vendita serie/anime
- (P1) CinemaStatsModal + ProducerProfileModal (dati reali)
- (P2) Sfida della Settimana
- (P3) Previsioni Festival, Marketplace diritti TV/Anime

## Integrazioni 3rd Party
- Emergent LLM Key (AI Avatar, Poster, Screenplay)
- Stripe (Payments - richiede API Key utente)
