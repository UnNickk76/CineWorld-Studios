# CineWorld Studio's - PRD

## Problema Originale
Gioco di gestione di un impero cinematografico. Full-stack React + FastAPI + MongoDB.

## Requisiti Core Implementati

### Film Production Pipeline (v2.0)
- UX centrata sul singolo film con card cliccabili + popup
- Step bar adattiva: Immediato (5 step) vs Coming Soon (7 step)

### Sistema Sequel Allineato (v2.0) — 2026-03-25
- Sequel = film_project con `is_sequel: true` nella pipeline standard
- `POST /sequel-pipeline/create` crea film_project con cast/genere/trama pre-compilati dal parent
- Cast ereditato dal film originale (sconto 30%), modificabile
- Stesso flusso film: proposed → casting → screenplay → production → release cinematico
- Supporta tutte le modalita rilascio (immediato, coming soon, programmato)
- Visibilita: pre-release in pipeline, post-release in tutte le sezioni standard
- `GET /sequel-pipeline/my` mostra sequel attivi + rilasciati
- Saga bonus: +5% a +15% in base al capitolo

### Rivivi il Rilascio (2026-03-25)
- `GET /api/films/{film_id}/release-cinematic` ritorna dati cinematici
- `ReleaseCinematic.jsx` componente condiviso inline/overlay
- Card "Rivivi il Rilascio" in FilmDetail per film rilasciati

### Fix Deployment (2026-03-25)
- Corretto ciclo redirect nginx: startup non sovrascrive piu file piazzati da Emergent
- Rimosso indice MongoDB obsoleto (likes)
- Build frontend generata correttamente con index.html

### Bug Fix Produzione P0 (2026-03-26)
- Serie TV bloccate in coming_soon: auto-transizione a casting quando timer scade (GET list + detail)
- Film duplicati al rilascio: controllo idempotenza nell'endpoint POST /films/{film_id}/release
- Bozze & Recupero esteso a Serie TV e Anime: nuovo endpoint GET /series-pipeline/drafts + UI con badge tipo e icone

### Fix Velion Tutorial & Consigli (2026-03-26)
- Tutorial mostrato 1 sola volta: flag velion_tutorial_completed salvato su backend (velion_prefs)
- Consigli: cooldown globale 10 min (era 45s), polling ogni 10 min (era 60s)
- Solo eventi importanti: revenue, stuck_film, countdown_imminent, countdown
- Blocco duplicati: stesso tipo non ripetuto per 30 min
- Cambio pagina non riattiva consigli

### Mini Espansione Coming Soon + Hype + Arena (2026-03-26)
- Hype visibile: label testuale (Interesse basso / Sta crescendo / Attesissimo) in thumbnail e detail
- Feedback supporto/boicotto: toast con "+Hype in crescita" / "Hype in calo" / "Operazione fallita"
- Urgenza countdown: badge "In uscita" (<2h) e "Uscita imminente" (<30min) con ring glow
- Velion: trigger low_hype e high_hype aggiunti come high priority
- Arena: bordo glow orange (hype alto) / rosso (hype basso) sulle FilmMiniCard

### Sistema Notifiche v2.0, PvP, Fame, Cast Skills, Tutorial, Festival v3.0, Velion AI v5.0
- Vedi changelog precedente

## Architettura
- Frontend: React + Tailwind + Shadcn/UI + Framer Motion
- Backend: FastAPI + MongoDB + APScheduler
- Integrazioni: OpenAI GPT-4o-mini + GPT-Image-1 via Emergent LLM Key

## Backlog

### P1
- Sistema "Previsioni Festival" (scommesse vincitori)
- Marketplace diritti TV/Anime

### P2
- Contest Page Mobile Layout Fix
- Velion Mood Indicator, Chat Evolution
- CinePass + Stripe, PWA

### P3
- Velion Levels, RBAC, Eventi globali, Guerre tra Major, Push notifications, Velion AI Memory
