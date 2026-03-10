# CineWorld Studio's - Product Requirements Document

## Descrizione
Gioco multiplayer online di produzione cinematografica. Proprietà di **Andreola Fabio**.

## Versione Attuale: v0.072

## Funzionalità Implementate (Ultime)

### v0.072 - Ribilanciamento Qualità Film & Fix P1 - 10/03/2026 (COMPLETATO)
- **Ribilanciamento Qualità Film (P0):**
  - Nuova formula quality_score: base 35 + bonus giocatore + casualità
  - Distribuzione reale testata su 2000 simulazioni per 3 livelli giocatore:
    - Nuovo (Lv1): ~22% flop, ~29% scarso, ~26% mediocre
    - Medio (Lv5): ~11% flop, ~22% scarso, ~28% mediocre, ~4% eccellente
    - Esperto (Lv10): ~3% flop, ~20% mediocre, ~28% medio, ~15% eccellente+
  - Fattore "giornata storta" (10%): penalità -5/-15
  - Fattore "magia" (5%): bonus +10/+20
  - Luck factor asimmetrico (più negative)
  - Tier aggiornati: masterpiece ≥88, excellent ≥75, good ≥62, average ≥48, mediocre ≥35, poor ≥20, flop <20
  - Probabilità flop aumentata al 25% (era 10%), max_score flop alzato a 42
  - Probabilità tier positivi ridotte leggermente
- **Fix Trailer Generation (P1):**
  - Aggiunto sistema di retry automatico (2 tentativi per durata)
  - Fallback a durata più corta (4s) se la richiesta originale fallisce
  - Errori precedenti dei trailer resettati nel DB (utenti possono riprovare)
- **Fix Creator Reply (P1):**
  - Le risposte del Creator ora vanno nella chat generale (room_id: 'general') invece che in una room diretta inesistente
  - Formato messaggio migliorato con nome destinatario
- **Fix Virtual Likes (P1):**
  - Aggiunto `virtual_likes` al modello Pydantic `FilmResponse` (prima veniva filtrato da extra="ignore")
  - Aggiunti anche: `trailer_url`, `trailer_generating`, `trailer_error`, `cumulative_attendance`, `popularity_score`
- **Fix Dati Storici:**
  - Corretti 2 film con quality_score > 100 (cappati a 100)

### v0.071 - Miglioramenti Sfide & Navigazione - 10/03/2026 (COMPLETATO)
- Icona Sfide nel Menu Fisso, Tutorial Sfide, Notifica Benvenuto Sfide
- Notifiche Sfide Cliccabili, Icone dedicate per sfide

### v0.070 - Sistema Sfide Completo - 10/03/2026 (COMPLETATO)
- Sistema Sfide Multiplayer (1v1, 2v2, 3v3, 4v4, FFA)
- 8 skill cinematografiche, 3 manche, matchmaking, classifica

### v0.069 - Video Cerimonia & Download Trailer (COMPLETATO)
### v0.068 - Sistema Pubblico Virtuale & Recensioni (COMPLETATO)
### v0.067 - Refactoring Architettura Fase 1 (COMPLETATO)
### v0.066 - Menu Mobile Migliorato (COMPLETATO)
### v0.065 - Bonus Visione Cerimonie (COMPLETATO)
### v0.064 - Festival System Update & Cinema Revenue (COMPLETATO)
### v0.063 - Sistema Sottotitoli e Sequel (COMPLETATO)
### v0.062 - Selettore Lingua Login/Registrazione (COMPLETATO)
### v0.061 - Sistema Pre-Ingaggio Completato (COMPLETATO)
### v0.060 - Sistema Pre-Ingaggio Cast (COMPLETATO)
### v0.059 - Recupero Password e Nickname (COMPLETATO)
### v0.058 - Notifiche Release Notes & Trailer Gratuiti (COMPLETATO)

## Architettura
- Backend: FastAPI + MongoDB (motor)
- Frontend: React + TailwindCSS + Shadcn/UI
- AI: OpenAI GPT-4o, Sora 2 (Emergent LLM Key)
- Audio: OpenAI TTS-1

## Backlog

### P0 - Critico
- [x] **Ribilanciamento Qualità Film** - COMPLETATO v0.072
- [ ] **Refactoring Critico**: `server.py` (~14400 righe) e `App.js` (~13500 righe) - URGENTE (in pausa su richiesta utente)

### P1 - Priorità Alta
- [x] **Fix Trailer Generation** - Migliorato con retry - v0.072
- [x] **Fix Creator Reply** - Corretto room_id chat - v0.072
- [x] **Fix Virtual Likes in API** - Aggiunto a FilmResponse - v0.072
- [ ] **Bug Mobile Residui**: Verificare funzionalità su mobile
- [ ] **Avvio Automatico Cerimonie 21:30**: Scheduler per avvio automatico
- [ ] **Automazione Note di Rilascio**

### P2 - Priorità Media
- [ ] **Cinema Distribution Page**: Sezione nella pagina film con lista cinema
- [ ] **Attività delle Major**: Co-Produzioni, Sfide tra Major
- [ ] **Sistema Acquisto CineCoins**: Integrazione Stripe (IN PAUSA)

### P3 - Future
- [ ] Mini-giochi Versus tra giocatori
- [ ] Traduzione categorie festival
- [ ] Script migrazione dati per errori Pydantic con dati vecchi
