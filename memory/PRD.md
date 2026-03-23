# CineWorld Studio's - PRD

## Problema Originale
Gioco di gestione di un impero cinematografico. Full-stack React + FastAPI + MongoDB.

## Utenti
- Produttori cinematografici (giocatori) che creano e gestiscono film virtuali

## Requisiti Core Implementati

### Film Production Pipeline (v2.0)
- UX centrata sul singolo film con card cliccabili + popup
- Pagina "Produci!" mostra lista film come card
- Click su card -> popup con header film + step bar per-film + contenuto step
- Step bar adattiva: Immediato (5 step) vs Coming Soon (7 step)
- Step 1 rinominato "Proposta"
- Notifiche linkano direttamente al popup del film specifico

### Sistema Notifiche v2.0
- Formato tempo in minuti (+18 min / -24 min) invece di ore decimali
- Eventi narrativi: titolo descrittivo, descrizione immersiva, effetto colorato
- CineWorld News: badge giallo su notifiche evento per immersione
- Colori effetti: verde = bonus, rosso = malus
- Boicottaggi tipizzati: 7 tipi
- Boicottaggi anonimi di default
- NewsEvent narrativi nella sezione Coming Soon
- Routing PvP: notifiche legali e contro-attacchi puntano a /hq

### Sistema PvP Infrastrutture (v1.0)
- Quartier Generale (HQ): Pagina dedicata /hq con 3 divisioni
- Divisione Investigativa: Indaga boicottaggi (55%-85% successo per livello)
- Divisione Operativa: Difesa (riduce danni) + Attacco mirato a sabotatori
- Divisione Legale: Cause legali con probabilita' calcolata
- Upgrade ibridi: Costi in $ + CinePass con requisiti livello/fama
- Daily limits basati sul livello
- Storico cause legali con dettagli vittoria/sconfitta

### Integrazione PvP in Coming Soon (v1.0)
- Card contenuti propri: bottoni Indaga + Difesa (divisioni PvP)
- Hint "Sblocca in HQ" quando divisioni sono a livello 0
- Sabotatori identificati mostrati con nome + tipo sabotaggio
- Bottoni Attacca (contro-boicottaggio mirato) e Causa (azione legale) per sabotatore
- Card contenuti altrui: Supporta + Boicotta (invariato)
- Endpoint details arricchito con identified_saboteurs

### Copy Login Aggiornata
- Sottotitolo coinvolgente: "Costruisci il tuo studio cinematografico e sfida altri player tra hype, sabotaggi e successo al botteghino."

### Modalita' Rilascio
- Immediato: Proposta -> Casting -> Script -> Produzione -> Uscita
- Coming Soon: Proposta -> Poster -> Hype (timer) -> Casting -> Script -> Produzione -> Uscita

### Altre Feature
- Login Reward System, Error Boundary cinematico, Buzz/Hype, Daily Bonus
- Acting School / Agenzia Attori, Sfide/Versus, Chat, Festival, Major, Marketplace Sceneggiature

## Architettura
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion
- Backend: FastAPI + MongoDB + APScheduler
- Integrazioni: OpenAI GPT-4o-mini + GPT-Image-1 via Emergent LLM Key

## DB Schema Chiave
- users: pvp_divisions (investigative/operative/legal), cinepass, funds
- coming_soon_interactions: boycott_type, investigated, revealed_to
- pvp_actions: attacker_id, target_id, type, effects
- pvp_legal_actions: attacker_id, target_id, success, probability
- pvp_blocks: blocked_user, blocked_from_attacking, expires_at

## API Endpoints PvP
- GET /api/pvp/status
- POST /api/pvp/upgrade
- POST /api/pvp/investigate
- POST /api/pvp/counter-boycott
- POST /api/pvp/legal-action
- GET /api/pvp/legal-history
- GET /api/coming-soon/{id}/details (arricchito con identified_saboteurs)

## Test
- Iter 127: 100% (Film Pipeline UX redesign)
- Iter 128: 100% (Notifiche + Eventi + Boicottaggi)
- Iter 129: 100% (PvP Backend + HQ Page - 21/21 tests)
- Iter 130: 100% (PvP Integration Coming Soon + Notifications - 12/12 tests)

## Backlog

### P1
- Chat Evolution Step 6: Rifinitura mobile e qualita' social
- Marketplace per diritti TV/Anime

### P2
- RBAC, CinePass + Stripe, PWA, Tutorial
- Contest Page Mobile Layout Fix

### P3
- Scommesse Coming Soon, Eventi globali, Push notifications, Guerre tra Major
