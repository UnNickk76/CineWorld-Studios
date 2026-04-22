# CineWorld Studio's — PRD

## Problema Originale
Gioco manageriale multigiocatore di produzione cinematografica. Pipeline V3 a più fasi, Cast System V3, AI event/avatar generation, "La Mia TV", Web Radio in-game, banner promo TV, Trailer AI cinematografico con 3 tier.

## Stack
- Frontend: React + Tailwind + Lucide + Framer Motion
- Backend: FastAPI + Motor/MongoDB + APScheduler
- LLM: Emergent LlmChat (GPT-4o-mini + Gemini Nano Banana) via Emergent Key
- Storage: Emergent Object Storage (trailer frames)

## Changelog
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
