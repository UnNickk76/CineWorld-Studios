# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica.

## Funzionalità Implementate (Sessione 09/03/2025)

### Bug Fix Critici
- [x] **Sistema XP Esponenziale**: Formula 50 * (1.037^level) → 51 XP livello 1, ~1891 XP livello 100
- [x] **Incassi Bilanciati**: Ridotti da quality×150000 a quality^1.5×1000 ($10K-$1M cap)
- [x] **Voti Non Modificabili**: I voti ai film sono permanenti

### Nuove Funzionalità
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

### Sistema Cast
- [x] Attori, Registi, Sceneggiatori con stelle/fama/esperienza
- [x] Compositori musicali (nuovo)
- [x] 12 nazionalità, 60+ location

### Infrastrutture
- [x] 9 tipi disponibili
- [x] Sistema programmazione film (propri + affitto altri)
- [x] Riscossione incassi ogni ora (max 4h)
- [x] Marketplace compravendita (livello 15+)

## Backlog Rimanente

### Da Completare (questa sessione)
- [ ] **Trailer Video AI** (15 sec) - Richiede integrazione Sora 2
- [ ] **Fix errori mobile** - Da investigare
- [ ] **Colonna Sonora AI** - Generazione musica con prompt

### P1 - Prossime Task
- [ ] Evoluzione abilità cast nel tempo
- [ ] Penalità valutazioni negative
- [ ] Messaggi vocali/immagini in chat

### P2 - Future
- [ ] Statistiche incassi per stato/città
- [ ] Sfide PvP avanzate

## API Endpoints Nuovi

### Tutorial & Credits
- `GET /api/game/tutorial` - 8 step tutorial
- `GET /api/game/credits` - Crediti gioco

### Notifiche
- `GET /api/notifications` - Lista notifiche
- `POST /api/notifications/{id}/read` - Segna come letta
- `POST /api/notifications/read-all` - Segna tutte lette

### Riscossione Incassi
- `GET /api/infrastructure/{id}/pending-revenue` - Incassi pendenti
- `POST /api/infrastructure/{id}/collect-revenue` - Riscuoti

### Sfide Versus
- `POST /api/challenges/send` - Invia sfida
- `POST /api/challenges/{id}/respond` - Accetta/Rifiuta
- `POST /api/challenges/{id}/submit-result` - Invia punteggio
- `GET /api/challenges/pending` - Sfide pendenti

### Saghe e Serie
- `GET /api/films/{id}/can-create-sequel` - Verifica possibilità
- `POST /api/films/{id}/create-sequel` - Crea sequel
- `GET /api/series/can-create` - Verifica per serie/anime
- `POST /api/series/create` - Crea serie/anime
- `GET /api/series/my` - Le mie serie

### Cast
- `GET /api/composers` - Lista compositori
- `POST /api/ai/soundtrack-description` - Descrizione colonna sonora AI

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
│   ├── server.py (5300+ righe)
│   ├── game_systems.py
│   ├── cast_system.py
│   └── tests/
├── frontend/
│   └── src/App.js (4200+ righe)
└── memory/
    └── PRD.md
```
