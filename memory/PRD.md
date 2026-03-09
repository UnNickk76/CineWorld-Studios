# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica.

## Funzionalità Implementate

### Sessione 09/03/2025 - Aggiornamento Completo

#### Nuove Feature Implementate
- [x] **Compositore/Produttore Musicale**: Nuovo tipo di cast con skills musicali (Melodic Composition, Orchestration, Emotional Impact, Genre Versatility)
- [x] **Colonna Sonora AI**: Step 9 nel wizard per generare descrizioni della colonna sonora con prompt personalizzato (GPT-5.2)
- [x] **Fix Trailer Video**: Durata corretta a 4/8/12 secondi (Sora 2)
- [x] **Sistema Anteprime Esclusive**: Invita amici alla premiere del trailer, guadagna XP e Fama
- [x] **Wizard 12 Step**: Aggiornato da 10 a 12 step

#### Wizard Creazione Film (12 Step)
1. Title - Titolo e genere
2. Sponsor - Selezione sponsor
3. Equipment - Attrezzature e location
4. Writer - Sceneggiatore
5. Director - Regista
6. **Composer** - Compositore (NUOVO)
7. Cast - Attori con ruoli
8. Script - Sceneggiatura (con AI)
9. **Soundtrack** - Colonna sonora AI (NUOVO)
10. Poster - Generazione poster AI
11. Ads - Pubblicità
12. Review - Riepilogo e conferma

### Funzionalità Core (Completate)
- [x] Sistema XP Esponenziale: 50 * (1.037^level)
- [x] Incassi Bilanciati: quality^1.5×1000
- [x] Voti Non Modificabili
- [x] Tutorial 8 step, Credits
- [x] Notifiche real-time
- [x] Riscossione Incassi (max 4h)
- [x] Prompt Sceneggiatura AI
- [x] Sfide Versus
- [x] Saghe/Sequel (Lv.15+), Serie TV (Lv.20+), Anime (Lv.25+)
- [x] Noleggio Film nei cinema

### Sistema Cast Completo
- [x] Attori con ruoli (protagonista, antagonista, etc.)
- [x] Registi
- [x] Sceneggiatori
- [x] **Compositori** (NUOVO) - Skills: Melodic Composition, Orchestration, Emotional Impact, Genre Versatility

## Backlog Rimanente

### P1 - Prossime Task
- [ ] Mini-giochi Versus dalla chat privata
- [ ] UI Saghe/Serie TV (endpoint pronti)
- [ ] Bonus trailer collegato agli incassi

### P2 - Future
- [ ] Evoluzione abilità cast nel tempo
- [ ] Messaggi vocali/immagini in chat
- [ ] Statistiche incassi per stato/città

## API Endpoints Nuovi

### Compositori
- `GET /api/composers` - Lista compositori con skills musicali

### Colonna Sonora AI
- `POST /api/ai/soundtrack-description` - Genera descrizione colonna sonora
  - Params: title, genre, mood, custom_prompt

### Trailer Video
- `POST /api/ai/generate-trailer` - Genera trailer (4/8/12 sec)
- `GET /api/films/{id}/trailer-status` - Stato generazione

### Anteprime Esclusive
- `POST /api/premiere/invite` - Invita amico (friend_nickname)
- `GET /api/premiere/invites` - Lista inviti ricevuti
- `POST /api/premiere/view/{id}` - Visualizza e guadagna XP (+10 viewer, +25 inviter)

## Architettura
```
/app/
├── backend/
│   ├── server.py (5600+ righe)
│   ├── game_systems.py
│   └── cast_system.py
├── frontend/
│   └── src/App.js (4500+ righe)
└── memory/
    └── PRD.md
```

## 3rd Party Integrations
- **OpenAI GPT-5.2**: Sceneggiature, descrizioni colonne sonore
- **Gemini Nano Banana**: Avatar/poster AI
- **Sora 2**: Trailer video (4/8/12 sec)

## Test Reports
- `/app/test_reports/iteration_12.json` - 100% pass rate
