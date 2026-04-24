## LAMPO + Infrastrutture fix (Feb 2026)
Tre fix critici post-rilascio LAMPO:
1. **Auto-seed production_studio Lv 0** — ogni utente (nuovo o legacy) riceve automaticamente uno studio di produzione di default al Livello 0 all'apertura di `GET /api/infrastructure/my`, gratuito. Idempotente (non sovrascrive studi esistenti). Sblocca core gameplay anche senza acquisto.
2. **Tooltip "i" infrastrutture popolato** — `INFRA_INFO` in `/app/backend/routes/studio_info.py` esteso a 17 tipi (prima: 6). Ogni infra ora mostra titolo, descrizione, a cosa serve, sblocchi per livello e ROI. Fix frontend: `InfrastructurePage.jsx` ora passa `infra.id` (non `infra.type` undefined) al tooltip nella tab Disponibili.
3. **LAMPO cooldown SEPARATO** — `studio_quota.py` ora accetta `mode="classic" | "lampo"`:
   - Tabella quota LAMPO dedicata (più veloce: 24h Lv 0-2, 12h Lv 3-5, 6h Lv 6-8, ...)
   - Cooldown LAMPO ancorato a `created_at` del LAMPO project (anti-evasione refresh)
   - Classic exclude `is_lampo: True` dai film/serie e `mode: lampo` dai pipeline V3
   - Anti-evasione: LAMPO auto-salvato al POST `/api/lampo/start` (già esistente)
- Touch target tooltip button maggiorato (w-6 h-6) con ring cyan per mobile UX


# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi, Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game, banner promo TV, Trailer AI cinematografico con 3 tier.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini + Gemini Nano Banana) via Emergent Key
- Storage: Emergent Object Storage (trailer frames)

## Changelog
- **Feb 24, 2026 — LAMPO v2: Lightning Icon + Distribuzione Auto + Eventi Flop/Top + XP**
  - **LampoLightning** (`components/LampoLightning.jsx` + keyframes CSS): icona ⚡ glow lampeggiante animata (flicker + pulse + drop-shadow amber/orange). Appare automaticamente su QUALSIASI poster di contenuto con `is_lampo=true` o `mode='lampo'`. Integrato in: `ContentTemplate` (modal dettaglio, top-right size md), `ComingSoonSection`, `LaPrimaSection`, Dashboard (tutte e 4 le sezioni serie/anime/film/prossimamente V3).
  - **Distribuzione automatica film LAMPO** (`utils/lampo_distribution.py`): 8 bucket di rarità pesata (tot 100%):
    - mondo 1% · 3 continenti 4% · 2 cont + 10 naz 8% · 1 cont + 20 naz 12% · 30 naz + 10 città 15% · 20 naz + 30 città 18% · 10 naz + 60 città 20% · 100 città 22%
    - I bucket con "nazioni" specificano paesi di continenti NON coperti dal bucket stesso (evita duplicazioni). Le città sampled da `db.cities` escludendo le nazioni già elencate.
    - Pool continenti: Europa, Nord/Sud America, Asia, Africa, Oceania. Pool nazioni: 76 in 6 continenti.
    - Applicato nel worker LAMPO solo per film (serie/anime usano flow TV).
    - Film doc ora include: `distribution_scope` (label), `distribution_bucket`, `release_continents`, `release_countries`, `release_cities`, `worldwide`.
    - Visibile nel modal dettaglio film con icona ⚡ e label "Distribuzione: 1 Continente + 20 Nazioni" (verificato via curl: su 30 draws i bucket rispettano le probabilità).
  - **Sistema flop/top + XP** integrato al release LAMPO:
    - Film LAMPO chiamano `generate_release_event()` della pipeline classica → cultural_phenomenon / surprise_hit / cult_following / public_flop / polarizing / scandal, ecc.
    - XP bonus per evento: cultural_phenomenon 300, surprise_hit 150, critics_rave 120, award_buzz 100, cult_following 80, soundtrack_charts 40, public_flop 30 (consolazione), polarizing/scandal/controversy 15-20, default 10.
    - XP base proporzionale al CWSv: film `cwsv×10`, serie/anime `cwsv×8`.
    - Serie/anime LAMPO: chance random (30% a CWSv<4) di "series_flop", (25% a CWSv≥8) di "series_phenomenon", (8% base) di "series_cult".
    - `db.users.xp` e `total_xp` incrementati al release.
  - Files: `utils/lampo_distribution.py` (NEW), `components/LampoLightning.jsx` (NEW), `routes/lampo.py` (enrichment release), `components/ContentTemplate.jsx`, `components/ComingSoonSection.jsx`, `components/LaPrimaSection.jsx`, `pages/Dashboard.jsx`, `index.css` (keyframes).


- **Feb 24, 2026 — FASE 1 (gating studio + tooltip i) + FASE 2 (Produzione LAMPO)**
  - **Studio Quota Policy** (`utils/studio_quota.py`):
    - Curva progettata con utente: Lv 0-2 = 1 parallel/5gg, Lv 3-5 = 2/5gg, Lv 6-8 = 3/3gg, Lv 9-14 = 5/2gg, Lv 15-24 = 8/1gg, Lv 25-49 = 12/12h, Lv 50-99 = 20/6h, Lv 100-199 = 40/1h, Lv 200+ = ∞/0.
    - `production_studio` è di DEFAULT per tutti (Lv 1 base) — film sempre accessibili. Gli altri studi (serie_tv/anime) richiedono acquisto esplicito.
    - Funzioni: `check_studio_quota`, `get_studio_quota_info`, `check_tv_station_slot`.
  - **Applicato il gating a creazione progetti** (`pipeline_v3.py` + `pipeline_series_v3.py`): /films/create e /projects/create ora verificano parallel limit + cooldown prima di consentire il nuovo progetto.
  - **Emittente TV**: slot per tipo = livello station (Lv 1 → 1 slot film + 1 serie + 1 anime, …, Lv 200+ → ∞). Funzione `check_tv_station_slot` pronta (integrata futura).
  - **Endpoint UI**: `GET /api/studio/quota` (tutte), `GET /api/studio/quota/{type}` (una), `GET /api/infrastructure/info/{type}` (tooltip i), `GET /api/infrastructure/info` (catalogo).
  - **Tooltip "i"** (`components/InfraInfoButton.jsx`): piccola "i" in alto a destra su ogni card infrastruttura. Modal con: descrizione breve, a cosa serve, sblocchi per livello (ogni tier spiegato), ROI. Integrato in `InfrastructurePage.jsx` sia su infrastrutture DISPONIBILI sia su POSSEDUTE. Catalogo descrittivo esposto in `routes/studio_info.py` (production_studio, studio_serie_tv, studio_anime, tv_station, cinema, agency).
  - **Produzione LAMPO** (`routes/lampo.py` + `components/LampoModal.jsx`):
    - `POST /api/lampo/start` — crea progetto + deduce fondi (con Economy Scaling) + avvia worker async 2 min.
    - `GET /api/lampo/{pid}/progress` — polling stato 0-100% con messaggio AI.
    - `POST /api/lampo/{pid}/release` — film va in `db.films` (in_theaters), serie/anime in `db.tv_series` (auto-adoption TV station dell'owner se target non impostato).
    - CWSv per tier livello studio: Lv 1-5 = 3.0-4.5 (5% jackpot 7-8), Lv 6-10 = 4.0-6.0 (7% jackpot), Lv 11-20 = 5.0-7.0, Lv 21-50 = 6.0-8.0, Lv 51-100 = 7.0-8.5, Lv 101+ = 7.5-9.0 (15% jackpot 9.2-9.8).
    - Budget tier: low (-1.0 CWSv), mid (baseline), high (+0.8 CWSv). Costi: 50k/150k/400k (film), 80k/250k/700k (serie), 100k/350k/900k (anime).
    - Niente trailer, mai (come richiesto).
    - Gating: LAMPO usa STESSO slot/cooldown dei progetti normali (bilanciamento).
  - **Modal frontend LAMPO** a 4 fasi:
    1. ModeChooser: 2 card grandi "Completa" vs "LAMPO!" (bene impaginate)
    2. LampoForm: titolo + genere + pretrama + 3 budget cards
    3. LampoProgress: cerchio SVG 0-100% con gradient amber + messaggi AI + bottone "Riduci a icona"
    4. LampoResult: locandina + CWSv colorato + pretrama + cast + episodi + bottone Rilascia
  - Integrato in `PipelineV3.jsx` (film) e `PipelineSeriesV3.jsx` (serie + anime) sul bottone "+ Nuovo progetto".
  - **Backlog**: royalty auto TV Rights, scheduler scadenza TV Rights, estensione TV Rights a film, audit Major/Alleanze.


- **Feb 24, 2026 — Fix "Aggiungi Serie TV" al palinsesto (bottone + su TV station)**
  - **BUG**: cliccando "+" per aggiungere "The Concept" al palinsesto della propria TV station, l'endpoint `POST /tv-stations/add-content` rifiutava con "Serie non trovata o non completata". Root cause: il filtro cercava `status: 'completed'` (legacy V2) ma le serie V3 rilasciate hanno `status: 'in_tv'` (Prossimamente TV) o `'catalog'` (My List only).
  - **Fix**: query ora accetta `status in ['completed', 'in_tv', 'catalog', 'released']` — compatibile con legacy V2 e serie V3.
  - File: `routes/tv_stations.py` linea 415.


- **Feb 24, 2026 — Fix "Orphan adoption" serie senza target TV station**
  - **BUG ROOT CAUSE**: Le serie V3 rilasciate con flag `prossimamente_tv=True` ma SENZA che l'utente avesse scelto una TV station specifica in DistributionPhase, restavano con `target_tv_station_id=null`. Risultato: apparivano nel banner dashboard "In Arrivo su TV" (dato che `/prossimamente` non filtra per station) ma non apparivano nella pagina della TV del proprietario (che filtra per `scheduled_for_tv_station`). Nessun bottone per accettarle/gestirle.
  - **Fix al release** (`pipeline_series_v3.py`): se `prossimamente_tv=True` ma nessun target station è scelto, auto-assegna alla prima TV station del proprietario (ordinata per created_at asc). Evita bug future.
  - **Self-heal retroattivo** (`routes/tv_stations.py` `/scheduled` endpoint): quando il proprietario apre una qualsiasi sua TV station, tutte le sue serie V3 "orfane" (prossimamente_tv=True, pipeline_version=3, senza target/scheduled TV) vengono auto-assegnate a quella station. Risolve serie già rilasciate con il bug (come "The Concept").
  - **Flow accept-pending**: era già presente (`POST /tv-stations/{id}/accept-pending/{content_id}`), ma nessuna serie arrivava alla coda. Ora le serie orfane ci arrivano e il proprietario può accettarle / modificare batching dal bottone `PendingTVEditModal` in `TVStationPage.jsx`.
  - **Bug 1 (non-proprietario vede vuoto)**: verificato che `/pipeline-series-v3/prossimamente`, `/coming-soon` e `dashboard/batch.recent_series_global` sono TUTTI globali (no filtro user_id). Se un non-proprietario vede vuoto, è cache browser oppure i dati della serie hanno `prossimamente_tv=False` o `status` non in `['in_tv', 'catalog', 'completed', 'released']`. Il self-heal sopra sistema anche questo.


- **Feb 24, 2026 — Producer Badge + Ordinamento per-sezione + TV Rights migliorato**
  - **Nuovo componente `ProducerBadge`** (`components/ProducerBadge.jsx`): piccola fascetta "DI [nickname]" con colore deterministico dal nickname. Appare SOLO quando il contenuto NON è del player corrente. Integrato in: Ultimi Film al Cinema, Ultimi Aggiornamenti Serie TV, Ultimi Aggiornamenti Anime, Prossimamente (ComingSoonSection), In Arrivo su TV (ProssimamenteV3Section), La Prima.
  - **Nuovo componente `SectionSortMenu`** + helper `sortItems()` (`components/SectionSortMenu.jsx`): piccola icona `ArrowDownUp` accanto ai banner sezione. Dropdown con opzioni (Più Recenti, Top Voto, Più Visti, Più Amati, A-Z). Scelte **persistite in localStorage** per-sezione. Integrato in tutte le 6 sezioni dashboard (LaPrima con "LIVE prima", Prossimamente con "Più Vicini", Ultimi Aggiornamenti Film/Serie/Anime, In Arrivo su TV).
  - **Sistema TV Rights migliorato** (`routes/market_v2.py`):
    - **Durata licenza**: `CreateTVRightsRequest` ora accetta `duration_months` (0=perpetuo, 6/12/24/36). Record `tv_rights` ora ha `expires_at` calcolato (+30 gg × mesi). Listing mostra label "12 mesi" / "Perpetuo".
    - **Integrazione palinsesto**: `GET /api/tv-stations/{id}/scheduled` ora include anche le serie/anime per cui il proprietario della station ha `tv_rights` attive (non scadute). I doc ritornano con `is_licensed: true`, `license_expires_at`, `license_royalty_pct`, `original_owner_id`. Risolve il problema "ho affittato una serie ma non appare nella mia TV".
  - **Backlog TV Rights** (non implementato, memoria per futuro):
    - Royalty automatica: ogni airing/box-office della serie dovrebbe incrementare `total_royalties_due` del record `tv_rights`; owner originale può incassare manualmente o tramite pagamento auto.
    - Estensione TV Rights anche per FILM (oggi solo serie/anime).
    - Auto-disattivazione record `tv_rights.active=False` alla scadenza (scheduler task).
  - Files: `components/ProducerBadge.jsx` (NEW), `components/SectionSortMenu.jsx` (NEW), `components/ComingSoonSection.jsx`, `components/LaPrimaSection.jsx`, `pages/Dashboard.jsx`, `routes/market_v2.py`, `routes/tv_stations.py`.


- **Feb 24, 2026 — Badge "Produci" fantasma + Feed globale Serie/Anime**
  - **Badge fantasma risolto**: `GET /api/pipeline-v2/production-counts` ora esclude dal conteggio "series_legacy"/"anime_legacy" i doc `tv_series` con `pipeline_version: 3` (serie V3 già rilasciate, non ancora in produzione). Prima il campo `status='concept'` orfano le contava come "in produzione", accendendo il badge "Produci" ma senza aprire nessun progetto reale.
  - **Self-heal status orfani**: stesso endpoint riscrive silenziosamente `status → catalog` (o `in_tv` se `prossimamente_tv`) per doc V3 con status legacy residuo (`concept|casting|screenplay|production|ready_to_release|coming_soon`). Nessuna migrazione manuale richiesta — basta aprire la dashboard.
  - **"Ultimi Aggiornamenti Serie TV / Anime" diventa feed globale**: `dashboard/batch` espone nuovi campi `recent_series_global` e `recent_anime_global` (top 20 rilasci di tutti gli utenti, arricchiti con `producer_nickname` + `producer_house`). `pages/Dashboard.jsx` usa il feed globale quando disponibile, fallback su `my_series/my_anime`. Ogni card mostra ora anche il nickname del proprietario sotto il titolo.
  - **Clic card anime** ora porta al dettaglio `/series/{id}` (prima andava genericamente a `/films?view=anime`).
  - Files: `routes/pipeline_v2.py` (self-heal + filtro V3), `routes/economy.py` (feed globale + enrich), `pages/Dashboard.jsx` (rendering + producer sotto card).


- **Feb 24, 2026 — Dashboard "IN ARRIVO SU TV" + Pipeline→TV Prossimamente fix**
  - **Dashboard**: `ProssimamenteV3Section` (`pages/Dashboard.jsx`) ora resta sempre visibile anche quando vuota. Stato vuoto: placeholder tratteggiato "Nessun contenuto in arrivo" (come altre sezioni della dashboard). Prima scompariva del tutto.
  - **Pipeline V3 Serie/Anime → Prossimamente**: BUG risolto. Al release in `pipeline_series_v3.py` l'accoppiata `scheduled_for_tv + scheduled_for_tv_station` richiedeva SIA `target_tv_station_id` SIA `prossimamente_tv`. Ora basta il `target_tv_station_id`: se l'utente ha esplicitamente scelto una TV in DistributionPhase la serie finisce automaticamente in Prossimamente di quella TV.
  - **Self-heal**: `GET /api/tv-stations/{id}/scheduled` ora ripara silenziosamente ogni serie dell'owner con `target_tv_station_id` impostato ma `scheduled_for_tv=False` (retrofit per serie rilasciate con il vecchio bug). Niente migrazione manuale necessaria.
  - **Memoria / follow-up futuri**:
    - **Sistema affitto (noleggio) TV rights**: risulta già implementato in `routes/market_v2.py` (`/market/tv-rights/list` + `/market/tv-rights/buy/{listing_id}`). Se un utente affitta la serie di un altro, oggi NON appare in Prossimamente della sua TV perché `/scheduled` filtra su `user_id`. Da valutare: estendere la query per accettare serie con licenza/affitto attivo verso il proprietario della station.
    - **Flusso "accept-pending"**: già presente (`POST /api/tv-stations/{id}/accept-pending/{content_id}` + `edit-pending`). Frontend `TVStationPage.jsx` li chiama. Quindi il flow "Conferma Prossimamente" è già funzionante; era solo il routing a monte che non popolava la coda.


- **Feb 24, 2026 — Content detail modal: 5 fix veloci (Serie TV/Anime)**
  - **Pretrama scrollabile** (`ct2-info-plot`): rimosso `-webkit-line-clamp`, aggiunto `max-height:78px + overflow-y:auto` + scrollbar custom dorata. Ora la pretrama lunga si può scorrere invece di troncarsi.
  - **Episodi cliccabili**: "24 EPISODI" nel data bar ora è un bottone sottolineato che apre `EpisodesModal`. Modal mostra tutti gli episodi; cliccando si espande la sinossi SOLO per quelli già andati in onda (+ il precedente). Regola di gating: se `release_policy === 'all_at_once'/'binge'` o `status === 'completed'/'catalog'` → tutte leggibili; altrimenti contiamo aired tramite `ep.air_date` oppure calcolo da `released_at + tv_eps_per_batch + tv_interval_days`.
  - **Cinema bar "IN SALA" nascosto per serie/anime** (`hidden={isSeries}` + `display:none`). Prima appariva "IN SALA · 0g · 21g rimasti" anche per Serie TV che non vanno mai al cinema.
  - **Screenplay per Serie V3 recuperato**: `db.tv_series` release ora include `screenplay_text`, `screenplay_source` e `trailer` nel doc (prima mancavano). Fallback runtime in `GET /api/series/{id}` che legge dal `source_project_id` → `series_projects_v3` se il field è mancante. Frontend ha inoltre fallback ulteriore: se nessuno screenplay top-level ma `episodes[]` ha `screenplay_text/synopsis` → concatena con separator per episodio.
  - **Trailer Serie/Anime**: aggiunto fallback in `GET /api/trailers/{content_id}`: se `coll in (tv_series, anime_series)` e trailer mancante, cerca in `series_projects_v3` via `source_project_id`. Ora il banner "Guarda Trailer" compare correttamente per le serie rilasciate.
  - Files: `components/ContentTemplate.jsx`, `styles/content-template.css`, `routes/pipeline_series_v3.py` (release), `routes/series_pipeline.py` (detail), `routes/trailers.py` (fallback).
  - **Memoria / follow-up futuri**:
    - **Da controllare**: Serie TV e Anime dovrebbero essere creabili SOLO se si possiede l'infrastruttura dedicata (acquistabile). Verificare lo stato attuale di questo check ed eventualmente ripristinarlo.
    - **Da ripristinare (evento)**: esisteva in passato un evento che permetteva a Serie TV/Anime di andare al cinema. Verificare se è stato rimosso e valutare ripristino, collegando la meccanica ai livelli delle infrastrutture del player.


- **Feb 24, 2026 — Economics Overhaul (Cost Scaling + Level-Gating + CWSv Variance)**
  - **Cost Scaling** (nuova util `utils/economy_scaling.py`): curva asintotica `0.35 + 1.15*(1-e^(-lvl/50))` → Lv 1 = 0.37x, Lv 30 = 0.87x, Lv 100 = 1.34x, asintoto 1.50x. Sconti extra: "Onramp esordiente" -10% per i primi 5 film (Lv≤5), "Bonus indie" -30% per veterani (Lv≥30) che fanno low/micro/indie budget.
    - Applicato dentro `_spend()` di `routes/pipeline_v3.py`: hype, cast, marketing, distribution, production (release finale). Le fonti non-scalabili (cinepass_purchase, fees, market) restano al prezzo base.
    - Applicato anche al save-hype di serie TV e anime (`routes/pipeline_series_v3.py`).
    - Esposto bundle trasparente (`label`, `multiplier`, `bonuses[]`, `discount_pct`) nel response di `GET /production-cost` e nelle balances dopo ogni spesa.
  - **Cast Level-Gating**: `GET /cast-proposals` di film/serie/anime filtra NPCs per livello player:
    - Lv 1-2 → max 2★ · Lv 3-5 → max 3★ · Lv 6-15 → max 4★ · Lv 16+ → 5★ sbloccato.
    - 5% chance (max 1 per ruolo) di un NPC "Interessato" del tier superiore a +50% costo. Flag `is_interested: true` nel response + `interested_surcharge_pct: 50`.
  - **CWSv Variance Rework** (`utils/calc_quality.py`, `calc_quality_idea.py`, `calc_quality_cast.py`):
    - Baseline idea: 5.0 → 4.5. Clamp 3.5-8.5 → 3.0-9.0. Luck ±0.3 → ±0.5.
    - Cast modifier: regista ±4% → ±6%, attori ±6% → ±10%. Clamp totale ±12% → ±18%.
    - Fattore fortuna finale: ±15% → ±25%. Cap finale: 10.0 → 9.8 (mai 10 perfetto).
    - **Jackpot genre match** (+1.2 bonus): se 3+ attori principali hanno il genere del film nei `strong_genres` E avg skill ≥ 75.
    - Test verifica: film pessimo → 3.9, film mediocre → 4.0, film eccellente → 9.8 (contro il precedente 7-8 compresso).
  - Testato via curl end-to-end con account fandrex1 (Lv 1): 10M budget mid → scalato a 3.36M (-66% Lv 1 + Onramp), hype $100k→$33.5k, cast proposals solo 2-3★.
  - Files: `utils/economy_scaling.py`, `utils/calc_production_cost.py`, `utils/calc_quality*.py`, `routes/pipeline_v3.py`, `routes/pipeline_series_v3.py`.


- **Feb 23, 2026 — CastPhase Serie/Anime V3 identico a Film + NPCs anime**
  - **Seed anime NPCs** (`scripts/seed_anime_crew.py`): 300 `anime_director` + 2000 `anime_illustrator` in `db.people`. Ogni NPC ha: 8 skill da 50 anime-coerenti (director: storyboard/visual_style/pacing/animation_direction/storytelling/emotional_scoring/action_choreography/character_design_sense; illustrator: linework/character_design/background_art/color_palette/motion_frames/expressions/chibi_sd_style/mecha_detail), sex (male/female/non-binary), nationality (preferenza JP + KR/CN/IT/...), age 22-68, imdb_rating, 2 primary_skills (punti di forza) + 1 secondary_skill (punto debole), stars 1-5, cost e fame. Script idempotente.
  - **Scheduler** `replenish_anime_crew_pool` ogni 14 giorni: rispawna NPCs se il pool scende sotto target.
  - **Backend endpoints serie V3** (`routes/pipeline_series_v3.py`):
    - `GET /projects/{pid}/cast-proposals`: per anime ritorna `directors=anime_director`, `illustrators=anime_illustrator`, `screenwriters=writer`, `composers=composer`. Per serie tv mantiene `directors/actors/screenwriters/composers`. Caps fama basati su livello/fame player (come film V3).
    - `POST /projects/{pid}/select-cast-member`: aggiunge NPC al cast con ruolo (protagonista/supporto/generico).
    - `POST /projects/{pid}/remove-cast-member`: rimuove.
    - `POST /projects/{pid}/auto-cast`: completa automaticamente (1 regista + 1 compositore + 2 sceneggiatori + 4 main pool attori/disegnatori).
  - **Frontend CastPhase** (`components/v3/PipelineSeriesV3.jsx` completamente riscritto):
    - 4 slot: Regista/Showrunner (cyan), Sceneggiatori (violet, max 4), Attori o **Disegnatori** per anime (amber, max 30 con tag ruolo Prota/Sup/Generico), Compositore/OP-ED (purple).
    - `CastPickerSheet`: bottom-sheet mobile con lista proposte, skill primary/weak chip, cost, click "Scegli".
    - `NpcSkillSheet`: visualizzazione 8 skill con barra di avanzamento, primary/weak highlighted, dati completi (età/sesso/nazione/IMDb/cost).
    - Bottone "Completamento Automatico" riusa auto-cast endpoint.

- **Feb 23, 2026 — Admin Panel: sezione Trailer**
  - **Backend**: 3 nuovi endpoint admin-only:
    - `GET /admin/all-trailers?q=` scansiona `films + film_projects + tv_series + series_projects_v3` cercando `trailer.frames` not empty. Ritorna `{content_id, collection, content_type, title, poster_url, tier, mode, views/likes/dislikes, generated_at, parent_exists, parent_stage, owner_nickname, studio_name, owner_exists}`.
    - `GET /admin/trailer-detail/{content_id}` → trailer completo con frames per playback.
    - `DELETE /admin/delete-trailer/{content_id}` → `$unset trailer` su tutte le 4 collezioni + cleanup `trailer_votes`.
  - **Frontend AdminPage**: nuova 4a tab "Trailer" a fianco di Film/Serie TV/Anime. Apre `TrailersAdminPanel` con:
    - Search box per titolo.
    - Grid compatta (48px) di poster con badge tier al centro.
    - Click sulla card → popup: proprietario (o "Ex-proprietario" se user cancellato), status del parent (Esiste/No), tier, views, 2 bottoni "Visualizza Trailer" (fetch detail + `TrailerPlayerModal`) e "Elimina per sempre" (ConfirmModal di sistema).
  - Verificato via curl: 4 trailer trovati, metadata corretti (owner, parent_exists, tier).
  - Files: `server.py` (endpoints), `pages/AdminPage.jsx` (TrailersAdminPanel).

- **Feb 23, 2026 — Tripletta admin/owner + eventi globali**
  - **Fix 1 (owner)**: aggiunto bottone "Elimina per sempre" con `CineConfirm` (Cineox+Velion, tono rose) in:
    - `ContentTemplate.jsx` (qualsiasi stato del film, qualsiasi sezione, visibile solo al proprietario)
    - `ProssimamenteDetailModal.jsx` (serie/anime V3 in fase idea/hype/etc.)
    - Backend: `DELETE /admin-recovery/delete/{id}` ora accetta **owner oltre admin**, scansiona tutte le 4 collezioni (`films`, `film_projects`, `tv_series`, `series_projects_v3`) + `source_project_id`. Cleanup likes/ratings inclusi.
  - **Fix 2 (eventi per tutti)**: `GET /api/events/history` ora restituisce gli eventi globali (non filtrati per `user_id`), con **campionamento deterministico 1/2** (fetch `limit*2`, keep alternati) per dimezzare il volume. Tutti i player vedono la stessa timeline ridotta.
  - **Fix 3 (admin panel ampliato)**:
    - `GET /api/admin/all-films?content_type={film|tv_series|anime}` unificato: scansiona `films + film_projects` per film, `tv_series + series_projects_v3` per serie/anime. Include stato V3 (idea, hype, cast, ciak, finalcut, distribution). Campi extra: `stage`, `collection`, `owner_nickname`, `studio_name`, `has_open_report`, `reports_count`, `needs_fix`.
    - `DELETE /api/admin/delete-film/{id}` esteso a tutte e 4 le collezioni + `source_project_id`. Risolve le bug_reports linkate.
    - **Frontend FilmsTab**:
      - Tab sottosezioni: Film / Serie TV / Anime.
      - Grid poster **ridotti del ~70%** (minmax 80→48px).
      - Card cliccabile → popup con owner, stage, qualita', genere, badge segnalazioni.
      - 2 bottoni: "Elimina definitivamente" (sempre) + "Fix" (abilitato se `needs_fix`).
      - **Cards con bug report aperte**: scale 150% + **pulse amber animato** via keyframes `admin-report-pulse` → l'admin le individua subito.
      - Badge sopra poster `"!<N>"` che indica il numero di segnalazioni.

- **Feb 23, 2026 — Tripletta veloce: Prossimamente cliccabile + Trailer Serie/Anime + Progress trailer**
  - **Fix 1**: `ComingSoonSection` (Dashboard "PROSSIMAMENTE SERIE TV / ANIME") ora apre `ProssimamenteDetailModal` invece di navigare a `/series/{id}`. La modale usa `/api/series/{id}` con fallback su `series_projects_v3` che gia' gestisce progetti incompleti omettendo i campi mancanti (CONTENT_TYPE filter copre `series|anime|tv_series`).
  - **Fix 2**: `_collect_trailers` (in `routes/trailer_events.py`) ora scansiona anche la collezione `series_projects_v3`, oltre a `films + tv_series + film_projects`. I trailer di serie TV e anime V3 (sia pre-release che released) **compaiono automaticamente nella strip "Ultimi Trailer"** della dashboard e **competono nel contest giornaliero/settimanale** (`/events/trailers/daily` e `/weekly`) perche' usano la stessa util. Type risolto via `doc.type` → `tv_series` o `anime`.
  - **Fix 3**: rimossa la live-preview grid dei frame durante la generazione trailer (non funzionava e creava confusione). Ora `TrailerGeneratorCard` mostra un **grande cerchio al centro con percentuale dentro** (28x28, `text-[24px] font-black`), stage corrente e countdown sotto. Mobile-first, piu' pulito e concentra l'attenzione sul progresso.
  - Files: `components/ComingSoonSection.jsx`, `components/TrailerGeneratorCard.jsx`, `routes/trailer_events.py`.

- **Feb 23, 2026 — Doppio fix rapido: "A breve" duplicato + freccia andamento spettatori**
  - **Bug 1**: la card "A BREVE" persisteva accanto alla card "AL CINEMA LIVE" dello stesso film. Il filtro frontend confrontava `r.id` (nuovo UUID post-confirm-release) con `ab.film_id` (project id) → non matchava mai.
    **Fix**: `routes/pipeline_v3.py recent-releases` ora include `source_project_id` nella projection. Il filtro frontend confronta sia `r.source_project_id === ab.film_id` che `r.id === ab.film_id`.
  - **Bug 2**: la `AttendanceTrendBadge` mostrava "—" quasi sempre perche' il `trend_dir` in `scheduler_tasks.update_film_attendance` confrontava `last tick vs previous tick` (10 min → rumore, rumore risolto come flat). Inoltre badge centrato tra lo sfondo verde, non visibile.
    **Fix cadenza**: confronto ora su **3 ore fa** (`attendance_history[-18]`, 18 tick × 10 min). Fallback all'entry piu' vecchia disponibile nelle prime 3 ore. Soglia ±3%.
    **Fix UI**: badge spostato a `absolute bottom-0.5 right-0.5` (fuori dalla pill "AL CINEMA", in angolo a destra), aggiunto `animate-pulse` + ombra bagliore piu' intensa quando trend e' `up`/`down` (resta statico per `flat`).
  - Files: `routes/pipeline_v3.py`, `scheduler_tasks.py`, `pages/Dashboard.jsx`, `components/AttendanceTrendBadge.jsx`.

- **Feb 23, 2026 — Badge rosso "Produci" visibile anche in fase IDEA e HYPE (V3)**
  - **Bug**: `GET /api/pipeline-v2/production-counts` (usato dal topbar + side-menu per il pallino rosso) non includeva gli stati V3 `idea`/`hype`/`cast`/`ciak`/`finalcut`/`distribution` per film. Non considerava la collezione `series_projects_v3` (tutte le serie/anime V3). Risultato: durante idea e hype il badge era 0.
  - **Fix** (`routes/pipeline_v2.py` get_production_counts):
    - Aggiunti stati V3 (`idea`, `hype`, `cast`, `ciak`, `finalcut`, `distribution`) al set `active_states` per `film_projects`.
    - Aggiunta query su `series_projects_v3` (serie + anime) filtrando `pipeline_state $nin [released, discarded, deleted]`.
    - Output totale = legacy V2 + V3.
  - Test: curl per fandrex1 → `{"total":5,"film":5,...}` (prima 0 per film in idea).

- **Feb 23, 2026 — Fix formato serie Lunga/Maratona: slider 20-26 / 40-52 ora funziona**
  - **Bug**: selezionando Thriller (range genere 4-13) + Lunga (20-26) o Maratona (40-52), la intersezione `max(lo)/min(hi)` dava range **invertito** (`[20,13]`), lo slider restava a max 13 e l'etichetta mostrava "20-13, formato: lunga" assurdo.
  - **Fix frontend** (`components/v3/PipelineSeriesV3.jsx` L146-154): se intersezione vuota (`epMin > epMax`), fallback al `formatRange` puro. Formato ha priorita'.
  - **Fix backend** (`routes/pipeline_series_v3.py save-idea`): stessa logica applicata lato server — il clamp a `num_ep` usa il range del formato quando estende oltre il range del genere. Cosi' un thriller Maratona puo' avere legittimamente 40+ episodi.
  - **Coerenza AI**: `generate-episode-titles` e `generate-screenplay` usano `project.num_episodes` direttamente → generano il numero esatto di titoli + mini-trame (40 per maratona). `_episode_duration` calcola le varianti per ogni ep, totale coerente.

- **Feb 23, 2026 — Durata episodi variabile e coerente con scelta utente**
  - **Bug**: la durata mostrata per ogni episodio era hardcoded via `estimateEpisodeDuration(type, genre)` che ritornava 55m per thriller/drama etc., ignorando la scelta utente `episode_duration_min` (30/45/60). Anche il totale era `num_ep * 55` errato.
  - **Fix backend** (`routes/pipeline_series_v3.py`): nuova util `_episode_duration(base, pid, ep_num)` che usa MD5 seeded da `pid+ep_num` per distribuire variazioni deterministiche in `[base-3, base+7]` (es. base 45 → ep individuali 43/47/48/50/51/52m). Salvato come `duration_min` su ogni episodio in `generate-episode-titles` e preservato in `generate-screenplay`.
  - **Fix frontend** (`components/v3/PipelineSeriesV3.jsx`): ora usa `project.episode_duration_min` come base e `ep.duration_min` per ogni singolo episodio. Totale = somma reale dei singoli. Badge modale episodio mostra `Ep N · Xm`. `ProssimamenteDetailModal` mostra anche la durata sotto il titolo.
  - **Verifica**: per pid fisso, base=45 / 13 ep → 624m totali (≈10h24m), media 48m, range 43-52m.

- **Feb 23, 2026 — IdeaPhase V3: Scarta + Ricomincia con Cineox+Velion**
  - **Nuovo componente condiviso** `components/v3/CineConfirm.jsx`: modale conferma con i mascot **Cineox + Velion**, glow tonale (rose/amber/violet), animazioni float dei personaggi, backdrop blur, auto-close su tap esterno. Mobile-first.
  - **Backend endpoints nuovi**:
    - `POST /pipeline-v3/films/{pid}/hard-delete` → elimina completamente il progetto film V3 (no transfer a mercato). Blocca se `pipeline_state=='released'`. Cleanup orfani `films` con stato `market|discarded`.
    - `POST /pipeline-v3/films/{pid}/restart` → reset totale: titolo, genere, pretrama, locandina, sceneggiatura, cast, locations, equipment, CGI/VFX, shooting_days, flag di fase, sponsor, marketing, premiere, distribuzione, hype, trailer, durata, cwsv ecc. tutti wiped. Stesso ID progetto. Salva `restarted_at`.
    - `POST /pipeline-series-v3/projects/{pid}/hard-delete` → idem per serie/anime V3. Cleanup orfani `tv_series` con stato `discarded|catalog`.
    - `POST /pipeline-series-v3/projects/{pid}/restart` → reset completo serie/anime V3 (include anche campi TV: target_tv_station_id, release_policy, eps/interval/split/delay).
  - **Frontend IdeaPhase Film** (`components/v3/IdeaPhase.jsx` → nuovo `DangerZoneFilm`): 2 bottoni in fondo "Ricomincia" (ambra, `RotateCcw`) + "Scarta" (rose, `Trash2`), ognuno apre `CineConfirm`. Su conferma discard → redirect a `/produci`. Su restart → `onRefresh()`.
  - **Frontend IdeaPhase Serie/Anime** (`components/v3/PipelineSeriesV3.jsx` → nuovo `SeriesDangerZone`): stessi 2 bottoni con `data-testid="series-idea-restart-btn"` e `series-idea-discard-btn`. Chiama gli endpoint serie.
  - **Sicurezza**: entrambi gli endpoint rigettano richieste su progetti `released` (code 400).
  - Zero breaking change sugli endpoint `/discard` legacy (conservati per eventuali flussi vecchi).

- **Feb 23, 2026 — Serie TV/Anime V3: emittente in pipeline + dashboard cliccabile + pending TV UX**
  - **Pipeline V3 DistributionPhase (serie+anime)**: se `prossimamente_tv=true`, il player ora sceglie l'**emittente TV di destinazione** tra le proprie + opzione "Nessuna emittente". Field nuovo `target_tv_station_id` (salvato via `/save-distribution`, propagato a `confirm-release`). Se seleziona una TV → al rilascio viene popolato `scheduled_for_tv=true, scheduled_for_tv_station=<id>` sulla `tv_series`, e config pipeline (eps_per_batch, interval, split, delay) propagata.
  - **Dashboard "IN ARRIVO SU TV" cliccabile**: ogni poster ora e' un button che apre `ProssimamenteDetailModal` (nuovo). Usa `/api/series/{id}` (normalizzato V1/V2/V3) per mostrare: hero, produttore, CWSv/quality, countdown airing, preplot, e **lista episodi cliccabili** — ogni episodio espande inline il `mini_plot` AI generato in IdeaPhase. Episodi senza mini-trama mostrano "Mini-trama disponibile al rilascio".
  - **Owner actions nella modal**: se l'owner clicca la propria serie senza `scheduled_for_tv_station`, appaiono 2 azioni owner-only: "Invia a TV" (station picker → POST `/tv-stations/{st}/assign-series/{sid}`) e "Vendi al Mercato" (redirect `/marketplace?sell=series&id=<id>`).
  - **TVStationPage "Prossimamente" con pending approval**: il `NetflixRow` ora renderizza le tile con `pending_tv_approval=true` come **poster oscurato** (opacity 55 + grayscale 30 + ring ambra), badge "DA PIPELINE" e countdown accanto. Overlay con 2 bottoni tondi grandi:
    - **✔️ verde** → `POST /tv-stations/{st}/accept-pending/{cid}` conferma le impostazioni pipeline.
    - **✏️ ambra** → apre `PendingTVEditModal` (nuovo) con controlli eps/interval/split/delay coerenti con la `release_policy`, poi `POST /tv-stations/{st}/edit-pending/{cid}` sovrascrive e accetta.
  - **Scheduler auto-apply** (`process_tv_pipeline_auto_apply`, ogni 5 min): trova serie V3 con `scheduled_for_tv_station` impostato, `tv_schedule_accepted_at` null, e `released_at + distribution_delay_hours` scaduto → auto-accetta con i settings pipeline + inserisce una notifica silenziosa `tv_auto_scheduled` nel campanello utente.
  - **`/tv-stations/{id}/scheduled`** esteso: ritorna ora il flag `pending_tv_approval`, `tv_airing_start` (computed), e tutta la config pipeline per alimentare la modal edit.
  - **`/tv-stations/available-content/{id}`** esteso a serie V3 con `status ∈ {completed, in_tv, catalog}` (prima solo `completed`, per questo la serie propria non compariva nel picker "Aggiungi Serie TV").
  - Files: `routes/pipeline_series_v3.py`, `routes/tv_stations.py` (nuovi endpoint accept/edit/assign-series), `scheduler_tasks.py` (+`process_tv_pipeline_auto_apply`), `server.py` (job registrato), `components/v3/PipelineSeriesV3.jsx` (selettore station), `components/ProssimamenteDetailModal.jsx` (nuovo), `components/PendingTVEditModal.jsx` (nuovo), `pages/Dashboard.jsx` (click handler), `pages/TVStationPage.jsx` (NetflixRow overlay + modal mount).

- **Feb 23, 2026 — Silent Bonuses system (invisibile, anti-frustrazione new players)**
  - **Nuovo modulo** `/app/backend/utils/silent_bonuses.py` con 3 layer totalmente silenziosi (nessun toast/evento frontend):
    1. **Onboarding boost** gg 0-6 (peak) con taper lineare gg 7-10: cap cumulativo in $ scalato per numero film posseduti (`0 film=$2M`, `1=$10M`, `2=$17M`, `3=$22M`, `4=$26M`, `5=$28M`, `6+=$28M` plateau). Pace `~0.5% del rimanente` per heartbeat, circa 200 beat per svuotare il cap in 6gg.
    2. **Session continuity**: 4 soglie con reset dopo 30min idle — `10m=$5K`, `30m=$15K`, `60m=$40K`, `120m=$100K`. Idempotente: ogni threshold pagato una sola volta per sessione.
    3. **Daily login + hourly**: `$50K` al primo heartbeat del giorno, poi `$20K/h` con cap `5/giorno`.
  - **Hook in heartbeat** (`routes/progression.py POST /progression/heartbeat`): chiama `apply_silent_bonuses(db, user.id)` dopo `award_session_heartbeat`. Il `diag` ritornato NON è incluso nel payload di risposta → zero possibilità di trigger toast frontend.
  - **Wallet log**: ogni credito inserito in `db.wallet_transactions` con `silent:true`, `source ∈ {onboarding_boost, session_bonus, daily_login, hourly_bonus}`, `detail` descrittivo, `geo: 'Totale'`. `users.funds` incrementato via `$inc` nello stesso turn.
  - **DB tracking fields aggiunti a `users`**: `onboarding_boost_granted`, `last_login_bonus_date`, `hourly_bonus_today ({date, count, last_at})`, `session_start_at`, `session_thresholds_crossed`, `last_heartbeat_at`.
  - **Test curl/python**:
    - Utente veterano fandrex1 (2026-03-08): heartbeat ritorna `awarded:false`, ma funds +$50K (daily_login, prima volta oggi) → tx silent loggata correttamente. ✓
    - Simulato user "3gg fa + 6 film": 5 heartbeat danno onboarding boost $140K → $137K decrescente (0.5% del residuo), totale $693K distribuiti. ✓
    - Simulato sessione 35min: session_bonus=$20K (5K+15K). Secondo heartbeat ritorna $0 (idempotency). ✓
    - Reset dopo 40min idle: nuova sessione, $0 (giusto). ✓
  - **Zero regressioni**: `award_session_heartbeat` XP/Fame + prestige_events intatti; silent bonus in `try/except` che fallisce silenzioso.
  - Files: `utils/silent_bonuses.py` (nuovo), `routes/progression.py`.


  - **Nuovo modulo** `/app/backend/routes/purchased_screenplays_v3.py` con 2 endpoint:
    - `POST /api/purchased-screenplays/create-v3-project` — acquista sceneggiatura (emerging pubblico o agency privata) e crea direttamente un `film_projects` V3 con `pipeline_state='hype'` (idea già completato). Modes: `avanzata` | `veloce`. Prezzi: veloce=2x, agency=60% sconto. Auto-fill cast (hired_stars user + NPC medium stars), prep preset, marketing preset per Veloce. Seeding dei flag `from_purchased_screenplay`, `purchased_screenplay_mode`, `purchased_screenplay_source`, `purchased_writer_name`, `idea_locked`, `cast_locked`, `prep_locked`, `auto_advance_veloce`. Atomic: fondi dedotti SOLO dopo insert+consume riusciti (no money loss su eccezioni).
    - `POST /api/purchased-screenplays/veloce-fast-track/{pid}` — solo Veloce, da stato `hype` salta a `distribution` settando ciak/finalcut come completati e `release_type='direct'` (salta La Prima). Richiede `poster_url` creato dal player.
  - **Deprecazione soft** del vecchio flusso V2 in `emerging_screenplays.py /accept` (non rimosso per safety).
  - **Propagazione flag**:
    - `pipeline_v3.confirm-release` copia `from_purchased_screenplay` + mode + source + writer_name su `films`.
    - `economy.recent_releases` expose i campi al frontend.
    - `la_prima.coming-to-cinemas` idem su items "A Breve".
  - **Reward -50%** per Veloce (+5xp/0fame vs +15xp/1fame Avanzata) — implementato via `utils.xp_fame.award_milestone`.
  - **Frontend**:
    - `EmergingScreenplays.jsx`: modale sceglie Avanzata (emerald) / Veloce (orange) con prezzi calcolati client-side.
    - `CastingAgencyPage.jsx (ScoutScreenplaysTab)`: modale modale analoga con badge "Sconto Agenzia -60%".
    - Dopo acquisto → `navigate('/create-film?p={pid}')` → PipelineV3 auto-seleziona.
    - **`PurchasedScreenplayBadge.jsx`** (nuovo componente): book-page icon overlay, colore mode-dependent (emerald=avanzata, orange=veloce), tooltip con sorgente.
    - Badge integrato in Dashboard (A Breve cards + Ultimi Film al Cinema), ComingSoonSection.
    - PipelineV3 header: pill 📖 AVANZATA/VELOCE accanto a CWSv + budget_tier.
    - PipelineV3 sticky advance: in Veloce mode a stato `hype`, mostra bottone **⚡ Fast-Track → Distribuzione** che chiama l'endpoint fast-track.
  - **Test**: 17/17 pytest passano (`/app/backend/tests/test_iter164_purchased_screenplays_v3.py`) — copre pricing, auto-cast, fund deduction safety, error cases, marketing presets veloce, la_prima integration, regressione endpoint esistenti.

- **Feb 22, 2026 — UI Navbar: "I Miei" al centro + colore blu**
  - Bottone "I Miei" spostato dalla prima posizione al centro (index 6/12) in `App.js`.
  - Colore da giallo/grigio a **blu** (`text-blue-400` default, `text-blue-300` attivo).
  - Popup "I Miei Contenuti" ri-ancorato al centro (`left-1/2 -translate-x-1/2`).

- **Feb 22, 2026 — P0 Blocker Fix: Backend Import + XP Migration Re-run**
  - **🐛 Backend KO per import errato**: `routes/progression.py` importava `from utils.deps import get_current_user, db` ma `utils/deps.py` non esiste. Fix: sostituito con `from database import db` + `from auth_utils import get_current_user` (pattern usato da tutti gli altri route).
  - **🐛 Migration XP/Fame v2 incompleta**: il primo run ha resettato 72 utenti ma ha granted solo 72 XP totali (1 XP/utente). Cause:
    - Filtro stati film `['in_theaters','released']` mancava `'market'` (release su home video, la maggior parte dei film rilasciati).
    - `db.infrastructure` usa campo `owner_id`, non `user_id`.
    - Collections `festival_winners` e `stars` non esistono → corrette a `festival_awards` e `hired_stars`.
  - **Re-run post-fix**: 72 utenti, 697 XP totali, 7 Fame totali distribuiti. Utente test `fandrex1@gmail.com` ora ha Level 1, total_xp=600, fame=6 (prestige "Sconosciuto", next threshold 50 "Emergente").
  - **Verifica endpoint**: `GET /api/progression/info`, `POST /api/progression/heartbeat`, `GET /api/progression/tiers` tutti funzionanti.
  - Files: `routes/progression.py`, `utils/xp_migration_v2.py`.

- **Feb 2026 — Status Badge Pulse Glow (tutti gli stati pipeline/release)**
  - **Nuovo keyframe CSS `status-pulse-glow`** in `index.css`: animazione 1.8s infinita che alterna `box-shadow 0-14px` + `transform scale 1.0-1.06` usando `currentColor` così il glow riprende il colore del badge. Rispetta `prefers-reduced-motion`.
  - **Applicato a tutti i badge di stato** in Dashboard (sezioni Film/Serie TV/Anime):
    - `ComingSoonSection` — badge `pipeline_status_label` (Idea/Hype/Cast/Preparazione/Riprese/Final Cut/Marketing/La Prima/Distribuzione/Uscita) ora pulsa con il suo colore originale.
    - Dashboard `pipeline_state` top-left pill amber (pre-release films) ora pulsa.
    - Dashboard "Ultimi Film al Cinema" bottom strip: "AL CINEMA" (verde), "LA PRIMA" (amber), "IN USCITA" (blu) tutti con pulse+glow che richiama i loro colori rispettivi.
    - Card "A BREVE" dimmed arancione: wrapper interno ora pulsa col glow orange.
  - Nessun cambio colori esistenti — solo l'animazione aggiunta via classe utility. Drop-in su qualsiasi elemento futuro.
  - Files: `index.css`, `pages/Dashboard.jsx`, `components/ComingSoonSection.jsx`.

- **Feb 2026 — Fix "A Breve duplicato" root cause + Genera Trailer → Pipeline V3**
  - **🐛 Root cause "Il Sospetto" A BREVE + AL CINEMA (il bug ricorrente)**: il safeguard in `/la-prima/coming-to-cinemas` matchava `db.films.id == film_project.id`, MA al `confirm-release` viene creato un NUOVO UUID in `films.id` mentre il project id resta salvato in `films.source_project_id`. Il match non è mai stato soddisfatto → il film "A Breve" non veniva mai escluso quando il film passava a `in_theaters`. **Fix definitivo**: il match ora usa `films.source_project_id IN [project_ids]` — coerente con il design effettivo del DB. Questo è il bug ricorrente che l'utente ha segnalato 10 volte e ora è risolto alla radice.
  - **Genera Trailer anche dopo release** (`PipelineV3.jsx` + `FilmActionsSheet.jsx`):
    - PipelineV3 ora legge query param `?p=<project_id>` al mount. Se presente chiama auto-select del progetto + reset `releasePhase` per evitare re-open dell'overlay cinematico → apre direttamente la vista read-only della pipeline con TrailerGeneratorCard sempre visibile (già implementata con `isReadOnly && selected?.user_id === user?.id`).
    - FilmActionsSheet `TrailerBanner.onGo` ora naviga a `/create-film?p={film.source_project_id}` (fallback `film.id` per film legacy V2). Il sheet si chiude e la pipeline si apre con il film selezionato + TrailerGeneratorCard in evidenza. Il resto è "freezato" (read-only) come richiesto.
  - `economy.py`: aggiunta proiezione `source_project_id` in `recent_releases_task` così il campo viaggia fino al frontend.
  - Files: `routes/la_prima.py` (safeguard match fix), `routes/economy.py` (projection), `pages/PipelineV3.jsx` (useSearchParams auto-select), `components/FilmActionsSheet.jsx` (navigate target).

- **Feb 2026 — Fix Uscite $0 nel saldo strip + Uscite by-type**
  - **🐛 Uscite da wallet_transactions vuote su film legacy**: sia il saldo strip (foto 2 "Uscite $0") sia `/finance/expenses-by-type` (foto 3 Tutti/Film/0) aggregavano da `wallet_transactions direction=out` che non esiste per film legacy (spese pre-sistema finanziario). **Fix seguendo il principio utente "X+X+X… dove presenti"**:
    - **`/finance/expenses-by-type`** riscritto: ora somma direttamente `films.total_cost` + `tv_series.total_cost` (differenziato per `type='anime'` vs `type='tv_series'`). Retrofit via `calculate_production_cost` + persistenza lazy quando `total_cost=0` sul doc (stessa logica di `/finance/films-history`).
    - **`/finance/overview`** (saldo strip): aggiunge fallback `real_content_cost = sum(films.total_cost) + sum(tv_series.total_cost)` con retrofit. Se `expenses_30d < real_content_cost`, override con quest'ultimo — garantisce che il saldo strip mostri l'effettivo speso complessivo anche quando mancano tx.
  - Ora le Uscite Tutti/Film/Serie TV/Anime mostrano i veri totali (es. Seeeee $11.73M appare in Film), e il saldo strip è coerente con lo Storico.
  - Files: `routes/finance_bank.py`.

- **Feb 2026 — La Prima voce globale + Retrofit film legacy + Back navigation**
  - **🐛 La Prima mancante nei totali globali**: Finanza tab Storico e Spettatori page non mostravano il totale La Prima come voce separata. **Fix**:
    - `HistoryTab` (Finanze): nuovo strip a 2 colonne in cima "Box Office / La Prima" (con count dei film con LP). Entrate Box Office = `sum(total_revenue - la_prima_revenue)`, La Prima = `sum(la_prima_revenue)`.
    - `SpectatorsPage`: summary strip passato da 2 a 3 colonne (Totale / Ultime 24h / La Prima con count). Entrambe mobile-first.
  - **🐛 Retrofit La Prima per film legacy**: `Seeeee` aveva `release_type='premiere'` su `film_projects` ma il campo `la_prima_revenue/spectators/city/nation` non era stato copiato al `confirm-release` (pre-fix). **Fix**: sia `/finance/films-history` che `/spectators/films-history` ora fanno retrofit dal `film_projects.premiere` se i campi del film doc sono vuoti. Legge `premiere.spectators_total`, `premiere.city`, `premiere.nation`, `project.total_revenue` e usa come fallback.
  - **🐛 Freccia back**: `navigate(-1)` non fa nulla se l'utente arriva direttamente via URL (no history). **Fix**: sia `FinancePage` che `SpectatorsPage` ora usano `(window.history.length > 1 ? navigate(-1) : navigate('/'))` garantendo sempre un back fallback alla Dashboard.
  - Files: `routes/finance_bank.py` (retrofit logic + source_project_id projection), `pages/FinancePage.jsx` (HistoryTab strip + back hybrid), `pages/SpectatorsPage.jsx` (strip 3-col + back hybrid).

- **Feb 2026 — Fix definitivo Costo film (pipeline V3 calculator)**
  - **🐛 Costo $0 film legacy + nuovi**: il fallback via `wallet_transactions` non funzionava perché molti film sono stati creati senza log transazionali taggati con `ref_id=project_id`. **Fix definitivo**: usato direttamente `calculate_production_cost(project)` da `utils/calc_production_cost.py` — la stessa funzione usata nell'ultimo step della pipeline V3 per mostrare il costo al produttore. Restituisce `total_funds` già **al netto degli sponsor** (`sponsor_offset`) includendo: base produzione (per budget_tier), cast, equipment, CGI, VFX, extras, riprese, marketing, distribuzione, meno rientro sponsor.
  - **`confirm-release`** (`routes/pipeline_v3.py`): ora calcola `total_cost` con `calculate_production_cost` + fallback a wallet_transactions se il calcolatore fallisce.
  - **`/finance/films-history`** (`routes/finance_bank.py`): 3 fallback a cascata per `total_cost` quando il film doc ha $0:
    1. **Retrofit via pipeline V3 calculator** dal `source_project_id` → persiste il valore nel DB così la prossima volta è già lì (lazy migration).
    2. Aggregate da `wallet_transactions` outgoing (film V3 nuovi).
    3. Somma campi budget diretti (`total_budget/marketing_cost/production_cost/trailer_cost/distribution_cost`) come ultima spiaggia.
  - Questo risolve "Costo $0" su Seeeee e tutti i film legacy mostrando il costo reale usato in pipeline.
  - Files: `routes/pipeline_v3.py`, `routes/finance_bank.py`.

- **Feb 2026 — Hotfix 4 bug Finanze/Dashboard**
  - **🐛 Foto 1 — Geo "Globale" vs "Totale" duplicati**: il breakdown mostrava DUE righe separate ("Globale" $14.1K + "Totale" $5.3K) per le tx legacy. **Fix**: normalizzazione estesa a `globale` (it), `global` (en), `sconosciuto`, `''` → bucket unico "Totale" + merge duplicati dopo normalizzazione (`routes/finance_bank.py /finance/breakdown`). Ora si vede una sola riga "Totale" che raggruppa tutte le tx catch-all.
  - **🐛 Foto 2 — Costo $0 film legacy + giorni 1,2 mancanti**: `/finance/films-history` mostrava "Costo $0" su Seeeee (legacy V2 senza wallet_transactions outgoing) e timeline saltava i giorni senza entries. **Fix**:
    1. Fallback costo secondario: se `total_cost==0` e nemmeno `wallet_transactions` ha spese, somma `total_budget/budget + marketing_cost + production_cost + trailer_cost + distribution_cost` dai campi diretti del film doc.
    2. Fill giorni mancanti: ora `daily_revenues` è generato dal `theater_start` fino ad oggi con Giorno 1, 2, 3... anche quando non ci sono transazioni per quel giorno (valore 0). Finalmente timeline continuativa.
  - **🐛 Foto 3 — Uscite $0 redundante + chart "banda verde"**:
    1. Rimossa la sezione "Uscite by source" redundante (riportava sempre "Nessuna uscita nel periodo").
    2. Sostituita con nuovo panel **"Uscite" a 4 tab** (Tutti/Film/Serie TV/Anime). Nuovo endpoint `GET /api/finance/expenses-by-type` aggrega `wallet_transactions.out` per `ref_type` classificando in film/tv_series/anime/tutti. Ogni tab mostra importo+count live.
    3. **CashflowChart riscritto**: filtra out i giorni con 0 attività (causa della "banda verde"), bar group income+expense affiancati con gradient + grid lines orizzontali. Header "N giorni attivi" + Max value. Ora leggibile anche con 1-2 giorni di dati.
  - **🐛 Foto 4 — Dashboard Incassi/Spettatori $0**: `stats.total_revenue` e `stats.total_spectators` leggevano solo i campi denormalizzati (`films.total_revenue`, `films.theater_stats`) che sono vuoti sui film legacy. **Fix**: ora aggregano dalla source of truth reale:
    1. `total_box_office = max(sum(films.total_revenue), wallet_transactions.in di box_office/la_prima/tv_broadcast)` (usa il più alto).
    2. `total_spectators = sum(films.cumulative_attendance + films.la_prima_spectators)` con fallback al legacy `theater_stats` o stima `revenue/11`.
    3. Proiezione `films.cumulative_attendance`, `la_prima_spectators`, `theater_stats` aggiunta in `films_light_fields`.
  - Files: `routes/finance_bank.py` (merge Totale, fallback costo, fill giorni, expenses-by-type endpoint), `routes/economy.py` (dashboard aggregazione box office + spettatori da wallet+attendance), `pages/FinancePage.jsx` (OverviewTab refactor con 4 tab Uscite + CashflowChart rewrite).

- **Feb 2026 — Hotfix Dashboard Incassi $0 + crash "selectedFilmDetail"**
  - **🐛 CRASH**: `FinancePage.jsx` aveva un edit perso (probabilmente dovuto al git restore precedente di scheduler_tasks.py): state `filmsHistory`/`selectedFilmDetail` non erano dichiarati, ma il JSX li referenziava → runtime error `Can't find variable: selectedFilmDetail` all'apertura di `/finanze` (schermata "La pellicola si è inceppata"). **Fix**: reintegrato `useState` per `filmsHistory` e `selectedFilmDetail`, rimosso lo state legacy `txs`.
  - **🐛 BUG INCASSI $0**: `auto_revenue_tick` (film `in_theaters`) incrementava `users.funds` e loggava `wallet_transactions` ma NON aggiornava `films.total_revenue`. La Dashboard Home aggregava `sum(films.total_revenue)` → sempre $0 anche con ricavi reali registrati sul wallet. **Fix**: aggiunto `$inc: {'total_revenue': tick_rev}` su `films` dentro il tick (solo per `_source='films'` per non toccare tv_series/anime). Convive correttamente con `update_all_films_revenue` che usa `max(current, realistic_box_office)` preservando il valore più alto.
  - Zero regressioni: tutti i meccanismi esistenti (realistic_box_office, cumulative_attendance, wallet_transactions) restano intatti.
  - Files: `pages/FinancePage.jsx`, `scheduler_tasks.py`.

- **Feb 2026 — Spettatori per-film + Badge trend affluenza**
  - **Sistema affluenza esistente analizzato (zero breaking)**: `update_film_attendance()` in `scheduler_tasks.py` già traccia `cumulative_attendance`, `current_attendance`, `attendance_history` (last 144 tick ≈ 24h) con decay basato su qualità, IMDB, new-film-boost e random ±20%. Revenue e attendance sono sistemi paralleli indipendenti. La Prima già incrementa `premiere.spectators_total` su ogni tick.
  - **Nuovi campi backend (additivi, zero regressioni)**:
    - `films.attendance_trend`: 'up'|'down'|'flat' calcolato confrontando ultimo vs precedente entry di `attendance_history` (±3% soglia).
    - `films.daily_attendance[]`: rollup persistente per-giorno (ultimi 90gg) incrementato ad ogni tick, supera il limite 24h di `attendance_history`.
    - `films.la_prima_spectators`: copiato da `premiere.spectators_total` al `confirm-release` (solo nuovi film, come richiesto).
  - **Nuovo endpoint** `GET /api/spectators/films-history`: ritorna per ogni film `total_spectators`, `today_spectators`, `attendance_trend`, `daily_spectators[{day, date, total}]` aggregati da `attendance_history` + `daily_attendance` merged, sezione La Prima con `la_prima_spectators/city/nation`.
  - **Nuova pagina `/spettatori`** (`pages/SpectatorsPage.jsx`): clone pattern FinancePage. Header con summary strip (Totale / Ultime 24h). Grid 5-col locandine mini con badge LP oro + trend icon mini (TrendingUp verde / TrendingDown rosso / Minus grigio). Tap → modal full-screen mobile con: 3 box Totale/Ora/Trend, sparkline SVG variabile (length = days_in_theaters, NON fissa a 14 come errato prima), sezione La Prima isolata, timeline per-giorno con barre proporzionali.
  - **Card Dashboard "Spettatori Totali" cliccabile**: naviga a `/spettatori`, `data-testid="stat-spettatori"`, hover border cyan.
  - **Componente riusabile `AttendanceTrendBadge`** (`components/AttendanceTrendBadge.jsx`): renderizza SOLO per `status==='in_theaters'` (non La Prima, non A Breve, non Prossimamente). Verde/rosso/grigio con glow subtle. Integrato in Dashboard "Ultimi Film al Cinema" accanto al testo "AL CINEMA" (come da foto utente).
  - **Backend economy.py**: aggiunta proiezione `attendance_trend` nel `recent_releases_task` per far viaggiare il campo alle card locandine in Dashboard.
  - **Rotta `/spettatori`** registrata in `App.js` con lazy loading.
  - **Calcolo trend**: confronto tick-vs-tick (ultima voce vs precedente in `attendance_history`) — soglia ±3% per evitare flickering su variazioni insignificanti.
  - **Zero breaking changes**: il tick revenue non è toccato, il tick attendance aggiunge solo 2 campi ($set additivo), la logica formule resta identica. Nessuna modifica ai calcoli esistenti.
  - Files: `routes/finance_bank.py` (new endpoint), `scheduler_tasks.py` (attendance_trend + daily_attendance), `routes/pipeline_v3.py` (la_prima_spectators al confirm-release), `routes/economy.py` (proiezione trend), `components/AttendanceTrendBadge.jsx` (nuovo), `pages/SpectatorsPage.jsx` (nuovo), `pages/Dashboard.jsx` (card cliccabile + badge integrato), `App.js` (route).

- **Feb 2026 — Storico per-film + Geo distribution-aware + Chart giornaliero leggibile**
  - **A. Storico ridisegnato** (`pages/FinancePage.jsx` + nuovo endpoint `/api/finance/films-history`): eliminata la lista spam di transazioni ogni 10 min per film. Ora tab "Storico" mostra **griglia 5 colonne di locandine mini** (badge "LP" oro se il film ha avuto La Prima, profit +/- in emerald/rose sotto). Tap su locandina → **modal detail full-screen mobile-first** con: 3 box fissi (Costo/Totale/Profit in grid-3), sezione "LA PRIMA" (se presente) con city + nation + $ delle 24h premiere, timeline **incassi giornalieri aggregati per giorno effettivo** dal `theater_start` (ogni riga = Giorno N con barra proporzionale al max). Il tick economico resta invariato ogni 10 min lato backend — l'aggregazione avviene solo in lettura.
  - **Backend `/finance/films-history`** (`routes/finance_bank.py`): aggrega `wallet_transactions` per `ref_id=film_id, direction=in` raggruppando per giorno (`$addFields day: $substr(created_at,0,10)`), separa le entrate `source=la_prima` dal box office. Ritorna `daily_revenues: [{day, date, total}]` con indice giorno 1-based calcolato rispetto al `theater_start`. Fallback `total_cost` da `wallet_transactions direction=out ref_id=source_project_id` se `film.total_cost` è 0 (film legacy).
  - **Confirm-release** (`routes/pipeline_v3.py`): al rilascio aggrega da `wallet_transactions` tutte le uscite (ref_id=project_id OR pid) e salva **`film_doc.total_cost`** come costo reale produzione (screenplay+cast+shooting+marketing+distribuzione+trailer+…). Salva anche `la_prima_revenue`, `la_prima_city`, `la_prima_nation` se `release_type=='premiere'`.
  - **B. Fix Geo coerente con distribuzione V3** (`scheduler_tasks.py`): nuova funzione `pick_revenue_geo(film)` scegliere ad ogni tick una city/nation/continent random coerente con le scelte di pipeline:
    1. `distribution_cities` non vuoto → random tra quelle città (con nation di riferimento);
    2. altrimenti `distribution_nations` → random tra quelle nazioni + city tra quelle note della nazione;
    3. altrimenti `distribution_continents` → random tra quei continenti + city dal pool `_CONTINENT_CITIES`;
    4. altrimenti `distribution_mondiale=True` → random pesata tra `_WORLD_TOP_MARKETS` (21 città top con share reale: NY 14%, LA 14%, London 8%, Tokyo 7%, Parigi 7%, Shanghai 6%, ecc.).
    Film_doc ora include `distribution_nations` e `distribution_cities` (prima mancavano). Tick proietta tutti i campi di distribuzione.
  - **Label "Sconosciuto" → "Totale"** (`finance_bank.py /finance/breakdown`): normalizza None/empty/"Global"/"Sconosciuto" → "Totale". Uniformazione italiana del label globale.
  - **C. Cashflow chart leggibile** (`FinancePage.jsx::CashflowChart`): aggiunte etichette asse X (3 tick: prima/mediana/ultima data formato `dd/m`), header con **Max $value** ed etichetta numero giorni, legenda colori in basso. Altezza aumentata da 60→80px, grid con line zero dashed, fallback "Nessun dato di flusso" + barre minime 0.8px per visibilità anche con valori microscopici.
  - **Badge LP**: locandine con `has_la_prima=true` mostrano pillola "LP" oro in alto-sinistra per indicare a colpo d'occhio i film con premiere (distinguibili da distribuzione diretta).
  - Files: `routes/finance_bank.py`, `scheduler_tasks.py` (pick_revenue_geo + proiezioni), `routes/pipeline_v3.py` (confirm-release total_cost + la_prima_*), `pages/FinancePage.jsx` (HistoryTab + FilmPosterMini + FilmDetailModal + CashflowChart redesign).

- **Feb 2026 — Hotfix "La Mia TV" + Infrastrutture bloccate cliccabili**
  - **FilmActionsSheet — "La Mia TV" rotellina infinita (root cause)**: il `useEffect` di caricamento stations dipendeva da `stations.length === 0`, e dopo un fetch che restituiva 0 stations l'effetto si riattivava (stationsLoading=false, stations.length=0 → chiama di nuovo loadStations → loop flickering). **Fix**: introdotto flag `stationsLoaded` (state separato) che si setta a `true` dopo il primo fetch (anche se 0 risultati) e resetta al re-open del sheet. Condizione ora: `if (tvSection && !stationsLoaded && !stationsLoading) loadStations()`.
  - **Empty state "Emittente TV mancante"**: redesign con icona circolare amber, titolo forte "Emittente TV mancante", testo contestuale al film ("Per trasmettere '{title}' devi prima costruire un'emittente"), e **CTA bottone gradient amber "Vai a Infrastrutture"** (lucide Building2 icon) che naviga a `/infrastructure` e chiude il sheet. Footer hint: "Acquisti l'emittente → torni qui → trasmetti il film (gratis)".
  - **InfrastructurePage — card bloccate cliccabili con popup informativo**: le card delle infrastrutture bloccate (level/fame insufficienti) prima facevano `if (canBuy)` e ignoravano il click. Ora aprono `<Dialog>` dedicato (`lockedInfoInfra` state) che mostra: icona + nome, descrizione, lista "A cosa serve" (derivata dai campi `screens`, `seats_per_screen`, `revenue_multiplier`, `can_show_3d`, `has_food_court`, `production_bonus`, `quality_bonus`, `daily_maintenance`), **box "Requisiti per sbloccarla"** con confronto Lv.X/F.X utente vs richiesti (verde se soddisfatto, rosso altrimenti), costo acquisto. Opacity card bloccate 50→60 con `hover:opacity-85 active:scale-[0.98]` per feedback touch.
  - Files: `components/FilmActionsSheet.jsx`, `pages/InfrastructurePage.jsx`.

- **Feb 2026 — Hotfix Dashboard A-BREVE + Slider Durata Prestito**
  - **"A BREVE" — filtro anti-doppione corretto** (`Dashboard.jsx`): ripristinato il blocco `aBreveCinema.map()` (erroneamente rimosso in hotfix precedente). Ora il filtro corretto è: la card "A breve" (dimmed/orange border) viene nascosta SOLO se quello stesso `film_id` appare anche in `recentReleases` con `status === 'in_theaters'` (= il film è effettivamente uscito → la card normale "AL CINEMA" è già visibile, evita doppione). Quando il film è ancora in La Prima (non in `in_theaters`), la card "A breve" resta visibile cliccabile come gli altri.
  - **Slider Durata Prestito — scrollabile + lock per livello** (`BankPage.jsx` + `routes/finance_bank.py`): grid 4 colonne sostituita con riga orizzontale `snap-x snap-mandatory` di 6 opzioni (3/7/14/30/60/90g). Opzioni 60g/90g mostrano badge Lv.3/Lv.5 richiesto + lucchetto + toast informativo se cliccate da player con livello insufficiente. Backend: `LOAN_DURATION_MIN_LEVEL` ({3:0,7:0,14:0,30:0,60:3,90:5}) + `LOAN_DURATION_MULT` (esteso con 60:2.7, 90:3.8). Check `infra_lvl < min_lvl` in `take_loan` con 400 se non rispettato. Test curl: "Durata 60g richiede Banca Lv.3+ (hai Lv.0)" ✓.
  - Files: `pages/Dashboard.jsx`, `pages/BankPage.jsx`, `routes/finance_bank.py`.

- **Feb 2026 — Hotfix UI: Slider mobile + "A BREVE" fuori Ultimi Film al Cinema**
  - **Dashboard — "Ultimi Film al Cinema"**: rimosso completamente il blocco `aBreveCinema.map()` dal rendering. Ora la sezione mostra SOLO film con status `in_theaters` / `premiere_live` / effettivamente al cinema (via `/pipeline-v3/recent-releases`). I film "A BREVE MONDO" (post-La Prima, pre-distribuzione) non appaiono più qui — hanno la loro sezione dedicata "Prossimamente Film". La Prima continua ad apparire correttamente perché già inclusa in `recent-releases` (condizione `film.status === 'premiere_live'` → badge "LA PRIMA" oro).
  - **BankPage — Slider importo prestito non raggiungibile su mobile**: su iOS il thumb nativo di `<input type="range">` fuoriesce oltre il track quando il valore è al max, rendendolo non-tappabile col dito. Wrappato lo slider in `<div className="px-3">` (24px padding laterale totale), aggiunto `block` + `maxWidth:100%` e etichette min/max sotto. Ora lo slider è contenuto nel viewport con margine sicuro per il thumb, mantenendo step 10k e range dinamico da `can_borrow`.
  - Files: `pages/Dashboard.jsx`, `pages/BankPage.jsx`.

- **Feb 2026 — Economia Realistica + Level-Up Cinematografico**
  - **Budget-tier revenue multiplier** (`scheduler_tasks.py::auto_revenue_tick`): i film ad alto budget generano più incassi (wider distribution = più schermi). Scala: micro=0.5x, low=0.8x, mid=1.0x, big=1.4x, blockbuster=1.8x, mega=2.5x. Applicato sia alla formula box-office regolare (daily_rev) sia alla formula La Prima (tick_rev via spectators × ticket). Helper `_budget_multiplier()` + dict `_BUDGET_REV_MULTIPLIER`.
  - **Banca — Livelli illimitati + scala esponenziale** (`routes/finance_bank.py`): rimosso dict statico `BANK_INFRA_LEVELS` (max Lv10), sostituito da `get_bank_tier(level)` dinamico senza cap. Max loan: 100k @ Lv1, raddoppia ogni livello (Lv1:100k, Lv2:200k, Lv3:400k, …, Lv10:51.2M, Lv15:1.6B). Min loan: 10k fisso. Interesse: 18% base, -1.2pt/livello, floor 3%. **Upgrade cost**: fase 1 (Lv1-4) "easy" con moltiplicatore 3x (50k/150k/450k/1.35M), fase 2 (Lv5+) esponenziale *1.63/livello → Lv10 ≈ 25.3M + 98 CP (vicinissimo al target utente 25M+100CP). CinePass richiesto solo da Lv5 in poi.
  - **BankPage UI**: mostra costo CinePass extra accanto al costo upgrade quando presente (`+ X CP` in sky-blue).
  - **LevelUpToast cinematografico** (`components/LevelUpToast.jsx`, nuovo): toast mobile-first (94vw max 420px) centrato sotto topbar, gradient amber/gold con shimmer animato (framer-motion), trophy icon con glow, confetti gold a 3 raffiche + audio cue WebAudio (C5→C6 triangle), progress bar di dismiss 4.4s. Ascolta evento custom `cw:level-up {newLevel, oldLevel}`.
  - **Level-up detection nell'AuthProvider** (`contexts/index.jsx`): `prevLevelRef` traccia il `user.level` corrente; al prossimo refresh `/auth/me` (post milestone XP server-side), se `curr > prev` dispatcha `window.dispatchEvent(new CustomEvent('cw:level-up'))`. Skip del primo load per evitare falsi positivi.
  - **Integrazione App.js**: import + `<LevelUpToast />` montato globalmente accanto ad `AutoTickNotifications`.
  - **Test**: `/api/bank/status` ritorna nuova struttura (min_loan 10k, upgrade_cinepass 0 per Lv<5). Verifica scala con script python: Lv10 = 51.2M loan / 25.3M upgrade / 98 CP / 6% interest ✓.
  - Files: `scheduler_tasks.py`, `routes/finance_bank.py`, `components/LevelUpToast.jsx` (nuovo), `contexts/index.jsx`, `App.js`, `pages/BankPage.jsx`.

- **Feb 2026 — Refinement Session**
  - **Doppione UserStripBanner rimosso**: BankPage + FinancePage non importano più `UserStripBanner` (era duplicato, il globale basta).
  - **Banca — Click su card infra**: click sulla card "La Tua Infrastruttura" passa automaticamente alla tab Upgrade (con hint "Clicca qui per acquistare Infrastruttura Banca"). Se lv≥1, la tab Upgrade mostra il next tier per potenziare.
  - **Banca — Slider importo**: step ridotto da 50K a 10K, min 10K. Slider ora realmente movibile. Disabled quando `can_borrow < 10K`.
  - **Coming-to-cinemas safeguard**: oltre al filtro `pipeline_state`, aggiunto check cross-collection: se lo stesso `id` esiste in `db.films` con status `in_theaters/released/la_prima/in_cinema`, il film viene escluso da "A Breve". Questo elimina ogni doppione residuo anche su dati production inconsistenti.
  - **Revenue tick — Geo coerente**: ogni film (box_office e la_prima) logga `wallet_transactions` individuali con `{continent, nation, city}` reali, estratti da `release_event`, `distribution_continents` o fallback `Globale`. Rimosso log aggregato "Global" a valle. Così il breakdown Geo è coerente coi incassi totali e con i singoli film.
  - **Finance Breakdown drill-down**: endpoint `/finance/breakdown` ora accetta `parent` + `parent_scope` per filtrare (es. nations in Europa). Ritorna sempre i 6 continenti noti (Europa/N.America/S.America/Asia/Africa/Oceania/Globale) anche con 0.
  - **Finance UI accordion**: nuovo `AccordionGeoRow` espande al click mostrando figli (continente→nazioni, nazione→città) on-demand via API. Caricamento progressivo, icona chevron rotante.
  - Files: `BankPage.jsx`, `FinancePage.jsx`, `la_prima.py` (cross-collection safeguard), `scheduler_tasks.py` (per-film geo log), `finance_bank.py` (breakdown parent filter).

- **Feb 2026 — 5 Quick Fixes**
  - **Fix 1 — Il Sospetto doppione**: `coming-to-cinemas` escludeva solo `released/discarded`. Esteso `pipeline_state` exclusion a `['released', 'discarded', 'la_prima', 'in_theaters']` per premiere & direct films. Ora i film in LA PRIMA LIVE non appaiono più anche in "A Breve".
  - **Fix 2 — Trailer CinePass**: TrailerGeneratorCard mostrava "cc" e leggeva `user.cinecrediti` (che è 0). Ora legge `user?.cinepass ?? user?.cinecrediti ?? user?.cinecredits` e mostra "CP". Backend `/trailers/*` decrementa `cinepass` (oltre agli alias cinecrediti per compat).
  - **Fix 3 — Cast Attori illimitati**: rimosso cap `max: 5` → `max: 999`. Label "5/5" → conteggio puro. Auto-cast in `pipeline_v3 /auto-cast` ora randomizza attori tra **5-8** (`random.randint(5, 8)`). Il player può aggiungere/rimuovere liberamente dopo l'auto.
  - **Fix 4 — XP/Fame sistema funzionante**: creato `utils/xp_fame.py` con `award_milestone(db, user_id, milestone, ...)` + `LEVEL_THRESHOLDS` (40 livelli), `MILESTONE_REWARDS` mappati (project_create, cast_done, ciak_done, la_prima_live, film_released, poster_generated, trailer_generated, tv_launch, ecc). Hook in `pipeline_v3.advance` e `confirm-release` con bonus qualità (+30xp/+3fame se quality≥80, +15xp/+1fame se ≥60) + bonus revenue (log10). Salvato `milestone_awards` collection per UX.
  - **Fix 5 — Serie TV/Anime AI Poster + Screenplay**: aggiunti endpoint `/pipeline-series-v3/projects/{pid}/generate-poster` (Gemini Nano Banana, style anime se `type=anime`) e `/generate-screenplay` (GPT-4o-mini con logline/personaggi/archi/cliffhanger). Frontend IdeaPhase serie: 2 bottoni grid (purple "Locandina AI", emerald "Sceneggiatura AI") + preview compact sotto (mini poster + details screenplay collapsible). Awards automatici (poster_generated, screenplay_done).
  - Files: `la_prima.py`, `trailers.py`, `TrailerGeneratorCard.jsx`, `IdeaPhase.jsx` + `PipelineSeriesV3.jsx` + `FilmDetailV3.jsx` (cinepass alias), `pipeline_v3.py` (auto-cast 5-8 + xp hooks), `CastPhase.jsx` (max 999), `utils/xp_fame.py` (nuovo), `pipeline_series_v3.py` (poster + screenplay endpoints).

- **Feb 2026 — Finance + Bank System + Real-Time Revenue**
  - **Root cause revenue mancanti**: `auto_revenue_tick` processava solo `db.films`, ignorando V3 `film_projects` in stato `la_prima`. Esteso tick per includere le LA PRIMA entro 24h dalla premiere con formula `spectators_per_tick × ticket × quality × city_mult`. Revenue scritto su `film_projects.total_revenue` + log geotagged.
  - **Wallet Transaction System**:
    - Nuova collection `wallet_transactions` + helper `utils/wallet.py::log_wallet_tx(user_id, amount, direction, source, ref_id, geo, ...)`.
    - Hook in `pipeline_v3._spend` (production costs) e nel revenue tick (box_office, la_prima, tv_broadcast).
    - Geo tagging per la_prima: `{continent, nation, city}` dal premiere → drill-down nella UI.
  - **WalletBadge topbar**: sostituisce il Funds badge statico. Mostra ▲/▼ delta animato 3s quando il saldo cambia + floating toast sonner con titolo, città e `±$X`. Polling automatico ogni 60s via `refreshUser`. Click → `/finanze`.
  - **Pagina `/finanze`** (FinancePage): Saldo card dorata + tabs Conto/Geo/Storico/Banca. Statement P&L, breakdown entrate per source, cashflow SVG bar chart 30g, profit netto.
  - **Pagina `/banca`** (BankPage): 3 tab Prestiti/Cambio/Upgrade.
    - **Prestiti**: slider importo, 4 durate (3/7/14/30g), preview interessi dinamica, rate giornaliere auto-dedotte dal job `bank_loan_repayments` (ogni 4h). Late fee: -2 fama, push next_due +12h.
    - **Cambio $ ↔ CinePass**: buy 15K/CP, sell 10K/CP (spread realistico).
    - **Upgrade Infrastruttura Bancaria**: 10 livelli (Ufficio → Empire Bank). Senza infra: prestito minimo $100K @ 18%. Lv10: fino a $1B @ 3%. Senza infra = solo prestiti base.
  - **Navbar bottom**: rimossa icona **Home** (doppione topbar), aggiunta **Banca** (Landmark icon). Topbar Home mantenuta.
  - **Titoli di Coda**: aggiunte icone **Finanza** e **Banca** nella griglia Navigazione.
  - **Dashboard**: click su "Incassi" → `/finanze` (prima andava a `/statistics`).
  - **Tested via curl**: take-loan ($100K/7g, interesse $10.8K), wallet_transactions log OK, recent-deltas OK, finance/overview + breakdown OK, revenue tick esegue pulito.
  - Files: `utils/wallet.py`, `routes/finance_bank.py` (nuovo), `scheduler_tasks.py` (auto_revenue_tick esteso + wallet log), `pipeline_v3.py` (_spend hook), `server.py` (router + scheduler job), `WalletBadge.jsx`, `FinancePage.jsx`, `BankPage.jsx`, `App.js` (routes + navbar + navItems), `Dashboard.jsx`.

- **Feb 2026 — UI Coherence Overhaul**
  - **Root cause "★ 0.0 · ⏱ —" (dati rotti)**: `formatDuration()` leggeva solo `duration_minutes`, mentre i film V3 salvano `film_duration_minutes`. **Fix**: `formatDuration` ora legge entrambi + fallback budget_tier; `confirm-release` V3 salva anche `duration_minutes` + `duration_category`. Imdb display nasconde lo star quando quality è 0/null.
  - **La Prima countdown**: chip animato con Clock dentro `PStarBanner` che mostra hh:mm rimanenti. Pulse dorato + glow.
  - **La Prima + Prossimamente in "I Miei"**: `/api/films/my` unifica `db.films` con `db.film_projects` (stati non-released) e mappa pipeline_state → status.
  - **PosterCard glow**: oro per LA PRIMA, azure per PROSSIMAMENTE, verde CINEMA, indigo IN TV. Label Bebas in fondo.
  - **FilmActionsSheet ovunque**: MyFilms dispatcha `open-film-actions` per i film (non più popup legacy). Include "Invia alla mia TV" + nuovo **Trailer banner** (play arancione se generato, lock grigio se freezato).
  - Files: `server.py` (/films/my), `pipeline_v3.py` (duration_minutes alias), `ContentTemplate.jsx` (formatDuration + imdb guard), `PStarBanner.jsx` (LaPrimaCountdown), `MyFilms.jsx` (PosterCard glow + dispatch), `FilmActionsSheet.jsx` (TrailerBanner).

- **Feb 2026 — Soft-lock Fix + Admin Rescue + Legacy Data Fix**
  - **Bug fix Emilians Anime stuck**: root cause = `/api/series/{id}` cercava SOLO in `db.tv_series`, ignorando V3 (`series_projects_v3`) e V2 (`film_projects` con `content_type='anime'/'serie_tv'`). Quando un anime V3 veniva cliccato, 404 → ContentTemplate loop infinito "Caricamento...".
  - **Backend patch**: esteso `/api/series/{series_id}` con fallback a `series_projects_v3` e `film_projects`, normalizzando i campi (title, type, pipeline_state, num_episodes, ecc.).
  - **Frontend patch** (`ContentTemplate.jsx`): nuovo state `notFound` + UI dedicata con messaggio "Contenuto non disponibile" + pulsanti "Torna indietro" / "Riprova" — mai più infinite loader.
  - **Admin rescue stuck content** (nuova sezione in `AdminFilmRecovery`):
    - `GET /api/admin/recovery/stuck-content`: scansiona tutte le collection (`tv_series`, `series_projects_v3`, `film_projects`, `films`) per anime/serie/film in stati iniziali (idea/proposed/concept/draft/screenplay) senza `poster_url`.
    - `POST /api/admin/recovery/rescue-stuck-content`: applica placeholder poster (`/posters/ai/placeholder_recovery.png`) + flag `poster_is_placeholder=true`, sbloccando il player.
  - **Admin "Fix dati legacy film"** (nuova sezione):
    - `GET /api/admin/recovery/legacy-film-preview`: report dry-run con conteggio campi da fixare (duration_minutes / quality_score / hype) + preview di max 50 film con i valori inferiti.
    - `POST /api/admin/recovery/legacy-film-fix`: applica i fix. Inferenza da: categoria durata → minuti, budget tier → minuti, weeks_in_theater → minuti; imdb_rating/pre_imdb_score/audience_satisfaction → quality; virtual_likes+likes_count (log10) + trend_score → hype.
  - Test via curl: `stuck-content` ritorna 1 film legacy, `legacy-film-preview` ritorna 0 (DB già pulito in questa istanza), `rescue-stuck-content` batch rescues OK.
  - Files: `/app/backend/routes/admin_recovery.py`, `/app/backend/routes/series_pipeline.py`, `/app/frontend/src/components/ContentTemplate.jsx`, `/app/frontend/src/components/AdminFilmRecovery.jsx`.

- **Feb 2026 — Film Actions Sheet + La Mia TV + Al Cinema Dashboard (this session)**
  - **Nuovo componente `FilmActionsSheet.jsx`**: bottom-sheet unificato cinematico (dark + accenti oro/rosso sala) che si apre ovunque (tranne I Miei) cliccando un poster proprio. Sezioni: Dettaglio, ADV, Rigenera Locandina, Ritira dal Cinema, Vendi, Elimina, **La Mia TV** (CTA oro primaria).
  - **Hook globale**: mount in `App.js` + listener `open-film-actions` con payload `{ film }`. Guardia: se `film.user_id !== user.id` → naviga al dettaglio. Dashboard `recent-releases` e `a-breve-cinema` usano il nuovo hook.
  - **La Mia TV panel**: picker stazioni proprie, 2 modalità:
    - **Subito**: ritira dal cinema + messa in onda immediata. GRATIS. Se il film era in calo (trend declining), hype bonus +6..+14 su share TV.
    - **Prossimamente**: film resta in sala, programmato in TV tra 6/12/24/48/96h.
  - **Backend `POST /api/tv-stations/transfer-from-cinema`** con logica B3 (bonus se calo) + C1 (gratis se TV posseduta). Salva `tv_transfer_from_cinema` o `tv_scheduled_transfer` sul film.
  - **Backend `GET /api/my-owned-tv-stations`** (path univoco per evitare collisione con `/tv-stations/{station_id}`): lista minima stazioni possedute + capacity info.
  - **Backend `GET /api/films/my/al-cinema`**: dashboard tracking film in sala. Ritorna per ciascun film: `daily_revenues_sparkline` (7gg), `cinema_sparkline`, `trend` (growing/declining/stable), `trend_delta_pct`, `residual_value` stimato, `ai_advice` ({level: gold/amber/green/gray, title, body}), `recommended_for_tv` flag, `is_personal_record` badge. Summary totale (today_revenue, residual, count).
  - **Nuovo componente `AlCinemaTab.jsx`**: mobile-first tab con summary 3-col (oggi / residuo / count), filtro "Consigliati per TV", lista film con sparkline SVG gradient oro, ribbon RECORD, consigli AI dorati pulsanti, CTA "AZIONI FILM" che apre il FilmActionsSheet.
  - **Nuovo tab "Al Cinema"** in MyFilms (`/films?tab=al_cinema`), icona Clapperboard. Tabs ora scrollabili orizzontalmente.
  - File: `/app/frontend/src/components/FilmActionsSheet.jsx`, `/app/frontend/src/components/AlCinemaTab.jsx`, `/app/backend/routes/tv_stations.py` (endpoint transfer + my-owned), `/app/backend/server.py` (endpoint al-cinema), `/app/frontend/src/App.js` (mount sheet), `/app/frontend/src/pages/Dashboard.jsx` (hook click), `/app/frontend/src/pages/MyFilms.jsx` (tab).

- **Apr 2026 — Pixazo + WaveSpeed AI Integration (Multi-provider extension)**
  - **Pixazo (FREE)**: Integrato Flux 1 Schnell tramite `gateway.pixazo.ai/flux-1-schnell/v1/getData` (header `Ocp-Apim-Subscription-Key`, sync, cost $0). Key in `PIXAZO_API_KEY`.
  - **WaveSpeed AI ($0.003/img)**: Integrato `wavespeed-ai/flux-schnell` tramite `api.wavespeed.ai/api/v3/...` (Bearer auth, `enable_sync_mode: true`). Key in `WAVESPEED_API_KEY`. Budget verificato via `/balance`.
  - Nuovi pesi default auto_rr: CF 30, HF-FLUX 25, Pixazo 20, HF-Together 10, WaveSpeed 10, Pollinations 5. Ordine smart fallback: CF → HF-FLUX → Pixazo → HF-Together → WaveSpeed → Pollinations.
  - Daily limits: Pixazo 500/day, WaveSpeed 300/day (~$0.90).
  - Admin UI `/admin` → AI Providers: nuovi pulsanti toggle Pixazo/WaveSpeed, quota tracker, test connettività (7/7 OK, Pixazo 3485ms, WaveSpeed 260ms).
  - Badge provider nel TrailerGeneratorCard: `PIX` (cyan), `WAVE` (indigo).
  - **Raphael AI**: verificato — NO public API, solo accesso web. Non integrato.
  - E2E test Python: Pixazo 834KB raw → 216KB WebP OK, WaveSpeed 239KB OK.


## Changelog
- **Feb 2026 — Trailer V3: Sub-Phase 4 + TStar Events + Dashboard Strip (this session, Option 3)**
  - **Trailer decision point integrato** in pipeline V3 Film come sub-fase 4 IdeaPhase (dopo sceneggiatura OK): bottoni Base/Cinematic/Pro + Salta. Non blocca l'avanzamento alla HYPE (canAdvance dipende solo da screenplay+poster). Stesso pattern per Serie TV e Anime (in `PipelineSeriesV3`).
  - **Progress circle 0-100%** nel TrailerGeneratorCard con countdown `elapsed / estimated_seconds`, X abort button (`trailer-abort-btn`), pulsante "Guarda Preview" (`trailer-watch-btn`), pulsante "Conferma e prosegui" (`trailer-confirm-btn`), pulsante "Salta trailer" (`trailer-skip-btn`).
  - **Guest bypass AI gratis**: generate-trailer skip `_spend` se `user.is_guest` (0 CP, 0 $). Costi mostrati strikethrough + "GRATIS" per guest sui 3 tier cards.
  - **Postuma (highlights) già funzionante** via auto-detect in `TrailerGeneratorCard` (`isReleasedContent`) — 50% costo, CTA oro con trofeo.
  - **Backend TStar 0-100** (`trailer_scoring.py`): formula pesata su tier_bonus 25% + views 25% + hype 20% + engagement 15% + recency 15%. Tier: legendary (85+) → weak (<25).
  - **Leaderboards trailer** (`routes/trailer_events.py`): `/events/trailers/daily|weekly|by-genre|hall-of-fame|my-history|formula|recent` + voto up/down community (`/trailers/{id}/vote`).
  - **Scheduler** (`scheduler_trailer_events.py`): daily 00:05 UTC paga top 10 giornaliera, weekly lun 00:15 UTC paga top 10 settimanale. Notifiche a vincitori. Guest esclusi dal payout.
  - **Premi**: daily #1 $500K+3CP → #10 $50K+1CP; weekly #1 $3M+15CP → #10 $200K+1CP.
  - **Nuova pagina** `/events/trailers` (`TrailerEventsPage.jsx`): tab Giornaliera / Settimanale / Per Genere / Hall of Fame / I Miei, formula explainer, tabella premi, player modal per vedere trailer in classifica.
  - **Nuova strip Dashboard** "ULTIMI TRAILER" (`UltimiTrailerStrip.jsx`) tra Featured e BestHighlights — ultimi 12 trailer generati (30gg) con badge tier, TStar score, time-ago, poster.
  - **SideMenu voce "Eventi Trailer"** in sezione Competizioni (🎬 icon) → `/events/trailers`.
  - **Anti-abuse**: già enforced (rate-limit 3/10min + up-tier only + 1 running job per content).
  - **View tracking >=10s**: endpoint `/trailers/{id}/view?completed=true` incrementa `completed_views`.
  - **Abort endpoint** `/trailers/{id}/abort`: il runner controlla `job.status == 'aborted'` tra storyboard/images e si ferma preservando CPU. Frontend conferma "Annullato, puoi proseguire senza trailer".
  - **Stretch-deferred (non implementati in questa sessione)**: voice-over TTS Pro, teaser 3s Pro, share-to-CineBoard button, anime character-coherence via seed_url in Nano Banana, Sunday community vote UI panel, compilation annuale AI mashup. Backend vote+recency+engagement già pronti, manca solo la UI.

- **Feb 2026 — Guest Tutorial V3 + Free Pipeline + Location Picker**
  - **Guest play is FREE** during tutorial: `_spend()` in `pipeline_v3.py` returns `{guest_free: true}` without charging when `user.is_guest`. `confirm_release` skips funds/cinepass pre-check for guests. All speedup + release actions are visually strikethrough + "GRATIS" badge.
  - **Location Picker restored in IdeaPhase V3**: replaced abstract `LOCATION_TAGS` with real `/api/locations` data — 4 category tabs (Studios / Città / Natura / Storici) + optional "Il Mio Studio" (gratis), search, multi-select up to 5, real `cost_per_day` per location. Guest sees strikethrough + GRATIS per location.
  - **Guest Tutorial rewired for V3 pipeline** (`GuestTutorial.jsx`): 18 steps (0-17) using correct V3 testids: `top-nav-produci`, `produci-film`, `new-project-btn`, `title-input`, `preplot-input`, `location-categories`, `idea-ok-phase0`, `poster-ai-auto`, `idea-ok-poster`, `screenplay-ai-auto`, `idea-ok-screenplay`, `advance-btn`, `speedup-*`, `confirm-release-btn`. Auto-advance polling detects DOM state for each step.
  - **Overlay clash fixed**: GuestTutorial z-index boosted to `9100-9200` so it wins over VelionPanel/TutorialModal/DashboardTour. `LoginRewardPopup` (Bonus Giornaliero) now suppressed during guest tutorial. VelionPanel/TutorialModal/DashboardTour all gated by `!(is_guest && !tutorial_completed)`.
  - **Backend tutorial range**: `TUTORIAL_STEPS = range(0,18)`, `TUTORIAL_COMPLETE_STEP = 17`.
  - Backend bypass test (iter163): 7/7 pass. Frontend smoke test OK: guest login → step 0..5 spotlight flow works, location picker renders with GRATIS badges visible.

- **Feb 2026 — PStar System: classifica La Prima + premi giornalieri/settimanali + bonus AI**
  - **Nuovo valore PStar 0.0-100.0** calcolato dopo ogni La Prima conclusa. Formula in `backend/la_prima_scoring.py`:
    - Qualita CWSv (x2) → 0-20
    - Hype accumulato (/5) → 0-20
    - Affluenza (spectators/target x20) → 0-20
    - Personalita Citta (weight x20 se genre match, x8 parziale, x5 fallback) → 0-20
    - Guadagni log10(x2.2) → 0-20
    - 6 tier: legendary (85+), brilliant (70+), great (55+), good (40+), ok (25+), weak (0+)
  - **Eventi con premi**: nuovo endpoint router `routes/la_prima_events.py`:
    - `GET /events/la-prima/daily` → top 10 della giornata con prize distribution
    - `GET /events/la-prima/weekly` → top 10 ISO week corrente
    - `GET /events/la-prima/my-history` → storico personale + veteran badge check
    - `GET /events/la-prima/film/{id}/pstar` → score persistito o compute on-the-fly
    - `GET /events/la-prima/formula` → explainer per UI
  - **Premi giornalieri** (top 10): 1° $3M+10cp · 2° $2M+7cp · 3° $1.5M+5cp · scalati fino a 10° $100K+1cp
  - **Premi settimanali**: 1° $10M+30cp · 2° $6M+20cp · 3° $4M+15cp · scalati fino a 10° $300K+2cp
  - **Scheduler** (`scheduler_la_prima_events.py`):
    - Ogni 15min: scan premiere concluse, compute PStar entry, auto-recensione critico (5 critici), cinegiornale auto-articolo
    - Ogni 30min: random "live reactions" durante le 24h (standing ovation, applausi, fischi) con hype +/-
    - Daily 00:05 UTC: payout top 10 giornaliera + notifiche
    - Weekly Mon 00:10 UTC: payout top 10 settimanale + **badge Veterano La Prima** auto-unlock a 5+ premiere (+150 fama)
  - **Premi CUMULATIVI**: oltre ai guadagni da distribuzione cinema, non al posto
  - **Frontend**:
    - `pages/LaPrimaEvents.jsx` — pagina dedicata con 2 tab (Giornaliera/Settimanale), explainer formula, history utente, veteran badge display
    - `components/PStarBanner.jsx` — banner oro animato (shine sweep 3.8s) nel popup film sotto "IN SALA...". Mostra città + cinema + spettatori + score se disponibile. Click → dialog "Resoconto La Prima" con `PStarScoreCard` (breakdown 5 ingredienti con barre) + link a pagina eventi
    - Route `/events/la-prima` protetta
    - LaPrimaSection dashboard: tasto "Classifiche & premi" che naviga alla pagina eventi
  - **Fix bug popup duplicato**: Dashboard recentReleases + aBreveCinema ora navigano a `/films/{id}` (ContentTemplate unificato) invece di aprire il vecchio `FilmDetailV3`.
  - **Andamento con icona trend**: sostituito "OTTIMO ANDAMENTO" con chip colorato `▲ +12% Ottimo` (verde up) / `▼ -8% In calo` (rosso down) / `■ 0% Stabile` (grigio flat).
- **Feb 2026 — La Prima + "A Breve Cinema" indipendenti dal pipeline_state**
  - **Bug fix critico (Fase A)**: il film in fase pre/live La Prima spariva dalla sezione "LA PRIMA" della dashboard appena il player avanzava allo step distribution/release_pending. Ora la query `/la-prima/active` filtra per `release_type='premiere'` + `premiere.datetime` window, **indipendentemente dal pipeline_state** (escludendo solo `released` e `discarded`).
  - **Nuovo endpoint (Fase B)**: `GET /api/la-prima/coming-to-cinemas` ritorna i film V3 nella finestra "in attesa uscita cinema":
    - premiere confermata + `now > premiere.datetime + 24h` + `distribution_confirmed=true` + non ancora released
    - oppure `release_type='direct'` + `distribution_confirmed=true` + non ancora released
    - Computa `a_breve_scope` con personality matching:
      - `distribution_mondiale=true` → "MONDO"
      - altrimenti: cross-match genre del film con `preferred_genres` delle city selezionate (usa `PREMIERE_CITIES` weights) e restituisce la citta' con score + weight piu' alto
      - tiebreaker: prima city/nation in ordine di lista; fallback a continente o "MONDO"
  - **Dashboard integration** (`Dashboard.jsx`): nuovo state `aBreveCinema`, fetch al load, pre-pende i film oscurati alla sezione "ULTIMI FILM AL CINEMA" con stile dimmed (opacity 55%, grayscale 30%) + overlay dark gradient + label "A BREVE {scope}" centrato.
  - **Bordi animati pulsanti** per fase (CSS in `content-template.css`):
    - Pre-La Prima waiting → `.animate-pulse-border-cyan` ciano (LaPrimaSection)
    - Post-La Prima "A BREVE" → `.animate-pulse-border-orange` arancione (Dashboard ultimi film)
    - AL CINEMA reale → bordo verde statico emerald-500/50 (recent releases con status in_theaters)
  - Film mai duplicati: le 3 fasi sono mutuamente esclusive per design.
- **Feb 2026 — Pre-La Prima in Sezione dedicata + Best Highlights Leaderboard**
  - **Task A (nuovo requisito utente)**: film in fase pre-La Prima (setup fatto, datetime futuro) ora sono visibili ANCHE nella sezione "La Prima" della dashboard, in aggiunta alla Prossimamente.
    - Backend `/la-prima/active` (in `la_prima.py`): aggiunge query separata per i film V3 in `pipeline_state='la_prima'` con `premiere.datetime > now`. Ogni evento ritorna `is_waiting: bool`, `countdown_to_start: "Xh Ym"` e `premiere_datetime`.
    - Frontend `LaPrimaSection.jsx`: card waiting ha poster oscurato (opacity 55% + grayscale 30%), overlay dark gradient, badge "IN ARRIVO" in ciano al posto del "LIVE" rosso, bottom label "In arrivo a {CITTA}" + countdown "-Xh Ym · al via". Bordo ciano invece che oro. Cliccabile normalmente (naviga a `/films/{id}`).
    - Badge header: "LIVE" (rosso pulsante) se almeno un live event presente, altrimenti "IN ARRIVO" (ciano statico).
  - **Task B — Best Highlights Leaderboard**: nuovo endpoint `GET /api/trailers/leaderboard/highlights?limit=N` che aggrega film/serie con `trailer.mode='highlights'` ordinati per `views_count` desc. Ritorna rank, poster, owner (nickname + studio + avatar), tier, views, generated_at.
  - Nuovo componente `BestHighlightsLeaderboard.jsx`: scroll orizzontale mobile-first, medaglie oro/argento/bronzo sui top 3, chip tier colorato (Base/Cinematico/PRO), play overlay on hover, contatore viste. Nascosto automaticamente se 0 items.
  - Integrato in Dashboard dopo `FeaturedTrailersStrip`, prima delle sezioni Prossimamente.
  - **Task C+D** (Compilation annuale AI + Remaster trailer): spostati in roadmap — richiedono video generation pesante (Sora 2) e saranno implementati come feature dedicate.
- **Feb 2026 — Trailer mode: Pre-Launch vs Highlights**
  - **Backend** (`trailers.py`): endpoint `/trailers/{id}/generate` accetta nuovo query param `mode=pre_launch|highlights`. Mode auto-detect + enforcement:
    - `pre_launch` bloccato se film già uscito (`is_released`)
    - `highlights` bloccato se film NON è uscito
  - **Costo**: mode `highlights` applica sconto 50% sul costo tier (es. Cinematico 10cc → 5cc; PRO 20cc → 10cc; Base rimane gratis).
  - **Hype boost**: solo mode `pre_launch` concede +hype boost durante fase hype/pre-release. Mode `highlights` è cosmetico, non influenza gameplay.
  - **DB**: campo `trailer.mode` persistito (default `pre_launch` per back-compat). Upgrade tier funziona solo all'interno dello stesso mode (il che permette di avere 2 trailer coesistenti: 1 pre-launch + 1 highlights).
  - **Frontend** (`TrailerGeneratorCard.jsx`): auto-switch UI in base a `contentStatus` prop. Pre-Launch = header azzurro + icona TrendingUp + "+hype". Highlights = header oro + icona Trophy + badge "HIGHLIGHTS" sui trailer esistenti + costo con prezzo base barrato (line-through) e prezzo scontato.
  - **Offer cross-mode**: se esiste già un trailer di mode diverso da quello corrente del film, la card mostra una mini-sezione "Crea anche un {altro tipo}" con i 3 tier al costo effettivo.
  - Prop `contentStatus` passato da `FilmDetailV3` e `PipelineSeriesV3`.
- **Feb 2026 — Fix Like "Contenuto non trovato" + Trailer content lookup**
  - **Bug critico Like**: `_find_content` in `likes.py` cercava solo in `films.id` e `tv_series.id`. Falliva per V3 films (film_projects), per `films.film_id` (campo alternativo), per anime_series e per serie con `series_id`. Esteso lookup a tutte le varianti.
  - **Fix identico in `trailers.py`**: stesso problema, stessa soluzione. Ora trailer e like funzionano su TUTTI i contenuti, indipendentemente da stato (pre-release, coming_soon, in_theaters, released, catalogo, serie, anime, V1/V2/V3).
  - **Trailer postumi**: verificato che l'endpoint `/trailers/{id}/generate` NON blocca in base allo stato del film. Il flag `allow_hype_boost` decide solo se concedere +hype (solo per stati pre-release come `hype`, `upcoming`, `prossimamente`, `pre_production`). Post-release la generazione funziona ma senza boost hype (logico: film gia' uscito).
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

## AI Image Providers — Multi-Provider Rotation (Apr 2026)
Default: **strategia C+D** combinata.
- **Locandine** → modalità `auto` (smart fallback): prova sempre il migliore per primo
- **Trailer** → modalità `auto_rr` (weighted round-robin): bilancia il carico tra i 4 provider

### Provider attivi
1. **Cloudflare Workers AI** (SDXL Lightning) — PRIMARIO, gratuito, 10.000 req/giorno, ~3-5s/img
2. **HuggingFace FLUX.1-schnell** (via router hf-inference) — SECONDARIO, gratuito, ~2-6s/img
3. **HuggingFace fal-ai FLUX** (via router fal) — TERZIARIO, stesso token HF, pool separato
4. **Pollinations anonimo** — QUATERNARIO (fallback finale), gratuito ma rate-limited
5. **Emergent LLM** — on-demand premium (richiede budget)

### Pesi default round-robin trailer
- Cloudflare 40% + HF-FLUX 40% + HF-Together 15% + Pollinations 5%

### Test risultati reali (trailer 6 frame)
- Poster: CF · 5.5s · 87KB PNG  
- 6 Frame: 4×CF + 2×HF-FLUX · 3-6s/frame · ~25s totale  
- Fallback cross-provider automatico in caso di errore

### File aggiornati
- `/app/backend/image_providers.py` — adapter CF + HF-FLUX + HF-Together + rotation logic + quota tracker (`get_usage_report()`)
- `/app/backend/routes/admin_ai_providers.py` — nuovi endpoint: `GET /usage`, esteso `POST /test` con tutti i provider
- `/app/backend/routes/trailers.py` — passa `frame_idx` a `generate_image_meta` per round-robin, aggiorna `partial_frames` nel job per preview live
- `/app/frontend/src/pages/AdminPage.jsx` — tab "AI Providers" con modalità Auto/Auto RR + quota tracker live (refresh 10s) + provider badges colorati
- `/app/frontend/src/components/TrailerGeneratorCard.jsx` — **preview live thumbnail grid** 3×2 con provider badges (CF/HF/POLL) + cerchio progress spostato a destra

### Env variables aggiunte
- `CLOUDFLARE_ACCOUNT_ID` · `CLOUDFLARE_API_TOKEN` · `HUGGINGFACE_TOKEN`

### Endpoint nuovi
- `GET /api/admin/ai-providers/usage` — contatore giornaliero per provider

## Promo Video Generator (Apr 2026)
Tool admin auto-generatore di video promozionali Instagram-ready (9:16 1080×1920 MP4).
- `/app/backend/promo_video.py` — engine: Playwright headless Chromium per screenshot, Emergent LLM (GPT-4o-mini) per caption italiani, FFmpeg (libx264 + drawtext + libfreetype) per composizione video con overlay testo
- `/app/backend/routes/promo_video_admin.py` — API: GET screens, POST generate, GET/DELETE jobs, GET download MP4
- Collection MongoDB: `promo_video_jobs` (job state, progress real-time, captions generate, video URL)
- AdminPage → tab "Promo Video" con: durata 30/60/90/120s, tono (energico/neutro/ironico), musica opz, prompt custom (≤400 char), picker 14 pagine, progress bar reale, download MP4, storico ultimi 10 video
- Flow: crea guest demo → seed 2 film fake → Playwright naviga le 14 pagine → screenshot → caption AI paralleli → FFmpeg compone → upload → cleanup demo user
- Job orphan recovery: al restart backend, job `running`/`queued` vengono marcati `failed` con stage=`orphaned`
- Primo test end-to-end: 5 pagine, 30s, 526KB MP4 valido, duration esatta 30s, caption italiani coerenti

Endpoint:
- `GET /api/admin/promo-video/screens` — lista pagine disponibili
- `POST /api/admin/promo-video/generate` — avvia job (body: duration_seconds, screens[], custom_prompt, tone, music)
- `GET /api/admin/promo-video/jobs` — storico
- `GET /api/admin/promo-video/jobs/{id}` — status + progress + log
- `GET /api/admin/promo-video/download/{id}` — MP4 scaricabile
- `DELETE /api/admin/promo-video/jobs/{id}` — elimina job + file

Dipendenze installate: `playwright==1.48.0`, `ffmpeg` (system apt), `fonts-dejavu-core`

## Integrazioni
- Emergent LLM Key (GPT-4o-mini + Gemini Nano Banana image gen)
- Emergent Object Storage
- ICY metadata proxy (Web Radio)
