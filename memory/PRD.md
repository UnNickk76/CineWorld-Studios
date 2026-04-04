# CineWorld Studio's — PRD (Product Requirements Document)

## Problema Originale
Sistema di gioco "CineWorld" — app di produzione cinematografica con pipeline di film, serie TV, anime. React + FastAPI + MongoDB.

## Architettura
- **Frontend**: React (Vite/CRA), Tailwind CSS, Shadcn UI
- **Backend**: FastAPI, Motor (async MongoDB)
- **DB**: MongoDB Atlas (`cineworld`)
- **Deploy**: Emergent Platform (Preview) + Railway (Production)

## Step Completati

### STEP 1 — Sistema Ruoli
- Campo `role` aggiunto (ADMIN / CO_ADMIN / MOD / USER)
- NeoMorpheus = ADMIN hardcoded nel backend
- Protezioni ADMIN su: reset, cambio password, recovery password
- Tutti gli utenti esistenti migrati a `role: USER`

### STEP EXTRA — Blocco Assoluto ADMIN
- `get_user_role()` -> nickname ha priorita assoluta sul DB
- `validate_role_assignment()` -> blocca creazione ADMIN su non-NeoMorpheus
- Startup -> auto-correzione: strip ADMIN da utenti non autorizzati
- Log `[SECURITY]` su ogni violazione

### STEP 2 — Permessi Ruoli
- ADMIN: pieno controllo
- CO_ADMIN: reports, search-users, feedback, reset utenti, cambio password utenti
- CO_ADMIN non puo: set-user-role, delete-user, modificare ADMIN
- MOD: placeholder
- Nuovi endpoint: `/admin/reset-user`, `/admin/change-user-password`

### STEP 3 — Flow Cancellazione Account
- Flusso completo: requested -> countdown_active (10gg) -> user_confirmed -> final deletion
- ADMIN approva/rifiuta, cooldown 5 giorni su rifiuto
- Failsafe: auto-eliminazione se ADMIN non risponde entro 5 giorni
- Modulo: `routes/deletion.py`

### STEP 4 — Admin Panel / Co-Admin Panel
- ADMIN: 6 tab (Utenti, Film, Ruoli, Segnalazioni, Cancellazioni, Manutenzione)
- CO_ADMIN: 2 tab (Segnalazioni, Manutenzione)
- Tab Gestione Ruoli: assegna Co-Admin/Mod/User
- Tab Cancellazioni: gestione richieste con azioni

### STEP 5 — Manutenzione Avanzata
- `routes/maintenance.py`: diagnostica + 4 azioni (auto_fix, force_step, complete_project, reset_step)
- Loop detection: `status == previous_step` -> flag LOOP
- Timer stuck: `scheduled_release_at` scaduto -> flag STUCK
- `previous_step` tracking in maintenance + scheduler

### STEP 5+ — Export/Import DB (Streaming ZIP)
- `GET /admin/db/export` — esporta ZIP streaming di TUTTE le collection (bypass RAM limits)
- `POST /admin/db/import-file-safe` — upsert senza cancellare (FormData upload)
- `POST /admin/db/import-file-hard` — hard reset con backup + rollback (FormData upload)
- `POST /admin/db/reset` — RESET COMPLETO: svuota tutte le 69 collection, preserva NeoMorpheus

### Fix Inconsistenze DB
- `POST /admin/maintenance/fix-all` — fix completo: duplicati + stati invalidi + previous_step
- Auto-fix applicato a tutti i progetti attivi dopo il fix consistenza

### STEP 9 — Fix UI Mobile
- Scrollbar: `no-scrollbar` class fix
- Tab touch area: min 44px
- Stats grid responsive: 2->4 colonne

### AI Avatar Generation
- `GET /avatar/image/{filename}` — endpoint per servire file avatar da disco
- `POST /avatar/generate` — genera avatar AI con OpenAI `gpt-image-1` via Emergent LLM Key
- `PUT /auth/avatar` — aggiorna avatar_url e avatar_source
- Timeout axios esteso a 120s per la generazione

### Auto-Backup DB (4 Apr 2026)
- `backend/utils/db_backup.py` per auto-backup leggero (`.json.gz`)
- Conserva gli ultimi 5 backup ad ogni startup
- Eseguito automaticamente su ogni avvio del server

### Pannello DB Management con Sottomenu (4 Apr 2026) - TESTATO OK
- `DbManagementCard` ristrutturata con 3 sub-tab: Stato DB / Backup-Import / Sincronizzazione
- **Stato DB**: mostra header stato sync (verde/giallo/rosso) + tabella dettaglio per-collection con confronto Corrente vs Atlas
- **Backup / Import**: Scarica ZIP, Upload file, Import Safe (upsert), Import Hard (reset)
- **Sincronizzazione**: Invia a Atlas / Ricevi da Atlas con conferma CONFERMO
- Visibile SOLO per NeoMorpheus (admin)
- Endpoint `/api/admin/db/sync-status` con estimated_document_count per performance
- APScheduler auto-sync locale->Atlas ogni 30 min (attivo solo se DB locale, non su preview)
- Backend protetto: CO_ADMIN riceve "Solo ADMIN puo' eseguire questa operazione"

## File Chiave
- `/app/backend/auth_utils.py` — Sistema ruoli completo
- `/app/backend/models/__init__.py` — UserResponse con role + deletion_status
- `/app/backend/routes/auth.py` — Protezioni ADMIN, Avatar AI
- `/app/backend/routes/deletion.py` — Flow cancellazione
- `/app/backend/routes/maintenance.py` — Manutenzione + Export/Import DB + Sync
- `/app/backend/server.py` — Importazioni, migration, scheduler, APScheduler
- `/app/backend/utils/db_backup.py` — Auto-backup
- `/app/frontend/src/pages/AdminPage.jsx` — Pannello Admin/Co-Admin completo
- `/app/frontend/src/contexts/index.jsx` — Auth context, API instance

## Backlog Prioritizzato

### P1
- Modularizzazione GAME CORE endpoints da `server.py` (17k+ righe)
- Sistema "Previsioni Festival" (Scommesse sui vincitori)
- Marketplace for TV/Anime rights

### P2
- Contest Page Mobile Layout (16+ segnalazioni)

### P3
- Velion features (Mood, Chat, Levels, AI Memory)
- CinePass + Stripe, Push notifications, RBAC
- Eventi globali, Guerre tra Major
