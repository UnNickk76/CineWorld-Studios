# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.092

## Funzionalità Implementate (Ultime)

### v0.092 - Refactoring Backend Step 1 + Feature v0.091 - 11/03/2026
**Refactoring:**
- Estratte auth routes in `routes/auth.py` (369 righe): register, login, recovery, profile, reset, avatar
- Estratte notification routes in `routes/notifications.py` (69 righe): CRUD notifiche, count, read, delete
- Creato `database.py`: connessione MongoDB condivisa
- Creato `auth_utils.py`: funzioni auth condivise (hash_password, verify_password, create_token, get_current_user)
- server.py ridotto da 15.564 a 15.026 righe (-538 righe)
- Rimossi duplicati route notifiche (erano presenti 2 volte)

**Feature v0.091:**
- Hamburger visibile su web
- Generazione Trailer con Sora 2 AI (costi variabili: base 10k, esponenziale)
- Sfide Offline grafica uniforme alle Online
- Cast espanso a 25 nazionalità (4000+ pool)
- Rinegoziazione cast verificata funzionante

### Versioni Precedenti
- v0.090: Fluidità Navigazione (PageTransition, Code-Splitting, Polling ottimizzato)
- v0.089: Report Manche Singole, Notifiche Cliccabili
- v0.087: Battaglie 3 Manche, Fix Qualità Film, Rinegoziazione Cast
- v0.085: Poster AI, Popup IMDb, Bonus Online
- v0.083: Mini-Giochi VS 1v1, Fix BattleAnimation

## Architettura Attuale
```
/app/backend/
├── server.py          # 15.026 righe (era 15.564) - Riduzione in corso
├── database.py        # Connessione MongoDB condivisa  
├── auth_utils.py      # Auth utilities condivise
├── models/            # Pydantic models
├── routes/
│   ├── auth.py        # Auth routes (369 righe)
│   └── notifications.py # Notification routes (69 righe)
├── cast_system.py     # Sistema cast (25 nazionalità)
├── challenge_system.py # Sistema sfide (3 manche)
└── ...
```

## Backlog Refactoring (In Corso)
- [ ] **Step 2**: Estrarre routes chat + users
- [ ] **Step 3**: Estrarre routes films  
- [ ] **Step 4**: Estrarre routes challenges
- [ ] **Step 5**: Estrarre routes infrastructure, marketplace
- [ ] **Step 6**: Estrarre routes festivals, minigames
- [ ] **Step 7**: Frontend - Estrarre pagine da App.js in file separati

## Backlog Feature
- P1: Completamento Gameplay Contest Live
- P1: Attività Major
- P2: Sistema Acquisto CineCoins (Stripe)
- P2: Classifiche VS / ELO
- P3: Scalabilità (Redis, load balancer)

## Credenziali di Test
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!
