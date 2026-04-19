# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi, Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game, banner promo TV, Trailer AI cinematografico con 3 tier.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini + Gemini Nano Banana) via Emergent Key
- Storage: Emergent Object Storage (trailer frames)

## Changelog
- **Feb 2026 — Fix bug dashboard + long-press likes + badge stato animato**
  - **Bug 1 risolto**: film V3 in fase `la_prima` ora esclusi da "Prossimamente" su dashboard (filtro in `ComingSoonSection.jsx`) e inclusi nell'endpoint `/la-prima/active` quando `release_type === 'premiere'`.
  - **Bug 2 risolto**: rimossa la scelta "La Prima vs Diretto" dallo step Sponsor & Marketing (`MarketingPhase`). La scelta ora e' esclusiva dello step dedicato "La Prima" (`LaPrimaPhase`), con pulsanti chiari. Backend blocca avanzamento se `release_type` non e' stato scelto.
  - **Long-press Likes**: tieni premuto il cuore rosso (500ms mobile, anche right-click desktop) per aprire popup con gli ultimi 20 like (avatar + nickname cliccabile + timestamp relativo). 2 avatar sovrapposti come anteprima accanto al counter. Nuovo endpoint `GET /api/content/{id}/likes/recent?context=X&limit=20` + componente `RecentLikesPopup.jsx`.
  - **Badge stato animato**: nella status bar del popup film/serie/anime (`ContentTemplate.jsx`) ora ogni fase ha colore+glow animato dedicato — Sceneggiatura viola, Casting giallo, Pre-Produzione blu chiaro, Riprese rosso, Final Cut arancione, Marketing verde acqua, Hype/Prossimamente azzurro, La Prima oro, Distribuzione blu cielo, Al Cinema verde, In TV indaco, In Catalogo grigio (neutro, no glow). Animazione `ct2-status-border-pulse` 2.2s ease-in-out infinite.
- **Feb 2026 (sessione precedente)**
  - **Trailer AI cinematografico** (Fase 1): 3 tier Base/Cinematico/PRO con durate 10/20/30s e costo 0/10/20 cinecrediti. Struttura narrativa 4 atti (Setup→Conflitto→Climax→Title card) via GPT-4o-mini. Immagini AI via Gemini Nano Banana con prompt genre-aware. Storage su Emergent Object Storage (URL only, no base64). Player fullscreen mobile-first con 4 gesti (tap/hold/swipe/X). Shareable URL `/trailer/{id}` (solo loggati). Trending automatico ≥50 viste. Hype bonus +3/+8/+15% applicato solo se fase ≤ pre-rilascio. Rate limit 3 trailer / 10 min. Upgrade paga solo il delta, riusa frame già generati. Fallback graceful se API fallisce (timeout 25s+30s).
  - **Fix bug locandina**: "Guarda Trailer" ora visibile in qualsiasi stato (Prossimamente + In Sala + Rilasciato) se trailer esiste.
  - Popup profilo: contatori follower/seguiti da endpoint `/players/{id}/profile`, bottone Segui/Seguito (POST /follow/{id}), filmografia collassabile, avatar+studio cliccabili, card "Miglior Produzione", unificato con sistema B.

## Backlog Prioritizzato
### P1
- Trailer AI Fase 2: reazioni (emoji+frase) e Sound FX ambientale
- Refactoring `/app/backend/scheduler_tasks.py` in worker specializzati
- Permessi specifici operativi ruolo MOD
- Integrare TrailerGeneratorCard anche in pipeline Serie TV/Anime (oggi solo Film V3)

### P2
- Notifiche push follower
- Personalizzazione avatar produttore
- Tornei PvP mensili
- Top Nav: pulsante "Online" fuori viewport ≤393px

## File di Riferimento Trailer AI
- `/app/backend/routes/trailers.py` — router completo
- `/app/backend/utils/storage.py` — wrapper Object Storage
- `/app/frontend/src/components/TrailerPlayerModal.jsx`
- `/app/frontend/src/components/TrailerGeneratorCard.jsx`
- `/app/frontend/src/components/ContentTemplate.jsx` — bottone Guarda Trailer in locandina
- `/app/frontend/src/components/v3/FilmDetailV3.jsx` — integrazione card pipeline

## Integrazioni
- Emergent LLM Key (GPT-4o-mini + Gemini Nano Banana image gen)
- Emergent Object Storage
- ICY metadata proxy (Web Radio)
