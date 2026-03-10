# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.076

## Funzionalità Implementate (Ultime)

### v0.076.1 - Bug Fix Creazione Film - 10/03/2026 (COMPLETATO)
- **Fix critico `cast_members` NameError:** La creazione del film falliva all'ultimo step perché `cast_members` non era definito nella funzione `create_film`. Ora i dati del cast vengono caricati dal DB prima del calcolo qualità.
- **Fix lista attori vuota:** Aggiunta gestione errori con retry automatico in `fetchPeople` (frontend). Se la chiamata fallisce, riprova dopo 1 secondo.
- **Fix endpoint composers:** Corretto crash quando `film.composer` era `None` invece di `dict` vuoto.

### v0.076 - Giornale del Cinema & Sistema Critiche - 10/03/2026 (COMPLETATO)
- Icona Giornale del Cinema nella navbar fissa
- Barra sticky con 4 categorie: News, Pubblico, Breaking News, Hall of Fame
- Hall of Fame con stelle scoperte e pre-ingaggio diretto
- Sistema Critiche Film con bonus/malus su spettatori/incassi/rating
- Note di rilascio aggiornate dalla v0.069 alla v0.076

### v0.075 - Ribilanciamento Qualità Film - 10/03/2026 (COMPLETATO)
- Nuova formula quality_score con distribuzione realistica
- Fix trailer con retry, Fix Creator reply, Fix virtual likes

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14500 righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~13600 righe App.js
- AI: OpenAI GPT-4o, Sora 2, TTS-1 (Emergent LLM Key)

## Backlog

### P0 - Critico
- [x] Ribilanciamento Qualità Film - COMPLETATO v0.075
- [x] Bug creazione film (cast_members) - COMPLETATO v0.076.1
- [ ] **Refactoring Critico**: server.py e App.js monolitici - URGENTE

### P1 - Priorità Alta
- [x] Fix Trailer Generation - v0.075
- [x] Fix Creator Reply - v0.075
- [x] Fix Virtual Likes - v0.075
- [x] Giornale del Cinema & Critiche - v0.076
- [x] Note di rilascio aggiornate - v0.076
- [ ] Bug mobile residui
- [ ] Automazione note di rilascio

### P2 - Priorità Media
- [ ] Attività delle Major
- [ ] Sistema Acquisto CineCoins (Stripe)

### P3 - Future
- [ ] Mini-giochi Versus
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati Pydantic
