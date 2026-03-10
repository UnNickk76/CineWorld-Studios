# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.076

## Funzionalità Implementate (Sessione Corrente)

### v0.076.2 - Automazione Note di Rilascio - 10/03/2026 (COMPLETATO)
- **POST /api/release-notes** (solo Creator): endpoint per aggiungere nuove note con auto-incremento versione
- **Creator Board - Tab "Note Rilascio":** form con titolo, tipo (Novità/Miglioria/Fix), testo e pulsante Pubblica
- **Sicurezza:** solo NeoMorpheus può pubblicare note (403 per tutti gli altri)

### v0.076.1 - Bug Fix Creazione Film - 10/03/2026 (COMPLETATO)
- Fix critico `cast_members` NameError in create_film
- Retry automatico fetchPeople nel frontend
- Fix endpoint composers (NoneType)

### v0.076 - Giornale del Cinema & Sistema Critiche - 10/03/2026 (COMPLETATO)
- Icona Giornale nella navbar, barra sticky 4 categorie
- Hall of Fame con pre-ingaggio, Sistema Critiche Film

### v0.075 - Ribilanciamento Qualità Film - 10/03/2026 (COMPLETATO)
- Nuova formula quality_score, fix trailer/creator reply/virtual likes

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14600 righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~13700 righe App.js
- AI: OpenAI GPT-4o, Sora 2, TTS-1 (Emergent LLM Key)

## Backlog

### P0 - Critico
- [x] Ribilanciamento Qualità Film - v0.075
- [x] Bug creazione film - v0.076.1
- [ ] **Refactoring Critico**: server.py e App.js monolitici

### P1 - Completato
- [x] Fix Trailer Generation - v0.075
- [x] Fix Creator Reply - v0.075
- [x] Fix Virtual Likes - v0.075
- [x] Giornale del Cinema & Critiche - v0.076
- [x] Note di rilascio aggiornate - v0.076
- [x] Automazione note di rilascio - v0.076.2

### P2 - Prossimi
- [ ] Bug mobile residui
- [ ] Attività delle Major
- [ ] Sistema Acquisto CineCoins (Stripe)

### P3 - Future
- [ ] Mini-giochi Versus
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati Pydantic
- [ ] Scalabilità (Redis, load balancer, etc.)

## Scalabilità
- Stato attuale: ~100-300 giocatori simultanei supportati
- Per 1000+: serve Redis cache, load balancer, WebSocket pub/sub, refactoring
