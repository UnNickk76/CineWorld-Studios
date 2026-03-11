# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.093

## Funzionalità Implementate (Ultime)

### v0.093 - Refactoring Backend P0 Completo (Steps 2, 4-6) - 11/03/2026
- Estratti 6 moduli route da server.py:
  - `routes/auth.py` (369 righe): Register, Login, Recovery, Profile, Avatar
  - `routes/notifications.py` (69 righe): CRUD Notifiche
  - `routes/social.py` (189 righe): Friends, Follow, Social Stats
  - `routes/infrastructure.py` (1220 righe): Infrastructure + Marketplace
  - `routes/minigames.py` (431 righe): Minigames, Cooldowns, Versus
- Creati moduli condivisi: database.py, auth_utils.py, game_state.py, game_data_minigames.py
- **server.py ridotto da 15.564 a 12.771 righe (-18%, -2.793 righe)**
- Rimossi duplicati route notifiche

### v0.091-092 - Feature + Refactoring Step 1
- Hamburger visibile su web, Trailer Sora 2 AI, Cast espanso 25 nazionalità
- Sfide Offline grafica uniforme, PageTransition animato, Code-splitting

## Architettura Attuale
```
/app/backend/
├── server.py              # 12.771 righe (era 15.564) - In corso di riduzione
├── database.py            # Connessione MongoDB condivisa
├── auth_utils.py          # Auth utilities condivise
├── game_state.py          # Stato globale (online_users, CHAT_BOTS)
├── game_data_minigames.py # Costanti minigame e trivia
├── models/                # Pydantic models
├── routes/
│   ├── auth.py            # 369 righe
│   ├── notifications.py   # 69 righe
│   ├── social.py          # 189 righe
│   ├── infrastructure.py  # 1.220 righe
│   └── minigames.py       # 431 righe
├── cast_system.py         # Sistema cast (25 nazionalità)
├── challenge_system.py    # Sistema sfide (3 manche)
├── game_systems.py        # Sistemi di gioco
└── social_system.py       # Sistema sociale
```

## Backlog Refactoring Rimanente
- [ ] Step 3: Estrarre routes films (~48 endpoint) - Il blocco più grande
- [ ] Step 4b: Estrarre routes challenges (~20 endpoint, dipendenze complesse)
- [ ] Step 6b: Estrarre routes festivals (~20 endpoint, dipendenze TTS)
- [ ] Step 7: Frontend - Estrarre pagine da App.js (~15k righe)

## Backlog Feature
- P1: Completamento Gameplay Contest Live
- P1: Attività Major
- P2: Sistema Acquisto CineCoins (Stripe)
- P2: Classifiche VS / ELO

## Credenziali
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!
