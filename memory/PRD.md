# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Trailer nel Giornale e Chat - 09/03/2026 (COMPLETATO)
- **Sezione "Nuovi Trailer"** nel Cinema Journal con anteprima poster
- **Annunci trailer in chat** tramite CineBot nella chat generale
- **Click per navigare** al film sia dal giornale che dalla chat
- Badge "TRAILER" sui film con trailer disponibile

### Aumento Introiti Film - 09/03/2026 (COMPLETATO)
- **+30% primo giorno** di uscita
- **+10% giorni successivi**
- Modifiche applicate in `server.py` e `game_systems.py`

### Sponsor Espansi - 09/03/2026 (COMPLETATO)
- **200 sponsor totali** (da 10 a 200)
- **40 sponsor a rotazione** per ogni film (randomizzati)
- **+40% guadagno** nei budget offerti
- 5 tier di sponsor: Entry ($50K-150K), Low-Medium ($150K-300K), Medium ($300K-500K), High ($500K-800K), Premium ($800K-1.8M)

### Cast Espanso nel Wizard - 09/03/2026 (COMPLETATO)
- **200 membri per tipo** mostrati nel wizard di creazione film
- Totale pool: 500+ attori, 500+ registi, 500+ sceneggiatori, 500+ compositori

### Sistema Film Incompleti (Pausa/Riprendi) - 09/03/2026 (COMPLETATO)
- **Pulsante "Metti in Pausa"** nel wizard
- **Board "Film Incompleti"** (navbar: Bozze)
- **Autosave ogni 30 secondi**
- **Salvataggio su chiusura browser**

### Bug Fix Creazione Film - 09/03/2026 (COMPLETATO)
- Corretto errore `genre_name` non definito nell'ultimo step

### Sistema Cast con Generazione Giornaliera - 09/03/2026 (COMPLETATO)
- **2000+ membri totali**
- **40-80 nuovi cast** generati automaticamente ogni giorno
- **Skill sempre interi** (fix decimali)

### CineBoard - 09/03/2026 (COMPLETATO)
- Top 50 film in sala
- Hall of Fame tutti i film
- Punteggio multi-variabile

## API Endpoints Principali

### Sponsor
```
GET /api/sponsors - Ritorna 40 sponsor randomizzati da pool di 200
```

### Trailer Annunci
- Il trailer completato viene automaticamente pubblicato:
  - Come notifica all'utente
  - Nel Cinema Journal (sezione "Nuovi Trailer")
  - Nella chat generale via CineBot

### Film Drafts
```
POST   /api/films/drafts              - Salva bozza
GET    /api/films/drafts              - Lista bozze
DELETE /api/films/drafts/{id}         - Elimina
POST   /api/films/drafts/{id}/resume  - Riprendi
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- Integrations: OpenAI GPT-4o, Gemini Nano Banana, Sora 2

## Backlog

### P1 - Priorità Alta
- [ ] **Refactoring Critico**: `server.py` (~9400 righe) e `App.js` (~8300 righe)

### P2 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live"

## Note Tecniche

### Formula Introiti
- Primo giorno: `base_revenue * 1.30` (+30%)
- Giorni successivi: `final_revenue * 1.10` (+10%)

### Sponsor Tier
| Tier | Budget Range | Revenue Share |
|------|-------------|---------------|
| 5★ Premium | $800K-1.8M | 8-18% |
| 4★ High | $500K-910K | 6-10% |
| 3★ Medium | $280K-560K | 3-6% |
| 2★ Low-Med | $140K-280K | 2-3% |
| 1★ Entry | $56K-140K | 1-2% |
