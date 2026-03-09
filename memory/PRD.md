# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica.

## Funzionalità Implementate

### Sessione 09/03/2025 - Aggiornamento
- [x] **Trailer Video AI (Sora 2)**: Sezione completa nel FilmDetail con generazione, stato, visualizzazione video
- [x] **Visibilità Lista Cast Aumentata**: Altezze aumentate da 280px/200px a 400px/350px nel wizard
- [x] **Bug Fix trailer-status API**: Corretto 404 per film senza campi trailer

### Funzionalità Core (Completate)
- [x] **Sistema XP Esponenziale**: Formula 50 * (1.037^level) → 51 XP livello 1, ~1891 XP livello 100
- [x] **Incassi Bilanciati**: Ridotti da quality×150000 a quality^1.5×1000 ($10K-$1M cap)
- [x] **Voti Non Modificabili**: I voti ai film sono permanenti
- [x] **Tutorial**: 8 step interattivi (/tutorial)
- [x] **Credits**: Pagina crediti (/credits)
- [x] **Sistema Notifiche**: /api/notifications con conteggio non lette
- [x] **Riscossione Incassi**: Bottone "Riscuoti Ora" nelle infrastrutture (max 4h cumulative)
- [x] **Prompt Sceneggiatura AI**: Campo per indicare la propria idea creativa
- [x] **Sfide Versus**: Minigiochi contro altri giocatori via chat ($0-$10K scommessa)
- [x] **Compositori Musicali**: Nuovo tipo di cast con skill dedicate
- [x] **Saghe/Sequel**: Livello 15+ Fama 100+ (max 5 sequel per saga)
- [x] **Serie TV**: Livello 20+ Fama 200+
- [x] **Anime**: Livello 25+ Fama 300+
- [x] **Noleggio Film**: Sistema completo per proiettare film altrui nei propri cinema

### Sistema Cast
- [x] Attori, Registi, Sceneggiatori con stelle/fama/esperienza
- [x] Compositori musicali
- [x] 12 nazionalità, 60+ location

### Infrastrutture
- [x] 9 tipi disponibili
- [x] Sistema programmazione film (propri + affitto altri)
- [x] Riscossione incassi ogni ora (max 4h)
- [x] Marketplace compravendita (livello 15+)

## Backlog Rimanente

### P1 - Prossime Task
- [ ] **Mini-giochi Versus avanzati**: Logica sfide dalla chat privata con ricompense XP/denaro
- [ ] **Saghe e Serie TV UI**: Sviluppare interfaccia per creare saghe e serie TV
- [ ] **Trailer Video con Bonus**: Collegare trailer a bonus/malus effettivo per incassi

### P2 - Future
- [ ] Evoluzione abilità cast nel tempo
- [ ] Penalità valutazioni negative
- [ ] Messaggi vocali/immagini in chat
- [ ] Statistiche incassi per stato/città

## API Endpoints

### Trailer Video
- `POST /api/ai/generate-trailer` - Genera trailer AI (Sora 2)
- `GET /api/films/{film_id}/trailer-status` - Stato generazione trailer
- `GET /api/trailers/{film_id}.mp4` - Serve video trailer

### Tutorial & Credits
- `GET /api/game/tutorial` - 8 step tutorial
- `GET /api/game/credits` - Crediti gioco

### Notifiche
- `GET /api/notifications` - Lista notifiche
- `POST /api/notifications/{id}/read` - Segna come letta

### Sfide Versus
- `POST /api/challenges/send` - Invia sfida
- `POST /api/challenges/{id}/respond` - Accetta/Rifiuta
- `GET /api/challenges/pending` - Sfide pendenti

### Saghe e Serie
- `GET /api/films/{id}/can-create-sequel` - Verifica possibilità
- `POST /api/films/{id}/create-sequel` - Crea sequel
- `POST /api/series/create` - Crea serie/anime

## Requisiti Sblocco

| Contenuto | Livello | Fama |
|-----------|---------|------|
| Cinema | 5 | 20 |
| Marketplace | 15 | - |
| Saghe/Sequel | 15 | 100 |
| Serie TV | 20 | 200 |
| Anime | 25 | 300 |

## Architettura
```
/app/
├── backend/
│   ├── server.py (5500+ righe)
│   ├── game_systems.py
│   ├── cast_system.py
│   └── tests/
├── frontend/
│   └── src/App.js (4400+ righe)
└── memory/
    └── PRD.md
```

## 3rd Party Integrations
- **OpenAI GPT-4o**: Generazione sceneggiature (Emergent LLM Key)
- **Gemini Nano Banana**: Generazione avatar/poster AI (Emergent LLM Key)
- **Sora 2**: Generazione trailer video (Emergent LLM Key)

## Test Reports
- `/app/test_reports/iteration_11.json` - Latest
