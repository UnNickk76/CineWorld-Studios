# CineWorld Studio's - PRD

## Problema Originale
Gioco di simulazione di studio cinematografico con economia virtuale (CinePass), scuola di recitazione, sfide 1v1 e gestione infrastrutture.

## Architettura
- **Frontend:** React + Tailwind + Shadcn/UI
- **Backend:** FastAPI + MongoDB
- **Integrazioni:** OpenAI GPT-4o (testo), GPT-Image-1 (poster), Emergent LLM Key

## Sessione 16 Mar 2026

### Batch 1 - Fix bug critici
- FIX: Premio CinePass sfide 1v1 (root cause: `xp` → `total_xp`)
- FIX: Nome Studio nella UI (production_house_name)
- FIX: Film duplicati Dashboard + poster mancanti
- FIX: Crash trailer rotti (onError handler)

### Batch 2 - Fix da screenshot utente
- FIX: Route CinemaJournal `/film/` → `/films/` (5 navigate calls)
- FIX: Pareggi falsi skill battle (draw_chance ridotta)
- FIX: CinePass update ottimistico dopo vittoria
- FIX: Locandine duplicate Giornale Cinema (dedup per titolo)

### Batch 3 - Trailer in pausa
- **Trailer generation disabilitata** - FFmpeg non disponibile in produzione. Sezione sostituita con "Funzionalità in Sviluppo / Coming Soon". I film con trailer esistenti continuano a funzionare.

## Bug Risolti (Storico)
- Premio +2 CinePass sfide 1v1: RISOLTO
- Pareggi falsi skill battle: RISOLTO
- Route `/film/` vs `/films/`: RISOLTO
- Locandine duplicate: RISOLTO
- CinePass non aggiornato dopo vittoria: RISOLTO
- Crash app su trailer rotto: RISOLTO

## Feature in Pausa
- **Trailer Generation** - In attesa di soluzione produzione-compatibile (FFmpeg non disponibile)

## Task Prossimi (P1-P2)
- Sistema ruoli Admin avanzato (RBAC)
- Tutorial popup per nuovi utenti
- Layout mobile Contest Page

## Task Futuri (P3)
- Runware Integration (trailer premium a pagamento)
- CineCoins Purchase System (Stripe)
- Conversione PWA
- Layout Android Chrome

## Dominio
- cineworld-studios.it → Cloudflare DNS → Emergent Host
