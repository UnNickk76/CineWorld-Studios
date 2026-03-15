# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), MoviePy/FFmpeg (trailer), Emergent LLM Key

## Sessione 15 Mar 2026
- Fix costo doppio CinePass per sceneggiature emergenti
- Ottimizzazione mobile (interceptor 401, transizioni veloci, cache 60s, timeout 30s, retry)
- Dashboard film grid 9 (3x3)
- Orario reset contest: 12:00 → 11:00
- Note di sistema v0.124-v0.129
- Pallino rosso contest disponibili in Dashboard
- Fix 1v1: refreshUser await + interceptor 401 meno aggressivo
- Rimossa sezione "Nuovi Trailer" dal Cinema Journal
- Ribilanciamento economia (base -50%, diminishing returns, cap livello, infra logaritmiche)
- Fix creazione film da sceneggiatura emergente (campo mancante nel model + display costi)
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
