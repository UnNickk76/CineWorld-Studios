# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.073

## Funzionalità Implementate (Ultime)

### v0.073 - Giornale del Cinema & Critiche Film - 10/03/2026 (COMPLETATO)
- **Icona Giornale del Cinema nella navbar:** Aggiunta icona Newspaper cliccabile nella barra fissa superiore, naviga a /journal
- **Rimozione Breaking News inline:** Rimossa la sezione "Breaking News" e "Hall of Fame" dalla board principale del Giornale
- **Barra sticky categorie:** 4 pulsanti fissi (News, Pubblico, Breaking News, Hall of Fame) che restano visibili durante lo scroll
- **Rinomina "Altre News" → "Breaking News":** Dialog aggiornato con stile rosso
- **Hall of Fame Dialog:** Popup con le nuove stelle del cinema scoperte, cliccabili per pre-ingaggiarle direttamente
- **Sistema Critiche Film:**
  - 2-4 recensioni generate automaticamente alla creazione di ogni film
  - 15 giornali fittizi (Variety, Cahiers du Cinéma, etc.) con bias e prestigio
  - 20 giornalisti fittizi
  - Sentimento basato sulla qualità del film (positivo/neutro/negativo)
  - Bonus/malus su: spettatori, incassi (%), rating
  - Popup animato al rilascio del film con tier + recensioni critiche
  - Template in italiano e inglese

### v0.072 - Ribilanciamento Qualità Film & Fix P1 - 10/03/2026 (COMPLETATO)
- Ribilanciamento qualità film con distribuzione realistica
- Fix trailer con retry automatico
- Fix Creator reply (room_id corretto)
- Fix virtual likes nel modello FilmResponse

## Architettura
- Backend: FastAPI + MongoDB (motor)
- Frontend: React + TailwindCSS + Shadcn/UI
- AI: OpenAI GPT-4o, Sora 2 (Emergent LLM Key)
- Audio: OpenAI TTS-1

## Backlog

### P0 - Critico
- [x] Ribilanciamento Qualità Film - COMPLETATO v0.072
- [ ] **Refactoring Critico**: server.py (~14500 righe) e App.js (~13600 righe) - URGENTE

### P1 - Priorità Alta
- [x] Fix Trailer Generation - Migliorato con retry - v0.072
- [x] Fix Creator Reply - v0.072
- [x] Fix Virtual Likes in API - v0.072
- [x] Icona Giornale nella navbar - v0.073
- [x] Riorganizzazione Giornale del Cinema - v0.073
- [x] Sistema Critiche Film - v0.073
- [ ] **Bug Mobile Residui**: Verificare funzionalità su mobile
- [ ] **Automazione Note di Rilascio**

### P2 - Priorità Media
- [ ] Attività delle Major: Co-Produzioni, Sfide tra Major
- [ ] Sistema Acquisto CineCoins (Stripe)

### P3 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati per errori Pydantic
