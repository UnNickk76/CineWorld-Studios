# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.083

## Funzionalità Implementate

### v0.083 - Mini-Giochi VS 1v1 & Fix Stabilità - 11/03/2026 (COMPLETATO)
- **Mini-Giochi VS 1v1**: Nuova modalità competitiva per tutti i 5 mini-giochi
  - Crea una sfida VS, rispondi alle domande e attendi un avversario
  - Tab "Sfide Aperte" per accettare sfide di altri giocatori
  - Tab "Storico" con vittorie, sconfitte e pareggi
  - Ricompense: vincitore x1.5, perdente x0.3, pareggio x0.8
  - Notifica al creatore quando l'avversario completa la sfida
- **Fix BattleAnimation (P0)**: Pulsante Chiudi (X), Salta Animazione e CONTINUA funzionanti
- **Fix Pydantic (P2)**: FilmResponse con campi Optional per compatibilità dati vecchi
- **Script Migrazione Dati**: 45 film e 41 utenti aggiornati con campi mancanti
- **Miglioramento Mobile**: overflow safety aggiunto a tutti i dialog
- **Note di Rilascio v0.083**: Aggiunte tutte le nuove funzionalità

### v0.082 - Sfide Offline VS + Upgrade Infrastrutture (COMPLETATO)
- Sfide Offline VS, Upgrade Infrastrutture, Statistiche Cinema, Popup Prezzi

### v0.080 - Locandina & Trailer Gratuiti (COMPLETATO)
### v0.079 - Contest, Revenue Infrastruttura & Mini-Giochi AI (COMPLETATO)
### v0.078 - GlobalPlayerPopup & Nickname Cliccabili (COMPLETATO)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~15.5k righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~14.7k righe App.js
- AI: OpenAI GPT-4o (Emergent LLM Key) per testo e mini-giochi
- Media: loremflickr.com (poster), FFmpeg (trailer)
- DB Collections nuove: `minigame_versus` per le sfide VS

## API Endpoints Nuovi (v0.083)
- `POST /api/minigames/versus/create` - Crea sfida VS
- `POST /api/minigames/versus/{id}/answer` - Invia risposte VS
- `GET /api/minigames/versus/pending` - Sfide aperte
- `POST /api/minigames/versus/{id}/join` - Unisciti a sfida VS
- `GET /api/minigames/versus/my` - Storico sfide VS

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>14k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Contest Live**: matchmaking in tempo reale, classifiche
- [ ] **Attività delle Major**: espandere sistema attività Major

### P2 - Futuri
- [ ] Sistema Acquisto CineCoins (Stripe)
- [ ] Mini-giochi Versus miglioramenti (classifiche VS, ELO system)

### P3 - Backlog
- [ ] Scalabilità (Redis, load balancer, etc.)

## Completati in questa sessione
- [x] Fix BattleAnimation (P0) - Pulsanti chiudi/salta/continua
- [x] Fix Mobile UI (P1) - overflow safety dialogs
- [x] Fix Pydantic Validation (P2) - FilmResponse Optional
- [x] Script Migrazione Dati (P3) - 45 film, 41 utenti aggiornati
- [x] Mini-Giochi VS 1v1 (P3) - Nuova funzionalità completa
- [x] Traduzione Categorie Festival (P3) - Già completato
- [x] Note di Rilascio v0.083
- [x] Pulizia codice morto backend (dead code dopo offline-battle)
