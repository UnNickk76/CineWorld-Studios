# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.077

## Funzionalità Implementate (Sessione Corrente)

### v0.077 - Utenti Online & Amicizie nella Navbar - 10/03/2026 (COMPLETATO)
- **Icona Amici sempre visibile** nella navbar (rimossa restrizione `hidden sm:flex`)
- **Icona Utenti Online** nella navbar con badge contatore verde
- **Pannello Utenti Online:** dialog con lista utenti reali (cliccabili) e bot separati
- **Profilo Utente dal pannello:** stats (Film, Incassi, Qualità, XP, Premi, Fame), generi preferiti, film recenti
- **Header sticky nel profilo:** pulsante "Amicizia" (richiesta amicizia) + "Sfida" (naviga a /challenges)
- **Heartbeat** aggiornato con campo level per badge nella lista

### v0.076.2 - Automazione Note di Rilascio (COMPLETATO)
### v0.076.1 - Bug Fix Creazione Film (COMPLETATO)
### v0.076 - Giornale del Cinema & Sistema Critiche (COMPLETATO)
### v0.075 - Ribilanciamento Qualità Film (COMPLETATO)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14650 righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~13830 righe App.js
- AI: OpenAI GPT-4o, Sora 2, TTS-1 (Emergent LLM Key)

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici

### P1 - Completato questa sessione
- [x] Ribilanciamento qualità film
- [x] Bug creazione film (cast_members)
- [x] Giornale del Cinema & Critiche
- [x] Note rilascio aggiornate + automazione
- [x] Utenti Online & Amicizie nella navbar

### P2 - Prossimi
- [ ] Bug mobile residui
- [ ] Attività delle Major
- [ ] Sistema Acquisto CineCoins (Stripe)

### P3 - Future
- [ ] Mini-giochi Versus
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati Pydantic
- [ ] Scalabilità (Redis, load balancer, etc.)
