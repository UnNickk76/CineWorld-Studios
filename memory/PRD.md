# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.080

## Funzionalità Implementate

### v0.080 - Poster & Trailer Gratuiti - 10/03/2026 (COMPLETATO)
- **Locandina**: Generazione gratuita via loremflickr.com (immagini stock per genere). Fallback a picsum.photos
- **Trailer**: Generazione gratuita via FFmpeg con effetto Ken Burns, sovrapposizioni testo (titolo, genere, cast, studio), fade in/out. ~3 secondi di elaborazione
- Rimossi servizi a pagamento (gpt-image-1 per poster, Sora 2 per trailer)
- Trailer supporta durate 4, 8 e 12 secondi in formato H.264 1280x720
- Testing: Backend 12/13 passed (92%), Frontend Login/Dashboard/Create OK

### v0.079 - Contest, Revenue Infrastruttura & Mini-Giochi AI (COMPLETATO)
- Rename Sfide → Contest in tutte le lingue
- Fix revenue infrastruttura: scheduler processa TUTTI i tipi
- Mini-giochi con domande AI (GPT-4o-mini)

### v0.078 - GlobalPlayerPopup & Nickname Cliccabili (COMPLETATO)
### v0.077 - Pannello Giocatori & Icona Amicizie (COMPLETATO)
### v0.076 e precedenti (vedi changelog)

## Architettura
- Backend: FastAPI + MongoDB (motor), ~14.8k righe server.py
- Frontend: React + TailwindCSS + Shadcn/UI, ~14.2k righe App.js
- AI: OpenAI GPT-4o/GPT-4o-mini (Emergent LLM Key) per testo e mini-giochi
- Media: loremflickr.com (poster), FFmpeg (trailer), TTS-1 (audio)

## Backlog

### P0 - Critico
- [ ] **Refactoring Critico**: server.py e App.js monolitici (>14k righe ciascuno)

### P1 - Prossimi
- [ ] **Completamento Gameplay Contest**: matchmaking, combattimento automatico, skill, classifiche
- [ ] Bug mobile residui

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
- loremflickr.com (Poster images): GRATUITO, nessuna chiave
- FFmpeg (Trailer video): GRATUITO, installato a livello di sistema
- OpenAI TTS-1 (Audio): Emergent LLM Key
- Resend (Email): User API Key

## Credenziali Test
- User 1: testpopup@test.com / Test1234!
- User 2: testpopup2@test.com / Test1234!
- Creator: NeoMorpheus
