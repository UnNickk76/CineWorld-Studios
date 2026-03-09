# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

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

### Sistema Social Completo - 09/03/2026 (COMPLETATO)

#### Major (Alleanze)
- Pagina `/major` per creare e gestire alleanze
- Requisito livello 20 per creare una Major
- Visualizzazione membri con ruoli (Fondatore, Vice, Produttore Senior, Membro)
- Bonus Major: Qualità, Incassi, XP basati sul livello dell'alleanza
- Sfide settimanali con rewards
- Sistema inviti membri
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
- Pulsanti segna come letto e elimina
- Icone colorate per tipo di notifica

### PWA - Progressive Web App - 09/03/2026 (COMPLETATO)
- App installabile su iOS e Android
- Pagina dedicata per download con istruzioni
- Manifest.json e icone PWA configurate

### Sistema Affinità Cast - 09/03/2025 (COMPLETATO)
- **Bonus +2%** per ogni film fatto insieme dallo stesso cast
- **Max +10%** per coppia, **Max +30%** totale
- API: `POST /api/cast/affinity-preview`
- Livelli affinità: Conoscenti → Colleghi → Partner Abituali → Collaboratori Affiatati → Dream Team

### Azioni One-Time sui Film - 09/03/2025 (COMPLETATO)
- **Crea Star**: Promuove un attore a star (una sola volta)
- **Skill Boost**: Aumenta skill di tutto il cast (una sola volta)
- **Genera Trailer**: Può essere generato una sola volta
- Pulsanti diventano "frozen" (disabilitati) dopo l'uso
- Icona lucchetto indica azione già utilizzata

### Altre Feature Esistenti
- Festival cinematografici (ufficiali + personalizzati)
- Mini Games
- Saghe & Serie TV
- Reset totale player
- Wizard creazione film a 12 step
- Sistema catch-up per incassi offline
- Re-release dei film (ripubblicazione)

## API Endpoints Principali

### CineBoard
```
GET  /api/cineboard/now-playing - Top 50 film in programmazione
GET  /api/cineboard/hall-of-fame - Hall of Fame tutti i film
```

### Trailer
```
POST /api/ai/generate-trailer - Genera trailer Sora 2
GET  /api/films/{id}/trailer-status - Stato generazione
POST /api/films/{id}/reset-trailer - Reset trailer bloccato
```

### Sistema Social
```
GET  /api/major/my - Info Major utente
POST /api/major/create - Crea nuova Major
POST /api/major/invite - Invita utente
POST /api/major/invite/{id}/accept - Accetta invito
GET  /api/friends - Lista amici
POST /api/friends/request - Invia richiesta
GET  /api/notifications - Lista notifiche
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- Integrations: OpenAI GPT-4o, Gemini Nano Banana, Sora 2

## Backlog

### P1 - Priorità Alta
- [ ] Traduzione categorie festival
- [ ] Attività delle Major (Sfide, Co-Produzioni, Classifiche)
- [ ] Mini-giochi Versus tra giocatori
- [ ] Indicatore UI "Ha già lavorato con noi" sul cast

### P2 - Future
- [ ] Cerimonie di premiazione "Live" animate
- [ ] Refactoring server.py e App.js (file monolitici ~8000+ righe ciascuno)

## Note Tecniche

### Bug Risolti
- **Trailer bloccato**: Implementato timeout automatico 15min + endpoint reset manuale
- **Film "Capitan World"**: Resettato manualmente il flag `trailer_generating`

### Campi DB Aggiunti
- `films.synopsis` - Sinossi generata dall'AI
- `films.cineboard_score` - Calcolato dinamicamente
- `films.trailer_started_at` - Timestamp inizio generazione trailer

## Test Reports
- `/app/test_reports/iteration_16.json` - Sistema Social (100% pass)
