# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sistema Sociale e Profili - 09/03/2025 (NUOVO)

#### Lista Utenti Online Cliccabile
- Utenti online e offline visibili nella Chat
- Click sul nome/avatar apre il profilo completo
- Pulsante DM per messaggi diretti

#### Modal Profilo Utente Completo
- Avatar, nickname, stato online/offline
- Nome studio e livello
- **Statistiche complete**: Film, Revenue, Likes, Qualità Media, Premi, Infrastrutture
- **Best Film**: Miglior film per revenue
- **Film Recenti**: Lista ultimi 4 film
- Pulsante "Send Message" per DM

#### Dashboard Statistiche Cliccabili
- Ogni stat card (Films, Revenue, Likes, Quality) è cliccabile
- Apre modal con dettagli approfonditi:
  - Film per genere
  - Distribuzione qualità (Excellent/Good/Average/Poor)
  - Top 5 film per revenue e likes

### Sistema Affinità Cast - 09/03/2025 (NUOVO)
- **Bonus +2%** per ogni film fatto insieme dallo stesso cast
- **Max +10%** per coppia, **Max +30%** totale
- API: `POST /api/cast/affinity-preview`
- Livelli affinità: Conoscenti → Colleghi → Partner Abituali → Collaboratori Affiatati → Dream Team

### Azioni One-Time sui Film - 09/03/2025 (NUOVO)
- **Crea Star**: Promuove un attore a star (una sola volta)
- **Skill Boost**: Aumenta skill di tutto il cast (una sola volta)
- **Genera Trailer**: Può essere generato una sola volta
- Pulsanti diventano "frozen" (disabilitati) dopo l'uso
- Icona lucchetto indica azione già utilizzata

### Schede Film Altri Utenti - 09/03/2025 (NUOVO)
- Pulsanti azione nascosti se non sei il proprietario
- Solo visualizzazione dati per film altrui

### Sistema Cast v2 - 09/03/2025
- **700 membri del cast** con skill variabili
- 5 categorie: Consigliati, Star, Conosciuti, Emergenti, Sconosciuti
- Filtri per categoria e skill
- Sistema bonus/malus cast-film

### Altre Feature Esistenti
- Festival cinematografici (ufficiali + personalizzati)
- Mini Games
- Saghe & Serie TV
- Reset totale player
- Wizard creazione film a 12 step

## API Endpoints Nuovi

### Profili e Social
```
GET  /api/users/{id}/full-profile - Profilo completo con stats e film
GET  /api/stats/detailed - Breakdown statistiche dettagliate
GET  /api/users/online - Utenti online
GET  /api/users/all - Tutti gli utenti
```

### Affinità Cast
```
POST /api/cast/affinity-preview - Calcola bonus affinità per gruppo cast
     Body: {"cast_ids": ["id1", "id2", ...]}
     Response: {"total_bonus_percent": X, "affinity_pairs": [...]}
```

### Azioni One-Time Film
```
GET  /api/films/{id}/actions - Stato azioni (create_star, skill_boost, trailer)
POST /api/films/{id}/action/create-star?actor_id=X - Promuovi attore
POST /api/films/{id}/action/skill-boost - Boost skill cast
```

## Architettura
- Backend: FastAPI + MongoDB
- Frontend: React + TailwindCSS + Shadcn/UI
- Integrations: OpenAI GPT-4o, Gemini Nano Banana, Sora 2

## Backlog

### P1 - In Progress
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live" animate

### P2 - Future
- [ ] Preascolto colonne sonore (bloccato - no API gratuite)
- [ ] Refactoring server.py e App.js (file monolitici)

## Test Reports
- `/app/test_reports/iteration_14.json` - Cast System v2 (100% pass)
- `/app/test_reports/iteration_15.json` - Social Features (100% backend, 95% frontend)
