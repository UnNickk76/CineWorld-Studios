# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Funzionalità Implementate

### Sistema Social Completo - 09/03/2026 (COMPLETATO)

#### Major (Alleanze)
- Pagina `/major` per creare e gestire alleanze
- Requisito livello 20 per creare una Major
- Visualizzazione membri con ruoli (Fondatore, Vice, Produttore Senior, Membro)
- Bonus Major: Qualità, Incassi, XP basati sul livello dell'alleanza
- Sfide settimanali con rewards
- Sistema inviti membri

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

#### Sincronizzazione Lingua
- La lingua dell'utente viene sincronizzata al login
- L'interfaccia si adatta automaticamente alla lingua del profilo

### Sistema Sociale e Profili - 09/03/2025

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

### Sistema Social
```
GET  /api/major/my - Info Major utente
POST /api/major/create - Crea nuova Major
POST /api/major/invite - Invita utente
POST /api/major/invite/{id}/accept - Accetta invito
GET  /api/major/challenge - Sfida settimanale

GET  /api/friends - Lista amici
GET  /api/friends/requests - Richieste in/out
POST /api/friends/request - Invia richiesta
POST /api/friends/request/{id}/accept - Accetta
POST /api/friends/request/{id}/reject - Rifiuta
DELETE /api/friends/{id} - Rimuovi amico

GET  /api/followers - Lista follower
GET  /api/following - Lista seguiti
POST /api/follow/{id} - Segui utente
DELETE /api/follow/{id} - Smetti di seguire

GET  /api/notifications - Lista notifiche
GET  /api/notifications/count - Contatore non lette
POST /api/notifications/read - Segna come lette
DELETE /api/notifications/{id} - Elimina
```

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
- [ ] Attività delle Major (Sfide, Co-Produzioni, Classifiche)
- [ ] Mini-giochi Versus tra giocatori
- [ ] Cerimonie di premiazione "Live" animate
- [ ] Indicatore UI "Ha già lavorato con noi" sul cast

### P2 - Future
- [ ] Preascolto colonne sonore (bloccato - no API gratuite)
- [ ] Refactoring server.py e App.js (file monolitici ~7000 righe ciascuno)

## Test Reports
- `/app/test_reports/iteration_16.json` - Sistema Social (100% pass) ✅
- `/app/test_reports/iteration_14.json` - Cast System v2 (100% pass)
- `/app/test_reports/iteration_15.json` - Social Features (100% backend, 95% frontend)
