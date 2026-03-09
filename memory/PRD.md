# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate - Sessione 09/03/2025

### Mini Games ✅ (già esistenti)
- **Film Trivia** - Domande sui film ($5K-$50K)
- **Guess the Genre** - Indovina il genere ($3K-$30K)
- **Director Match** - Abbina registi ai film ($4K-$40K)
- **Box Office Bet** - Indovina incassi ($10K-$100K)
- **Release Year** - Indovina anno uscita ($6K-$60K)

**Sfide Giornaliere/Settimanali:**
- Social Butterfly, Chatterbox, Gamer, Explorer

### UI Saghe & Serie TV ✅ (NUOVO)
- **Pagina /sagas** con 3 tab: Saghe & Sequel, Serie TV, Anime
- **Requisiti visualizzati:**
  - Saghe/Sequel: Livello 15+, Fama 100+
  - Serie TV: Livello 20+, Fama 200+
  - Anime: Livello 25+, Fama 300+
- **Creazione Serie/Anime** con dialog:
  - Titolo, Genere, Episodi, Durata, Sinossi
  - Budget calcolato automaticamente
- **Lista film idonei** per creare sequel (max 5 per saga)

### Altre Feature della Sessione
- Reset totale player (doppia conferma)
- Festival personalizzati (player-created)
- Cerimonie live
- Toggle visualizzazione password login

## API Endpoints

### Saghe & Serie
```
GET  /api/saga/can-create          - Verifica requisiti sequel
GET  /api/films/{id}/can-create-sequel
POST /api/films/{id}/create-sequel
GET  /api/series/can-create        - Verifica requisiti serie
POST /api/series/create
GET  /api/series/my
```

### Mini Games
```
GET  /api/minigames
POST /api/minigames/{game_id}/play
GET  /api/challenges/daily
GET  /api/challenges/weekly
```

## Backlog

### P1 - Completato
- ✅ Mini Games UI
- ✅ Saghe & Serie TV UI

### P2 - Future
- [ ] Bonus trailer collegato agli incassi
- [ ] Sfide versus dalla chat privata
- [ ] Evoluzione abilità cast

## Test Reports
- Frontend: Screenshots confermano funzionamento
