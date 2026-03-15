# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), Emergent LLM Key

## Funzionalità Completate
- Acting School, CinePass, Notifiche, UI/UX, Poster AI, Tutorial, Release notes
- v0.124: Traduzione, CinePass Sfide & Fix Cinema
- v0.125: Sessione Persistente, Skill & Ottimizzazione
- v0.126: Donazioni, UI & Bilanciamento Sfide
- v0.127: Admin, Tutorial & Bilanciamento
- v0.128: Fix CinePass doppio & Contest Migliorati
- v0.129: Velocità Mobile & Fix Vari

## Sessione Corrente (15 Mar 2026)
- Fix costo doppio CinePass per sceneggiature emergenti
- Ottimizzazione mobile (interceptor 401, transizioni veloci, cache 60s, timeout 30s, retry)
- Dashboard film grid 9 (3x3) invece di 10
- Orario reset contest corretto: 11:00
- Note di sistema aggiornate (v0.124-v0.129)
- Pallino rosso contest disponibili in Dashboard
- Fix 1v1: refreshUser await + interceptor 401 meno aggressivo (2+ errori per logout)
- Rimossa sezione "Nuovi Trailer" dal Cinema Journal
- **Ribilanciamento economia**: base revenue -50%, rendite decrescenti offline, cap catchup per livello, rimosso boost +20%, infra logaritmiche

## Economia Ribilanciata
- **Film base revenue**: `4000 + Q*175` (era `8000 + Q*350`)
- **Catchup diminishing**: 0-3h=100%, 3-6h=50%, 6h+=25%
- **Cap catchup**: `livello × $50,000`
- **Boost +20% rimosso** dal calcolo orario
- **Infrastrutture**: scaling `level^0.5` (logaritmico)

## Bug da verificare
- Layout Android Chrome (in attesa screenshot utente)
- Premio +2 CinePass sfide 1v1 offline (verifica utente)

## Task Prossimi (P1-P2)
- Sistema ruoli Admin avanzato
- Tutorial popup per nuovi utenti

## Task Futuri (P3)
- CineCoins Purchase System (Stripe)
- Conversione PWA

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
- NS: nero.ns.cloudflare.com, olivia.ns.cloudflare.com
