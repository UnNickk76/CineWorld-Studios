# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.048

## Funzionalità Implementate (Ultime)

### v0.048 - Sistema Rifiuto Ingaggio Cast - 09/03/2026 (COMPLETATO)
- **Backend**: Endpoint `POST /api/cast/offer` per fare offerte ai membri del cast
- **Backend**: Endpoint `GET /api/cast/rejections` per ottenere lista rifiuti (ultime 24h)
- **Backend**: 23 motivazioni di rifiuto in italiano e inglese
- **Backend**: Calcolo probabilità rifiuto basato su: livello giocatore, fama cast, ricavi, genere film
- **Frontend**: Modal "Offerta Rifiutata" con nome, motivazione, stelle e fama
- **Frontend**: Card con badge "Ha rifiutato" e visivamente disabilitata
- **Persistenza**: Rifiuto memorizzato per 24 ore (non richiederlo di nuovo)

### v0.047 - Sistema Ingaggio Star - 09/03/2026 (COMPLETATO)
- **Sezione dedicata "Stelle Scoperte"** con pagina completa
- **Card star cliccabili** per vedere skill dettagliate
- **Sistema ingaggio anticipato**: paghi ora, disponibile nel prossimo film
- **Costo calcolato** su fama, skill e stelle
- **Star ingaggiate** mostrate in verde nel wizard
- **Pagina Release Notes** con versioning (0.000 → 0.047)
- **48 release documentate** nella storia

### v0.046 - Trailer in Chat & Giornale
- Annunci trailer automatici in chat via CineBot
- Sezione "Nuovi Trailer" nel Cinema Journal
- Click su trailer naviga al film

### v0.045 - Boost Introiti & Sponsor
- +30% introiti primo giorno
- +10% introiti giorni successivi
- 200 sponsor totali (40 a rotazione)
- Budget sponsor aumentato +40%

### v0.044 - Cast Pool Espanso
- 200 cast members per tipo nel wizard
- 2000+ membri totali nel database
- Generazione automatica giornaliera

### v0.043-v0.042 - Sistema Film Incompleti
- Autosave ogni 30 secondi
- Board Film Incompleti (Bozze)
- Pausa/Riprendi creazione film

### v0.041-v0.040 - CineBoard & Fix Trailer
- CineBoard classifiche
- Timeout automatico trailer stuck

## API Endpoints Nuovi

### Stelle Scoperte & Ingaggio
```
GET  /api/discovered-stars     - Lista star scoperte con costo ingaggio
POST /api/stars/{id}/hire      - Ingaggia star per prossimo film
GET  /api/stars/hired          - Star ingaggiate (non ancora usate)
DELETE /api/stars/hired/{id}   - Rilascia star ingaggiata
```

### Release Notes
```
GET  /api/release-notes        - Storico versioni e cambiamenti
```

### Sistema Rifiuto Cast
```
POST /api/cast/offer           - Fai un'offerta a un membro del cast
                                 Body: { person_id, person_type, film_genre }
                                 Returns: { accepted, reason, stars, fame, already_refused }
GET  /api/cast/rejections      - Lista rifiuti ultime 24h per l'utente corrente
                                 Returns: { rejections: [], refused_ids: [] }
```

## Menu Principale
1. Dashboard
2. I Miei Film
3. Crea Film
4. Bozze
5. Saghe e Serie
6. Infrastrutture
7. Mercato
8. Tour Cinema
9. **Giornale del Cinema**
10. **Stelle Scoperte** (NUOVO)
11. Festival
12. CineBoard
13. Mini Giochi
14. Classifica
15. Chat
16. **Note di Rilascio** (NUOVO)
17. Tutorial
18. Crediti

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- AI: OpenAI GPT-4o, Gemini Nano Banana, Sora 2
- Versione: v0.047

## Backlog

### P1 - Priorità Alta
- [ ] **Refactoring Critico**: `server.py` (~9600 righe) e `App.js` (~8700 righe)

### P2 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live"

## Note Tecniche

### Formula Costo Ingaggio Star
```python
base_cost = 100000  # $100k
fame_mult = 1 + (fame_score / 100)
skill_mult = 1 + (avg_skill / 100)
hire_cost = base_cost * fame_mult * skill_mult * stars
```

### Versioning
- Formato: `0.XXX`
- Incremento: +0.001 per ogni feature/fix
- Storia: 48 release dalla v0.000
