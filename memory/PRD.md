# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.078

## Funzionalità Implementate

### v0.078 - GlobalPlayerPopup & Nickname Cliccabili - 10/03/2026 (COMPLETATO)
- **GlobalPlayerPopup** si apre cliccando sul nickname di qualsiasi giocatore
- **ClickableNickname** wrappa i nickname in: Leaderboard, Chat, Festivals, Friends, Challenges
- **Pannello Giocatori** con lista online/offline nella navbar
- **Profilo nel pannello**: stats, film recenti, pulsanti azione (Amicizia, Sfida 1v1, Messaggio)
- **Testing completo**: Backend 11/11 test passati, Frontend 100% funzionante

### v0.077 - Utenti Online & Amicizie nella Navbar (COMPLETATO)
- Icona Amici sempre visibile nella navbar
- Icona Utenti Online nella navbar con badge contatore verde
- Pannello Utenti Online con lista utenti reali e bot separati
- Heartbeat aggiornato con campo level per badge nella lista

### v0.076.2 - Automazione Note di Rilascio (COMPLETATO)
### v0.076.1 - Bug Fix Creazione Film (COMPLETATO)
### v0.076 - Giornale del Cinema & Sistema Critiche (COMPLETATO)
### v0.075 - Ribilanciamento Qualità Film (COMPLETATO)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14675 righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~14228 righe App.js
- AI: OpenAI GPT-4o, Sora 2, TTS-1 (Emergent LLM Key)

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>14k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Sfide**: matchmaking, combattimento automatico, calcolo skill, bonus/malus, classifiche
- [ ] Bug mobile residui (nuove UI non testate su mobile)

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Attività delle Major
- [ ] Mini-giochi Versus

### P3 - Backlog
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati Pydantic
- [ ] Scalabilità (Redis, load balancer, etc.)

## Integrazioni 3rd Party
- OpenAI GPT-4o (Text): Emergent LLM Key
- Sora 2 (Video/Trailer): Emergent LLM Key
- OpenAI TTS-1 (Audio): Emergent LLM Key
- Resend (Email): User API Key
- FFmpeg: Sistema

## Credenziali Test
- User 1: testpopup@test.com / Test1234!
- User 2: testpopup2@test.com / Test1234!
- Creator: NeoMorpheus
