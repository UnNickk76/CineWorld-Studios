# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.079

## Funzionalità Implementate

### v0.079 - Contest + Infrastructure Revenue + AI Mini-Games - 10/03/2026 (COMPLETATO)
- **Rename Sfide → Contest**: Testo cambiato in tutte le 5 lingue (EN, IT, ES, FR, DE) e nell'UI Dashboard
- **Fix Infrastructure Revenue**: Lo scheduler ora processa TUTTI i tipi di infrastruttura (cinema, drive_in, multiplex_small/medium/large, vip_cinema, production_studio, cinema_school, ecc.), non più solo `type: 'cinema'`. Frequenza aggiornata da 6h a 2h. Aggiunto reddito minimo garantito per livello
- **AI Mini-Games**: Le domande sono ora generate da GPT-4o-mini ad ogni partita. Supportati tutti e 5 i tipi (trivia, guess_genre, director_match, box_office_bet, year_guess). Le domande già viste vengono tracciate e il prompt le esclude. Fallback alla pool statica in caso di errore AI
- **Testing completo**: Backend 14/14 test passati, Frontend 100%

### v0.078 - GlobalPlayerPopup & Nickname Cliccabili - 10/03/2026 (COMPLETATO)
- GlobalPlayerPopup si apre cliccando sul nickname di qualsiasi giocatore
- ClickableNickname wrappa i nickname in: Leaderboard, Chat, Festivals, Friends, Challenges
- Pannello Giocatori con lista online/offline nella navbar

### v0.077 e precedenti (vedi changelog)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14.7k righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~14.2k righe App.js
- AI: OpenAI GPT-4o/GPT-4o-mini, Sora 2, TTS-1 (Emergent LLM Key)

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>14k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Sfide/Contest**: matchmaking, combattimento automatico, calcolo skill, bonus/malus, classifiche
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
- OpenAI GPT-4o-mini (Mini-games AI): Emergent LLM Key
- Sora 2 (Video/Trailer): Emergent LLM Key
- OpenAI TTS-1 (Audio): Emergent LLM Key
- Resend (Email): User API Key
- FFmpeg: Sistema

## Credenziali Test
- User 1: testpopup@test.com / Test1234!
- User 2: testpopup2@test.com / Test1234!
- Creator: NeoMorpheus
