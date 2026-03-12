# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.095

## Funzionalità Implementate (Ultime)

### v0.095b - Cast Realistico & Solo Italiano - 12/03/2026
- **Distribuzione età attori realistica:**
  - 45% (18-36), 33% (37-50), 12% (51-70), 5% (70-90), 3% (14-17), 2% (6-13 baby actors)
  - Registi, sceneggiatori, compositori hanno distribuzioni separate più mature
- **Skill decimali 0-100** (es. 78.7, 42.3) — 0 rarissimo, distribuzione realistica
  - SkillBadge mostra i decimali nell'interfaccia
  - `calculate_stars` ricalibrato per scala 0-100
- **Refresh cast automatico** ogni 12 giorni: +5% nuovi membri per tipo
- **Lingua forzata a italiano** — selettore lingua rimosso da TopNavbar, sidebar e AuthPage
- 8000 cast rigenerati (2000/tipo) con nuove regole

### v0.095 - Ottimizzazione Velocità & Nuova Colonna Sonora - 12/03/2026
- Fix crash Giornale del Cinema, fix login auth (interceptor)
- Colonna Sonora automatica con punteggio IMDb
- Riepilogo costi dettagliato prima della creazione film
- Cast ampliato a 2000/tipo, 50 visibili con refresh casuale
- ErrorBoundary + LoadingSpinner su tutte le pagine
- Infrastrutture e Sfide VS disabilitate temporaneamente
- Generazione trailer disabilitata temporaneamente

## Architettura Attuale
```
/app/backend/
├── server.py              # ~12.7k righe
├── cast_system.py         # Sistema cast con età/skill realistiche
├── database.py, auth_utils.py, game_state.py
├── routes/ (auth, notifications, social, infrastructure, minigames)
├── tests/ (test_iter43_cast_skills.py)

/app/frontend/
├── src/
│   ├── App.js             # Router, TopNavbar (senza selettore lingua)
│   ├── contexts/index.jsx # Auth interceptor, lingua forzata IT
│   ├── components/        # ErrorBoundary, LoadingSpinner, PageTransition
│   └── pages/             # 31+ pagine (lazy-loaded)
```

## Features Disabilitate Temporaneamente
- Generazione Trailer AI (Sora 2)
- Infrastrutture (visibili, non cliccabili)
- Sfide VS Online (visibili, non cliccabili)

## Backlog
- P1: Riabilitare Infrastrutture, Sfide VS, Trailer
- P1: Completamento Gameplay Contest Live
- P1: Attività Major
- P1: Continuare refactoring backend (films, challenges, festivals, chat)
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
