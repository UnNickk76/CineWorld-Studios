# CineWorld Studio's — PRD (Product Requirements Document)

## Problema Originale
Sistema di gioco "CineWorld" — app di produzione cinematografica con pipeline di film, serie TV, anime. React + FastAPI + MongoDB.

## Architettura
- **Frontend**: React (Vite/CRA), Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **DB**: MongoDB Atlas (`cineworld`)
- **Deploy**: Emergent Platform (Preview) + Railway (Production)

## Step Completati (Sessione Corrente - 3 Apr 2026)

### STEP 1 — Sistema Ruoli ✅
- Campo `role` aggiunto (ADMIN / CO_ADMIN / MOD / USER)
- NeoMorpheus = ADMIN hardcoded nel backend
- Protezioni ADMIN su: reset, cambio password, recovery password
- Tutti gli utenti esistenti migrati a `role: USER`

### STEP EXTRA — Blocco Assoluto ADMIN ✅
- `get_user_role()` → nickname ha priorità assoluta sul DB
- `validate_role_assignment()` → blocca creazione ADMIN su non-NeoMorpheus
- Startup → auto-correzione: strip ADMIN da utenti non autorizzati
- Log `[SECURITY]` su ogni violazione

### STEP 2 — Permessi Ruoli ✅
- ADMIN: pieno controllo
- CO_ADMIN: reports, search-users, feedback, reset utenti, cambio password utenti
- CO_ADMIN non può: set-user-role, delete-user, modificare ADMIN
- MOD: placeholder
- Nuovi endpoint: `/admin/reset-user`, `/admin/change-user-password`

### STEP 3 — Flow Cancellazione Account ✅
- Flusso completo: requested → countdown_active (10gg) → user_confirmed → final deletion
- ADMIN approva/rifiuta, cooldown 5 giorni su rifiuto
- Failsafe: auto-eliminazione se ADMIN non risponde entro 5 giorni
- Modulo: `routes/deletion.py`

### STEP 4 — Admin Panel / Co-Admin Panel ✅
- ADMIN: 6 tab (Utenti, Film, Ruoli, Segnalazioni, Cancellazioni, Manutenzione)
- CO_ADMIN: 2 tab (Segnalazioni, Manutenzione)
- Tab Gestione Ruoli: assegna Co-Admin/Mod/User
- Tab Cancellazioni: gestione richieste con azioni

### STEP 5 — Manutenzione Avanzata ✅
- `routes/maintenance.py`: diagnostica + 4 azioni (auto_fix, force_step, complete_project, reset_step)
- Loop detection: `status == previous_step` → flag LOOP
- Timer stuck: `scheduled_release_at` scaduto → flag STUCK
- `previous_step` tracking in maintenance + scheduler

### STEP 5+ — Export/Import DB ✅
- `GET /admin/db/export` — esporta JSON
- `POST /admin/db/import-safe` — upsert senza cancellare
- `POST /admin/db/import-hard` — hard reset con backup + rollback
- NeoMorpheus protetto in tutti i casi
- UI: card "Gestione Database" nel tab Manutenzione

### STEP 9 — Fix UI Mobile ✅
- Scrollbar: `no-scrollbar` class fix
- Tab touch area: min 44px
- Stats grid responsive: 2→4 colonne
- Icone ingrandite su mobile

## File Chiave Modificati
- `/app/backend/auth_utils.py` — Sistema ruoli completo
- `/app/backend/models/__init__.py` — UserResponse con role + deletion_status
- `/app/backend/routes/auth.py` — Protezioni ADMIN
- `/app/backend/routes/deletion.py` — NUOVO: Flow cancellazione
- `/app/backend/routes/maintenance.py` — NUOVO: Manutenzione + Export/Import DB
- `/app/backend/server.py` — Importazioni, migration, scheduler, nuovi endpoint CO_ADMIN
- `/app/backend/scheduler_tasks.py` — previous_step tracking
- `/app/frontend/src/pages/AdminPage.jsx` — Pannello Admin/Co-Admin completo
- `/app/frontend/src/App.js` — Nav CO_ADMIN

## Backlog Prioritizzato

### P0
- TV Series pipeline loop infinito (segnalato dall'utente, non ancora investigato)

### P1
- 20 poster film mancanti/404
- Modularizzazione GAME CORE endpoints (paused)
- Sistema "Previsioni Festival"
- Marketplace diritti TV/Anime

### P2
- Contest Page Mobile Layout (16+ segnalazioni)

### P3
- Velion features (Mood, Chat, Levels, AI Memory)
- CinePass + Stripe, Push notifications, RBAC
- Eventi globali, Guerre tra Major
