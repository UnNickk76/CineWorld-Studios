# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.082

## Funzionalità Implementate

### v0.082 - Sfide Offline VS + Upgrade Infrastrutture - 11/03/2026 (COMPLETATO)
- **Sfide Offline VS**: Toggle nella pagina Contest per accettare sfide offline. AI sceglie i migliori 3 film per il difensore
- **Report Battaglia**: Notifica dettagliata con risultati, film scelti dall'AI, round per round
- **Penalità ridotte**: Bonus vincitore invariati, penalità perdente ridotte dell'80% in modalità offline
- **Upgrade Infrastrutture**: Sistema 10 livelli con costi esponenziali, +2 sale, +25 posti, nuovi prodotti sbloccati per livello
- **Statistiche Cinema**: Affluenza/giorno, Occupazione, Gradimento sostituiscono i prezzi nel dettaglio (prezzi in popup separato)

### v0.080 - Locandina & Trailer Gratuiti (COMPLETATO)
### v0.079 - Contest, Revenue Infrastruttura & Mini-Giochi AI (COMPLETATO)
### v0.078 - GlobalPlayerPopup & Nickname Cliccabili (COMPLETATO)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~15.3k righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~14.5k righe App.js
- AI: OpenAI GPT-4o/GPT-4o-mini (Emergent LLM Key) per testo e mini-giochi
- Media: loremflickr.com (poster), FFmpeg (trailer)

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>14k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Contest Live**: matchmaking in tempo reale, classifiche
- [ ] Bug mobile residui

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Attività delle Major
- [ ] Mini-giochi Versus

### P3 - Backlog
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati Pydantic
- [ ] Scalabilità (Redis, load balancer, etc.)
