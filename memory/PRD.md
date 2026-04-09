# CineWorld Studio - PRD

## Problema Originale
Gioco browser di simulazione cinematografica. L'utente gestisce uno studio, produce film/serie/anime, gestisce una rete TV.

## Architettura
- **Frontend**: React (SPA), pagine in `/app/frontend/src/pages/`
- **Backend**: FastAPI, routes in `/app/backend/routes/`
- **Database**: MongoDB

## Funzionalità Implementate

### Core
- Auth (login/register), Dashboard, Profilo
- Sistema fondi, Moneta virtuale, Daily bonus

### Pipeline V2 (Film/Serie/Anime)
- Produzione multi-step (concept -> script -> cast -> filming -> post -> release)
- Sistema stagioni multiple con franchise fatigue
- Generazione episodi persistente (titolo, trama, tipo: normal/peak/filler/plot_twist/season_finale)
- Cast con animatori/doppiatori per anime
- UI stile Netflix per episodi

### Emittente TV (Palinsesto)
- Creazione stazione TV con infrastruttura
- Aggiunta contenuti (film/serie/anime) al palinsesto
- Sistema Broadcast Episodi:
  - Trasmissione in tempo reale (1 ep ogni X giorni, configurabile)
  - Modalità Binge (tutti gli episodi subito)
  - Auto-avanzamento basato su timestamp reale
  - Performance per-episodio (viewers, revenue, rating)
  - Post-stagione: Repliche (audience al 40%) o Ritiro
  - Revenue accreditato automaticamente all'utente
- Sezioni Netflix, Classifica stazioni, Marketplace

### Sistema Notifiche Globale (NUOVO)
- **Backend**: `notification_helper.py` - utility globale richiamabile da qualsiasi route
- **Categorie**: production, tv_episodes, events, economy, social, infrastructure, arena, minigames
- **Priorità**: high (popup), medium (toast), low (badge only)
- **Anti-spam**: raggruppamento notifiche simili (finestra 5 min), cooldown popup 30s
- **NotificationProvider**: polling centralizzato (30s count, 15s popup), soppressione popup al login
- **UI**: Badge rosso con conteggio nella navbar, pagina con tab categorie + tab severità
- **Endpoints**: GET /notifications (con category filter), GET /notifications/stats, GET /notifications/popup (solo high/medium)

### Dialog Conferma Custom (NUOVO)
- `ConfirmDialog.jsx` con `useConfirm()` hook - sostituisce tutti i `window.confirm()`
- Design: sfondo scuro, bordo giallo glow, mascotte Velion + CineOx, bottoni stilizzati
- Tutti i confirm del gioco (10+ occorrenze) convertiti al nuovo stile

### Minigiochi Arcade
- TapCiak, SceneFlip, CatchTheStar, Velion AI

### Admin
- Tool Migrazione V1 -> V2

## Backlog

### P1
- Fix minigiochi residui (TapCiak, ecc.)
- Fase 3 Mercato: vendita serie/anime e distribuzione

### P2
- Sfida della Settimana (minigioco rotante con premi)

### P3
- Previsioni Festival
- Marketplace diritti TV/Anime
- Velion Mood, Chat Evolution, CinePass+Stripe
- Push notifications, Velion Livelli

## Credenziali Test
- Email: fandrex1@gmail.com
- Password: Fandrel2776
- Nickname: NeoMorpheus
