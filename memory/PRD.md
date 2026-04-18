# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi (Hype → Pre-Produzione → CIAK → Final Cut → La Prima → Marketing → Distribuzione), Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game con 27 stazioni + metadata ICY + player fluttuante draggable, banner promo TV (-80%), navbar custom con label e contatore utenti online.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini) via Emergent Key

## Changelog
- **Feb 2026** — ETA Pipeline V3 Hype (P0): aggiunto countdown live "Mancano: Xh Ym Zs" alla `HypePhase` usando `hype_started_at`/`hype_complete_at` dal backend, affiancato alla barra arancione e alla percentuale già presenti. CIAK e Final Cut mostravano già il tempo residuo (invariati).
- Avatar base64 persistence fix, Web Radio system completo (27 stazioni, ICY proxy, UI draggable, banner -80%), Top/Bottom navbar con label e radio icon, profilo Emilians fix (500), hamburger center button Quick Commands.

## Backlog Prioritizzato
### P1
- Refactoring `/app/backend/scheduler_tasks.py` in worker specializzati
- Permessi specifici operativi ruolo MOD

### P2
- Notifiche push follower
- Personalizzazione avatar produttore (UI builder)
- Tornei PvP mensili con bracket

## Aree da Refactor
- `scheduler_tasks.py` troppo grande
- Valutare anche split `server.py` in moduli

## File di Riferimento Principali
- `/app/frontend/src/components/v3/Phases.jsx`
- `/app/frontend/src/components/RadioFloatingPlayer.jsx`
- `/app/frontend/src/contexts/RadioContext.jsx`
- `/app/backend/routes/pipeline_v3.py`
- `/app/backend/routes/radio.py`

## Integrazioni
- Emergent LLM Key (GPT-4o-mini)
- ICY metadata proxy (FastAPI)
