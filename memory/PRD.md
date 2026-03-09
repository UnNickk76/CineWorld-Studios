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
- [x] Studios: Hollywood, Warner Bros, Universal, Pinewood, Cinecittà, Babelsberg
- [x] Urban: Manhattan, West End, Montmartre, Shibuya, Dubai, Hong Kong
- [x] Nature: Grand Canyon, Swiss Alps, New Zealand, Amazon, Sahara
- [x] Historical: Colosseum, Versailles, Taj Mahal, Great Wall, Machu Picchu
- [x] Beach: Maldives, Hawaii, Bali, Caribbean, Santorini
- [x] Industrial: Akihabara, Detroit, London Docklands
- [x] Exotic: Antarctica, Arctic Circle, Space Simulation, Underwater Studio

### Marketplace Infrastrutture (COMPLETATO - 09/03/2025)
- [x] Compravendita tra giocatori (richiede livello 15)
- [x] Valutazione automatica basata su livello, fama, ricavi
- [x] Sistema offerte con accettazione/rifiuto
- [x] Trasferimento proprietà e fondi
- [x] Storico annunci e offerte

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
- [ ] Sistema "scoperta di una stella": annuncio nelle news quando un attore sconosciuto si rivela un talento
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

## Note Refactoring
- `frontend/src/App.js` è molto grande (3600+ righe) - considerare estrazione componenti in `/pages/`
- `backend/server.py` è il file principale - modularizzazione in corso con `game_systems.py` e `cast_system.py`
