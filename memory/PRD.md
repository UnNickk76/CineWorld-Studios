# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.087

## Funzionalità Implementate

### v0.087 - Battaglie 3 Manche, Fix Qualità & Rinegoziazione - 11/03/2026 (COMPLETATO)
- **Battaglie 3 Manche**: Ogni sfida = 3 manche, ciascuna Film vs Film con 8 skill battles
- **Spareggio Gradimento**: Se una manche finisce 4-4, spareggio basato sul gradimento del pubblico
- **Fix Qualità Film**: Base qualità da 35→42, luck factor bilanciato, random roll simmetrico. I film non escono più tutti scarsi/flop
- **Rinegoziazione Cast**: Quando un attore rifiuta, puoi rilanciare fino a 3 volte con offerta più alta

### v0.085 - Poster AI, Battaglie 8 Skill & Popup IMDb (COMPLETATO)
- Locandine AI GPT Image 1, Popup IMDb dettaglio, Bonus Online +15%, Dashboard pulita

### v0.083 - Mini-Giochi VS 1v1 & Fix Stabilità (COMPLETATO)
- Mini-Giochi VS 1v1, Fix BattleAnimation, Fix Pydantic, Script migrazione dati

### Versioni precedenti (v0.080-v0.082)
- Sfide Offline VS AI, Upgrade Infrastrutture, Statistiche Cinema, Locandine Gratuite

## Architettura
- Backend: FastAPI + MongoDB (motor), server.py (~15.5k righe)
- Frontend: React + TailwindCSS + Shadcn/UI, App.js (~15k righe)
- AI: OpenAI GPT-4o (text), GPT Image 1 (poster) via Emergent LLM Key
- Battle System: challenge_system.py (3 manche x 8 skill + tiebreaker)
- DB Collections: films, users, user_infrastructures, challenges, minigame_versus, rejections, notifications

## API Endpoints Chiave
- `POST /api/ai/poster` - Genera poster AI con GPT Image 1
- `POST /api/cast/renegotiate/{id}` - Rinegozia contratto cast (max 3 tentativi)
- `POST /api/minigames/versus/create` - Crea sfida VS mini-giochi
- `POST /api/challenges/offline-battle` - Sfida offline vs AI

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>15k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Contest Live**: matchmaking avanzato, classifiche
- [ ] **Attività delle Major**: espandere sistema attività

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Classifiche VS e sistema ELO per mini-giochi

### P3 - Backlog
- [ ] Scalabilità (Redis, load balancer)

## Credenziali di Test
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!
