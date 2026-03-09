# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sistema Cast v2 - 09/03/2025 (NUOVO)
- **700 membri del cast totali:**
  - 400 Attori con 8 skill attoriali
  - 100 Registi con 8 skill di regia
  - 100 Sceneggiatori con 8 skill di sceneggiatura
  - 100 Compositori con 6 skill musicali

- **Skill variabili:** Ogni membro ha un sottoinsieme unico di 3-6 skill (non tutti hanno le stesse)

- **5 Categorie:** Consigliati, Star, Conosciuti, Emergenti, Sconosciuti

- **Display skill nel wizard:**
  - 2 skill primarie (badge gialli) accanto al nome
  - 1 skill secondaria (badge grigio) accanto al nome
  - Indicatore "Ha già lavorato con noi" se utilizzato in film precedenti

- **Filtri nel wizard:**
  - Barra ricerca per categoria (All, Recommended, Star, Known, Emerging, Unknown)
  - Barra ricerca per skill specifica

- **Sistema Bonus/Malus:**
  - Cast adatto al genere del film → Bonus (+5% a +20%)
  - Cast senza skill del genere → Malus (-15%)
  - Endpoint: `GET /api/cast/bonus-preview?actor_id=X&film_genre=Y`

### Festival Cinematografici
- Festival ufficiali (tipo Oscar)
- Festival personalizzati creati dai giocatori
- Votazioni e classifiche
- Cerimonie di premiazione

### Mini Games
- Film Trivia, Guess the Genre, Director Match, Box Office Bet, Release Year
- Sfide giornaliere/settimanali

### Saghe & Serie TV
- Saghe/Sequel (Livello 15+)
- Serie TV (Livello 20+)
- Anime (Livello 25+)

### Altre Feature
- Reset totale player
- Toggle visualizzazione password login
- Wizard creazione film a 12 step (include compositore e colonna sonora AI)
- Bonus trailer dinamico (1-15% in base alla valutazione)

## API Endpoints

### Cast System v2
```
GET  /api/actors?category=X&skill=Y&limit=N
GET  /api/directors?category=X&skill=Y&limit=N
GET  /api/screenwriters?category=X&skill=Y&limit=N
GET  /api/composers?category=X&skill=Y&limit=N
GET  /api/cast/skills?role_type=actor|director|screenwriter|composer
GET  /api/cast/bonus-preview?actor_id=X&film_genre=Y
POST /api/cast/initialize  (auto-chiamato al startup)
```

### Saghe & Serie
```
GET  /api/saga/can-create
POST /api/films/{id}/create-sequel
GET  /api/series/my
POST /api/series/create
```

### Mini Games
```
GET  /api/minigames
POST /api/minigames/{game_id}/play
GET  /api/challenges/daily|weekly
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS
- Integrations: OpenAI GPT-4o (sceneggiature), Gemini Nano Banana (immagini), Sora 2 (trailer)

## Backlog

### P1 - In Progress
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live" animate

### P2 - Future
- [ ] Preascolto colonne sonore (bloccato - no API gratuite)
- [ ] Evoluzione abilità cast
- [ ] Refactoring server.py e App.js (file monolitici > 5000 righe)

### Issue Noti
- Traduzione categorie festival (da verificare)

## Test Reports
- `/app/test_reports/iteration_14.json` - Cast System v2 (100% pass)
