# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi, Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game (27 stazioni + ICY metadata + player fluttuante), banner promo TV (-80%), navbar custom con label e contatore utenti online.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini) via Emergent Key

## Changelog
- **Feb 2026 (sessione corrente)**
  - ETA Pipeline V3 Hype (P0): countdown live "Mancano: Xh Ym Zs" in `HypePhase` da `hype_started_at`/`hype_complete_at`.
  - Fix Profilo Player Emilians recurring: popup con `z-[120]` (sopra OnlineUsersPanel z-[100]), loading state visibile con spinner, import `Loader2` aggiunto in `App.js`.
- Web Radio system completo (27 stazioni, ICY proxy, draggable UI, banner -80%), avatar base64 fix, Top/Bottom navbar labels + radio icon + online counter, profilo Emilians 500 backend fix, hamburger center button Quick Commands.

## Backlog Prioritizzato
### P1
- Refactoring `/app/backend/scheduler_tasks.py` in worker specializzati
- Permessi specifici operativi ruolo MOD

### P2
- Notifiche push follower
- Personalizzazione avatar produttore (UI builder)
- Tornei PvP mensili con bracket
- Top Nav: il pulsante "Online" esce dal viewport su telefoni stretti (≤393px). Valutare riduzione icone o hamburger.

## Aree da Refactor
- `scheduler_tasks.py` troppo grande
- `server.py` valutare split in moduli
- `App.js` (2200+ righe) — spostare PlayerProfilePopup in componente dedicato

## File di Riferimento
- `/app/frontend/src/App.js` (PlayerProfilePopup, openPlayerPopup, OnlineUsersPanel)
- `/app/frontend/src/components/v3/Phases.jsx` (HypePhase ETA)
- `/app/frontend/src/components/RadioFloatingPlayer.jsx`
- `/app/backend/routes/pipeline_v3.py`
- `/app/backend/routes/radio.py`

## Integrazioni
- Emergent LLM Key (GPT-4o-mini)
- ICY metadata proxy (FastAPI)
