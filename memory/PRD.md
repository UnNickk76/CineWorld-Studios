# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi, Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game, banner promo TV, Trailer AI cinematografico con 3 tier.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini + Gemini Nano Banana) via Emergent Key
- Storage: Emergent Object Storage (trailer frames)

## Changelog
- **Feb 2026 — Navigazione libera stepper + sblocco advance post-Setup La Prima**
  - **StepperBar cliccabile** (`V3Shared.jsx`): ogni step e' ora un button che apre quella fase in sola visione. `onSelect(sid,idx)` prop.
  - **Read-only preview** (`PipelineV3.jsx`): nuovo stato `viewStepOverride`. Quando l'utente clicca uno step ≠ currentStep, la fase viene mostrata in modalita' anteprima (pointer-events-none + opacity-80 + banner blu "Anteprima: STEP (da fare / gia completato)" con bottone "Torna al tuo step"). Il banner advance viene nascosto in read-only.
  - **Reset automatico override** quando cambia film o avanza step.
  - **Advance post La Prima**: rimosso il blocco 24h. Ora la pipeline sblocca `la_prima → distribution` immediatamente dopo la configurazione citta'+datetime. Il player puo' completare Distribuzione durante le 24h della Prima.
  - **Blocco release finale** (backend `confirm_release` + frontend `StepFinale`): il bottone "Confermi spendendo..." viene disabilitato se La Prima non e' ancora conclusa (datetime + 24h). Banner countdown giallo (in attesa) / rosso (live in corso) con tempo restante in ore/minuti e citta'. Endpoint `POST /films/{pid}/confirm-release` ritorna 400 con messaggio d'attesa.
- **Feb 2026 — La Prima V3 completa (wizard città + datetime + hype buildup + animazione WOW)**
  - **LaPrimaPhase wizard 3 step** (in `Phases.jsx`): dopo scelta `premiere`, picker città (48 citta' in 7 regioni, grouped grid con nome+vibe), datetime picker libero (da domani 00:00 a +3 giorni 23:59), slider release_delay_days (1-6, default 3). Conferma → `POST /la-prima/setup/{id}`.
  - **Dashboard filter**: film V3 in fase `la_prima` rimangono in "Prossimamente" finche' `now < premiere.datetime` (flag `la_prima_waiting`). Diventano visibili nella sezione dedicata "La Prima" per le 24h successive (`la_prima_live`). Dopo spariscono fino a distribuzione.
  - **Backend `/la-prima/setup`**: ora auto-enable per V3 projects, compatibile con pipeline V3. Salva `premiere.setup_at` oltre a datetime/city/delay_days.
  - **Backend `/la-prima/active`**: ora ritorna solo film V3 con `premiere.datetime <= now < +24h`.
  - **Backend `/coming-soon`**: aggiunge campi `la_prima_waiting` / `la_prima_live` per ogni item V3.
  - **Pipeline advance**: blocca `la_prima → distribution` finche' non sono passate 24h dal `premiere.datetime`. Blocca anche senza city/datetime configurati.
  - **DistributionPhase**: opzione "Immediato" **freezata** (con line-through) se `release_type='premiere'`. Default 24 ore.
  - **Scheduler `process_la_prima_buildup`** (ogni 30 min): durante pre-La Prima applica hype +0.5..+1.5/tick variabile con 12% chance di surge (+2-4), cap +25 sul baseline. 30% chance/tick di auto-generare news teaser ("I fan di X sono in trepidazione per la premiere a {citta}...") — 8 template con variazione.
  - **Animazione WOW La Prima**: completamente riscritta in `PipelineAnimations.jsx`. 5 fasi drammatiche (spotlight+carpet, poster con 3D flip + doppio glow ring pulsante, citta fluttuanti con città della premiere evidenziata in oro, burst flash fotografi, 5 stelle con spring animation, LIVE badge pulsante). Trigger automatico via `useEffect` in LaPrimaPhase quando window transita `waiting → live`.
- **Feb 2026 — Barra "In Sala" ricolorata + andamento + Bacheca badge**
  - **Barra "IN SALA"** nel popup film ora ha lo stesso stile della barra FILM/CWSv/durata (gradiente borgogna/fucsia) al posto del ciano acceso. Classe `.ct2-cinema-bar` in `content-template.css`.
  - **Andamento in sala**: la stringa ora mostra `IN SALA · Xg · Yg rimasti · {Successone|Ottimo|Stabile|In calo|Affluenza scarsa|FLOP}` con colore per performance. Il label FLOP ha flicker animato.
  - **Hint prolungamento/ritiro anticipato**: se `days_remaining <= 4` e performance `great/good` → banner verde "Possibile prolungamento". Se performance `bad/flop` → banner rosso "Rischio ritiro anticipato". Mostra anche `+Xg prolungato` o `-Yg ridotto` quando i campi `days_extended/days_reduced` di `theater_stats` sono popolati (sistema esistente in `theater_life.py`).
  - **Bacheca badge** (enhancement approvato): ogni locandina in `/films` (I Miei) ora ha in basso un badge fase colorato (SCEN, HYPE, CAST, PREP, CIAK, F.CUT, MKT, LA PRIMA, DIST, USCITA, CINEMA, IN TV, CATAL) — helper `getPhaseBadge` in `MyFilms.jsx`, coerente con `ContentTemplate.getStatusInfo`.
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
