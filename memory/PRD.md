# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sistema Cast Espanso - 09/03/2026 (COMPLETATO)
- **Pool di 2000+ membri** (500 per tipo: attori, registi, sceneggiatori, compositori)
- **Generazione automatica giornaliera**: 40-80 nuovi membri del cast ogni giorno
- **Fix skill decimali**: Tutte le skill ora sono interi (nessun decimale)
- **Database nomi esteso**: Migliaia di nomi realistici da 12+ paesi
- **Endpoint nuovi**: `/api/cast/stats`, `/api/cast/new-arrivals`

### CineBoard & Film Rankings - 09/03/2026 (COMPLETATO)
- **CineBoard** con due tab: "In Sala (Top 50)" e "Hall of Fame"
- Punteggio CineBoard calcolato con formula multi-variabile:
  - Qualità 30%, Incassi 25%, Popolarità 20%, Premi 15%, Longevità 10%
- Sinossi film generata automaticamente via AI (GPT-4o-mini) alla creazione
- Valutazione IMDb integrata nella pagina dettaglio film
- Endpoint: `/api/cineboard/now-playing`, `/api/cineboard/hall-of-fame`

### Sistema Trailer con Auto-Reset - 09/03/2026 (COMPLETATO)
- Fix del bug dei trailer bloccati (generazione che non termina mai)
- Aggiunto timeout automatico di 15 minuti per trailer stuck
- Nuovo endpoint per reset manuale: `POST /api/films/{film_id}/reset-trailer`
- Campo `trailer_started_at` per tracciare l'inizio della generazione

### Attività delle Major - 09/03/2026 (COMPLETATO)
- **Sfide Settimanali** che ruotano automaticamente (6 tipi diversi)
- **Attività disponibili**: 
  - Co-Produzione (+10% Qualità, +15% Incassi)
  - Condivisione Risorse (-20% costi)
  - Premiere della Major (+50 Likes, +10 Fame)
  - Scambio Talenti (scambio stelle scoperte)
  - Proiezione Collettiva (x1.25 incassi)
- UI con visualizzazione bonus e cooldown

### Sistema Social Completo - 09/03/2026 (COMPLETATO)

#### Major (Alleanze)
- Pagina `/major` per creare e gestire alleanze
- Requisito livello 20 + $5M per creare una Major
- Visualizzazione membri con ruoli (Fondatore, Vice, Produttore Senior, Membro)
- Bonus Major: Qualità, Incassi, XP basati sul livello dell'alleanza
- Generazione logo AI (Gemini Nano Banana)

#### Amici & Follower
- Pagina `/friends` con 4 tab: Amici, Follower, Seguiti, Richieste
- Invio e accettazione richieste di amicizia
- Sistema follow/unfollow
- Visualizzazione profili cliccando sugli utenti

#### Centro Notifiche
- Pagina `/notifications` per tutte le notifiche
- Contatore badge rosso nella navbar
- Notifiche automatiche per: friend_request, friend_accepted, new_follower, major_invite, etc.

### Indicatore "Ha già lavorato con noi" - (GIA' IMPLEMENTATO)
- Badge ciano "Ha lavorato con noi" sulle card del cast
- Mostra se un membro del cast ha già lavorato con il giocatore

### Traduzione Categorie Festival - (GIA' IMPLEMENTATO)
- Le categorie dei festival vengono tradotte in base alla lingua dell'utente
- Backend passa il parametro `language` e ritorna i nomi tradotti

### PWA - Progressive Web App - 09/03/2026 (COMPLETATO)
- App installabile su iOS e Android
- Pagina dedicata per download con istruzioni
- Manifest.json e icone PWA configurate

### Sistema Affinità Cast - 09/03/2025 (COMPLETATO)
- **Bonus +2%** per ogni film fatto insieme dallo stesso cast
- **Max +10%** per coppia, **Max +30%** totale

## API Endpoints Principali

### Cast System (NUOVO)
```
GET  /api/cast/stats - Statistiche pool cast (totale, nuovi oggi)
GET  /api/cast/new-arrivals - Nuovi membri del cast
```

### CineBoard
```
GET  /api/cineboard/now-playing - Top 50 film in programmazione
GET  /api/cineboard/hall-of-fame - Hall of Fame tutti i film
```

### Trailer
```
POST /api/ai/generate-trailer - Genera trailer Sora 2
GET  /api/films/{id}/trailer-status - Stato generazione (con auto-reset 15min)
POST /api/films/{id}/reset-trailer - Reset trailer bloccato (manuale)
```

### Sistema Social
```
GET  /api/major/my - Info Major utente (include activities e weekly_challenge)
POST /api/major/create - Crea nuova Major
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- Integrations: OpenAI GPT-4o, Gemini Nano Banana, Sora 2

## Backlog

### P1 - Priorità Alta
- [ ] **Refactoring Critico**: `server.py` (~9000 righe) e `App.js` (~7900 righe) sono monolitici

### P2 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live" animate

## Note Tecniche

### Generazione Automatica Cast
La funzione `generate_daily_cast_members()` viene eseguita all'avvio del server e genera:
- 10-20 nuovi membri per tipo (attore, regista, sceneggiatore, compositore)
- Marcati con `is_new: True` per evidenziazione UI
- La data dell'ultima generazione è salvata in `system_config`

### Fix Skill Decimali
La funzione `fix_decimal_skills_in_db()` viene eseguita all'avvio e:
- Cerca tutti i cast members con skill decimali
- Arrotonda a interi tutte le skill
- Aggiorna anche fame_score e avg_film_quality

## Test Reports
- `/app/test_reports/iteration_16.json` - Sistema Social (100% pass)
