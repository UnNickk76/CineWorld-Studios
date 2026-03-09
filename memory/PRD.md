# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sistema Film Incompleti (Pausa/Riprendi) - 09/03/2026 (COMPLETATO)
- **Pulsante "Metti in Pausa"** nel wizard di creazione film
- **Board "Film Incompleti"** accessibile dalla navbar (icona orologio)
- **Salvataggio automatico** dello stato del wizard (step corrente, dati inseriti)
- **Ripresa** da qualsiasi step con tutti i dati preservati
- **Eliminazione** delle bozze non più necessarie
- **Badge stato**: In Pausa, Errore, Incompleto
- **Endpoint**: `/api/films/drafts`, `/api/films/drafts/{id}`, `/api/films/drafts/{id}/resume`

### Bug Fix Creazione Film - 09/03/2026 (COMPLETATO)
- Corretto errore `genre_name` non definito nell'ultimo step
- La variabile ora viene inizializzata prima del blocco try/except

### Sistema Cast Espanso - 09/03/2026 (COMPLETATO)
- **Pool di 2000+ membri** (500 per tipo: attori, registi, sceneggiatori, compositori)
- **Generazione automatica giornaliera**: 40-80 nuovi membri del cast ogni giorno
- **Fix skill decimali**: Tutte le skill ora sono interi (nessun decimale)
- **Database nomi esteso**: Migliaia di nomi realistici da 12+ paesi

### CineBoard & Film Rankings - 09/03/2026 (COMPLETATO)
- **CineBoard** con due tab: "In Sala (Top 50)" e "Hall of Fame"
- Punteggio CineBoard calcolato con formula multi-variabile
- Sinossi film generata automaticamente via AI
- Valutazione IMDb integrata

### Sistema Trailer con Auto-Reset - 09/03/2026 (COMPLETATO)
- Timeout automatico di 15 minuti per trailer stuck
- Endpoint reset manuale: `POST /api/films/{film_id}/reset-trailer`

### Attività delle Major - 09/03/2026 (COMPLETATO)
- Sfide Settimanali (6 tipi)
- 5 Attività: Co-Produzione, Condivisione Risorse, Premiere, Scambio Talenti, Proiezione Collettiva

### Sistema Social Completo - (COMPLETATO)
- Major (Alleanze) con logo AI
- Amici & Follower
- Centro Notifiche

### Altre Feature
- PWA installabile
- Sistema Affinità Cast
- Azioni One-Time sui Film
- Festival cinematografici
- Saghe & Serie TV

## API Endpoints Principali

### Film Drafts (NUOVO)
```
POST   /api/films/drafts              - Salva bozza film
GET    /api/films/drafts              - Lista bozze utente
GET    /api/films/drafts/{id}         - Dettaglio bozza
DELETE /api/films/drafts/{id}         - Elimina bozza
POST   /api/films/drafts/{id}/resume  - Riprendi creazione
```

### Cast System
```
GET  /api/cast/stats        - Statistiche pool cast
GET  /api/cast/new-arrivals - Nuovi membri del cast
```

### CineBoard
```
GET  /api/cineboard/now-playing  - Top 50 film in sala
GET  /api/cineboard/hall-of-fame - Hall of Fame
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- Integrations: OpenAI GPT-4o, Gemini Nano Banana, Sora 2

## Backlog

### P1 - Priorità Alta
- [ ] **Refactoring Critico**: `server.py` (~9200 righe) e `App.js` (~8200 righe)

### P2 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live" animate

## Note Tecniche

### Schema DB - film_drafts (NUOVO)
```json
{
  "id": "uuid",
  "user_id": "string",
  "title": "string",
  "genre": "string",
  "current_step": 1-12,
  "paused_reason": "paused|error|incomplete",
  "created_at": "datetime",
  "updated_at": "datetime",
  // ... tutti i campi del wizard
}
```

## Test Reports
- Tutti gli endpoint testati con curl
- Screenshot UI verificati
