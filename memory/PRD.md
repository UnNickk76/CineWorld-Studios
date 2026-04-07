# CineWorld Studio's — PRD

## Problema Originale
Sistema di produzione cinematografica con pipeline completa. Esperienza utente visiva, cinematografica e immersiva con PvP, infrastrutture, arena e guerre tra Major.

## Architettura
- **Frontend**: React + Tailwind + Shadcn/UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Background**: `apscheduler` per il loop economia (ogni 10min)

## Funzionalita Completate

### Core (DONE precedentemente)
- La Prima, Content Template, Cinema Journal ULTRA, Guest + Tutorial
- DB Bloat Fix, Pulizia server.py, Soft Expansion Major
- Timing Cinematici, Serie TV/Anime nel Auto-Tick
- Throttling Coda, Anti-Spam Notifiche, Major con navbar interna

### Sistema Eventi (DONE)
- event_pressure per utente, trigger sigmoide, rarita per pressione
- 5 tab, bottone "Rivedi Evento"

### FASE 1 & 2 (DONE)
- Infrastrutture, Arena Mirata, Major Warfare, Data Integrity

### Sistema Contest Mini-giochi (DONE - 2026-04-07)
- 11 step, 5 mini-giochi, cap 20 crediti, reset 09:00 UTC

### Test Lab Sandbox Visiva (DONE - 2026-04-07)
- Tab Admin con 7 simulazioni visive (Film Pipeline, Contest, 3 Eventi, Arena, Major)
- Usa componenti reali: VelionCinematicEvent, ReleaseCinematic, MatrixOverlay
- Nessun JSON/output tecnico, tutto visuale come nel gioco reale
- Storico con timeline leggibile e replay cliccabile
- Zero impatto DB, sandbox locale pura
- Backend endpoints mantenuti per future integrazioni

## Backlog

### P1
- [ ] Sistema "Previsioni Festival" (scommesse vincitori)

### P2
- [ ] Marketplace TV/Anime rights

### P3
- [ ] Velion Mood, Chat Evolution, CinePass+Stripe, Push, Velion Levels, Eventi globali, Velion AI Memory

## Credenziali Test
- Utente: NeoMorpheus (fandrex1@gmail.com / Fandrel2776)
