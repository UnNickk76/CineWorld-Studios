# CineWorld Studio's — PRD (Product Requirements Document)

## Problema Originale
Sistema di gioco "CineWorld" — app di produzione cinematografica con pipeline di film, serie TV, anime. React + FastAPI + MongoDB.

## Architettura
- **Frontend**: React (CRA + Craco), Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **DB**: MongoDB Atlas (`cineworld`) + Emergent Managed DB (.it)
- **Deploy**: Emergent Platform (.it) + Railway (backup)

## Step Completati

### Sistema Ruoli & Sicurezza ADMIN
- NeoMorpheus = ADMIN hardcoded, intoccabile da codice e in game
- RBAC: ADMIN / CO_ADMIN / MOD / USER
- Auto-correzione ruoli su startup
- Blocco assoluto creazione altri ADMIN

### Pannello Admin
- 6 tab ADMIN: Utenti, Film, Ruoli, Segnalazioni, Cancellazioni, Manutenzione
- 2 tab CO_ADMIN: Segnalazioni, Manutenzione
- Flow cancellazione account completo (10gg countdown + failsafe)

### Manutenzione & Diagnostica
- Loop/stuck detection per progetti
- Auto-fix, force_step, complete_project, reset_step
- Export/Import DB in streaming ZIP (bypass RAM limits)

### AI Avatar Generation
- OpenAI `gpt-image-1` via Emergent LLM Key
- Timeout 120s, salvataggio URL automatico

### Pannello DB Management (4 Apr 2026) — COMPLETATO E TESTATO
- 3 sub-tab: Stato DB / Backup-Import / Sincronizzazione
- Sync-status con `dbStats` + cache 30s (3s vs 17s precedenti)
- Gestione errore elegante (no più "Caricamento..." infinito)
- Visibile SOLO per NeoMorpheus

### Fix Deploy Emergent (4 Apr 2026) — COMPLETATO
- `.gitignore` ricostruito (era 1095 righe malformate → 70 righe pulite)
- `DISABLE_ESLINT_PLUGIN=true` per build con CI=true
- `load_dotenv()` senza `override=True`
- Backup automatico su startup disabilitato (previene OOM)
- Startup robusto con try/except

### Fix Sincronizzazione Completa (4 Apr 2026) — COMPLETATO
- Rimossa protezione NeoMorpheus nel sync (causava mancato aggiornamento soldi/crediti)
- Ora "Invia a Atlas" e "Ricevi da Atlas" copiano TUTTO fedelmente, incluso NeoMorpheus

### Redesign Cinematografico Pipeline Film (5 Apr 2026) — COMPLETATO
- Pipeline trasformata da form gestionale a esperienza cinematografica immersiva
- 6 step visivi: IDEA → HYPE → CAST → PRODUZIONE → LA PRIMA → USCITA
- Film carousel (un film alla volta, stile slideshow)
- Full-page step sections con sfondi cinematografici placeholder
- Eliminato popup Dialog, sostituito con vista inline full-page
- Step bar con colori e glow per stato corrente/completato/bloccato
- La Prima preview evocativa (testi come "Presentato a Cannes")
- Placeholder per effetti cinema (tappeto rosso, luci, proiettore)
- CSS dedicato: cinematic-pipeline.css

### Fix Status Sponsor Frontend/Backend (5 Apr 2026) — COMPLETATO
- FilmPopup.jsx: aggiunto mapping `sponsor` → step `script` in getCurrentStepId
- film_pipeline.py: endpoint write-screenplay e advance-to-preproduction ora accettano status `sponsor`
- Film bloccati in status `sponsor` ora proseguono correttamente nella pipeline

## File Chiave
- `/app/backend/server.py` — Main server (17k+ righe, da modularizzare)
- `/app/backend/routes/maintenance.py` — DB management, sync, export/import
- `/app/backend/routes/auth.py` — Auth, Avatar AI
- `/app/backend/routes/deletion.py` — Flow cancellazione
- `/app/backend/auth_utils.py` — Sistema ruoli
- `/app/backend/utils/db_backup.py` — Backup utility
- `/app/frontend/src/pages/AdminPage.jsx` — Pannello Admin completo
- `/app/frontend/src/contexts/index.jsx` — Auth context, API instance

## Backlog Prioritizzato

### P1 — Prossimi
- Modularizzazione GAME CORE endpoints da `server.py` (17k+ righe → route files)
- Sistema "Previsioni Festival" (Scommesse sui vincitori)
- Marketplace for TV/Anime rights

### P2
- Contest Page Mobile Layout (16+ segnalazioni)

### P3 — Futuro
- Velion features (Mood, Chat, Levels, AI Memory)
- CinePass + Stripe, Push notifications
- Eventi globali, Guerre tra Major
