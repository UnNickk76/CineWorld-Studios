# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica dove i giocatori creano film, gestiscono cast, infrastrutture e competono per fama e incassi.

## Funzionalità Implementate

### Sistema di Autenticazione
- [x] Login/Registrazione con JWT
- [x] Profilo utente personalizzabile
- [x] Avatar generati via AI (Gemini Nano Banana)

### Creazione Film (Wizard 10 step)
- [x] Titolo, genere e sottogeneri
- [x] Sponsor e attrezzature
- [x] 60+ location (studios, urban, nature, historical, beach, industrial, exotic)
- [x] Sceneggiatori con stelle, fama, esperienza
- [x] Registi con stelle, fama, esperienza
- [x] Attori con stelle, fama, esperienza e ruoli
- [x] Sceneggiatura (manuale o AI con GPT-4o)
- [x] Campagna marketing
- [x] Pubblicità e riepilogo

### Sistema Cast Migliorato (COMPLETATO - 09/03/2025)
- [x] Rating a stelle (1-5) basato su skill
- [x] Categoria fama: unknown, known, rising, famous, superstar
- [x] Anni di esperienza (0-40)
- [x] Costo calcolato su stelle + fama + esperienza
- [x] 12 nazionalità con nomi autentici
- [x] Hidden Gems: talenti sconosciuti con alto potenziale

### Location Espanse (COMPLETATO - 09/03/2025)
- [x] 60+ location in 7 categorie
- [x] Studios, Urban, Nature, Historical, Beach, Industrial, Exotic

### Marketplace Infrastrutture (COMPLETATO - 09/03/2025)
- [x] Compravendita tra giocatori (richiede livello 15)
- [x] Valutazione automatica basata su livello, fama, ricavi
- [x] Sistema offerte con accettazione/rifiuto
- [x] Trasferimento proprietà e fondi

### Sistema Scoperta delle Stelle (COMPLETATO - 09/03/2025)
- [x] Hidden Gems: attori sconosciuti con alto potenziale (stelle >= 4)
- [x] Scoperta automatica quando usati in film di successo
- [x] News nel Cinema Journal per ogni scoperta
- [x] Annuncio nella chat pubblica
- [x] Ricompensa scopritore: $500K + 200 XP + 5 likeability
- [x] Hall of Fame delle stelle scoperte
- [x] L'attore scoperto diventa superstar

### Sistema Progressione
- [x] Livelli senza limite massimo
- [x] XP da mini-giochi, interazioni, film
- [x] Fama del giocatore che influenza incassi
- [x] Barra progressione sempre visibile

### Infrastrutture
- [x] 9 tipi: Cinema, Drive-In, Mall, Scuola Cinema, Studio, Megaplex, Arena, Studio Indie, Centro Post-Produzione
- [x] Acquisto in città mondiali con moltiplicatori
- [x] Gestione cinema (prezzi, programmazione film)

### Social
- [x] Feed con like, commenti, voti
- [x] Chat privata tra giocatori
- [x] Classifica globale e locale
- [x] Profili pubblici visitabili
- [x] Tour dei Cinema di altri giocatori

### Mini-Giochi
- [x] 4 partite ogni 4 ore
- [x] Ricompense in denaro e XP

### Economia
- [x] Incassi orari per i film
- [x] Durata programmazione dinamica
- [x] Rating IMDb simulato
- [x] Interazioni AI fittizie

### Eventi
- [x] Eventi Mondiali che influenzano il gameplay

## Backlog (Prossime Task)

### P0 - Alta Priorità
- [ ] Miglioramento/peggioramento abilità cast nel tempo

### P1 - Media Priorità
- [ ] Penalità per troppe valutazioni negative
- [ ] Immagini e messaggi vocali nelle chat
- [ ] Traduzione automatica chat

### P2 - Bassa Priorità
- [ ] Statistiche incassi per stato/città
- [ ] Sfide PvP tra giocatori

## Architettura Tecnica

```
/app/
├── backend/
│   ├── server.py         # FastAPI, API routes, WebSocket
│   ├── game_systems.py   # Livelli, infrastrutture, eventi
│   ├── cast_system.py    # Cast migliorato (stelle, fama, exp)
│   └── requirements.txt
├── frontend/
│   ├── src/App.js        # React SPA monolitico
│   └── package.json
└── memory/
    └── PRD.md
```

## Integrazioni
- **OpenAI GPT-4o**: Generazione sceneggiature (Emergent LLM Key)
- **Gemini Nano Banana**: Generazione avatar AI (Emergent LLM Key)
- **MongoDB**: Database principale

## API Endpoints Principali

### Cinema News & Stars
- `GET /api/cinema-news` - News delle scoperte
- `GET /api/discovered-stars` - Stelle scoperte

### Marketplace
- `GET /api/marketplace` - Lista annunci
- `POST /api/marketplace/list` - Metti in vendita
- `POST /api/marketplace/offer` - Fai offerta
- `GET /api/infrastructure/{id}/valuation` - Valutazione

### Cast
- `GET /api/actors` - Lista attori con stelle, fama, exp
- `GET /api/directors` - Lista registi
- `GET /api/screenwriters` - Lista sceneggiatori
- `GET /api/locations` - 60+ location disponibili
