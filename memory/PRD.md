# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.095

## Funzionalità Implementate (Ultime)

### v0.095 - Ottimizzazione Velocità & Nuova Colonna Sonora - 12/03/2026
- **P0 Fix Critici:**
  - Fix crash Giornale del Cinema (NoneType su director/screenwriter)
  - Fix autenticazione login (axios interceptor per token reattivo, timeout ridotto a 30s)
  - Generazione trailer temporaneamente disabilitata (badge "In pausa")
- **P1 Velocità e Fluidità:**
  - Loading spinner ("Caricamento...") su ogni sezione del gioco con Suspense fallback
  - ErrorBoundary: le pagine non si bloccano più, mostrano pulsante "Riprova"
  - Infrastrutture disabilitate (visibili ma non cliccabili, opacity 40%)
  - Sfide VS disabilitate (visibili ma non cliccabili, opacity 40%)
- **P2 Gameplay:**
  - Rimossa generazione AI colonna sonora e relativo prompt
  - Nuovo sistema colonna sonora automatico: punteggio stile IMDb (stella + voto /10) basato su abilità compositore + genere film
  - Riepilogo costi dettagliato prima della creazione del film (Attrezzatura, Cast, Location, Sponsor, Net Cost vs Fondi)
  - Cast ampliato a 2000 per tipo (8000 totali) con 25+ nazionalità
  - 50 cast visibili per genere con refresh casuale ($sample) per massima varietà
- **P3:** Note di rilascio aggiornate a v0.095

### v0.094 - Fix Refactoring Frontend + Rinegoziazione - 11/03/2026
- Fix critico frontend post-refactoring (4 pagine + 3 inner components + 8+ import mancanti)
- Fix rinegoziazione contratti cast (probabilità minima 12%)
- Test di regressione completo frontend (iteration 41)

## Architettura Attuale
```
/app/backend/
├── server.py              # ~12.7k righe - In corso di riduzione
├── database.py, auth_utils.py, game_state.py
├── models/, routes/ (auth, notifications, social, infrastructure, minigames)

/app/frontend/
├── src/
│   ├── App.js             # ~1k righe (router + TopNavbar + ProtectedRoute)
│   ├── contexts/index.jsx # Auth con interceptor, LanguageContext, PlayerPopupContext
│   ├── components/        # ErrorBoundary, LoadingSpinner, PageTransition, shadcn/ui
│   └── pages/             # 31+ file di pagina (lazy-loaded)
```

## Features Disabilitate Temporaneamente
- Generazione Trailer AI (Sora 2)
- Infrastrutture (visibili, non cliccabili)
- Sfide VS Online (visibili, non cliccabili)
- Generazione AI Colonna Sonora (sostituita con scoring automatico)

## Backlog Refactoring
- [ ] Estrarre routes films da server.py
- [ ] Estrarre routes challenges da server.py
- [ ] Estrarre routes festivals da server.py
- [ ] Estrarre routes chat da server.py
- [ ] Estrarre TopNavbar, ProtectedRoute, UrlManager da App.js

## Backlog Feature
- P1: Completamento Gameplay Contest Live
- P1: Attività Major
- P1: Riabilitare Infrastrutture (dopo ottimizzazione)
- P1: Riabilitare Sfide VS (dopo ottimizzazione)
- P1: Fix e riabilitazione Trailer AI
- P2: Sistema Acquisto CineCoins (Stripe)
- P2: Classifiche VS / ELO
- P3: Script migrazione dati permanente

## Credenziali Test
- TestPlayer1: test1@test.com / Test1234!
- TestPlayer2: test2@test.com / Test1234!

## 3rd Party Integrations
- OpenAI GPT-4o (Text) - Emergent LLM Key
- OpenAI GPT-Image-1 (Images) - Emergent LLM Key
- Sora 2 (Video) - Emergent LLM Key (DISABILITATO TEMP)
- Resend (Email) - User API Key
