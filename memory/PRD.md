# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), MoviePy/FFmpeg (trailer), Emergent LLM Key

## Sessione 16 Mar 2026 - Bug Fix Critici

### Batch 1 - Fix iniziali
- **FIX CRITICO: Premio CinePass sfide 1v1** - Root cause: `$inc` usava campo `xp` invece di `total_xp`. Corretto in offline e online battle. Aggiunto `cinepass` increment anche alle sfide online.
- **FIX: Nome Studio nella UI** - Dashboard, profilo dropdown e menu mobile mostrano `production_house_name`
- **FIX: Film duplicati Dashboard** - Deduplicazione lato frontend per ID + pulizia DB test film duplicati
- **FIX: Poster mancanti** - Aggiunto fallback `onError` per immagini poster rotte
- **FIX: Crash trailer rotti** - Aggiunto `onError` handler sul video element

### Batch 2 - Fix da screenshot utente
- **FIX: Route commenti/poster CinemaJournal** - Tutte le route `/film/` corrette a `/films/` (5 navigate calls)
- **FIX: Pareggi falsi nelle skill battle** - Ridotta draw_chance: diff=0→50%, diff=1→15%, diff=2+→5% (era 80%/55%/30%)
- **FIX: CinePass update ottimistico** - Aggiunto `updateUser()` nel context per update immediato dopo vittoria, + `refreshUser()` asincrono in background
- **FIX: Locandine duplicate Giornale Cinema** - Backend deduplica `recent_posters` per titolo prima di restituire

## Sessione 15 Mar 2026
- Fix costo doppio CinePass per sceneggiature emergenti
- Ottimizzazione mobile (interceptor 401, transizioni veloci, cache 60s)
- Dashboard film grid 9 (3x3)
- Pallino rosso contest disponibili
- Fix 1v1 refreshUser await
- Ribilanciamento economia (base -50%, diminishing returns, cap livello)
- Fix creazione film da sceneggiatura emergente
- Fix padding bottom menu hamburger
- Sistema trailer gratuito FFmpeg

## Bug Risolti (Storico)
- Premio +2 CinePass sfide 1v1: RISOLTO (root cause: campo $inc sbagliato `xp` → `total_xp`)
- Pareggi falsi skill battle: RISOLTO (draw_chance ridotta drasticamente)
- Route `/film/` vs `/films/`: RISOLTO (tutte corrette a `/films/`)
- Locandine duplicate: RISOLTO (deduplicazione per titolo nel backend)
- CinePass non aggiornato dopo vittoria: RISOLTO (update ottimistico + refresh background)
- Crash app su film con trailer rotto: RISOLTO (onError handler)

## Verifica Utente Pendente
- Bug premio sfide 1v1 offline - fix implementato, utente deve verificare

## Task Prossimi (P1-P2)
- Sistema ruoli Admin avanzato (RBAC)
- Tutorial popup per nuovi utenti
- Layout mobile Contest Page (da verificare)

## Task Futuri (P3)
- Runware Integration (trailer premium)
- CineCoins Purchase System (Stripe)
- Conversione PWA
- Layout Android Chrome (attesa screenshot utente)

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
