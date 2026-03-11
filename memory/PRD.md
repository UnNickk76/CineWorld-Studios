# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.094

## Funzionalità Implementate (Ultime)

### v0.094 - Fix Refactoring Frontend + Rinegoziazione - 11/03/2026
- **Fix critico frontend post-refactoring:**
  - Creati 4 componenti pagina mancanti: PasswordRecoveryPage, NicknameRecoveryPage, StatisticsPage, PlayerPublicProfile
  - Aggiunti 3 inner components mancanti: StatsDetailModal (Dashboard), SkillBadge (FilmWizard), UserProfileModal (ChatPage)
  - Corretti 8+ import mancanti di icone lucide-react in 6 file (ChallengesPage, InfrastructurePage, MarketplacePage, Dashboard, CinemaJournal, AuthPage)
  - Fix import mancanti: Smartphone, PlayerPopupContext, usePlayerPopup, API, TrendingDown, Calendar
  - Rimosso codice duplicato da NotificationsPage.jsx (App/ProtectedRoute/UrlManager)
  - Fix path alias (`@/` → `./`) per index.js e App.js
  - Esportato `API` da contexts per uso in UrlManager
- **Fix rinegoziazione contratti cast (P1):**
  - Introdotta probabilità minima di rifiuto del 12% per rendere la meccanica di rinegoziazione visibile a tutti i livelli
  - La rinegoziazione era tecnicamente funzionante ma invisibile per giocatori di basso livello con cast a 1-2 stelle
- **Test di regressione completo:** 18+ pagine verificate, 100% frontend pass rate (iteration 41)

### v0.093 - Refactoring Backend P0 Completo (Steps 2, 4-6) - 11/03/2026
- Estratti 6 moduli route da server.py (auth, notifications, social, infrastructure, minigames)
- server.py ridotto da 15.564 a 12.771 righe (-18%)

### v0.091-092 - Feature + Refactoring Step 1
- Hamburger visibile su web, Trailer Sora 2 AI, Cast espanso 25 nazionalità
- Sfide Offline grafica uniforme, PageTransition animato, Code-splitting

## Architettura Attuale
```
/app/backend/
├── server.py              # 12.771 righe - In corso di riduzione
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
├── cast_system.py, challenge_system.py, game_systems.py, social_system.py

/app/frontend/
├── src/
│   ├── App.js             # ~1.000 righe (router + TopNavbar + ProtectedRoute + UrlManager)
│   ├── contexts/index.jsx # AuthContext, LanguageContext, PlayerPopupContext, API
│   ├── constants/index.js # SKILL_TRANSLATIONS
│   ├── components/        # PageTransition, shared UI, shadcn/ui
│   └── pages/             # 31 file di pagina estratti (lazy-loaded)
```

## Backlog Refactoring Rimanente
- [ ] Estrarre routes films (~48 endpoint) da server.py
- [ ] Estrarre routes challenges (~20 endpoint) da server.py
- [ ] Estrarre routes festivals (~20 endpoint) da server.py
- [ ] Estrarre routes chat da server.py
- [ ] Frontend: Estrarre TopNavbar, ProtectedRoute, UrlManager da App.js in components/

## Backlog Feature
- P1: Completamento Gameplay Contest Live (matchmaking, classifiche)
- P1: Attività Major
- P2: Sistema Acquisto CineCoins (Stripe)
- P2: Classifiche VS / ELO
- P3: Script di migrazione dati permanente

## Credenziali
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!

## 3rd Party Integrations
- OpenAI GPT-4o (Text Generation) - Emergent LLM Key
- OpenAI GPT-Image-1 (Image Generation) - Emergent LLM Key
- Sora 2 (Video Generation) - Emergent LLM Key
- Resend (Email) - User API Key (RESEND_API_KEY)
