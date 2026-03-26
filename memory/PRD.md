# CineWorld Studio's - PRD

## Problema originale
Gioco di gestione cinematografica (Film, Serie TV, Anime) con meccaniche PvP, hype, boicottaggi, e sistema di produzione completo.

## Architettura
- **Frontend**: React + TailwindCSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **AI**: OpenAI GPT-4o-mini (testo) + GPT-Image-1 (immagini) via Emergent LLM Key
- **Jobs**: APScheduler

## Funzionalità implementate
- Sistema completo di produzione Film/Serie TV/Anime (draft → casting → produzione → release)
- PvP Arena con supporto/boicotto, difesa, statistiche
- Coming Soon con countdown, hype, interazioni (supporto/boicotto)
- TV Station scheduling manuale
- Velion AI assistant (tutorial, suggerimenti con cooldown)
- Cancellazione permanente contenuti
- Popup dettaglio contenuti con permessi proprietario
- **Popup esito Supporto/Boicotto** con immagini dedicate (supporto_successo, boicotto_ritorto, etc.)

## Fix completata (26 Mar 2026)
- **OutcomePopup non mostrato**: Convertito da Radix Dialog (conflitto con Dialog parent) a overlay fisso con z-index:9999 + framer-motion
- **Backfire non rilevato**: Corretta logica outcome detection in PvPArenaPage con nuova funzione `parseOutcome()`

## Task in corso
Nessuno

## Prossimi task (P1)
- Sistema "Previsioni Festival" (scommesse sui vincitori)
- Marketplace per diritti TV/Anime

## Backlog (P2+)
- Contest Page Mobile Layout rotto (P2, recurring 12+)
- Velion Mood Indicator
- Chat Evolution
- CinePass + Stripe
- Push notifications
- Velion Levels
- RBAC
- Eventi globali
- Guerre tra Major
- Velion AI Memory

## Integrazioni 3rd party
- OpenAI GPT-4o-mini (text) — Emergent LLM Key
- OpenAI GPT-Image-1 (image) — Emergent LLM Key
- APScheduler (cron)

## Vincoli utente
- Veloce, pratico, senza modifiche strutturali
- NO testing agent (crediti)
- NO refactoring di server.py
- Lingua: Italiano
