# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), MoviePy/FFmpeg (trailer), Emergent LLM Key

## Sessione 16 Mar 2026 - Bug Fix Critici
- **FIX CRITICO: Premio CinePass sfide 1v1** - Root cause: `$inc` usava campo `xp` invece di `total_xp` nel backend. Corretto in offline e online battle. Aggiunto `cinepass` increment anche alle sfide online.
- **FIX: Nome Studio nella UI** - Dashboard, profilo dropdown e menu mobile ora mostrano `production_house_name` al posto di `nickname`
- **FIX: Film duplicati Dashboard** - Deduplicazione lato frontend per ID + pulizia DB test film duplicati
- **FIX: Poster mancanti** - Aggiunto fallback `onError` per immagini poster rotte
- **FIX: Crash trailer rotti** - Aggiunto `onError` handler sul video element per gestire trailer URL corrotti

## Sessione 15 Mar 2026
- Fix costo doppio CinePass per sceneggiature emergenti
- Ottimizzazione mobile (interceptor 401, transizioni veloci, cache 60s, timeout 30s, retry)
- Dashboard film grid 9 (3x3)
- Orario reset contest: 12:00 → 11:00
- Pallino rosso contest disponibili in Dashboard
- Fix 1v1: refreshUser await + interceptor 401 meno aggressivo
- Rimossa sezione "Nuovi Trailer" dal Cinema Journal
- Ribilanciamento economia (base -50%, diminishing returns, cap livello, infra logaritmiche)
- Fix creazione film da sceneggiatura emergente
- Fix padding bottom menu hamburger (donazioni)
- **Sistema trailer gratuito FFmpeg** (MoviePy, nessun costo API, ~300KB per video)

## Economia Ribilanciata
- Film base revenue: `4000 + Q*175` (era `8000 + Q*350`)
- Catchup diminishing: 0-3h=100%, 3-6h=50%, 6h+=25%
- Cap catchup: `livello × $50,000`
- Boost +20% rimosso
- Infrastrutture: scaling `level^0.5` (logaritmico)

## Sistema Trailer (FFmpeg)
- Endpoint: POST /api/films/{film_id}/generate-trailer
- Serve: GET /api/trailers/{trailer_id}.mp4
- Storage: /app/backend/static/trailers/
- 6 scene cinematografiche, ~12s, 720x1280 verticale
- Gratuito e illimitato

## Bug Risolti (Storico Ricorrenti)
- Premio +2 CinePass sfide 1v1: RISOLTO (root cause: campo $inc sbagliato)
- Crash app su film con trailer rotto: RISOLTO (onError handler)
- Film duplicati dashboard: RISOLTO (deduplicazione)

## Bug da Verificare
- Layout Android Chrome (in attesa screenshot utente)

## Task Prossimi (P1-P2)
- Sistema ruoli Admin avanzato (RBAC)
- Tutorial popup per nuovi utenti
- Layout mobile Contest Page (da verificare)

## Task Futuri (P3)
- Runware Integration (trailer premium)
- CineCoins Purchase System (Stripe)
- Conversione PWA

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
- NS: nero.ns.cloudflare.com, olivia.ns.cloudflare.com
