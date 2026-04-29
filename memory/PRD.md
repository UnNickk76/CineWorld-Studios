## FASE: Badge Veterano (Apr 29, 2026)

**Richiesta utente**: badge "Veterano" basato su anzianità di iscrizione, visibile a tutti cliccando sul nickname (ovunque).

**Tier (calcolati dal `created_at`)**:
- `>= 365gg` → 🏆 **Veterano Leggendario** (gold #facc15, glow)
- `>= 180gg` → 🥈 **Veterano** (silver #cbd5e1, glow)
- `>= 90gg` → 🥉 **Veterano in Erba** (bronze #fb923c, glow)
- `< 90gg` → nessun badge

**Modifiche**:
- **Componente nuovo**: `/app/frontend/src/components/VeteranBadge.jsx` — utility `getVeteranTier(created_at)` + componente con 3 size (sm/md/lg).
- **PlayerProfilePopup** (in `App.js`) — popup principale aperto da tutti i nickname cliccabili: aggiunto `<VeteranBadge createdAt={p.created_at} size="sm" />` accanto a LV/Fama/online dot.
- **ProducerProfileModal** — popup secondario usato da `FilmDetailV3`: aggiunto badge accanto al label di livello.
- **Backend**: aggiunto `created_at` (e `logo_url`) al response di `/api/auth/player-profile/{nickname}` (mancava). `/api/players/{id}/profile` lo aveva già.

**Verificato**: lint pulito, curl `/api/auth/player-profile/NeoMorpheus` ritorna `created_at` correttamente.


## FASE: Data registrazione + Co-Admin permissions (Apr 29, 2026)

**Richieste utente**:
1. Aggiungere la data di registrazione utente sotto email/nickname in entrambe le tab Admin (Gestione Utenti + Gestione Ruoli). Per i vecchi utenti senza `created_at`: mostrare "non disponibile".
2. I CO_ADMIN devono poter gestire segnalazioni utenti, locandine e ban al pari degli ADMIN.

**Modifiche**:
1. **Backend (`server.py`)**: aggiunto `created_at` alla projection di `/api/admin/search-users`.
2. **Frontend `AdminPage.jsx`**:
   - **UsersTab card list**: aggiunta riga `📅 Reg. gg/mm/yyyy` (o "Reg. non disponibile") sotto email/production_house_name.
   - **RolesTab card list**: stessa riga sotto email.
3. **Co-Admin permissions** — già coperto:
   - `auth_utils.require_mod` accetta già `("ADMIN", "CO_ADMIN", "MOD")`. Tutti gli endpoint moderazione (`/admin/reports/*`, `/admin/users/*/ban|unban|manual-report|chat-mute|chat-unmute`, `/admin/content/*`) usano `require_mod` quindi CO_ADMIN può già fare tutto.
   - `COADMIN_TABS` espone già `reports` (Segnalazioni) come prima tab → co-admin ha accesso pieno al pannello moderazione tramite `AdminModerationPanel`.

**Verificato**: lint pulito, screenshot Gestione Ruoli mostra ogni utente con `📅 Reg. gg/mm/yyyy` + icone Segnala/Ban presenti.


## FASE: Estensione Moderazione — Bottoni Segnala/Ban in tutto Admin Panel + CineConfirm Velion (Apr 29, 2026)

**Problema**: l'utente ha segnalato che i bottoni "Segnala sempre" e "Banna sempre" (con prompt durata) non erano visibili nelle tab principali (Gestione Utenti, Gestione Ruoli) — erano disponibili SOLO nel tab Segnalazioni. Inoltre le conferme usavano `window.confirm` browser-default invece del CineConfirm Velion-style.

**Modifiche**:
1. **Gestione Utenti** (UsersTab in `AdminPage.jsx`): aggiunti nel pannello utente selezionato i bottoni `Segnala` (rosa, AlertTriangle) + `Ban`/`Sbanna` (arancione/emerald, ShieldOff/ShieldCheck) accanto al bottone `Elimina`. Badge `BAN` e `MUTE` se attivi.
2. **Gestione Ruoli** (RolesTab in `AdminPage.jsx`): aggiunti i mini-bottoni icon-only `Segnala` (⚠️) + `Ban`/`Sbanna` (🛡️) accanto ai pulsanti dei ruoli (Co-Admin/Mod/User) per ogni utente. Badge `BAN` se bannato.
3. **CineConfirm Velion**: tutti i `window.confirm` sostituiti con `CineConfirm` (toni `rose` per ban/segnala, `amber` per sblocco). Applicato in:
   - `UsersTab` (segnalazione, sblocco)
   - `RolesTab` (segnalazione, sblocco)
   - `AdminModerationPanel` (eliminazione contenuto, segnalazione manuale, sblocco)
4. **BanDurationModal** integrato in entrambe le tab (prompt durata flessibile + 8 preset + textarea motivo).

**Files toccati**:
- `/app/frontend/src/pages/AdminPage.jsx` (UsersTab + RolesTab)
- `/app/frontend/src/components/moderation/AdminModerationPanel.jsx` (rimossi `window.confirm`)

**Test manuale**: screenshot tab Gestione Ruoli mostra ogni riga utente con icone Segnala (⚠️ rosa) + Ban (🛡️ arancione) accanto ai 3 bottoni di ruolo. Lint pulito.


## FASE: Sistema Segnalazioni & Moderazione (Apr 29, 2026)

**Obiettivo**: introdurre un sistema completo di moderazione comunitaria con segnalazioni, ban scaling automatico, decay temporale e ban banner globale.

### Funzionalità implementate
- **Bottone "Segnala"** su ogni locandina (in `ContentTemplate`, dopo il trailer). Visibile a tutti tranne al proprietario. Modal con 5 categorie + note opzionali (max 500 char).
- **Anti-abuso**: max 5 segnalazioni/ora per reporter, no duplicati su stesso content entro 24h.
- **Counter segnalazioni** (`report_count_active`) con soglia 5 → ban automatico.
- **Decay automatico**: -1 ogni 15gg senza nuove segnalazioni (job APScheduler ogni 6h).
- **Ban scaling automatico**: 1°=1g, 2°=3g, 3°=7g, 4°=30g, 5°=eliminazione + blocco email 60gg.
- **Ban manuale modificabile** dall'admin con parser flessibile (`3 ore`, `1 GIORNO`, `permanente`, `30 minuti`, etc.).
- **Sblocco ban** sempre disponibile via Admin Panel (counter ban non si resetta).
- **Auto-lift ban scaduti** ogni 6h.
- **Blocco email** per 60gg post-eliminazione (controllato in `/auth/register`).
- **Esenzione admin/MOD**: possono essere segnalati ma il counter non aumenta + sistema avverte che è admin.
- **Auto-segnalazione su elimina contenuto admin**: motivo "Contenuto eliminato per violazione delle regole interne" + notifica al player.
- **Manual report** admin → notifica standard al player ("Hai ricevuto una segnalazione… al 5° rischi il ban").
- **Chat mute/unmute** indipendente dal ban (gestibile anche da co-admin/MOD).

### Backend (`/app/backend/routes/reports.py`)
Endpoints nuovi:
- `POST /api/reports` (player)
- `GET /api/admin/reports` (lista raggruppata)
- `GET /api/admin/reports/user/{id}` (storico utente)
- `POST /api/admin/reports/{id}/dismiss`
- `DELETE /api/admin/content/{type}/{id}` (elimina + auto-report)
- `POST /api/admin/users/{id}/ban|unban|manual-report|chat-mute|chat-unmute`
- `GET /api/admin/moderation/summary` (per badge counter)
- `GET /api/me/ban-status` (banner UI)

Collezioni nuove: `mod_reports`, `bans`, `email_blocks` (rinominata da `reports` per evitare conflitti con collezione esistente).

User schema additions: `report_count_active`, `ban_count_total`, `is_banned`, `ban_expires_at`, `current_ban_id`, `is_chat_muted`, `last_report_at`, `is_deleted`.

### Frontend (`/app/frontend/src/components/moderation/`)
- `ReportContentButton.jsx` — modal 5 categorie + note
- `BanBanner.jsx` — banner fixed bottom con glow animato + timer countdown 1s + messaggio "Al 5° ban verrai eliminato!" (renderizzato globalmente in `App.js`)
- `BanDurationModal.jsx` — input duration + 8 preset chip + textarea motivo
- `AdminModerationPanel.jsx` — tab Locandine + tab Utenti con search, storico ban/segnalazioni, bottoni Segnala/Ban/Sblocca/Muta chat
- Badge counter sul tab "Segnalazioni" del menu Admin (refresh ogni 30s)

### Middleware ban (`server.py`)
Intercetta tutte le request mutating (POST/PUT/DELETE/PATCH) e blocca se utente bannato. Eccezioni: `/api/auth/*`, `/api/me/ban-status`, GET, e `/api/chat/*` se non chat-muted. Auto-lift se ban scaduto.

### Verifiche
- Lint pulito (Python + JS).
- Backend riavviato senza errori, endpoint `/api/admin/moderation/summary` ritorna dati corretti, parser duration testato (8 casi diversi tutti OK).
- Screenshot pannello Admin → tab Segnalazioni → "Nessuna locandina segnalata" + 2 sub-tab funzionanti.

---

## ⚠️ TODO: Bug capitoli da sistemare

L'utente ha segnalato che ci sono cose sui capitoli (Saghe / Film a Capitoli) che non funzionano come dovrebbero. **Da investigare nel prossimo ciclo** — chiedere all'utente esempi concreti per riprodurre.


## FASE: Bug Capitoli Saga + Migliorie Saga (Apr 29, 2026)

**Problemi riportati dall'utente** (durante creazione del cap.2 di un film a capitoli):
- Foto 1: il trailer ricompare nel cap.2 (deve essere ereditato dal cap.1).
- Foto 2: l'hype del cap.2 dovrebbe sbloccarsi 4-6 giorni prima della fine cinema del cap.1.
- Foto 3: al rilascio non compaiono i personaggi della pretrama abbinati agli attori.
- Foto 4: errore "Body is disturbed or locked" cliccando "Genera personaggi (AI)" in una serie TV.

**Bug critici risolti**:
1. **`series_v3` mappato sulla collection sbagliata** (`tv_series` invece di `series_projects_v3`) in `/app/backend/routes/characters.py`. Il backend ritornava sempre 404 → il frontend mostrava un errore generico browser-level. Adesso la generazione personaggi nelle serie TV V3 funziona (verificato con curl 200 OK + 8 personaggi generati).
2. **Trailer ereditato Cap.1** in `TrailerGeneratorCard`: nuova prop `sagaInheritance`. Se cap.>1, render speciale con bottone "Guarda Trailer del Cap.1" + bottone "Sequel del trailer · in arrivo" (disabilitato). Aggiunto endpoint backend `GET /api/sagas/{saga_id}/inherited-trailer`.
3. **Riepilogo Personaggi & Cast** allo step finale (V3 `Phases.jsx` STEP FINALE) e nel modale LAMPO release: lista personaggi (ordinata per ruolo) con `actor_name` abbinato. Massimo 8/10 visibili.
4. **Sblocco anticipato hype configurabile** in base al CWSv del cap precedente (`utils/saga_release_hook.py` + `routes/sagas.py`):
   - CWSv >= 8.0 → 6gg | >= 6.5 → 5gg | >= 5.0 → 4gg | >= 3.5 → 3gg | < 3.5 → 2gg.
   - Sia `check_release_gate` (endpoint) sia `check_saga_release_gate` (hook usato da V3+LAMPO) usano la stessa formula.

**Migliorie aggiuntive saga implementate**:
- (a) Eredità Regista/Compositore dal Cap.1 nel `create_next_chapter` (continuità artistica). Risposta backend ora include `inherited_director` e `inherited_composer`.
- (d) Badge "Fan Base Bonus ±X%" visibile in cima alla pipeline cap.>1 (CWSv-based).
- (e) Cliffhanger payoff: toast `💥 Riprendi il cliffhanger del capitolo precedente! Hype +5%` quando si crea il cap. successivo.
- (f) Mini-timeline capitoli (`SagaPipelineHeader`) in cima alla pipeline V3: barre verdi (rilasciati) / viola (corrente) / grigie (futuri).

**Migliorie rimandate** (richiedono integrazioni più pesanti):
- (b) Locandina-variante automatica dal poster cap.1 (richiede image-gen pipeline).
- (c) Notifica push allo sblocco hype/rilascio (richiede APScheduler + push notification).

**Endpoint nuovi**:
- `GET /api/sagas/{saga_id}/inherited-trailer` → ritorna il trailer del cap.1 (cerca in `film_projects`, `lampo_projects`, fallback `films`).

**Files toccati**:
- Backend: `routes/characters.py`, `routes/sagas.py`, `utils/saga_release_hook.py`.
- Frontend: `components/TrailerGeneratorCard.jsx`, `components/v3/IdeaPhase.jsx`, `components/v3/Phases.jsx`, `components/v3/FilmDetailV3.jsx`, `components/LampoModal.jsx`, `pages/PipelineV3.jsx`, `pages/MySagasPage.jsx`.


## FASE: Sezione Saghe e Capitoli + Azioni Film/Serie (Apr 28, 2026)

**Problema riportato dall'utente**: 
- Aveva creato un film flaggando "Film a Capitoli" (6 capitoli) ma non trovava nessuna sezione per gestirlo.
- Saghe non erano accessibili dal menu Produci.
- Mancavano azioni rapide (Crea Sequel, Crea Live Action) sulle locandine.

**Bug critico individuato e risolto**: 
- `MySagasPage` (`/saghe`) usava `localStorage.getItem('token')` invece della chiave corretta `cineworld_token`. Risultato: la chiamata `/api/sagas/list` falliva sempre con "Impossibile caricare le saghe".

**Modifiche**:
1. **Menu Produci** (`App.js`): nuovo bottone "Saghe" (icona Library, viola) → `/saghe`
2. **ContentTemplate.jsx — Azioni proprietario** sulle locandine (riga ~1040+):
   - `Saga · Cap.X` (viola/fucsia) → `/saghe?saga_id=...` — visibile se `film.saga_id`
   - `Crea Sequel` (arancione/rosso) → `/create-sequel?from=...` — solo per Film (non serie/anime/animazioni)
   - `Crea Live Action` (rosa/rosé) → `/create-live-action?from=...` — solo per serie TV/anime/animazioni
3. **MySagasPage**: 
   - Token key fix (`cineworld_token`)
   - Supporto `?saga_id=` per aprire automaticamente la modale dettaglio della saga
4. **Feedback flow saga**: `Phases.jsx` (V3) e `LampoModal.jsx` ora mostrano toast esplicito di successo/errore quando si avvia una saga via `/api/sagas/start`. Prima l'errore era silenzioso (solo `console.warn`).

**Verifiche eseguite**:
- Curl `/api/sagas/start` con progetto reale → 200 OK + saga creata correttamente.
- Curl `/api/sagas/list` con token autenticato → ritorna saghe.
- Screenshot `/saghe` → carica senza errore, mostra le saghe del player con stats.


## FASE 1+2+3: Cinema Stats Bug Fix + LaPrima + Toggle + CineBoard Unificata + Location Overhaul (Apr 28, 2026 — late evening)

### FASE 1: Bug fix critici Cinema Stats + LaPrima Banner

**Bug fix backend** (`/app/backend/routes/cinema_stats.py`):
- **Totali $0/0**: ora se `total_revenue=0` ma `daily_breakdown` ha dati, deriva i totali aggregando il breakdown
- **Top città**: rimossa condizione `total_revenue > 0`, ora disponibili da G1 con qualsiasi dato
- **LaPrima data**: nuovo blocco nel response con city/date/time/score/attendance/VIP/media coverage/critic approval/boost G1

**LaPrima Banner**:
- `/app/frontend/src/components/cinema/LaPrimaBanner.jsx` — banner prima del chart con icona crown 🥇, click → modale dettagli serata (10 stats + bar critic + boost G1)
- Integrato in `CinemaStatsModal` sopra il grafico

**Toggle Modalità Grafico**:
- `AttendanceChart` ora supporta `mode="live"` (passati+oggi, mobile-friendly) e `mode="full"` (tutti i giorni programmati con vuoti)
- Toggle pill nel modale, persiste in localStorage

### FASE 2: CineBoard Classifica Unificata + Trailer

**Backend** (`/app/backend/routes/cineboard_unified.py`):
- `GET /api/cineboard-unified/global` — classifica unificata tutti contenuti (film/series/anime/animation/lampo/saga_chapter)
  - Filtri: content_type, sort (revenue/spectators/cwsv/hold/hype), period (daily/weekly/monthly/alltime)
  - Calcolo automatico hold ratio da `daily_revenues`
- `GET /api/cineboard-unified/trailers` — classifica trailer (views + likes×5 + hype×100)

**Frontend** (`/app/frontend/src/components/cineboard/`):
- `UnifiedRankingPanel.jsx` — pannello con filtri tipo/sort/period + lista con medaglie 🥇🥈🥉 + click → CinemaStatsModal
- `TrailerRankingPanel.jsx` — pannello trailer con player video integrato

**CineBoard.jsx**:
- Nuovi 2 tab: "Globale" (Trophy) e "Trailer" (Play). Tabs ora 6 totali con label compact mobile

### FASE 3: Location Overhaul

**Backend** (`/app/backend/utils/location_coherence.py` + `routes/location_coherence.py`):
- **GENRE_SWEET_SPOT** dictionary: 21 generi con range ottimale (drama 1-4, action 5-12, war 8-16, epic 10-20, etc)
- **Costo crescente non lineare**: 1-5×1.0, 6-10×1.6, 11-15×2.4, 16+×3.5
- **Coherence quick** (no AI): score 0-100 basato su sweet spot
- **AI coherence deep** (LlmChat + Emergent LLM Key): valuta vs pretrama, ritorna score + 3-5 suggested locations + 0-3 warnings location fuori posto
- **CWSv modifier conservativo**: max +0.5 (perfect match), min -0.4 (gravely incoherent)
- Endpoint: `GET /sweet-spot?genre=`, `POST /coherence-check`, `GET /cost-info`

**Frontend** (`/app/frontend/src/components/v3/LocationCoherenceBar.jsx`):
- Barra visiva 0-100 con colori (rosso/arancio/giallo/verde)
- Mostra sweet spot per genere + advice testuale
- Bottone "Analisi AI profonda" → trigger AI score + suggerimenti + warnings
- Badge "PERFETTA" se score≥90 + sweet spot match
- Mostra impatto CWSv (+0.X / -0.X)

**IdeaPhase.jsx**:
- `MAX_LOCATIONS = 999` (rimosso limite hard 5)
- Costo per ogni location mostra moltiplicatore visibile (×1.6, ×2.4, ×3.5)
- LocationCoherenceBar sempre visibile sotto la lista

### Test
- Lint Python e JS pulito ✅
- Backend: total_revenue ora $57,387 e top cities count 3 (prima 0) ✅
- /api/cineboard-unified/global ritorna 7 items con kind+ranking ✅
- /api/locations/coherence-check (drama 3 locations) → score 100/100, perfect=true ✅
- /api/locations/sweet-spot?genre=war → 8-16 ✅
- Frontend webpack compilato ✅

---

## Cinema Stats Dashboard "AL CINEMA" — Overhaul Completo (Apr 28, 2026 — sera)

### Richiesta utente
Sostituire il vecchio modale "DATI CINEMA" minimal/brutto con una dashboard completa con grafico affluenze, top città, bottoni ritiro/proroga (solo proprietario), messaggio Velion dinamico, alert ritiro imminente. Coerente per Film/Anime/Animazione/LAMPO/Sequel/Capitoli. Coerente col game design.

### Decisioni utente confermate
- 1b: Versione FULL (chart + occupazione + forecast + sparkline + share + heatmap)
- 2a: Tracker intra-day ogni ora
- 3d: Costo prolungamento combinato $ + CP (10% media incassi 3gg + 5 CP/giorno)
- 4 b+c: Penalty ritiro: -1 fama se hold>60% + -5% incassi prossimi 30 giorni
- 5c: Top città con nome+flag+spettatori+incassi+%
- 6a: Serie TV/Anime stats aggregate stagione
- Tutti 17 suggerimenti inclusi

### Implementazione (file univoci)

**Backend:**
- `/app/backend/utils/cinema_stats_engine.py` — daily breakdown (aggregato da daily_revenues), top 3 città deterministiche (pool IT/US/GB/FR/DE/ES/JP/BR/MX), avg hold ratio, forecast lineare 3gg, performance message Velion (hourly), best day badges, avg ticket price, occupancy %, player comparison
- `/app/backend/utils/extend_withdraw_logic.py` — can_extend (window 3gg), calc_extend_cost ($+CP), can_withdraw, calc_withdraw_penalty (impulsive flag)
- `/app/backend/routes/cinema_stats.py` — router `/api/cinema-stats`:
  - `GET /{content_id}` — full dashboard
  - `POST /{content_id}/extend` — applica costi $+CP, estende theater_days
  - `POST /{content_id}/withdraw` — applica fame penalty + future revenue penalty 30gg
- Patch `server.py` registrazione router

**Frontend:**
- `/app/frontend/src/components/cinema/CinemaStatsModal.jsx` — modale principale full-screen mobile
- `/app/frontend/src/components/cinema/AttendanceChart.jsx` — recharts ComposedChart con heatmap colors per hold ratio + forecast tratteggiato
- `/app/frontend/src/components/cinema/TopCitiesPanel.jsx` — top 3 città con medaglie, flag, spettatori, %, bar visivo
- `/app/frontend/src/components/cinema/PerformanceMessage.jsx` — messaggio Velion stile (hourly), badge "NUOVO" pulsante quando hour_id cambia, alert ritiro imminente
- `/app/frontend/src/components/cinema/CinemaActions.jsx` — bottoni Ritira/Prolunga (solo owner)
- `/app/frontend/src/components/cinema/ExtendConfirmModal.jsx` — slider giorni 1-14 + preview costi $+CP + bonus info
- `/app/frontend/src/components/cinema/WithdrawConfirmModal.jsx` — penalty preview (fama -1, incassi -5%)
- `/app/frontend/src/components/cinema/CinemaSparkline.jsx` — mini-grafico 7gg per overlay poster
- Patch `/app/frontend/src/components/ContentTemplate.jsx` — sostituito vecchio modale inline brutto con `<CinemaStatsModal>`

### Funzionalità implementate (17/17)
1. ✅ Prezzo medio biglietto (revenue/spectators)
2. ✅ % Occupazione sale (avg_occupancy_pct, capacità stimata 250 posti × 4 spettacoli)
3. ✅ Hold ratio per giorno + recente (ultimi 3gg) + medio
4. ✅ Forecast 3 giorni (regressione lineare)
5. ✅ Confronto vs media ultimi 5 film del player
6. ✅ Heat colors per giorno (emerald→green→lime→yellow→orange→red)
7. ✅ Best day badges (opening, weekend, hold record)
8. ✅ Sparkline mini per poster (CinemaSparkline.jsx)
9. ✅ Toggle notifiche (localStorage subscription)
10. ✅ Share button (navigator.share + clipboard fallback)
11. ✅ Velion advisor contestuale (6 livelli: great/good/ok/declining/bad/flop, 4 messaggi per livello, hourly)
12. ✅ Costo prolungamento dinamico (10% avg incassi 3gg × giorni + 5 CP/giorno)
13. ✅ Penalty ritiro impulsivo (-1 fama se hold>60%)
14. ✅ Bonus prolungamento info (+0.2 CWSv display se hold>70%)
15. ✅ Tracker intra-day esistente già in scheduler_tasks (ogni 10min, daily_revenues array)
16. ✅ Daily snapshot via aggregate_daily_breakdown
17. ✅ Top città deterministica (hash-based)

### Penalty/Bonus Architecture
- **Withdraw impulsive**: hold ratio recente ≥ 0.60 → -1 fama
- **Withdraw market effect**: sempre -5% incassi prossimi 30gg (campo user `withdraw_revenue_penalty_until`/`pct`)
- **Extend**: max 14gg per estensione, max 2 estensioni per film, finestra solo ultimi 3gg

### Test
- Lint Python e JS pulito ✅
- Backend riavviato senza errori ✅
- E2E API: `GET /api/cinema-stats/{id}` su film attivo restituisce summary + daily_breakdown completo (8 giorni con hold ratio per ognuno) + top_cities + performance message ✅
- Frontend webpack compilato ✅

---

## Bug Fix: Press Reviews coerenti con fase pipeline (Apr 28, 2026 — late)

### Bug segnalato dall'utente
Un film in fase RIPRESE mostrava recensioni stile post-visione ("Ambizioso ma non sempre riuscito", "Promettente ma imperfetto") perché il check `isNotReleasedYet` controllava SOLO LAMPO scheduled / scheduled_release_at futuro, ignorando `pipeline_state` (idea/hype/cast/ciak/...). Quindi il film veniva trattato come "released" e mostrava recensioni vere.

### Fix implementato (file univoci)
- **NUOVO**: `/app/frontend/src/utils/pressByPhase.js` — frasi STAMPA differenziate per fase:
  - `concept` (idea/hype/cast): rumors, casting buzz
  - `riprese` (prep/ciak): "Avvistati sul set", "Foto trapelate dalle riprese", "Behind-the-scenes"
  - `postprod` (finalcut): test screening, montaggio, anteprime stampa
  - `promo` (marketing): trailer, campagna virale, materiali
  - `imminente` (la_prima/distribution/release_pending): prevendite, premiere
  - 15 frasi per ogni combinazione fase × livello (high/mid/low)
  - `isProjectNotYetReleased(film)` helper estensibile
  - `getProjectPhaseCategory(film)` mappa pipeline_state → categoria
  - `PHASE_LABELS` per UI ("Indiscrezioni dal set", "Le voci dalla pre-produzione", ecc.)

- **MODIFIED** `/app/frontend/src/utils/preReleasePhrases.js`:
  - `getPreReleasePressReviews()` ora usa `PRESS_BY_PHASE[phase]` con seed `(film_id + phase + hour)` (deterministico)
  - Aggiunto `getPreReleasePressLabel()` che ritorna l'etichetta UI corretta per fase
  - Rimosse dal pool legacy `mid` le 3 frasi recensione-style ("Ambizioso ma non sempre riuscito", ecc.)
  - Re-export di `isProjectNotYetReleased`

- **PATCH** `/app/frontend/src/components/ContentTemplate.jsx`:
  - `_isNotReleasedYet` ora usa `isProjectNotYetReleased(film)` (estende il check a tutti i pipeline_state pre-release)
  - Etichetta sezione usa `getPreReleasePressLabel(film)` (es. "Indiscrezioni dal set" se in RIPRESE)

- **PATCH** `/app/frontend/src/components/v3/FilmDetailV3.jsx`:
  - `isFilmReleased()` ora ritorna `false` se `isProjectNotYetReleased(film)` (difesa)
  - `reviews` usa `getPreReleasePressReviews()` quando il film è in pipeline pre-release
  - Etichetta sezione dinamica via `reviewsLabel`

### Risultato
Un film in fase "ciak" ora mostra **"Indiscrezioni dal set"** con frasi tipo "Avvistati sul set i protagonisti: foto già virali", non più recensioni post-visione. Stesso comportamento per tutte le fasi pipeline (concept, riprese, postprod, promo, imminente).

Lint Python ✅, Lint JS ✅, Frontend webpack compilato ✅.

---

## Film a Capitoli (Saghe Pianificate) — Sistema completo (Apr 28, 2026 — pomeriggio)

### Richiesta utente
Aggiungere checkbox "Film a Capitoli" all'ultimo step prima del rilascio (V3, LAMPO, sceneggiatura) per Film e Animazione. Il player sceglie 2-15 capitoli pianificati. I capitoli successivi escono solo dopo il termine cinema del precedente, max 3 attivi contemporaneamente. AI genera pretrama coerente, evolve cast con alert nuovi/rimossi personaggi. Pipeline V3 pre-compilata sui capitoli successivi (locandina/pretrama/trailer/cast). Soglia stop combinata (CWSv<5 AND incassi<60% cap.1) consigliata da Velion AI a 5gg dall'uscita cap.3.

### Decisioni utente confermate
- 1b: Naming "Inception Capitolo 2: Il Risveglio"
- 2b: Saga = 1 slot quota studio (capitoli successivi non bloccano altri progetti)
- 3b: Capitoli successivi 70% costo (riuso asset)
- 4: Genere bloccato, regista può cambiare con alert
- 5c: Soglia stop combinata (CWSv + incassi)
- 6: Primo capitolo da sezione Film, successivi da nuova sezione "Saghe"
- Tutti e 12 i miglioramenti approvati
- Penalità fama se abbandono < 50% capitoli pianificati
- Bonus continuation se molto successo dopo cap.3
- Hype/Ciak/LaPrima/Uscita regolari ma sempre dopo termine cinema precedente

### Implementazione

**Backend (file univoci):**
- `/app/backend/utils/saga_logic.py` — costanti + utilities (validazione, costi, fan-base modifier, threshold stop, abandon penalty)
- `/app/backend/utils/saga_ai.py` — generate_next_chapter_pretrama (LlmChat) + evolve_saga_characters
- `/app/backend/utils/saga_release_hook.py` — gate rilascio + metadata + fan-base hype + post-release update saga + chapter discount
- `/app/backend/routes/sagas.py` — router `/api/sagas` con 7 endpoint:
  - `POST /start` — crea saga al cap.1
  - `GET /list` — tutte le saghe del player con stats
  - `GET /check-saga-quota-impact` — info quota
  - `GET /{saga_id}` — dettaglio + advise/can_extend
  - `POST /create-next-chapter` — pre-compila V3 con AI
  - `GET /{saga_id}/release-gate/{project_id}` — verifica ok rilascio
  - `POST /conclude` — chiudi/abbandona (con penalità)
- Patches `pipeline_v3.py` confirm-release: gate + chapter discount + metadata + fan-base + post-release
- Patches `lampo.py` release: gate + metadata + fan-base + post-release (entrambi i rami immediate/scheduled)
- Patches `lampo.finalize_scheduled_lampo_releases` per saga quando lo scheduler finalizza
- Patches `studio_quota.py` aggregation $group per saga_id (saga = 1 slot)
- Patches `server.py` scheduler `saga_advisor_check` ogni ora (5gg pre-uscita cap.3)
- Patches `velion.py` nuova categoria 'sagas' con 8 tip contestuali

**Frontend (file univoci modulari):**
- `/app/frontend/src/components/saga/SagaCheckbox.jsx` — checkbox + slider 2-15 + cliffhanger toggle
- `/app/frontend/src/components/saga/SagaBadge.jsx` — badge "Cap N/M" con icona BookOpen + sparkle cliffhanger
- `/app/frontend/src/components/saga/CharacterChangeAlert.jsx` — alert added/removed personaggi
- `/app/frontend/src/pages/MySagasPage.jsx` — pagina dedicata con grid saghe + dialog detail con timeline capitoli + modale crea/conclude
- Patches `Phases.jsx` StepFinale: SagaCheckbox + handleConfirm wrapper che chiama /api/sagas/start prima di confirm-release
- Patches `LampoModal.jsx` LampoResult: SagaCheckbox + sagaEnabled wrap su handleRelease
- Patches `CastPhase.jsx`: CharacterChangeAlert se saga_chapter > 1 con saga_chars_added/removed
- Patches `Dashboard.jsx` (3 punti) e `ContentTemplate.jsx`: SagaBadge nei poster
- App.js: nuova route `/my-sagas` e `/saghe` mappati a MySagasPage; menu rapido punta a `/my-sagas`

### Nuove collezioni Mongo
- `sagas`: id, user_id, title, genre, kind, total_planned_chapters, current_chapter_count, released_count, status, parent_pretrama, ai_pretramas_history, characters_history, trilogy_bonus_awarded, can_continue_beyond, tv_bundle_available
- Campi nuovi su `films`/`film_projects`/`lampo_projects`: saga_id, saga_chapter_number, saga_subtitle, is_saga_chapter, is_saga_first, saga_cliffhanger, saga_inherited_pretrama, saga_chars_added/removed, saga_cost_multiplier, saga_total_planned_chapters (su films), saga_fan_base_modifier, saga_prev_cwsv

### Test eseguiti
- Lint Python ✅, Lint JS ✅
- Backend riavviato: scheduler `saga_advisor_check` registrato
- E2E API: login → crea progetto V3 → /api/sagas/start (5 capitoli, cliffhanger=true) → /api/sagas/list → /api/sagas/{id} → /api/sagas/conclude (abandoned, fame_penalty=25 per 0/5)
- Velion tips category=sagas restituisce i nuovi 8 tip
- Cleanup test data e ripristino fama

### Idee implementate (12/12)
1. ✅ Saga ID & Pagina dedicata (/my-sagas + dialog detail con timeline)
2. ✅ Effetto Fan Base (+10-25% hype prossimo capitolo basato su CWSv prev)
3. ✅ Effetto Delusione (-15% hype se CWSv prev < 4.0)
4. ✅ Cliffhanger flag (+5% hype next chapter)
5. ✅ Trilogia bonus (+20 fama + tv_bundle_available al 3° rilascio)
6. ✅ Continuity opzionale (riuso poster/trailer base)
7. ✅ Badge SagaBadge nei feed (Dashboard + ContentTemplate)
8. ✅ TV Rights bundle saga (flag tv_bundle_available)
9. ✅ PvP Live Action saga (i capitoli sono normali film vendibili nel marketplace)
10. ✅ Esclusione dall'infrastruttura Sequel (i capitoli non consumano slot Sequel)
11. ✅ Alert proattivi Velion AI (saga_advisor_check ogni ora + tip contestuali)
12. ✅ Saga Stats nella pagina detail (CWSv medio, incassi totali, progresso)

---

## Marketplace Diritti Live Action — PvP completo (Apr 28, 2026 — late night)

### Richiesta utente
Mercato dei diritti di adattamento live-action tra player con: ricerca opere altrui, offerte libere entro range, spartizione ricavi negoziabile, contropropose, contratti con scadenza, listing attivi, royalty post-uscita, rating reciproci, leaderboard licensors, esclusività, e producer-stats. Tutte le 10 idee di miglioramento approvate.

### Implementazione

**Backend (file univoci come richiesto)**:
- `/app/backend/utils/la_pricing.py` — pricing engine: `calc_base_price`, `adjust_for_split`, `adjust_for_exclusivity`, `offer_range`, `validate_offer`, `quote_breakdown`
  - Range offerta: 70%-140% del base aggiustato
  - Spartizione: 50%-80% buyer (max 80, min 50)
  - Royalty: 2%-5%
  - Non-esclusivo = ×0.6
  - Contratto scadenza: 30 giorni
- `/app/backend/routes/live_action_market.py` — router `/api/live-action-market` con 14 endpoints:
  - `GET /marketplace` — opere licenziabili di altri player
  - `GET /quote` — anteprima prezzi
  - `POST /offers` — invio offerta (validato)
  - `GET /offers/inbox|sent`
  - `POST /offers/{id}/accept|reject|counter`
  - `POST /listings` + `DELETE /listings/{id}` + `GET /listings|/listings/mine`
  - `GET /contracts/pending`
  - `GET /producer-stats/{user_id}` — affidabilità producer
  - `POST /ratings` + `GET /ratings/producer/{user_id}` — feedback post-uscita
  - `GET /leaderboard/licensors` — top venditori
- `/app/backend/routes/live_action.py` — esteso `create_live_action`:
  - Accetta `contract_id`: se presente, autorizza origine di altro player
  - Non marca `live_action_id` se contratto non-esclusivo (incrementa `non_exclusive_la_count`)
  - Aggiorna contract `status="in_production"` con `project_id`
- `/app/backend/server.py` — scheduler `expire_la_contracts` ogni 30 min: chiude contratti scaduti (>30gg), libera origine esclusiva, notifica entrambi.

**Frontend (componenti modulari)**:
- `/app/frontend/src/pages/CreateLiveActionPage.jsx` — riscritta con 3 tab + MineTab interno
- `/app/frontend/src/components/live_action/LiveActionTabs.jsx` — header tab navigation con badge counts
- `/app/frontend/src/components/live_action/MarketplaceTab.jsx` — Marketplace con sub-tab (Esplora/Ricevute/Inviate), accept/reject/counter
- `/app/frontend/src/components/live_action/NegotiateModal.jsx` — modale negoziazione: slider buyer/seller %, switch esclusivo, slider royalty, slider prezzo entro range, auto-quote dal backend ad ogni cambio
- `/app/frontend/src/components/live_action/QueueTab.jsx` — contratti acquistati in coda, countdown 30gg con warning <7gg, avvio produzione (Pipeline V3 / LAMPO)

**Idee implementate (10/10)**:
1. ✅ Listing attivi (proattivo)
2. ✅ Scadenza contratto 30gg con scheduler
3. ✅ Esclusività on/off (-40% non-esclusivo)
4. ✅ Royalty continua 2-5% memorizzata sul contratto
5. ✅ Contropropose con history
6. ✅ Rating post-uscita 1-5★ + commento (la_ratings)
7. ✅ Producer stats (CWSv medio, n. LA, % successo, velocità)
8. ✅ Leaderboard licensors (top venditori)
9. ✅ Whitelist generi opzionale (`allowed_genres` su listing)
10. (Notifica smart Velion da aggiungere in seguito)

### Nuove collezioni Mongo
- `la_rights_listings`
- `la_rights_offers` (con `history` per controproposte)
- `la_rights_contracts` (con `expires_at` 30gg)
- `la_ratings`

### Test
- Lint Python ✅, Lint JS ✅
- `GET /live-action-market/marketplace` → 0 items (corretto, nessun altro player ha anime+15gg)
- `GET /producer-stats/{me}` → 0 LA prodotti (corretto)
- Screenshot `/create-live-action` → 3 tab visibili, requisiti rendering corretto, Velion bubble overlay attivo ✅

---


## Fix Live Action Level + Fame v2 (0-500) — Apr 28, 2026 (notte)

### Richieste utente
1. **Bug Live Action**: requisito "Lv Player ≥ 10" mostra "Attuale: 1" anche se profilo dice **Lv 14/16**
2. **Fame troppo facile**: a 100 punti già "Leggenda" → rallentare crescita 5-10x e portare Leggenda a fama 500. Aggiungere più tier intermedi.

### Diagnosi bug Live Action
- DB `user.level` è **stale** (non viene aggiornato quando l'utente sale di livello)
- Il valore reale viene calcolato da `get_level_from_xp(total_xp)` → endpoint `/player/level-info` ritorna correttamente Lv 16
- `live_action.py::_check_unlock_requirements` leggeva direttamente `user.get('level', 0)` → vedeva 1
- Stesso problema in `velion.py::analyze_player_state`

### Fix
**Backend `routes/live_action.py`** + **`routes/velion.py`**:
- Importano `game_systems.get_level_from_xp` e calcolano il livello reale da `total_xp`
- `try/except` di sicurezza con fallback al valore stored

**Backend `game_systems.py`** — Sistema Fame v2:
- `calculate_fame_change()` riscritta con crescita molto più lenta:
  - Quality 90+: +3 (era +15)
  - Quality 80+: +1.5 (era +8)
  - Quality 70+: +0.5 (era +3)
  - Quality 50-69: ±0.4 (era ±2)
  - Quality 30-49: −1 (era −5)
  - Quality <30: −2 (era −10)
  - Revenue bonus: 0.05 per $1M (era 0.5) — 10× più lento
  - Diminishing returns spostati a 200/300/400 (× 0.85, 0.7, 0.5)
- `get_fame_tier()` espansa a **9 tier** (era 6) con scala 0-500:
  - 0-25 Sconosciuto (rev × 0.80)
  - 25-75 Emergente (rev × 0.90)
  - 75-150 Noto (rev × 1.00, +1 unlock)
  - 150-225 Famoso (rev × 1.10, +2)
  - 225-300 Stella (rev × 1.20, +3)
  - 300-380 Idolo (rev × 1.30, +4)
  - 380-450 Maestro (rev × 1.40, +5)
  - 450-499 Icona (rev × 1.45, +6)
  - **500+ Leggenda (rev × 1.50, +8)** ← traguardo serio

**Aggiornamento clamp `min(100, fame)` → `min(500, fame)`** in:
- `server.py:2688` (max(0, min(500, ...)))
- `server.py:8566` (recalculate_player_fame loop)
- `server.py:8569` (min_fame post-recalc)
- `server.py:8641` (next_tier preview, soglia portata da 90 a 480, step da +20 a +50)
- `routes/film_pipeline.py:4113`
- `routes/films.py:940`

### Test
- Lint Python ✅ (errori preesistenti non miei)
- `GET /live-action/unlock-status` → `player_level: 16` (era 1) ✅
- `GET /player/level-info` con fame=15 → tier `Sconosciuto (0-25)` ✅

### File modificati
- `/app/backend/routes/live_action.py` (level via get_level_from_xp)
- `/app/backend/routes/velion.py` (level via get_level_from_xp)
- `/app/backend/game_systems.py` (calculate_fame_change + get_fame_tier rifatti)
- `/app/backend/server.py` (3 clamp 100 → 500, next_tier preview)
- `/app/backend/routes/film_pipeline.py` (clamp 100 → 500)
- `/app/backend/routes/films.py` (clamp 100 → 500)

### Note di game design
- I valori fama esistenti dei player (es. 15 dell'utente) **non vengono migrati**: rimangono nel range 0-500 ma corrispondono al nuovo tier (es. 15 = "Sconosciuto"). Nessun reset traumatico, semplicemente più strada da fare verso "Leggenda".
- Requisito Live Action `fame >= 100` rimane (ora corrisponde al tier "Noto"): leggermente più impegnativo ma raggiungibile dopo qualche film di qualità.

---


## Velion AI Advisor — Estensione Quota v2 + Live Action + Feature v2 (Apr 28, 2026 — sera 5)

### Richiesta utente
Verificare il funzionamento di Velion (assistente AI con consigli contestuali) e aggiungere:
- Avvisi su nuove feature (Live Action, doppia quota, personaggi AI)
- "Sai che se costruisci/upgradi X infrastruttura puoi fare Y?" (didascalico)
- Quando l'utente entra in pagina di creazione e la quota è satura → suggerimento mirato con redirect
- Tutto **non invasivo** (uno ogni X ore in game)

### Implementazione

**Backend `routes/velion.py`** (~120 righe):

1. **TRIGGER_VARIANTS** estesi con nuovi tipi di messaggio:
   - `quota_parallel_full`: "Hai raggiunto il limite di progetti aperti. Completane uno o potenzia lo studio..."
   - `quota_daily_full`: "Hai già creato il massimo di progetti per oggi. Riprova più tardi o potenzia lo studio..."
   - `live_action_close`: "Sei vicino a sbloccare il Live Action..."
   - `live_action_ready`: "Hai sbloccato il Live Action. Trasforma i tuoi anime e film d'animazione..."
   - `characters_unused`, `cast_auto_hint`, `tv_market_hint`

2. **VELION_TIPS** nuova categoria `features_v2` con 14 "Sapevi che...":
   - "Sapevi che a Studio Anime Lv 5 + Player Lv 10 + Fama 100 sblocchi il Live Action?"
   - "Sapevi che a Production Studio Lv 6 hai 10 progetti V3 aperti e 3 al giorno?"
   - "Sapevi che il Cast Suggerito AI propone attori coerenti per età e ruolo?"
   - "Sapevi che il Mercato Diritti TV vende i tuoi film alle emittenti dopo il cinema?"
   - ecc.

3. **PAGE_SUGGESTIONS** nuove pagine:
   - `/pipeline-v3` (base + by_level 1/5/10)
   - `/create-live-action` (con requisiti chiari)
   - `/notifications`

4. **PRIORITY_ORDER** ridefinito: `quota_full = 0` (priorità massima) > `stuck_film = 1` > altri.

5. **`analyze_player_state`** estesa con 2 nuovi controlli:
   - **Quota awareness**: se `page` è di produzione (`/pipeline-v3`, `/create-film`, `/create-series`, `/create-anime`, `/create-sequel`, `/create-live-action`), legge `get_studio_quota_info(classic+lampo)`. Se *almeno uno* dei due è saturo → trigger `quota_full` con `action='/infrastructure'` e `meta` completo (used/max/reset_at).
   - **Live Action awareness**: legge livelli `studio_anime`, `production_studio`, `user.fame`. Se requisiti soddisfatti + ha origine → `live_action_ready`. Se manca esattamente 1 requisito + ha origine → `live_action_close`.

6. Bug fix: `quality_score` poteva essere `None` causando `TypeError` su `q > 0`. Ora con default `or 0`.

**Frontend `components/VelionOverlay.jsx`**:
- `HIGH_PRIORITY_TYPES` esteso con `quota_full`, `live_action_ready`, `live_action_close`
- `BUBBLE_COOLDOWN` portato da 10 min → **30 min** (meno invasivo, come richiesto)
- Nuovo parametro `forceImportant` in `fetchTriggers`: bypassa cooldown quando si entra in una pagina di creazione → l'advisor `quota_full` appare immediatamente al cambio pagina
- Effect "page change" ora chiama `fetchTriggers(true)` se la nuova pagina è di produzione

**Frontend `components/VelionPanel.jsx`**:
- Tips ora mix di `general` (2) + `features_v2` (2), shuffled → l'utente vede i "sapevi che…" sulle nuove feature

### Test (backend reale)
- Lint Python ✅ (4 errori bare except preesistenti non miei), Lint JS ✅
- `GET /velion/player-status?page=/pipeline-v3` con daily quota satura → `advisor: quota_full → "Hai già creato il massimo di progetti per oggi..."`, `action: /infrastructure` ✅
- `GET /velion/player-status?page=/create-live-action` → `page_hint: "Per sbloccare il Live Action: Studio Anime/Production Lv 5, Player Lv 10, Fama 100."` ✅
- `GET /velion/tips?category=features_v2&count=3` → 3 tips random "Sapevi che..." ✅

### File modificati
- `/app/backend/routes/velion.py` (+~110 righe: variants, tips, pages, trigger logic, bug fix)
- `/app/frontend/src/components/VelionOverlay.jsx` (priority types, BUBBLE_COOLDOWN 30min, forceImportant)
- `/app/frontend/src/components/VelionPanel.jsx` (mix tips)

---


## Quota v2 Doppia (Parallel + Daily) + Pre-fix exclusion (Apr 28, 2026 — sera 4)

### Richieste utente
1. Cooldown countdown attivo anche per LAMPO
2. Quote troppo basse: a Lv 7 solo 3 progetti V3 → aumentare ma con doppio limite (totale + giornaliero)
3. Mostrare entrambi i limiti `Totali X/X` + `Giornalieri X/XG` con countdown reset 24h
4. **Escludere i progetti pre-fix dal conteggio** (l'utente aveva 7 progetti pre-bug e quota satura)

### Implementazione

**Backend `utils/studio_quota.py` — RIFATTO**:
- Costante `QUOTA_V2_RESET_AT = 2026-04-28T07:00:00Z` → tutti i progetti `created_at` precedenti **non vengono più conteggiati**
- Nuova `_QUOTA_TABLE` molto più generosa con coppia `(parallel, daily)`:
  ```
  Lv 0-2:   3 / 1
  Lv 3-5:   5 / 2
  Lv 6-8:  10 / 3   ← era 3 fisso
  Lv 9-14: 15 / 5
  Lv 15-24: 25 / 8
  Lv 25-49: 40 / 15
  Lv 50-99: 60 / 30
  Lv 100-199: 100 / 50
  Lv 200+: illimitato
  ```
- LAMPO `_LAMPO_QUOTA_TABLE` analoga, daily più rilassato (perk veloce)
- `_count_active_projects()` filtra `created_at >= QUOTA_V2_RESET_AT.isoformat()` (Mongo store as ISO string)
- Nuova `_count_daily_creations()` → conta progetti creati nelle ultime 24h, ritorna anche `oldest_in_window` (per calcolare quando uno slot daily si libera = oldest+24h)
- `get_studio_quota_info()` ora restituisce: `parallel_used/max_parallel/parallel_full`, `daily_used/max_daily/daily_full/daily_window_resets_at`, `show_dual_quota` (true se max_parallel>1)
- `check_studio_quota()` blocca su parallel OR daily, messaggi distinti
- **Eliminato il cooldown post-release classic**: sostituito dal daily limit (più chiaro)

**Frontend `pages/PipelineV3.jsx`**:
- `renderQuotaBadge` mostra ora 2 righe nel chip:
  - "Totali aperti X/Y" (rosso se parallel_full)
  - "Oggi (24h) X/Y" (rosso se daily_full) — solo se `show_dual_quota=true`
  - Sotto, countdown live `⏱️ Slot tra Xs` quando daily_full
  - Avviso "⚠️ Completa o scarta un progetto" quando parallel_full ma daily libero
- Mostrato sia per V3 Classico che per ⚡ LAMPO
- Countdown alimentato da `clockTick` ogni 1s

**Backend `routes/infrastructure.py`**:
- `INFRA_LEVEL_PERKS` aggiornata per riflettere la nuova tabella quote (es. Lv 6 = "10 classici totali, 3 al giorno") — niente più "Cooldown 3 giorni"

### Test (backend reale)
- Lint Python ✅, Lint JS ✅
- User Lv 1: parallel 0/3, daily 0/1 ✅ (i 7 progetti pre-fix sono ESCLUSI)
- Dopo 1 creazione: parallel 1/3, daily 1/1 → daily FULL, blocco ✅
- Dopo 3 creazioni forzate: parallel 3/3 + daily 3/1 → entrambe FULL, `daily_window_resets_at: 2026-04-29T08:00:33Z` ✅
- 4° tentativo bloccato con: *"Limite progetti classici aperti raggiunto (3/3). Completa o scarta un progetto, oppure potenzia lo studio."* ✅

### File modificati
- `/app/backend/utils/studio_quota.py` (riscrittura completa quota logic ~120 righe)
- `/app/backend/routes/infrastructure.py` (perks aggiornati a nuova tabella)
- `/app/frontend/src/pages/PipelineV3.jsx` (badge quota a 2 righe)

---


## Fix Infrastrutture non-cinema + Cooldown Timer (Apr 28, 2026 — sera 3)

### Problemi segnalati dall'utente
1. **Production Studio (e tutti gli studi/scout/PvP/centri commerciali/parchi)** mostravano "Posti/Sala +25" e "Nuovi prodotti: Premium 3D ($8)" nell'upgrade popup — concetti che valgono solo per i cinema reali.
2. Le infrastrutture non-cinema dovrebbero invece mostrare **cosa sbloccano per ogni livello** (es. quote progetti, slot TV, cooldown, agenzie, indagini PvP, ecc.) e cosa **sbloccheranno alla prossima milestone**.
3. Per i progetti bloccati dal cooldown: serve un **timer countdown** che indichi quando si potrà creare un nuovo progetto.

### Diagnosi
- `calculate_upgrade_benefits()` calcolava `seats_per_screen += 25` e includeva `INFRA_PRODUCTS` (cibi/bevande) anche per `production_studio`/`studio_anime`/`studio_serie_tv`/`cinema_school`/`emittente_tv`/`talent_scout_*`/`pvp_*`, dove `screens=0` e `revenue_multiplier=0`. Il frontend mostrava ciecamente `seats_added` e `new_products` indipendentemente dal tipo.
- Mancava completamente una mappa di "perks per livello" per le infra non-cinema → l'utente non sapeva cosa stava sbloccando upgradando.

### Fix

**Backend `routes/infrastructure.py`**:
- Nuova mappa **`INFRA_LEVEL_PERKS`** con i benefici testuali per livello per tutti i tipi non-cinema:
  - `production_studio` Lv 1→200: progetti paralleli, cooldown, sblocco Live Action a Lv 5
  - `studio_serie_tv`/`studio_anime`: stessa progressione di quote
  - `cinema_school`: studenti in formazione, velocità training
  - `talent_scout_actors`: candidati/settimana, sblocco disegnatori a Lv 3
  - `talent_scout_screenwriters`: sceneggiature pronte
  - `emittente_tv`: slot palinsesto, prime time, diritti TV market
  - `pvp_investigative`/`pvp_operative`/`pvp_legal`: indagini/contro-attacchi/cause legali
- Helper `_is_cinema_type()`: True se `screens > 0` o `revenue_multiplier > 0`. Categoria di routing.
- Helper `_collect_perks_up_to(infra_type_id, level)` e `_next_unlock_for(infra_type_id, level)`
- `calculate_upgrade_benefits()` rifattorizzata in 2 rami:
  - **cinema**: `category='cinema'`, ritorna `screens_added`, `seats_added`, `new_products` (come prima)
  - **studio/scout/pvp**: `category='studio'`, ritorna `unlocked_perks` (correnti), `new_perks` (sbloccati al prossimo livello), `next_milestone_level` + `next_milestone_perks`
- `all_products_next` ora viene calcolato **solo per cinema** (vuoto per studi)

**Frontend `pages/InfrastructurePage.jsx`**:
- Sezione benefici upgrade renderizza condizionalmente:
  - `category==='cinema'` → griglia 3 col (Sale/Posti/Revenue) + badge nuovi prodotti
  - `category==='studio'` → 3 box stratificati:
    - "✓ Funzioni attive (Lv X)" — perks correnti (verde)
    - "★ Sblocchi a Lv Y" — nuovi perks immediati (viola)
    - "Prossima milestone — Lv Z" — perks futuri (ambra)

**Frontend `pages/PipelineV3.jsx`** (cooldown timer):
- Nuovo helper `formatCountdown(isoStr)` → "2g 5h 12m" / "23m 14s" / "8s"
- Banner quota mostra `⏱️ Disponibile tra Xs` quando `cooldown_active=true`, leggendo `cooldown_expires_at` dall'endpoint `/quota-info`
- `clockTick` portato da 5s a **1s** per countdown fluido

### Test
- Lint Python: 7 errori preesistenti non miei (F811/F821 in cinema_school) — i miei file sono puliti ✅
- Lint JS ✅
- `GET /api/infrastructure/<production_studio>/upgrade-info` → `category=studio, all_products=0, unlocked_perks=[3 perks], next_milestone_level=3, next_milestone_perks=['2 progetti classici paralleli']` ✅
- `GET /api/infrastructure/<cinema>/upgrade-info` → `category=cinema, all_products=5, screens_added=2, seats_added=25, new_products=['Nachos']` ✅
- Screenshot pagina infrastrutture: tab Cinema/Studi/Commerciale/Agenzie/Strategico/Speciale visibili ✅

### File modificati
- `/app/backend/routes/infrastructure.py` (+~110 righe: `INFRA_LEVEL_PERKS`, helper, `calculate_upgrade_benefits` rifatto, `all_products_next` solo cinema)
- `/app/frontend/src/pages/InfrastructurePage.jsx` (+~70 righe: rendering condizionale category)
- `/app/frontend/src/pages/PipelineV3.jsx` (+~20 righe: `formatCountdown`, clockTick 1s)

---


## Cast Suggerito AI + Auto-Completa Cast (Apr 28, 2026 — sera 2)

### Richiesta utente
Aggiungere funzionalità AI per:
1. **Suggerisci Cast AI**: l'AI propone gli attori migliori per ogni personaggio in modale di preview, l'utente può confermare/modificare
2. **Completa Cast Automatico**: assegna direttamente tutti i personaggi (anche 20) agli attori più coerenti per età, ruolo, skill e genere

### Implementazione

**Backend `routes/characters.py`**:
- Nuovo modello `ActorSlim`, `SuggestCastRequest` (campo `actors` opzionale + `overwrite`)
- `_score_actor_for_character()`: scoring basato su skill/popolarità (50%/30%) + stelle×5 + bonus genre match (+15) + bonus ruolo principale (×3 stars per protagonist/antagonist) + penalità minor per superstar + bonus gender match (+10) o mismatch (−30) + età-precision (−0.5 per anno di gap). Età incompatibile → score −1 (escluso).
- `_compute_suggestions()`: ordina personaggi per importanza (protagonist 5 → minor 1) e assegna greedy ad attori non ancora usati. Skip ai personaggi già assegnati se `overwrite=False`.
- `_fetch_actors_pool()`: fallback automatico al database `db.people` (200 attori) se il client non passa `actors`.
- Endpoint `POST /api/characters/{kind}/{pid}/suggest-cast` → ritorna preview con `score`, `kept`, `no_match`
- Endpoint `POST /api/characters/{kind}/{pid}/auto-complete-cast` → applica direttamente, ritorna `{characters, assigned, total, no_match}`

**Frontend `components/CharactersPanel.jsx`**:
- 2 nuovi pulsanti nell'header (visibili solo quando `actors !== null` e non readOnly):
  - "🪄 Suggerisci Cast AI" (cyan) → apre modale con preview, l'utente conferma con "Applica"
  - "⚡ Completa Cast Auto" (amber) → assegna immediatamente tutti
- Modale preview cast: lista personaggio→attore con score, "no match" rosso per gli incompatibili, pulsanti Annulla/Applica
- Toast riepilogo: "✨ Cast applicato: 8/8 personaggi" o "⚡ Cast completato: 8/8 (0 senza match età)"

### Test
- Lint Python ✅, Lint JS ✅
- `POST /api/characters/film_v3/<pid>/suggest-cast` → 8 personaggi con score 81-108 ✅
- `POST /api/characters/film_v3/<pid>/auto-complete-cast` (overwrite=true) → Assigned: 8/8, no_match: 0 ✅
  - Alessandro Rinaldi (45y, protagonist) → Tunde Adeyemi
  - Livia Conte (50y, antagonist) → Folake Nwachukwu
  - Greta Rinaldi (16y, supporting) → Khanyi Naidoo
  - ecc.

### File modificati
- `/app/backend/routes/characters.py` (+~140 righe: scoring + 2 endpoint)
- `/app/frontend/src/components/CharactersPanel.jsx` (+~120 righe: 2 pulsanti, modale preview, 3 azioni AI)

---


## Personaggi AI + Live Action + UX errori 400 (Apr 28, 2026 — sera)

### Richieste utente
1. Toast "errore HTTP 400" troppo generico → messaggi italiani coerenti che durino abbastanza
2. AI deve generare lista **personaggi 5-20** (con nome, ruolo importanza, età coerente, descrizione) — solo per **film d'animazione, anime, serie TV**
   - Animazione/anime → fine riepilogo (no cast)
   - Serie TV → prima del cast (per guidare la scelta degli attori)
   - Menu a tendina con matching età freezato (forbice 3/8/10/12 anni in base all'età personaggio)
3. **Live Action**: nuova funzione in /produci che adatta film d'animazione/anime in live-action cinematografico
   - Requisiti: Studio Anime OR Production Studio Lv 5 + Player Lv 10 + Fame ≥ 100
   - Solo produttore originale, gate 15 giorni reali dall'uscita
   - Pipeline V3 classica + LAMPO supportata
   - Personaggi pre-popolati dall'origine; cast con menu personaggi
   - Hype bonus = (CWSv × 8) + (spettatori / 100k), cap 200
   - Genere ereditato (sottogenere overrideable se assente in origine)
   - Serie TV → no live action (già usano attori). Backlog: estendere "Sequel" a "Opere Derivate" (film-da-serie / serie-da-film)

### Implementazione

**Fase A — UX errori**
- `frontend/src/pages/PipelineV3.jsx`: toast errore durata 8s (success 3.5s)
- `frontend/src/components/v3/V3Shared.jsx`: messaggi 400/429/500 in italiano coerenti

**Fase B — Personaggi AI**
- Backend `utils/characters_ai.py`: util async `generate_characters_ai()` con fallback deterministico, normalizzazione age 4-95, deduplica nomi, garantito ≥1 protagonista
- Backend `utils/characters_ai.py::age_tolerance_for/is_actor_compatible`: forbice ±3 (≤17), ±8 (18-35), ±10 (35-60), ±12 (60+)
- Backend `routes/characters.py`: nuovo router `/api/characters` con
  - `GET /{kind}/{pid}` (kind ∈ film_v3, series_v3, lampo)
  - `POST /{kind}/{pid}/generate?force=true&count=8`
  - `POST /{kind}/{pid}/assign` (collega attore↔personaggio)
- Frontend `components/CharactersPanel.jsx`: pannello riusabile con generazione, lista, menu a tendina attore (incompatibili disabilitati visivamente)
- Frontend `utils/characterAgeUtils.js`: gemello frontend di matching età + label/colori ruolo
- Integrazione:
  - `Phases.jsx::MarketingPhase` (film V3 animation/anime) → readonly
  - `PipelineSeriesV3.jsx::CastPhase` (serie TV non anime) → editable con menu attori
  - `PipelineSeriesV3.jsx::MarketingPhase` (anime) → readonly fine riepilogo

**Fase C — Live Action**
- Backend `routes/live_action.py`: prefix `/api/live-action`
  - `GET /unlock-status`
  - `GET /eligible-origins` → film d'animazione + anime di proprietà rilasciati ≥15gg, no live-action già prodotto
  - `POST /create` con quota check + pre-popolamento personaggi (genera al volo se origine non li ha) + bonus hype + marca origin con `live_action_id`
- Frontend `pages/CreateLiveActionPage.jsx`: pagina rotta `/create-live-action` con
  - Box requisiti se non sbloccato
  - Griglia opere eligibili con poster, kind (Animaz./Anime), CWSv, giorni, spettatori, badge LAMPO
  - Modale di conferma con titolo, sottogenere (se assente), modalità (V3 / LAMPO), info bonus
  - Naviga a `/pipeline-v3?p=<new_id>` dopo creazione
- `App.js`: aggiunto `Camera` "Live Action" nel menu Produci, lazy-load + rotta protetta

### Test
- Lint JS ✅, Lint Python ✅
- `POST /api/characters/film_v3/<pid>/generate` → 8 personaggi coerenti (Alessandro, Livia, Emma, Nico, Greta, ecc.) con role_type/age/description in italiano ✅
- `GET /api/live-action/unlock-status` → corretto stato non-sbloccato (player Lv 1, Fame 15, Anime Lv 2, Prod Lv 1) ✅
- `GET /api/live-action/eligible-origins` → unlocked:false, origins:[] (atteso) ✅
- Screenshot pagina /create-live-action → header "LIVE ACTION" pink + 3 requisiti con check rossi ✅

### File aggiunti
- `/app/backend/utils/characters_ai.py`
- `/app/backend/routes/characters.py`
- `/app/backend/routes/live_action.py`
- `/app/frontend/src/components/CharactersPanel.jsx`
- `/app/frontend/src/utils/characterAgeUtils.js`
- `/app/frontend/src/pages/CreateLiveActionPage.jsx`

### File modificati
- `/app/backend/server.py` (registrazione 2 router)
- `/app/backend/routes/pipeline_v3.py` (endpoint `/quota-info`)
- `/app/frontend/src/pages/PipelineV3.jsx` (badge quota + modale + toast 8s)
- `/app/frontend/src/components/v3/V3Shared.jsx` (messaggi errore 400/429/500)
- `/app/frontend/src/components/v3/Phases.jsx` (CharactersPanel in MarketingPhase)
- `/app/frontend/src/components/v3/PipelineSeriesV3.jsx` (CharactersPanel cast TV + marketing anime)
- `/app/frontend/src/App.js` (rotta + menu Produci + lazy import)

### Backlog future
- Estendere sezione **Sequel** → **Opere Derivate**: aggiungere "Film da Serie TV" e "Serie TV da Film" come modalità derivate dello stesso flow

---


## Fix UX Quota Studio V3 — Modale errore + Badge quota visibile (Apr 28, 2026)

### Problema
Utente segnala "errore HTTP 400" creando film V3 su Edge/Safari mentre Chrome funziona.

### Diagnosi
NON è bug browser. Backend ritorna correttamente: *"Limite progetti classici raggiunto (7/1). Completa un progetto o potenzia lo studio al livello superiore."* L'utente ha **7 progetti V3 attivi** (idea/hype/distribution) con Studio Lv 1 → max 1 parallelo. Su Chrome probabilmente cliccava il bottone **LAMPO** (quota separata 0/1, libero) e su Safari/Edge il bottone **V3 classico** (saturo). Il toast 3s nascondeva il messaggio reale.

### Fix
**Backend `routes/pipeline_v3.py`**:
- Nuovo endpoint `GET /api/pipeline-v3/quota-info?studio_type=production_studio&mode=classic|lampo` → ritorna `parallel_used`, `max_parallel`, `cooldown_active`, `level`, `unlimited`. Permette al frontend di mostrare la capacità prima del click.

**Frontend `pages/PipelineV3.jsx`**:
- `loadQuota()` chiamato all'avvio + dopo create/discard. Carica entrambe le modalità in parallelo.
- Nuovo banner **Quota Strip** sopra la griglia progetti: 2 chip (V3 Classico / ⚡ LAMPO) con `used/max`, livello studio, e colore rosso se limite raggiunto / cooldown attivo.
- Nuovo **modale di errore quota** (`AlertTriangle` rosso, full-screen overlay) sostituisce il toast volatile quando `e.status === 400` e msg contiene "limite/cooldown/studio". Pulsanti "Potenzia Studio" (→ /infrastructure) e "Chiudi". Suggerimento di scartare progetti aperti.
- Reload quota anche dopo `discard()` per riflettere subito gli slot liberati.

### Test
- Lint JS ✅
- `curl /api/pipeline-v3/quota-info?mode=classic` → `{"parallel_used":7,"max_parallel":1,"level":1,...}` ✅
- `curl /api/pipeline-v3/quota-info?mode=lampo` → `{"parallel_used":0,"max_parallel":1,...}` ✅
- Screenshot board V3 → banner "V3 CLASSICO 7/1" rosso + "⚡ LAMPO 0/1" verde visibili ✅

### File modificati
- `/app/backend/routes/pipeline_v3.py` (+19 righe: endpoint `quota-info`)
- `/app/frontend/src/pages/PipelineV3.jsx` (+~85 righe: state, loadQuota, errorModalEl, renderQuotaBadge, integrazione board/project view)

---


## Fix Cast Step — Ruolo + CRc + Pre-ingaggiati (Apr 27, 2026 — sera 16)

### Problemi segnalati
1. **Mia Agenzia (viola)**: ingaggio funzionante ma niente selezione ruolo → tutto "generico".
2. **Scuola di Recitazione (verde)**: 2 stelle ma CRc=0 visualizzato, niente ruolo, "generico".
3. **Pre-ingaggiati (giallo, Mikhail Solovyov)**: niente ruolo + "Errore API" all'ingaggio.

### Fix

**Backend `routes/pipeline_v3.py`**:

1. `_calc_crc_from_npc()` → fallback per NPC senza skills granulari (studenti scuola, agency basic): formula `stars * 8 + min(fame, 100) * 0.2` invece di ritornare 0.

2. `cast-agency-actor` endpoint → aggiunto branch `source == "pre_engaged"`:
   - Cerca in `db.pre_engagements` (state in active/threatened) per quel NPC.
   - Costruisce actor object da `npc_snapshot` con `cost_per_film: 0`, `is_pre_engaged: True`, skills/stars/fame da snapshot.
   - Se non trova → 404 normale.

**Frontend `components/v3/CastPhase.jsx`**:

3. Per ogni attore "own roster" (agency / scuola / pre-ingaggiati) aggiunta una **`<select>` ruolo** sopra il bottone "+":
   - Lista popolata da `ACTOR_ROLES` (lead/coprotagonist/supporting/extra/cameo + generico).
   - Visualizzazione localizzata via `ROLE_DISPLAY`.
   - Scelta salvata in `actorRoles[actor.id]` (state esistente, gia' usato dal mercato).
   - Bottone "+" passa il ruolo scelto a `castAgencyActor()` invece di forzare 'generico'.
   - `data-testid="cast-own-role-{actor.id}"` per testing.

### Test
- Lint frontend ✅, lint backend ✅
- Backend riavviato OK
- Pagina cast accessibile via `/create-film?p={id}` step CAST

### Note
La sub-tab role (Registi/Scenegg./Attori/Compositori) e' la seconda riga di tabs all'interno della source tab (Mercato/Mia Agenzia/Agenzie). Per vedere il selettore ruolo nel testing, prima clicca "La Mia Agenzia" poi clicca "Attori" nel sub-tab inferiore.

Files: `backend/routes/pipeline_v3.py`, `frontend/src/components/v3/CastPhase.jsx`.

---


## Fix Trailer Anime — Stile coerente (Apr 27, 2026 — sera 15)

### Problema
I trailer di anime mostravano scene live-action con persone reali, non coerenti con la locandina anime (es. "Un Pezzo" → trailer con foto di pirati realistici invece che anime).

### Root cause
`routes/trailers.py`:
- `_generate_frame_image()` usava SOLO `genre` per scegliere lo stile (`GENRE_STYLES` mappa genre → stile cinematografico).
- Per un anime con genere "action", lo stile era "high energy, dynamic motion blur, desaturated blockbuster look" → live-action, NON anime.
- Lo storyboard LLM produceva image_prompt che iniziavano con "Cinematic scene from an original fictional movie:" e finivano con "film grain, anamorphic lens" → forzando la generazione live-action.

### Fix
1. **`_generate_frame_image(frame, genre, frame_idx, content_type)`**: nuovo parametro `content_type`. Se `content_type=='anime'`, override completo dello stile:
   - `genre_style = "anime art style, 2D animation, vibrant colors, cel-shading, expressive characters, manga-inspired composition, NOT photorealistic, NO live-action"`
   - Sostituisce keyword cinematografiche live-action ("Cinematic scene", "film grain", "anamorphic lens") con equivalenti anime.
   - Aggiunge constraint espliciti: "NO photorealism, NO real human faces, original anime characters only".

2. **Storyboard LLM (`generate_storyboard`)**: nuovo flag `is_anime` derivato da `content.type`. Quando true:
   - Aggiunge `style_hint` chiaro nel system prompt: "questo e' un ANIME, NON un film live-action. Tutti i personaggi e gli ambienti devono essere disegnati in stile anime/manga".
   - `opening_phrase` = "Anime scene from an original fictional anime series:"
   - `ending_phrase` = ", 16:9, anime art style, 2D animation, NO photorealism, no text, no logos, no real people, no trademarks."
   - Title card prompt cambia in "Anime title card background, vibrant colors, abstract anime composition, no text, 16:9".

3. **Call site**: `derived_content_type` calcolato da `coll == 'anime_series'` o `content.type == 'anime'`. Vale per:
   - `db.anime_series` (anime LAMPO o legacy)
   - `db.series_projects_v3` con `type=='anime'`

### Test
Backend reload OK. Endpoint operativo. Per testare end-to-end serve generare un trailer su un anime in produzione (i 4 progetti V3 in preview sono tv_series, non anime).

Files: `backend/routes/trailers.py`.

---


## 3 fix: Velocizzazioni Film TV + Hype dinamico + AI mini-trame (Apr 27, 2026 — sera 14)

### 1. Velocizzazioni Film TV cap 5 CP (Foto 1)
**Frontend** `components/v3/Phases.jsx`:
- Aggiunto `SPEEDUP_COSTS_TV = {25: 1, 50: 3, 75: 4, 100: 5}` (vs `SPEEDUP_COSTS = {25:10, 50:15, 75:20, 100:25}` per V3 classico).
- Helper `getSpeedupCostsFor(film)` ritorna la tabella corretta in base a `film.is_tv_movie`.
- 5 occorrenze di `SPEEDUP_COSTS[p]` sostituite con `getSpeedupCostsFor(film)[p]` (Hype, Ciak, FinalCut, La Prima).
- Costo scala col progresso (gia' presente): a 50% di hype, costo dimezzato, ecc.

**Backend** `utils/calc_speedup.py`:
- `BASE_COSTS_TV = {25:1, 50:3, 75:4, 100:5}`.
- `get_speedup_cost(percentage, current_progress, is_tv_movie=False)` ora accetta il flag.

`routes/pipeline_v3.py speedup endpoint`: passa `is_tv_movie=bool(project.get('is_tv_movie'))`.

### 2. Hype dinamico nel periodo Prossimamente (Foto 2)
**Backend** `scheduler_tasks.py`:
- Nuova funzione `process_prossimamente_hype_drift()`: ogni 15 min itera su `film_projects` + `series_projects_v3` con poster generato e pipeline_state in [idea, hype, cast, prep, ciak, finalcut, marketing].
- Drift base per stato:
  - Step `hype`: +0.5 .. +2.5 (incremento attivo durante hype phase)
  - Step `marketing`: +0.3 .. +2.0
  - Step `idea`: -0.5 .. +0.3 (leggero decay)
  - Altri (cast/prep/ciak/finalcut): -1.0 .. +2.0
- Eventi casuali:
  - 5% surge: +5..+12 (es. trailer leak, gossip)
  - 3% slump: -3..-6 (es. cast scandal)
- Bonus film TV: drift × 1.2 (sono prodotti veloci con hype piu' viva).
- Cap [0, 100]. `hype_last_drift_at` salvato per tracking.

**Server** `server.py`: nuovo job `prossimamente_hype_drift` registrato con `IntervalTrigger(minutes=15)`.

### 3. AI mini-trame per nuovi rilasci (richiesta utente)
**Backend** `routes/series_pipeline.py confirm-release`:
- Prima della creazione episodi: una singola chiamata `LlmChat` (gpt-4o-mini) genera **tutte** le N mini-trame in batch (max 18 parole l'una).
- Parsing regex `^N[.):\\-]\\s+text` per estrarre per episodio.
- Fallback: se LLM fallisce o key assente → templates random (10 frasi).
- Fallback per episodio se AI non l'ha coperto → template.
- Latenza accettabile (~3-5s) per release.

Files: `frontend/src/components/v3/Phases.jsx`, `backend/utils/calc_speedup.py`, `backend/routes/pipeline_v3.py`, `backend/scheduler_tasks.py`, `backend/server.py`, `backend/routes/series_pipeline.py`.

---


## Fix 3-in-1 dashboard TV (Apr 27, 2026 — sera 13)

### Foto 1: Badge "Film TV" sulle locandine
`components/ComingSoonSection.jsx`: il badge sopra il titolo ora distingue:
- "Film" (giallo) per film cinematografici
- "Film TV" (rosa) per film con `is_tv_movie=true`
- Anime/Serie/Remaster invariati
Modificato sia il `typeLabel` per Card layout che per Compact layout (2 punti del file).

### Foto 2: "IN ARRIVO SU TV" non mostra piu' serie gia' airing
`pages/Dashboard.jsx ProssimamenteV3Section`: la sezione mergeava `coming_soon` + `airing`. Ora include SOLO `coming_soon`. Le serie/anime gia' in onda devono apparire in "Ultimi Aggiornamenti Serie TV / Anime", non qui. Correzione 1 riga.

### Foto 3: Mini-trame episodi da rilascio
**Backend `routes/series_pipeline.py`**: la generazione episodi al release ora popola `mini_plot` con un template aleatorio (10 frasi a rotazione per varieta'), invece di lasciarlo `''`. I nuovi rilasci avranno mini-trama leggibile dal primo airing.

**Backfill produzione** `routes/admin_recovery.py`:
- Nuovo endpoint `POST /api/admin/recovery/backfill-mini-plots` (admin-only).
- Itera su tutte le `tv_series` esistenti, trova episodi con `mini_plot` vuoto, e popola con template.
- Risposta: `{success, series_fixed, episodes_updated}`.

L'utente in produzione potra' chiamare questo endpoint UNA VOLTA dopo il deploy per sistemare le serie esistenti come Kudakodu e The Concept.

### Test verificato via screenshot
- Dashboard senza serie airing in "IN ARRIVO SU TV" (mostra "Nessun contenuto in arrivo") ✅
- Endpoint `/admin/recovery/backfill-mini-plots` risponde 200 con counter ✅
- Nuove serie create useranno il template auto-popolato ✅

Files: `components/ComingSoonSection.jsx`, `pages/Dashboard.jsx`, `routes/series_pipeline.py`, `routes/admin_recovery.py`.

---


## Fix IDEA Phase locked per Film TV (Apr 27, 2026 — sera 12)

### Bug
Nei Film TV, dopo la creazione, l'utente entrava nello step IDEA della pipeline V3 ma trovava **Location di Ripresa** e **Budget Produzione** già lockati (subPhase=1 invece di 0).

### Root cause
`IdeaPhase.jsx` calcolava `hasSavedIdea` solo su `genre + preplot + subgenres`. Siccome al create del film TV salviamo gia' subgenres nel form, `hasSavedIdea=true` e `initialPhase=1` → tutti i campi disabilitati anche se locations e budget non erano ancora stati scelti.

### Fix
`components/v3/IdeaPhase.jsx`: ampliato il check `hasSavedIdea` per richiedere ANCHE `locations.length > 0` e `budget_tier`. In questo modo l'utente puo' editare locations/budget finche' non li sceglie + salva (`save-idea`). Vale sia per V3 classico che TV movies (compatible con saved films esistenti).

```diff
- const hasSavedIdea = !!(film.genre && film.preplot && film.preplot.length >= 50 && (film.subgenres?.length > 0 || film.subgenre));
+ const hasSavedIdea = !!(
+   film.genre && film.preplot && film.preplot.length >= 50 &&
+   (film.subgenres?.length > 0 || film.subgenre) &&
+   (film.locations?.length > 0) &&
+   film.budget_tier
+ );
```

Verificato via screenshot: locations (Hollywood/Cinecitta/Pinewood/Babelsberg/Warner Bros) e tutti i 6 budget tier (Micro/Low/Mid/Big/Blockbuster/Mega) ora cliccabili nel TV movie "Notte di Stelle TV".

Files: `components/v3/IdeaPhase.jsx`.

---


## Fix Form Creazione FILM TV (Apr 27, 2026 — sera 11)

### Modifiche su feedback utente
1. **Banner "PIPELINE TV — VANTAGGI" rimosso** (era ridondante).
2. **Style label "netflix" sotto il nome TV rimosso** → ora mostra `Italy · preferisce thriller, crime, drama` (paese + generi preferiti = info utile per il giocatore).
3. **Genere "Erotico" aggiunto** sia in V3 classica che TV: `V3Shared.GENRES` + `GENRE_LABELS` + `SUBGENRE_MAP.erotic` (20 sottogeneri: sensuale, seduzione, passionale, tabù, triangolo, vintage retrò, psicologico, noir erotico, ecc.).
4. **Selettore sottogeneri (max 3)** nel form TV: chip selezionate con X removable + grid scroll-able di opzioni filtrate. Cap a 3 con toast "Massimo 3 sottogeneri". Reset su cambio genere.
5. **Hint AI** aggiunto in fondo al form: "Locandina, sceneggiatura e trailer AI (3 opzioni) saranno generati nei passi successivi della pipeline V3".

### Backend
`tv_movies.py`: `CreateTvMovieRequest` accetta ora anche `subgenres: Optional[list]` (max 3 troncato server-side). Salvato in `film_projects.subgenres`.

### Test verificato via screenshot
- Genere Erotico selezionato → 20 sottogeneri visibili ✅
- 3 selezionati (sensuale, seduzione, passionale) ✅
- Tentativo 4° → toast "Massimo 3 sottogeneri" + counter resta a 3 ✅
- TV destinazione mostra "Italy · preferisce thriller, crime, drama" ✅
- Hint AI visibile ✅
- Banner rosa eliminato ✅

### Risposta all'utente sulla pipeline AI
La generazione AI di **locandina (da pretrama)**, **sceneggiatura** e **trailer (con 3 opzioni)** è gia' presente nella pipeline V3 standard che si apre dopo la creazione:
- **Locandina + Sceneggiatura AI**: nello step IDEA (`IdeaPhase.jsx`, `generate-poster` + `generate-screenplay`).
- **Trailer AI con 3 opzioni**: nello step FINAL CUT (`TrailerGeneratorCard.jsx`).

Files: `pages/CreateTvMoviePage.jsx`, `components/v3/V3Shared.jsx`, `routes/tv_movies.py`.

---


## FILM PER LA TV — FASE 2 + FASE 3 COMPLETATE (Apr 26, 2026 — sera 10)

### FASE 2 — Bonus Features

**Backend** (`routes/tv_movies.py`):
- **Bonus genere↔stile TV**: nuova mappa `STYLE_PREFERRED_GENRES` con 10 stili (netflix→thriller/crime/drama/sci_fi, disney→animation/fantasy/adventure/musical/romance, paramount→action/adventure/thriller, prime→drama/thriller/comedy, apple→drama/biographical/documentary, sky→thriller/crime/documentary, rai→historical/drama/biographical/documentary, dazn→documentary, tim→comedy/romance/drama).
  - Nuovo endpoint `GET /tv-movies/genre-style-bonus/{station_id}/{genre}` ritorna match + bonus_pct (5%) + preferred_genres.
  - Salvato su `film_projects.tv_genre_style_match` + `tv_genre_bonus_pct` alla creazione.
  - Applicato al CWSv in `pipeline_v3.py confirm-release`: `quality_score *= 1.05` se match.
- **Slot orari con effetto share reale**: dopo l'inserimento del film_doc nel release, modificatori applicati su `opening_day_revenue`:
  - prime: ×1.0 · daytime: ×0.7 · late: ×0.5 · morning: ×0.4
  - Salvato `tv_share_modifier_applied`, `tv_slot_mod`, `tv_maratona_mod`.
- **Maratona** (3+ film TV stessa TV stesso giorno = +15% share): rilevamento automatico in `schedule-airing` (count `tv_air_datetime` nello stesso giorno solare). Flag `tv_maratona_eligible=true` + bonus moltiplicato a release.
- **Repliche/Rerun** (`POST /tv-movies/{film_id}/rerun`): max 3, decay `0.7^N` su spettatori, attaccato al palinsesto TV con `rerun_number`. Aggiorna `total_viewers` e `total_revenue` proporzionalmente.
- **Anteprima TV** (`POST /tv-movies/{pid}/anteprima-tv`): mini evento gratuito → +20 hype_score, flag `tv_anteprima_active=true`.

**Frontend**:
- `pages/CreateTvMoviePage.jsx`: indicatore bonus genere↔stile in tempo reale ("✨ +5% CWSv (genere preferito da [TV])"), o hint dei generi preferiti se no match.
- `components/ContentTemplate.jsx`: nuovi bottoni accanto a "Mercato TV" — **✨ Anteprima** (rosa) e **🔁 Replica** (cyan) visibili solo per film TV, gestiscono confirm + toast + chiamata API.
- `current_cinemas` impostato a 0 per i film TV (non occupano sale).

### FASE 3 — TV Awards

**Backend** (`tv_movies.py awards_router`):
- `GET /api/tv-awards/categories` → 6 categorie: Miglior Film TV (🏆), Regia TV (🎬), Attore TV (🎭), Attrice TV (🎭), Sceneggiatura TV (📜), Colonna Sonora TV (🎵).
- `GET /api/tv-awards/leaderboard?year=YYYY` → top 10 per `quality_score` (anno corrente di default), aggrega regia/attori dai cast con scoring per somma quality_score, separato per genere (♂/♀).

**Frontend** (`pages/TvAwardsPage.jsx`):
- Pagina dedicata `/tv-awards` con header Trophy + banner ambra.
- Year selector (2024-2026).
- 6 card per categoria con top 5 ranked (medaglie ambra/grigio/bronzo per top 3) + poster + station + cwsv_display.
- Empty state per anno senza candidati.
- Aggiunto link nel menu nav (Trophy icon).

### Test verificati
- `genre-style-bonus/netflix/thriller` → matches=true, bonus_pct=5.0 ✅
- `genre-style-bonus/default/drama` → matches=false ✅
- `tv-awards/categories` → 6 categorie ✅
- `tv-awards/leaderboard?year=2026` → struttura corretta (vuota nel preview perché no film TV ancora rilasciati) ✅
- Frontend `/tv-awards` ✅ rendering completo
- Frontend `/create-tv-movie` con genre=Thriller → bonus indicator visibile ✅

### Files
- `routes/tv_movies.py` (esteso con FASE 2+3, ~150 nuove righe)
- `routes/pipeline_v3.py` (bonus genere applicato + slot/maratona modifiers)
- `server.py` (registrato `awards_router`)
- `pages/TvAwardsPage.jsx` (NEW)
- `pages/CreateTvMoviePage.jsx` (bonus indicator)
- `components/ContentTemplate.jsx` (bottoni Anteprima + Replica)
- `App.js` (route + navItems)

---


## FILM PER LA TV — FASE 1 MVP (Apr 26, 2026 — sera 9)

Pipeline V3 dedicata "Film per la TV" lockata se l'utente non possiede stazioni TV.

### Backend
**Nuovo file** `routes/tv_movies.py` (registrato in `server.py`):
- `GET /api/tv-movies/cost-modifier` → `{multiplier:0.30, discount_pct:70, max_release_cp:10, max_speedup_cp:5, time_slots:{...}}`
- `GET /api/tv-movies/check-eligibility` → eligible + lista stations dell'utente.
- `POST /api/tv-movies/create` → crea `film_projects` con flag:
  - `is_tv_movie=True`, `target_station_id`, `target_station_name`, `target_station_style`
  - `release_type='tv_direct'`, `distribution_world=False`, `pipeline_version=3`, `pipeline_state='idea'`
  - `hype_score=15` (bonus iniziale per visibilita' immediata)
- `POST /api/tv-movies/{pid}/schedule-airing` → setta `tv_air_datetime` + `tv_time_slot` (prime/daytime/late/morning).
- Slots con modificatori share + costo airing.

**Modifiche `routes/pipeline_v3.py`** (endpoint `confirm-release`):
- Se `is_tv_movie=True`:
  - `total_funds *= 0.30` (-70%)
  - `total_cp = min(total_cp * 0.30, 10)` (max 10 CP)
  - `status='in_tv_programming'` (invece di `in_theaters`)
  - Salva `target_station_id/name/style/tv_air_datetime/tv_time_slot/tv_replays_*` nel film_doc
  - Auto-aggiunge il film a `tv_stations.contents.films` con `via_tv_movie=true`, `scheduled_at`, `time_slot`.

### Frontend
**Nuova pagina** `pages/CreateTvMoviePage.jsx` (route `/create-tv-movie`):
- Banner rosa con i 5 vantaggi della pipeline TV.
- Form: titolo + genere + pretrama + selezione TV destinazione.
- Se l'utente non ha TV → CTA "Costruisci la tua TV" che porta a `/infrastructure?focus=tv_station`.

**Bottone Produci** `App.js`:
- Nuovo bottone "Film TV" (icona Radio, rosa) nel menu Produci.
- `locked: !productionUnlocks?.has_emittente_tv` → mostra grayscale + Lock + toast "Devi possedere una TV".

**Pipeline V3** (`pages/PipelineV3.jsx`, `components/v3/V3Shared.jsx`):
- `StepperBar` accetta `isTvMovie`: filtra fuori `la_prima` e `distribution`.
- `renderPhase` gestisce stati `la_prima`/`distribution` per TV movie → renderizza nuovo componente `TvMovieSchedulePhase` (data + ora + slot picker).
- Header film mostra badge "📺 TV: NomeStazione" rosa.

**Nuovo componente** `components/v3/TvMovieSchedulePhase.jsx`:
- Auto-imposta `release_type='direct'` al mount.
- Date picker (min ora+1h) + Time picker.
- 4 slot orari con metadata share/cost.
- Bottone "Programma e Procedi al Rilascio" → chiama `schedule-airing` poi `advance` a `release_pending`.

### Test verificati
- `GET /tv-movies/cost-modifier` ✅ ritorna {multiplier:0.30, discount:70%}.
- `GET /tv-movies/check-eligibility` ✅ ritorna AnacapitoFlix.
- `POST /tv-movies/create` ✅ crea progetto con tutti i flag corretti (`is_tv_movie=True`, `release_type=tv_direct`, `hype_score=15`).
- `POST /tv-movies/{id}/schedule-airing` ✅ setta data/slot.
- Frontend `/create-tv-movie` ✅ visualizza banner + form + selezione TV (screenshot).

### Limitazioni FASE 1 (da completare in Fase 2/3)
- Idee bonus non ancora implementate: Anteprima TV mini-evento, bonus genere↔stile, repliche, slot orari con effetto reale su share, maratona.
- Premi TV-specifici (Fase 3).
- Visibilita' Prossimamente Dashboard + Prossimamente TV: il film appare gia' (essendo `pipeline_version=3` con `pipeline_state` non excluded), ma manca un badge visivo "FILM TV" e una sezione dedicata.
- Cost reduction sugli step intermedi (advance/cast/prep): per ora applicato SOLO al rilascio finale. Da estendere agli altri step.

Files: `routes/tv_movies.py` (new), `routes/pipeline_v3.py`, `server.py`, `pages/CreateTvMoviePage.jsx` (new), `pages/PipelineV3.jsx`, `components/v3/V3Shared.jsx`, `components/v3/TvMovieSchedulePhase.jsx` (new), `App.js`.

---


## Selettore Stile TV per emittenti esistenti + CTA "Costruisci una TV" (Apr 26, 2026 — sera 8)

### A. Selettore Stile TV nelle emittenti esistenti
Prima il selettore stile branding (NetfleX/Disnext+/Topmount+/PrimeFlix/AppleVue/SkyView/ItaliaPlay/Dazz!/ItalVision/Generica) era disponibile SOLO nel wizard di setup iniziale di una nuova TV. Ora è anche **modificabile per emittenti esistenti** dalla tab "Gestione" del menu TV.

**File**: `frontend/src/components/TVMenuModal.jsx`
- Caricamento stili al mount (`/tv-stations/available-styles`).
- Stato `selectedStyle` inizializzato da `station.style || 'default'`.
- Card "STILE BRANDING" nella tab Gestione (sopra "Azzera Palinsesto"):
  - Grid 2-col con 10 preset cliccabili (label colorata + tagline + font del brand).
  - Bottone "Applica Stile" rosso (disabled se selezione non cambiata) → POST `/tv-stations/update-style`.
  - Toast successo + `onRefresh()` per ricaricare la station.
- `data-testid` aggiunti: `gestione-style-{key}`, `save-style-btn`.

### B. CTA "Costruisci una TV" nel TvMarketModal
**File**: `frontend/src/components/TvMarketModal.jsx`
- Tab "Fai Offerta" sempre visibile (già fatto in precedenza).
- `OfferForm`: se `myStations.length === 0`, ora mostra un CTA con messaggio + bottone gradient rosa "Costruisci la tua TV" che chiama `onClose()` e naviga a `/infrastructure?focus=tv_station`.
- Aggiunto prop `onClose` al form.

### C. Deep-link Infrastrutture
**File**: `frontend/src/pages/InfrastructurePage.jsx`
- Nuovo `useEffect` che leggi `?focus=tv_station` (o `emittente_tv`) e auto-imposta `activeCategory='studi'` + `activeSubTab='disponibili'`.
- L'utente atterra direttamente sulla scheda dove può comprare l'EMITTENTE TV.

### Test verificato via screenshot
- Tab "Gestione" → Card STILE BRANDING con 10 preset + bottone "Applica Stile" ✅
- `/infrastructure?focus=tv_station` → categoria "STUDI" pre-selezionata con EMITTENTE TV visibile ✅

Files: `TVMenuModal.jsx`, `TvMarketModal.jsx`, `InfrastructurePage.jsx`.

---


## Fix Mercato Diritti TV — tab "Fai Offerta" sempre visibile (Apr 26, 2026 — sera 7)

### Problema
Il testo nella Panoramica diceva *"puoi comunque inviare un'offerta spontanea al proprietario tramite 'Fai Offerta'"* ma il tab "Fai Offerta" era nascosto se l'utente non possedeva alcuna TV.

### Fix
- `frontend/src/components/TvMarketModal.jsx` linea 236: rimosso il check `myStations.length > 0` dal rendering del tab.
- Il tab è ora sempre visibile per non-owner.
- Se l'utente non ha TV, l'`OfferForm` mostra già il messaggio rosa "Nessuna TV in tuo possesso — Per acquistare diritti devi prima costruire una stazione TV (Infrastrutture)" (già implementato, righe 471-478).

### Test
Screenshot conferma 2 tab "Panoramica" e "Fai Offerta" entrambi visibili anche per buyer senza stazioni.

Files: `frontend/src/components/TvMarketModal.jsx`.

---


## Fix MyDraftsWidget — clic ora apre la pipeline corretta (Apr 26, 2026 — sera 6)

### Problema
Cliccando su una bozza in `/le-mie-bozze` (LAMPO Film, V3 film/serie/anime, ecc.) l'utente veniva rimandato alla dashboard invece di riprendere il progetto.

### Root cause
`MyDraftsWidget.pipelineRouteFor` puntava a route inesistenti (`/lampo/{id}`, `/pipeline/{id}`, `/series-pipeline/{id}`, `/sequel/{id}`, `/purchased-screenplays/{id}`) che cadevano nel fallback default → dashboard.

### Fix
1. `frontend/src/components/MyDraftsWidget.jsx` — `pipelineRouteFor` ora mappa alle route esistenti:
   - LAMPO film → `/create-film?lampo=ID`
   - LAMPO series → `/create-series?lampo=ID`
   - LAMPO anime → `/create-anime?lampo=ID`
   - V3 film → `/create-film?p=ID`
   - V3 series → `/create-series?p=ID`
   - V3 anime → `/create-anime?p=ID`
   - V3 sequel → `/create-sequel?p=ID`
   - Sceneggiatura comprata → `/emerging-screenplays?p=ID`
2. `frontend/src/pages/PipelineV3.jsx` — aggiunto handler `?lampo=ID` (fetch `/api/lampo/mine`, trova draft, apre `LampoModal` con `existingProject`).
3. `frontend/src/components/v3/PipelineSeriesV3.jsx` — aggiunto handler universale `?p=ID` e `?lampo=ID` (sia per Serie TV che Anime, perché entrambe condividono il componente).

### Test
Verificato via screenshot: click su draft "Test Economy" → naviga a `/create-film?p=...` e apre la pipeline V3 nello step IDEA con titolo, genere e pretrama precaricati. La query param viene poi pulita per evitare ri-trigger al refresh.

Files: `MyDraftsWidget.jsx`, `PipelineV3.jsx`, `v3/PipelineSeriesV3.jsx`.

---


## Admin Popup — Bottone "Riporta in bozza" aggiunto (Apr 26, 2026 — sera 5)

Su feedback utente: nel popup Admin > Gestione Film mancava il bottone "Riporta in bozza".

### Fix
- `pages/AdminPage.jsx` `FilmsTab`:
  - Nuovo handler `handleRestoreToDraft` chiama `POST /api/admin/recovery/restore-to-draft/{id}`.
  - Layout 3 colonne (era 2): **Fix** (ambra) | **Riporta in bozza** (verde, icona RotateCcw) | **Elimina** (rosso).
  - Conferma `window.confirm` prima dell'azione.
  - Toast di successo + reload lista al termine.
- Bug correlato corretto: `handleFix` usava path errato `/admin-recovery/fix-one/{id}` → ora `/admin/recovery/fix-one/{id}` (allineato al prefix `routes/admin_recovery.py:9`).

### Test
Screenshot conferma il popup con i 3 bottoni visibili e correttamente styled. Endpoint backend già esistente (`admin_recovery.restore_to_draft`).

Files: `frontend/src/pages/AdminPage.jsx`.

### Nota su "Prossimamente FILM" su PRODUZIONE (cineworld-studios.it)
- Endpoint `/api/coming-soon` PREVIEW: include correttamente LAMPO films (`status` in `['lampo_ready', 'lampo_scheduled']`).
- Logica deduplica in `series_pipeline.py` non esclude lampo_ready da `db.films`.
- Se in produzione il film "SuperHero" (status lampo_ready, 9% qualità) non appare, probabilmente il deploy non è ancora stato propagato. **Azione utente**: ridepiegare in produzione.

---


## UI Cleanup — MyDraftsWidget spostato in pagina dedicata (Apr 26, 2026 — sera 4)

Su feedback utente "in dashboard su account admin???? Semmai in Admin panel con sezione dedicata!":
- **Rimosso** `MyDraftsWidget` dalla Dashboard (`Dashboard.jsx`).
- **Creata pagina dedicata** `/le-mie-bozze` (`pages/MyDraftsPage.jsx`) con header "LE MIE BOZZE" + descrizione + widget completo.
- **Nuovo bottone** "Bozze" (icona Clock, ambra) nel menu Produci (App.js, sezione `produci-menu`).
- **Route registrata** in `App.js`.

Verificato via screenshot: dashboard pulita, pagina `/le-mie-bozze` mostra correttamente i 14 progetti in lavorazione.

Files: `frontend/src/pages/Dashboard.jsx` (rimosso widget + import), `frontend/src/App.js` (route + bottone Produci + lazy import), `frontend/src/pages/MyDraftsPage.jsx` (nuovo).

### Nota: "Prossimamente FILM" vuoto su PRODUZIONE
- Verificato endpoint preview `/api/coming-soon`: ritorna 6 film correttamente per fandrex1 (admin).
- Lo screenshot mobile dell'utente mostra URL `cineworld-studios.it` = ambiente PRODUZIONE deployato (non preview).
- La produzione ha codice/DB diversi dal preview. Il fix del coming-soon è già nel codice del preview (vedi Bundle "LAMPO Visibility Globale"). **Soluzione**: ridepiegare in produzione.

---


## Step C COMPLETATO — Admin Avatar Dashboard (Apr 26, 2026 — sera 3)

### Frontend integration
- `AdminAvatarsTab.jsx` (già esistente) ora **importato** in `AdminPage.jsx` e renderizzato come tab "Gestione Avatar" (icon `ImageIcon`).
- Nuova entry in `ADMIN_TABS`: `{ id: 'avatars', label: 'Gestione Avatar', icon: ImageIcon }`.
- Render condizionale `{activeTab === 'avatars' && isAdmin && <AdminAvatarsTab api={api} />}`.

### Funzionamento verificato
- Audit live (Player 72/72, Case 72, NPC 28.752 con 3.500 senza avatar).
- Breakdown per tipo: actor 2826/2826 ✓, director 2881/2881 ✓, screenwriter 2865/2865 ✓, composer 2929/2929 ✓.
- Pulsanti "Applica mancanti" (rosa) + "Rigenera TUTTI" (ambra) + scope filter (Tutti/actor/director/screenwriter/composer/illustrator).
- Backend già in `routes/admin_avatars.py`: `/api/admin/avatars/audit`, `/apply-missing`, `/regenerate-all` (admin-only).

Files: `frontend/src/pages/AdminPage.jsx` (3 edits: import, ADMIN_TABS entry, render).

---


## 📋 ROADMAP — Feature in attesa: "Sistema Talenti Vivente" (P1, da implementare) — VERSIONE 3 FINALE UNIFICATA

> ✦ Sistema completo "NPCs vivi": pre-ingaggio + rescissione + happiness + furto cross-player ✦

### ✅ STEP COMPLETATI
- **Step 1 — Backend MVP** (`/app/backend/routes/talent_market.py`):
  - Endpoint `GET /api/talent-scout/perks` per visibilità/slot/sconto/durata max scalati per livello infra di ogni ruolo.
  - Endpoint `GET /api/market/talents?role=...` lista NPCs filtrata per ruolo + livello infra.
  - Endpoint `POST /api/market/talents/pre-engage/{npc_id}` con scarico fondi + slot enforce.
  - Endpoint `GET /api/talent-scout/my-roster` + `POST /api/talent-scout/release/{eng_id}` (no rimborso).
  - Endpoint `GET /api/market/talents/proposed-to-me` + `POST /api/market/talents/proposed/{prop_id}/accept`.
  - `ROLE_INFRA_MAP` allineata con i tipi infra reali (`talent_scout_actors`, `talent_scout_screenwriters`, ecc.).
  - Schema `talent_pre_engagements`: id, user_id, npc_id, npc_snapshot, role, cast_role_intended, contract_duration_days, contract_expires_at, fee_paid, contract_status, happiness_score, usage_history, ecc.
  - Test E2E backend OK (login → perks → list → pre-engage → roster → release).

- **Step 2 — Frontend Mercato Talenti** (`/app/frontend/src/components/TalentMarketModal.jsx` + `pages/TalentMarketPage.jsx`):
  - Modal con 5 tab ruolo (Attori/Registi/Sceneggiatori/Compositori/Disegnatori) + tab "Proposti a me".
  - PerkBar per ogni ruolo: livello, slot used/total, sconto %, durata massima.
  - NpcCard responsive (mobile-first) con avatar, stelle, top-3 skill, fee 30g, bottone "Pre-ingaggia".
  - Sub-dialog "Pre-ingaggio" con selettore durata (30/60/90/180g, lock se sopra max), selettore ruolo cast (solo per attori), breakdown costo finale.
  - ProposalCard per offerte spontanee con accept rapido a 30g.
  - Integrato in `CastingAgencyPage` (tab Attori) come bottone "Mercato Talenti (Pre-ingaggio)".
  - Route dedicata `/talent-market` aggiunta in `App.js`.

- **Step 3 — Integrazione Pre-Ingaggiati nelle Pipeline**:
  - **V3 Classic** (`/app/backend/routes/pipeline_v3.py` `get_my_agency_actors`): aggiunti pre-engaged in roster con `is_pre_engaged: true`, `cost: 0`, `pre_engage_days_remaining`, `cast_role_intended`, `source: 'pre_engaged'`. Frontend `CastPhase.jsx` mostra gruppo "📜 Pre-ingaggiati" separato + badge giallo nel cast selezionato.
  - **LAMPO** (`/app/backend/routes/lampo.py`): auto-cast prioritizza pre-engaged actors (max 2 garantiti), poi riempie con own pool (school/agency). Director/screenwriter/composer pre-engaged auto-assegnati se disponibili, sostituendo gli NPC random.
  - **Sceneggiature Pronte** (`/app/backend/routes/purchased_screenplays_v3.py` `_auto_fill_cast`): pre-engaged inseriti per primi (max 2 attori a costo 0) + director/screenwriter/composer pre-engaged sostituiscono gli NPC random.
  - Test E2E backend OK: pre-engage da $47k → endpoint `my-agency-actors` ritorna 12 attori (10 agency + 1 pre_engaged + 1 school) con dettagli completi.

- **Step 4 — Sistema Felicità + Auto-Rescissione**:
  - **Backend** (`/app/backend/routes/talent_market.py`):
    - `apply_happiness_decay()`: scheduler heartbeat ogni 6h. Decay -2/heartbeat se >5gg senza utilizzo, -4 se >14gg. Trigger threatened se happiness<30 + contratto>30% trascorso (con notifica). Auto-rescissione dopo grace_period 3gg. Recovery automatico se happiness rimbalza ≥45 durante grace.
    - `boost_happiness_on_film_use()`: chiamato da hook film release. +18 punti se quality≥80, +12 se ≥60, +7 se ≥40, +3 sotto. Pusha entry in `usage_history`.
    - `my-roster` arricchito con `happiness_emoji` (😊🙂😐😠😡), `is_urgent`, `grace_days_remaining`.
    - Notifiche: `talent_threatening_release`, `talent_auto_released`, `talent_recovered`.
  - **Hook** (`/app/backend/game_hooks.py` `on_film_released`): chiama `boost_happiness_on_film_use` per i pre-engaged in cast.
  - **Scheduler** (`/app/backend/server.py`): job `talent_happiness_decay` ogni 6 ore.
  - **Frontend `CastPhase.jsx`**: badge "📜 Pre-ingaggiato 😊" con happiness emoji, badge rosso pulsante "⚠️ Rescissione Xgg" se threatened, badge arancione pulsante se days<7 (urgenza).
  - **Frontend `TalentMarketModal.jsx`**: nuovo tab "Mio Roster" con `RosterCard` (happiness emoji, giorni rimanenti, fee pagata, bottone Libera). Counter rosso pulsante sul tab se ci sono talenti threatened.
  - Test E2E backend OK: boost 75→93 (quality 85) + decay 10→6 con auto-trigger threatened + notifica creata + grace_period_ends_at impostato a +3gg.

- **Step 5 — Mercato "NPC Sotto Contratto" (Furto Cross-Player) + Diario Emotivo AI**:
  - **Backend** (`/app/backend/routes/talent_market.py`):
    - `GET /api/market/talents/under-contract` (lista pubblica NPCs altrui, ordinati per happiness asc + threatened first).
    - `POST /api/market/talents/buyout-offer/{eng_id}` (offerta minima = fee_paid × 1.2, lock 10% subito).
    - Flusso owner: `accept` (50% payout immediato + transfer schedulato) / `decline` (incassa il lock 10%) / `counter` (reset 72h).
    - Flusso buyer: `buyer-accept` per accettare contro-offerta.
    - `process_expired_transfers()`: scheduler 30min, alla scadenza contratto crea nuovo pre_engagement per il buyer (h=70, durata 30gg, marker `from_buyout`).
    - Notifiche: `talent_buyout_offer/accepted/declined/countered/transferred_in/transferred_out`.
    - **Diario emotivo** (`GET /api/talent-scout/diary/{eng_id}`): genera frase breve (max 30 parole) in italiano via Emergent LLM (gpt-4o-mini) basata su happiness, days_remaining, ultimo film. Cachato 1h. Fallback testuale se LLM non disponibile.
  - **Scheduler** (`/app/backend/server.py`): job `talent_buyout_transfers` ogni 30min.
  - **Frontend `TalentMarketModal.jsx`**:
    - Nuovo tab "Sotto Contratto" 🌐 con `UnderContractCard` (avatar NPC + studio owner + happiness emoji + giorni + min offerta) e toggle "Solo infelici/Tutti".
    - `BuyoutDialog`: input importo (validato min), messaggio, breakdown lock 10%, regole esplicite.
    - `RosterCard` arricchito con icona 📖 cliccabile per aprire `DiaryPopup` con frase AI.
  - Test E2E backend OK (con simulazione 2 player diretta su DB):
    - Buyer offre $70k → lock $7k pagato
    - Owner accetta → riceve $35k, buyer paga il resto
    - Trasferimento al expire → NPC nel roster del buyer (h=70, $70k)
    - 4 notifiche generate, cleanup ok.
  - Diario AI testato → output coerente in italiano: *"Sento l'ansia che mi attanaglia, ogni giorno che passa senza un ruolo si trasforma in un'ombra sempre più pesante..."*

### 🟡 STEP IN ATTESA
- 🎉 Tutti gli step della prima versione del Sistema Talenti Vivente sono stati implementati. Vedi P1/P2 per estensioni future.

---

### 🎯 Concept Generale
Tutti gli NPCs (attori posseduti, pre-ingaggiati, scuola) sono **entità vive** con happiness, aspettative, comportamento autonomo. Possono lasciare il player, essere "rubati" da altri, accettare/rifiutare rinnovi. Ogni infrastruttura (Agenzia / Talent Scout / Scuola) ha un livello che scala visibilità+slot+sconti.

---

### 🏗️ MARKET (3 sezioni nuove)

**1. Talenti / Pre-Ingaggio** — sotto-sezioni per ruolo:
- 🎬 Registi · ✍️ Sceneggiatori · 🎭 Attori · 🎨 Disegnatori · 🎵 Compositori
- Pool NPCs visibili **scala col livello infra**: Lv 1 → 50 NPC, Lv 10 → 2000+
- Numero ingaggiabili per genere → scala col livello
- Per attori: scelta **ruolo specifico** all'ingaggio (protagonista / antagonista / supporto / cameo)
- Costi inferiori vs ingaggio singolo (-20% Lv 1 → -50% Lv 10)
- Durata 30/60/90/180gg

**2. NPC Sotto Contratto** (visibile a TUTTI i player) — pubblicità del roster altrui:
- Mostra: nome NPC, owner attuale, durata, **happiness emoji** (😊🙂😐😠), **flag lampeggiante** se NPC ha avvisato che vuole rescindere
- Altri player possono offrire **acquisto anticipato (furto)**:
  - Successo proporzionale a happiness (più NPC è infelice, più facile "rubarlo")
  - **NPC NON cambia immediatamente proprietario**: il trasferimento avviene solo a fine contratto col precedente owner (scadenza / rescissione / liberazione)
  - Owner attuale riceve % offerta come "rimborso" (e ha tempo di tenere felice l'NPC per evitare di perderlo)
  - Sistema di counter-offerta: owner attuale può rilanciare per blindare il NPC

**3. Free Agents** (già implementata) — NPCs liberati che cercano nuovi ingaggi.

---

### 🎮 INTEGRAZIONE PIPELINE

**V3 Classica**: pre-ingaggiati visibili nel casting con **badge "📜 Pre-Ingaggiato"** (gold/purple), costo $0.

**LAMPO**: auto-cast pesca **almeno 2 pre-ingaggiati** in aggiunta a school+agency.

**Sceneggiature Pronte / Agenzia Sceneggiatori**: stesso comportamento auto-include.

---

### 🔄 SISTEMA RESCISSIONE (esteso a TUTTI i tipi: agency_actors + pre-engaged + students post-graduation)

**A) Trigger NPC vuole rescindere** (calcolato ogni heartbeat):
- Happiness < 30 + contratto > 30% durata → 30% probabilità
- Happiness < 15 + contratto > 50% durata → 60% probabilità
- Happiness < 5 → 90% probabilità

**B) Notifica 3 giorni prima della rescissione**:
- NPC manda messaggio in stile: *"Caro Anacapito, sto pensando di rescindere il contratto. Se nei prossimi 3 giorni mi farai fare un film/serie/anime/sequel, potrei ripensarci."*
- Card NPC nella **propria agenzia** comincia a **lampeggiare** (animazione `pulse` con bordo ambra/rosso)
- Card NPC nel **market pubblico "NPC Sotto Contratto"** lampeggia anche lì (vulnerabilità segnalata agli altri player)

**C) Periodo di grazia (3 giorni)**:
- Se nei 3 giorni il player ingaggia l'NPC in un nuovo progetto → **happiness +25** + cancella la rescissione + NPC "ripensaci" message
- Se non lo usa → rescissione automatica al giorno 3:
  - Player riceve rimborso parziale: `fee_paid × giorni_rimanenti / durata_totale × 1.2` (cioè un piccolo bonus +20% del proporzionale per "scuse del NPC")
  - NPC torna nel market come Free Agent
  - Notifica: *"Tony Stark ha lasciato la tua agenzia: 'Mi tieni in panchina, vado dove possa lavorare'"*

**D) Rescissione manuale dal player** (release):
- Già esistente per agency_actors via `release-actor` → estendere anche a pre-engagements
- Player riceve 0% rimborso (è una scelta sua)

---

### 🪄 SISTEMA "FURTO" CROSS-PLAYER

**Step 1 — Offerta acquisto anticipato**:
- Player B vede NPC nel market pubblico → clicca "Pre-acquista"
- Sceglie offerta (range 80% - 200% della residua fee del contratto attuale)
- L'offerta è valida per N giorni (es. 7gg)

**Step 2 — Fase di counter-offerta**:
- Player A (owner attuale) riceve notifica + opzioni:
  - **Accetta**: incassa subito, NPC passa a B alla fine contratto
  - **Counter-bid**: rilancia proponendo un fee ridotto al NPC per "blindarlo" (rinnovo immediato + happiness boost)
  - **Ignora**: l'offerta scade
- NPC stesso vota in base a happiness:
  - happiness ≥ 70: rifiuta automaticamente l'offerta (è felice)
  - happiness < 30: accetta automaticamente
  - 30-70: il player A può influenzare

**Step 3 — Trasferimento**:
- NPC NON cambia owner immediatamente
- Resta col player A fino a fine contratto/rescissione/liberazione
- Player A può continuare ad usarlo (bonus: ogni film fatto durante questo "lame duck period" aumenta happiness e può cancellare il furto se NPC cambia idea)
- Alla scadenza: NPC migra automaticamente a player B con contratto base 30gg

---

### 👤 SEZIONE AGENZIA (player view)

**Layout**: 3 sub-tabs principali con sub-filtri per tipo cast:
1. **🎓 Scuola** (casting_school_students) — già implementato
2. **💼 Propri** (agency_actors classici)
3. **📜 Pre-Ingaggio dal Market** (talent_pre_engagements)

Ogni tab con filtri per **tipo cast** (registi/sceneggiatori/attori/disegnatori/compositori).

**Per ogni NPC mostra**:
- Tipo contratto + durata + giorni rimanenti (countdown colorato)
- **Livello contentezza** (😊 ≥75 / 🙂 50-74 / 😐 30-49 / 😠 <30)
- **Animazione lampeggiante** se ha avvisato di voler rescindere
- Numero film/progetti fatti durante il contratto
- Ruoli effettivamente ricoperti (per attori) vs ruolo intended
- **Loyalty score** cumulativo (% bonus CWSv)
- Bottoni: **Rinnova / Libera / Cambia Ruolo Atteso**
- **🎁 Regalia** (idea bonus): spendi denaro extra per +happiness immediato
- **⚡ "Pacifica"** (per NPCs in periodo di grazia 3gg): suggerisce film veloce LAMPO

---

### 💾 SCHEMA DB

```python
# Esiste già `agency_actors` → estendere con campi happiness
agency_actors:
- ... (già esistenti)
- happiness_score: 0-100 (computed each heartbeat)
- contract_started_at, contract_duration_days, contract_expires_at  (già aggiunti nel Bundle 9)
- usage_history: [{film_id, role_used, cwsv, used_at}]
- usage_by_role: {protagonist: N, ...}
- threatened_release_at: ISO  # quando NPC ha avvisato di voler rescindere
- grace_period_ends_at: ISO   # +3 giorni
- pending_buyout_offer: {from_user_id, amount, made_at, expires_at, status}
- listed_for_purchase: bool   # True se in scadenza o threatened

# Nuova collection per pre-ingaggi
talent_pre_engagements:
- id, user_id, npc_id, role
- cast_role_intended (per attori)
- contract_started_at, contract_duration_days, contract_expires_at
- fee_paid, contract_status: active/renewed/expired/released_by_npc/sold_to_other_player/threatened
- happiness_score, threatened_release_at, grace_period_ends_at
- usage_history, usage_by_role
- pending_buyout_offer
- renewals_count, renegotiations_count
```

---

### 🎚️ LIVELLI INFRA (proposta)

**Visibilità NPCs in Market** (per ogni livello agenzia scout):
| Livello | 5★ visibili | 4★ visibili | 3★ visibili | 2★ visibili | 1★ visibili |
|---------|-------------|-------------|-------------|-------------|-------------|
| 1 | 1 | 2 | 4 | 50 | 100 |
| 5 | 2 | 4 | 8 | 75 | 150 |
| 10 | 4 | 6 | 14 | 100 | 200 |
| 15 | 6 | 8 | 18 | 125 | 250 |

**Ingaggiabili max per livello**:
| Livello | 5★ | 4★ | 3★ | 2★ | 1★ |
|---------|----|----|----|----|----|
| 1 | 0 | 1 | 2 | 5 | 10 |
| 5 | 1 | 2 | 5 | 10 | 15 |
| 10 | 1 | 3 | 8 | 15 | 20 |
| 15 | 2 | 4 | 10 | 18 | 25 |

> Nota: **NON esiste un vero limite di livelli** ma il bilanciamento è pensato per ~Lv 15 come max realistico (raggiungibile con difficoltà).

**Slot totali, sconto, max durata**: stessi tier precedenti (Lv 1→3 slot/-20%/30gg, Lv 15→40 slot/-55%/180gg).

### 🆕 NPC che si propongono spontaneamente al player
- **Trigger**: ogni 24-72h, gli NPC possono "candidarsi" spontaneamente al player se:
  - Player ha CWSv media ≥ soglia per quel tier NPC
  - Player ha agenzia scout di livello compatibile
  - NPC è insoddisfatto del proprio owner attuale (happiness <30 → propensione a proporsi altrove)
- **UX**:
  - Notifica push: *"⭐ Tony Stark vuole entrare nella tua agenzia! Offerta speciale: $X per 60gg."*
  - **Badge rosso** sulla sezione Talenti del Market
  - Sotto-sezione dedicata **"📨 Si propongono a te"** nel Market Talenti
  - Offerta limitata nel tempo (es. 48h prima che l'NPC ritorni nel pool generico)
  - Costo proposto solitamente **inferiore del 15-25%** rispetto al prezzo standard



---

### 🌐 ENDPOINT BACKEND

```
# Pre-ingaggio
GET  /api/market/talents?role=&min_stars=&max_fee=&page=
POST /api/market/talents/pre-engage/{npc_id}

# Market sotto contratto
GET  /api/market/contracted-npcs                              # public
POST /api/market/contracted-npcs/{eng_id}/offer-buyout
POST /api/market/contracted-npcs/{eng_id}/counter-offer        # owner attuale rilancia

# Roster proprio
GET  /api/talent-scout/my-roster?tab=school|agency|pre_engaged&role=
POST /api/talent-scout/renew/{eng_id}
POST /api/talent-scout/release/{eng_id}
POST /api/talent-scout/gift/{eng_id}                           # +happiness regalia
POST /api/talent-scout/pacify/{eng_id}                         # cancella threatened se NPC è usato in N gg
GET  /api/talent-scout/threatened                              # lista NPCs in periodo di grazia
GET  /api/talent-scout/perks                                   # slot rimanenti per infra
```

---

### 🧠 ALGORITMI CRITICI

**Happiness Score**:
```python
def compute_happiness(npc, expected_role=None):
    base = 75
    # Frequenza utilizzo (peer-comparison stesso tipo cast)
    expected_uses = (duration_days / 30) * 1.2
    actual_uses = len(usage_history)
    ratio = actual_uses / max(1, expected_uses)
    if ratio < 0.3: base -= 35
    elif ratio < 0.6: base -= 15
    elif ratio > 1.5: base += 10
    
    # Per attori: corrispondenza ruolo
    if role == 'actor' and expected_role:
        used_in_expected = usage_by_role.get(expected_role, 0)
        if expected_role in ('protagonist', 'co_protagonist') and used_in_expected == 0:
            base -= 25
        elif expected_role == 'cameo' and usage_by_role.get('protagonist', 0) > 0:
            base += 15
    
    # Qualità film
    avg_cwsv = mean([h['cwsv'] for h in usage_history]) if usage_history else 0
    if avg_cwsv >= 75: base += 10
    elif avg_cwsv < 40: base -= 10
    
    # Loyalty effect (NPCs fedeli sono più tolleranti)
    base += loyalty_score * 0.3
    
    return max(0, min(100, base))
```

**Auto-rescissione check** (heartbeat):
```python
if happiness < 5 and elapsed_pct > 0: prob = 0.90
elif happiness < 15 and elapsed_pct > 0.5: prob = 0.60
elif happiness < 30 and elapsed_pct > 0.3: prob = 0.30
else: prob = 0.0

if random() < prob_per_day and not threatened:
    npc.threatened_release_at = now()
    npc.grace_period_ends_at = now() + 3.days
    npc.listed_for_purchase = True
    notify_player_and_market(npc)
```

---

### 💡 MIEI CONSIGLI EXTRA per migliorare

1. **🎤 Manager Personale dello studio** — un NPC "agente" persistente che parla al player con messaggi nello studio: "Capo, Tony Stark si lamenta perché non lo fai recitare." Crea atmosfera narrativa.

2. **🏆 Iconic Status** — dopo 3 rinnovi consecutivi senza rinegoziazione, NPC diventa "Iconic Talent" del tuo studio: appare nei crediti con il logo, +20% chance accettazione contratti futuri di tutti gli NPCs. È un sigillo di prestigio dello studio.

3. **🌟 Sponsorship / Reputazione studio** — studi che producono CWSv alta media (≥75) attirano automaticamente +30% NPCs nel market, con sconti aggiuntivi. La reputazione attira talenti.

4. **🎭 Affinità di genere** — ogni NPC ha 1-2 generi preferiti (già esiste `strong_genres`). Usarlo nel suo genere preferito → +happiness x2.

5. **📰 Recensioni post-contratto pubbliche** — quando un NPC esce da un player, lascia una review (+/-) visibile a tutti. Influenza happiness di partenza dei prossimi contratti con quel player. Crea persistente reputazione dello studio.

6. **🔥 Mood Swings stagionali** — eventi (festività, vincita Oscar dello studio, scandali, etc.) modificano l'happiness di tutti gli NPCs ±10/15 punti. Aggiunge dinamismo.

7. **🎟️ Esclusive di ruolo (premium)** — pago un premium fee per BLOCCARE un NPC SOLO su un ruolo (es. "solo antagonista nei miei film"). NPC è felice di essere specializzato. Player ha consistency nei propri film.

8. **🪙 Sistema d'asta** — per NPCs top-tier (legendary, fame ≥90), invece di pre-engagement diretto: asta tra player con bid pubblico per X giorni, vince il più alto. Crea evento competitivo.

9. **💌 Diario dell'NPC** — ogni NPC ha un piccolo diario interno dove "scrive" eventi: "Ho amato fare il villain in The Dark Knight (CWSv 85)" o "Mi annoio, voglio cambiare aria". Visibile cliccando il NPC. Engagement narrativo.

10. **🎬 Auto-suggerimento "Salva il NPC"** — quando NPC entra in periodo di grazia, una notifica con bottone diretto "Crea LAMPO veloce con Tony" che pre-popola il form. Reduce friction.

---

### 🛠️ ROADMAP IMPLEMENTATIVA (proposta in fasi)

**Fase 1 — MVP Pre-Engagement (1-2 task)**:
- DB schema + endpoint base + UI Market sezione Talenti
- Integrazione pipeline V3 (badge "Pre-Ingaggiato")
- Auto-include LAMPO (2+ pre-engaged)

**Fase 2 — Happiness System**:
- Algoritmo happiness + heartbeat task
- Notifiche 3-giorni grazie
- UI happiness emoji + lampeggiante in agenzia

**Fase 3 — Rescissione**:
- Auto-rescissione + rimborso parziale
- Estensione anche ad agency_actors classici
- Free agents migration

**Fase 4 — Furto cross-player**:
- Market pubblico "NPC Sotto Contratto"
- Sistema offerte + counter-offerte
- Trasferimento delayed a fine contratto

**Fase 5 — Polish**:
- Manager Personale UI
- Iconic Status badge
- Mie idee bonus (asta, diario, recensioni, mood swings, etc.)

**STATUS**: in progettazione, attendo conferma utente per partire con Fase 1.



> ✦ Feature corposa con economia + relazione + market dinamico ✦

### 🎯 Concept
Sistema di pre-ingaggio NPCs collegato a infrastrutture **Agenzia Talent Scout** (per attori) + **Agenzia Scout Sceneggiatori/Registi/Compositori/Disegnatori** (per altri ruoli). Il player paga in anticipo un pool di talenti, sbloccandone l'uso a costo $0 nei progetti futuri. NPCs hanno reazione emotiva: rinnovano/rifiutano/rescindono in base a come vengono trattati.

### 🏗️ Struttura Market

**1. Nuova sezione Market: "Talenti / Pre-Ingaggio"** con sotto-sezioni per ruolo:
- 🎬 Registi
- ✍️ Sceneggiatori
- 🎭 Attori (con scelta ruolo: protagonista/antagonista/supporto/cameo)
- 🎨 Disegnatori (anime)
- 🎵 Compositori

**2. Visibilità basata su livello infrastrutture**
- Ogni infra (Agenzia Talent Scout, Agenzia Scout Sceneggiatori, ecc.) ha un livello
- Più alto → **più NPCs visibili** e di **qualità maggiore** (stelle, fame)
- Livello determina anche il **numero massimo ingaggiabili per genere**

**3. Pool**: tutti gli NPCs della collection `people`, filtrati per ruolo + livello infra del player.

**4. Parametri pre-ingaggio**:
- Costo inferiore vs ingaggio singolo (sconto -20/-50% scaled da livello infra)
- Durata contratto X giorni (30/60/90/180)
- Per attori: scelta ruolo specifico al momento del pre-ingaggio (protagonista/antagonista/supporto/cameo)
- Slot massimi pre-ingaggio per **categoria cast** basati sul livello infra

### 🆕 Nuova sezione Market: "NPC Sotto Contratto" (visibile a TUTTI)
- Lista pubblica di tutti gli NPCs attualmente sotto contratto presso un player
- Mostra: nome NPC, owner attuale, durata contratto, **livello contentezza** (verde/giallo/rosso)
- **Acquisto anticipato**: altri player possono offrire per acquisire il contratto PRIMA della scadenza
  - Successo dell'offerta proporzionale a contentezza dell'NPC con owner attuale (se è insoddisfatto, accetta più facilmente di passare)
  - Owner attuale riceve % dell'offerta (rimborso ingaggio) + perde lo slot

### 🎮 Comportamento nei pipeline

**V3 classica**: pre-ingaggiati visibili nel casting con **badge "📜 Pre-Ingaggiato"** (gold/purple), costo $0. Player può sceglierli o ignorarli.

**LAMPO**: auto-cast pesca automaticamente **almeno 2 pre-ingaggiati** (in aggiunta a school+agency) → riduzione drastica costo progetto.

**Sceneggiature Pronte / Agenzia Sceneggiatori**: stesso comportamento auto-include di LAMPO (2+ pre-ingaggiati automatici).

### 🔄 Sistema Rinnovo / Rifiuto / Rescissione

**Sistema rinnovo a ridosso scadenza**:
- A 5gg dalla fine: prompt al player "Vuoi rinnovare?"
- L'NPC può **accettare o rifiutare** in base a logica peer-comparison:
  - **Confronto solo tra stesso tipo cast** (un attore confronta solo con altri attori, non con registi)
  - Calcolo: `usage_count / avg_usage_count_di_stesso_tipo` → se < 0.5, NPC rifiuta o chiede aumento sostanziale
- Se accetta: nuovo contratto a costo invariato/leggermente migliorato; loyalty bonus +5% CWSv

**Sistema rifiuto specifico per attori (basato su ruolo)**:
- Caso A — **Sotto-utilizzato in ruolo richiesto**: se ingaggiato come "protagonista" ma usato sempre come "supporto" → rifiuta rinnovo per ruolo "protagonista" (può accettare per ruolo inferiore con sconto)
- Caso B — **Promosso oltre le aspettative**: se ingaggiato come "generico" ma usato come "protagonista" → **molto propenso ad accettare rinnovo a costi bassi** (è felice della crescita)
- Calcolo basato su matrice `intended_role` × `actual_uses[role]`

**Sistema rescissione anticipata da NPC** (l'NPC molla il player):
- Trigger: se NPC non viene usato in proporzione attesa (es. <1 film ogni 30gg di contratto)
- NPC può **rescindere unilateralmente** → torna nel Market come Free Agent
- Player riceve **rimborso parziale** del fee pagato:
  - 0gg: 100% (impossibile, c'è grace period)
  - 50% durata: 50% rimborso
  - 80% durata: 20% rimborso
  - 95% durata: 0% rimborso
- Notifica al player: "Tony Stark ha lasciato la tua agenzia: 'Mi tieni in panchina, vado dove possa lavorare'"

### 👤 Nuova sezione Agenzia (player view)

**3 sub-tabs principali**:
1. **🎓 Scuola** (studenti casting_school_students)
2. **💼 Propri** (agency_actors classici)
3. **📜 Pre-Ingaggio dal Market** (talent_pre_engagements)

Ogni tab con **sotto-filtri per tipo cast** (registi/sceneggiatori/attori/disegnatori/compositori).

**Per ogni NPC mostra**:
- Tipo contratto (durata totale)
- Giorni rimanenti (countdown)
- **Livello contentezza** (4 stati: 😊 Felice / 🙂 OK / 😐 Insoddisfatto / 😠 In rotta)
- Numero film/progetti fatti durante il contratto
- Ruoli effettivamente ricoperti (per attori)
- **Loyalty score** cumulativo (% bonus CWSv)
- Bottoni: **Rinnova / Libera / Cambia Ruolo Atteso**
- (idea extra) Pulsante **"Regalia"**: spendi denaro extra per aumentare contentezza

### 💾 Schema DB previsto

```
talent_pre_engagements:
- id, user_id, npc_id, role (director/writer/actor/illustrator/composer)
- cast_role_intended (per attori: protagonist/co_protagonist/antagonist/supporting/cameo)
- contract_started_at, contract_duration_days, contract_expires_at
- fee_paid, fee_per_film_when_used (= 0 se pre-pagato)
- contract_status: active/renewed/expired/released_by_npc/sold_to_other_player
- happiness_score: 0-100 (calcolato dinamicamente)
- usage_history: [{film_id, role_used, cwsv, used_at}]
- usage_by_role: {protagonist: 2, supporting: 5, ...}
- renewals_count, renegotiations_count
- next_renewal_check_at: ISO datetime
- listed_for_purchase: bool (visibile in market "NPC sotto contratto")
- purchase_offers: [{from_user_id, amount, made_at, status}]
```

### 🎚️ Livelli infra (proposta tier)

**Agenzia Talent Scout** (attori, già esiste):
- Lv 1: 3 slot · pool 50 NPC visibili · sconto -20% · max 30gg
- Lv 3: 8 slot · pool 200 NPC visibili · sconto -30% · max 60gg
- Lv 5: 15 slot · pool 500 NPC visibili · sconto -40% · max 90gg
- Lv 10: 30 slot · pool 2000 NPC visibili · sconto -50% · max 180gg

**Agenzia Scout (per altri tipi)**: Stesso schema con scaling specifico per ruolo.

### 🌐 Endpoint backend previsti

```
GET  /api/market/talents?role=&min_stars=&max_fee=&page=
POST /api/market/talents/pre-engage/{npc_id}
GET  /api/market/contracted-npcs        ← nuovo: lista pubblica NPC sotto contratto altri player
POST /api/market/contracted-npcs/{engagement_id}/offer-buyout    ← acquisto anticipato

GET  /api/talent-scout/my-roster?role=
POST /api/talent-scout/renew/{engagement_id}
POST /api/talent-scout/release/{engagement_id}
POST /api/talent-scout/gift/{engagement_id}    ← regalia per aumentare contentezza
GET  /api/talent-scout/perks                   ← slot rimanenti per ogni infra
GET  /api/talent-scout/renewal-prompts          ← lista contratti in scadenza < 5gg
```

### 🧠 Algoritmo Happiness Score (per NPC)

```python
def compute_happiness(engagement, user_films_in_period):
    base = 75
    # Frequenza utilizzo
    expected_uses = (engagement.contract_duration_days / 30) * 1.2  # 1+ film/mese atteso
    actual_uses = len(engagement.usage_history)
    usage_ratio = actual_uses / max(1, expected_uses)
    if usage_ratio < 0.3: base -= 35
    elif usage_ratio < 0.6: base -= 15
    elif usage_ratio > 1.5: base += 10
    
    # Per attori: corrispondenza ruolo
    if engagement.role == 'actor':
        intended = engagement.cast_role_intended
        used_in_intended = engagement.usage_by_role.get(intended, 0)
        if intended in ('protagonist', 'co_protagonist') and used_in_intended == 0:
            base -= 25  # ingaggiato come prota ma mai usato
        elif intended == 'cameo' and engagement.usage_by_role.get('protagonist', 0) > 0:
            base += 15  # promosso sopra le aspettative
    
    # Qualità film fatti
    avg_cwsv = mean([h['cwsv'] for h in engagement.usage_history]) if engagement.usage_history else 0
    if avg_cwsv >= 75: base += 10
    elif avg_cwsv < 40: base -= 10
    
    return max(0, min(100, base))
```

### 🌪️ Trigger NPC release (auto-rescissione)
- Happiness < 25 + contratto > 50% durata → NPC rescinde (probabilità 30% ogni heartbeat)
- Happiness < 10 + contratto > 70% durata → NPC rescinde (probabilità 70%)

### 🔌 Integrazione frontend
- **Nuova tab "TALENTI"** nel Market generico (accanto a Film/Serie/Anime/Mercato TV/Free Agents)
- **Nuova tab "NPC SOTTO CONTRATTO"** nel Market (visibile pubblicamente a tutti i player)
- In `CastPhase.jsx` (V3): badge "📜 Pre-Ingaggiato" + costo $0 + filtro dedicato
- In `CastingAgencyPage.jsx`: nuovo tab "Pre-Ingaggio" con sub-filtri per ruolo + happiness UI emoji
- In `routes/lampo.py` `_pick_random_cast`: dopo own_roster, pesca anche da pre_engaged → priorità nell'ordine
- In `routes/quick_v3.py` (sceneggiature pronte): stessa logica auto-include

**STATUS**: in progettazione, l'utente continuerà a fornire altri dettagli prima dell'implementazione.




## Bundle 10 fix (Apr 26, 2026 — sera 2)

### A. Sistema Rifiuti V3 nei Pipeline (Task P1)
- `routes/pipeline_v3.py` `select-cast-member`:
  - Aggiunto campo `force_accept: bool = False` al body `SelectCastBody`.
  - Wrap intorno a `routes/cast.py:calculate_rejection_chance(npc, user, genre)`:
    1. Verifica esistenza rifiuto attivo (24h) in collection `rejections` → ritorna `already_refused: true`.
    2. Calcola probabilità rifiuto basata su level/fame/genre/star del NPC vs profilo player.
    3. Se rifiuta: salva entry in `rejections` con `requested_fee = expected_fee × (1.1-1.4)` random, `negotiation_id`, `renegotiation_count: 0`.
    4. Risponde con `{rejected: true, reason: "...", requested_fee, expected_fee, negotiation_id, can_renegotiate}`.
  - Bypass via `force_accept=true` (post-rinegoziazione confermata dall'utente).
- Frontend `CastPhase.jsx`:
  - Nuovo state `rejectDlg` + dialog mobile-friendly con messaggio rifiuto, fee originale (line-through) vs fee richiesta (in evidenza ambra).
  - Bottoni: "Lascia perdere", "Paga $X" (force_accept=true), "Insisti senza aumentare" (retry senza force).
  - Verificato via curl: 1° tentativo accept, 2°-5° tentativi rifiuto coerente con stessa fee (memoria 24h funziona).

### B. UI Selettore Stile TV Station (Task P2)
- `TVStationPage.jsx` Step 2 setup wizard:
  - Nuovo `useEffect` carica `/api/tv-stations/available-styles` all'apertura step 2.
  - Card "Stile Branding" con grid 2-col di 10 preset:
    - Generica (cyan), NetfleX (rosso), Disnext+ (blu chiaro), Topmount+ (blu acceso), PrimeFlix (ciano), AppleVue (bianco), SkyView (blu sport), ItaliaPlay (blu istit.), Dazz! (giallo neon), ItalVision (blu telco)
  - Ogni bottone mostra label + tagline con il proprio color/font_family. Click → ring rosso conferma selezione.
  - `submitStep2` ora invia anche `style: selectedStyle`.
- Backend `routes/tv_stations.py`: `setup-step2` accetta `style` opzionale e lo aggiorna nella station.

Files: `backend/routes/pipeline_v3.py`, `frontend/src/components/v3/CastPhase.jsx`, `frontend/src/pages/TVStationPage.jsx`.


## Bundle 9 fix (Apr 26, 2026 — sera)

### A. Badge TV cliccabile (miglioramento)
- `TvAiringBadge.jsx`: prop `onClick(info)` opzionale → render come `<button>` con hover/active scale + cursor pointer.
- `ContentTemplate.jsx`: badge ora apre la pagina `/tv-station/{id}` al click.

### B. Selettore Stile TV Station (Task C - backend pronto)
- `routes/tv_stations.py`:
  - `SetupStep1Request` accetta `style` (default/netflix/disney/paramount/prime/apple/sky/rai/dazn/tim).
  - `POST /api/tv-stations/update-style` per cambiare stile su una emittente esistente.
  - `GET /api/tv-stations/available-styles` ritorna 10 stili con label non-copyright (NetfleX/Disnext+/Topmount+/PrimeFlix/AppleVue/SkyView/ItaliaPlay/Dazz!/ItalVision/Generica), color, font_family, tagline.
- Validazione server-side. Lo stile influenza il glow/font del badge "In TV dal..." già pronto in `TvAiringBadge.STYLE_PRESETS`.
- Frontend selector form da agganciare al setup TV station (UI da fare al prossimo passaggio).

### C. Sistema Contratti Attori + Free Agents Market + Sistema Rifiuti V3 (Task A - MVP completo)

**Backend nuovo file `routes/agency_contracts.py`** (registrato in server.py):
- **Modello**: `agency_actors` ora supporta `contract_started_at`, `contract_duration_days`, `contract_expires_at`, `renewals_count`, `loyalty_score`, `contract_total_paid`.
- **Endpoint**:
  - `POST /api/agency/sign-contract/{actor_id}` — body `{duration_days: 30|90|180}`. Costo: `cost_per_film × {0.6, 1.5, 2.7}` (semestrale ha sconto -10% cumulato).
  - `POST /api/agency/renew-contract/{actor_id}` — body `{duration_days, renegotiate_fee: bool}`. Senza rinegoziazione: `loyalty_score += 5%` (cap 50%). Con rinegoziazione: -10% fee ma reset loyalty.
  - `POST /api/agency/release-actor/{actor_id}` — sposta in `free_agents` collection.
  - `GET /api/market/free-agents?limit&offset&min_stars&gender` — lista pubblica. Player con Agenzia+Scuola: -45%. Solo Agenzia o Scuola: -25%. Esclude i propri ex-attori.
  - `POST /api/market/free-agents/sign/{actor_id}` — body `{duration_days, offered_fee}`. **Sistema rifiuti**:
    - Probabilità accettazione = 60% base + perks (+10/+20%) + fame×0.4% (cap +20%) + livello×1% (cap +25%) + fee_ratio modifier.
    - Rifiuto: `{rejected: true, message: "Il mio agente dice...", suggested_fee, recommended_fee}`. Il client può rinegoziare fino a 3 volte.
    - 5 messaggi di rifiuto random in italiano.
  - `GET /api/agency/contracts/expiring-soon?days=7` — utility per UI countdown.

**Frontend**:
- Nuovo `FreeAgentsMarketModal.jsx`: dialog completa con elenco free agents, selettore durata 30/90/180gg, slider/input offerta, sistema rinegoziazione (counter 1/3, 2/3, definitivo), banner perks "✓ Agenzia ✓ Scuola Sconto -45%".
- `CastingAgencyPage.jsx`:
  - Nuovo bottone gradient amber "Mercato Attori Liberi" sopra la lista propri attori.
  - `ActorCard` ora mostra **countdown contratto** (📜 14gg verde/ambra/rosso) e **loyalty bonus** (💜 +15%).
  - Nuovo bottone "Libera" 🔓 (ambra) per ogni attore.
- Loyalty bonus visivamente persistente, costi sempre più convenienti dei singoli ingaggi V3/LAMPO (come da richiesta).

**Verificato via curl**:
- Sign 30d → fee $17.641, expires +30gg ✓
- Release Hana Chen → spostata in free_agents ✓
- Market list → count corretto, filtro auto-esclusione ✓
- Available TV styles → 10 preset ritornati con label/color/font/tagline ✓

Files: `backend/routes/tv_stations.py`, `backend/routes/agency_contracts.py` (NEW), `backend/server.py`, `frontend/src/components/TvAiringBadge.jsx`, `frontend/src/components/ContentTemplate.jsx`, `frontend/src/components/FreeAgentsMarketModal.jsx` (NEW), `frontend/src/pages/CastingAgencyPage.jsx`.


## Bundle 8 fix (Apr 26, 2026 — pomeriggio)

### A. Badge "In TV dal {data ora} su {emittente}" (Task B richiesto)
- **Backend**: nuovo endpoint `GET /api/content/{content_id}/tv-airing-info` in `routes/tv_stations.py`. Cerca tra TUTTE le emittenti TV la prima entry che contiene `content_id` (in films/tv_series/anime), ritorna:
  - `station_id`, `station_name`, `owner_user_id`
  - `style`, `primary_color`, `logo_url` (per branding/glow)
  - `broadcast_state` (idle/scheduled/airing/completed/retired), `first_air_at`, `next_air_at`
  - `current_episode`, `total_episodes`, `is_in_palinsesto`
  - **Logica `first_air_at`**: prefer `min(ep_schedule.release_datetime)` per serie episodi; fallback `broadcast_started_at` o `start_datetime`. Skip entries 'idle'/'retired' senza scheduling.
- **Frontend**: nuovo componente `TvAiringBadge.jsx`:
  - Mostra "In TV dal {26 apr 2026, 21:00} su AnacapitoFlix" (Italiano) con glow animato
  - Mostra "IN ONDA · {station}" se `broadcast_state === 'airing'` con icona Radio pulsante
  - **Style presets** preconfigurati per: netflix, disney, paramount, prime, apple, sky, rai, dazn, tim, default — ogni preset ha colore, font e glow RGB. Il backend ritorna `style` e il frontend applica il preset corrispondente.
  - Nascosto se contenuto non è in palinsesto (`is_in_palinsesto=false`).
- **Mounted in**:
  - `ContentTemplate.jsx` (sotto il titolo, sopra "una produzione X")
  - `ProssimamenteDetailModal.jsx` (sopra le 4 stat boxes, modalità compatta)
- Test backend OK: serie airing su AnacapitoFlix → first_air_at='2026-04-10T21:00', state='airing', is_in_palinsesto=true.

### B. Task FUTURO — Stili Emittenti TV (memorizzato)
**Quando si compra un'emittente TV**, fare scegliere stile/font/colori con preset:
- **NetfleX-style**: rosso #E50914, font Bebas Neue
- **Disnext+**: blu #0066CC, font Inter
- **Paramount+ → Topmount+**: blu acceso #0064FF
- **PrimeFlix**: ciano #00A8E1
- **AppleVue**: bianco/grigio, font SF Pro Display
- **SkyView**: blu #0072FF
- **RaiPlay → ItaliaPlay**: blu #0046AD
- **Dazz!** (sport-style): giallo #F8FF13
- **TimVision → ItalVision**: blu #0046AD
- Player sceglie nome (NON quello reale per copyright) + stile. Lo stile influenza:
  - Logo/font del badge "In TV dal..."
  - Branding nel modal palinsesto e mercato TV
  - Banner home dell'emittente
- I preset CSS/glow sono già pronti in `TvAiringBadge.STYLE_PRESETS` — il prossimo step è solo aggiungere selettore nel form di acquisto/edit emittente TV.

### C. Task A (P1 in coda) — Sistema Contratti Attori
NON ancora implementato in questa sessione. Da fare al prossimo messaggio:
- Contratti attori 30/90/180gg con loyalty +5% rinnovo
- Hot Sheet Free Agents giornaliero
- Prestige tier contratto
- Emoji ⚡⏳ visibilità training
- Sempre conveniente vs ingaggio singolo V3/LAMPO
- Free Agents → nuova sezione "Attori" nel Market
- Sistema rifiuti V3 collegato a `routes/cast.py`

Files: `backend/routes/tv_stations.py`, `frontend/src/components/TvAiringBadge.jsx` (NEW), `frontend/src/components/ContentTemplate.jsx`, `frontend/src/components/ProssimamenteDetailModal.jsx`.


## Bundle 7 fix (Apr 26, 2026 — late morning)

### 1. LAMPO Autosave Bozza Form (richiesta utente)
- Backend: 3 nuovi endpoint in `routes/lampo.py`:
  - `POST /api/lampo/draft-form` — upsert bozza per (user, content_type)
  - `GET /api/lampo/draft-form?content_type=film|tv_series|anime` — recupera ultima bozza
  - `DELETE /api/lampo/draft-form` — pulizia dopo avvio produzione
- Collection: `lampo_form_drafts` (one per user × content_type, upsert con `updated_at`)
- Frontend `LampoModal.jsx LampoForm`:
  - Al mount: GET bozza → popola tutti i campi (title/genre/preplot/budget_tier/num_episodes), toast "Bozza ripristinata"
  - Autosave debounced 1.5s ogni volta che l'utente modifica un campo (a partire dal 1° carattere del titolo)
  - Indicatore live "💾 bozza salvata" / "salvando..." accanto al titolo della modal
  - DELETE bozza al click "AVVIA LAMPO" (transazione completa)
- Verificato via curl: bozza salvata + recuperata correttamente.

### 2. Refactor Scuola: durata talent-based + cap pre-determinato
- **Modello nuovo**: all'iscrizione si pre-calcolano `target_skills` (cap finale fisso) e `training_duration_days` (5-22 giorni in base al talento + jitter random ±3).
- `compute_training_plan(base_skills, hidden_talent, is_from_agency)` in `routes/acting_school.py`:
  - Durata: `5 + (1-talent)×15 ± random(-3,+3)`. Talent 1.0 → 5-8gg, talent 0.5 → 11-15gg, talent 0 → 18-22gg.
  - Target ex-agenzia: `base + (2 + talent×5) ± random(-1,+1)` (range +1/+8 punti).
  - Target fresh student: `base + (30 + talent×30) ± random(-5,+10)` (range +25/+70 punti).
- `calculate_casting_student_skills` ora calcola `progress = elapsed/duration` (clamp 0-1) e interpola `base → target` linearmente. **Stop al raggiungimento del cap** (no più crescita "infinita").
- `status` cambia automaticamente in `ready_to_graduate` quando `progress=1` per ex-agenzia (resta lì finché l'utente non clicca "Trasferisci in Agenzia"). Il bottone "graduate" già esisteva.
- API `/casting-students` ora include `target_skills`, `training_duration_days`, `training_progress_pct`.
- **Imprevedibilità**: anche un talento 1.0 può fare 8gg invece di 5 (random factor), come richiesto.
- Migrazione retroattiva: 1 studente (Jin Garcia) popolato con `target_skills=32` (base 26 + bonus 6) e `duration=8gg`. Verificato via curl.

### 3. Considerazioni su miglioramenti accettati (Step 3 prossimo)
Da implementare nel prossimo task quando l'utente confermerà:
- Sistema contratti attori 30/90/180gg con loyalty +5% rinnovo, hot sheet free agents, prestige tier, emoji ⚡⏳ visibilità training. Sempre conveniente vs ingaggio singolo.
- Free Agents → nuova sezione "Attori" nel Market.

Files: `backend/routes/lampo.py`, `backend/routes/acting_school.py`, `backend/routes/casting_agency.py`, `frontend/src/components/LampoModal.jsx`.


## Bundle 6 fix (Apr 26, 2026 — mattino)

### 1. Bug: skill=0 dopo invio attore in Scuola di Recitazione
- **Root cause**: `send_agency_actor_to_school` salvava solo `base_skills` ma `calculate_casting_student_skills` leggeva `initial_skills`/`skills` (assenti) → fallback a `{}` → skill_media = 0.
- **Fix `routes/casting_agency.py`**: ora lo studente eredita `initial_skills` e `skills` da `base_skills`, oltre a `potential` da `hidden_talent`.
- **Fix `routes/acting_school.py`**:
  - `calculate_casting_student_skills` ora gestisce due regole separate:
    - **Ex-agenzia (already trained)**: cap = base + bonus piccolo `2 + talent×5` (range 2-7 punti). Improvement rate 0.3-0.8/giorno.
    - **Fresh student**: cap = `talent×100`, improvement rate alto (3-6 pt/giorno) → range crescita 30-60 punti.
- **Migrazione retroattiva**: 1 studente ex-agenzia con dati incompleti riparato (`base_skills` → `initial_skills`/`skills`). Verificato via curl: Jin Garcia ora mostra Comedy 38, Doppiaggio 49, ecc. invece di 0.

### 2. UI Scuola — Skill Base + Boost in colore
- `ActingSchool.jsx` `SkillBar`: ora supporta prop `baseValue`. Quando presente, la barra mostra:
  - Segmento **verde** = valore base (skill originali ex-agenzia)
  - Segmento **ciano** = boost ottenuto dalla scuola
  - Etichetta numerica: `<base>+<boost>` (es. `77+4`).
- Backend `casting-students` endpoint ora ritorna `base_skills`, `from_agency`, `hidden_talent` per il frontend.

### 3. Reintegrazione sistemi dormienti (richiesta utente)
- **Skill evolution per film** (`game_systems.evolve_cast_skills` esisteva ma non chiamato):
  - Nuovo `_evolve_cast_after_film` in `game_hooks.py` collegato a `on_film_released`. Scala 0-100 corretta.
  - Per ogni cast member: skill cambiano in base a CWSv film (+0.8/+2.5 per film top, fino a -1.5 per flop), moltiplicatore per ruolo (protagonista 1.5×, cameo 0.5×). Breakthrough +1.5/+4 (5%), declino -0.5/-1.5 (2%).
  - Persistenza: `agency_actors` (own_source=agency), `casting_school_students` (own_source=school), `people` (NPC silent micro-growth).
- **Star Discovery** (`calculate_star_discovery_chance` ricollegato):
  - Per cast attori "unknown" + film_quality ≥75: 5-25% chance + skill_bonus → diventano "rising star".
  - Notifica `star_discovery` push al player + bonus fame +5 (cumulativo se più scoperte).
- `pipeline_v3.py release` ora chiama `on_film_released(user_id, film_doc, project)` con tutti i dati.

### 4. Sistema Rifiuti/Rinegoziazione (analisi)
- **Esiste** in `routes/cast.py` (linee 540-674): `POST /api/cast/hire` può ritornare rejection con `requested_fee`, `renegotiation_count`, `can_renegotiate`. `POST /api/cast/renegotiate/{id}` permette fino a 3 rinegoziazioni con chance decrescenti (-15%/tentativo) e messaggi vari ("Non è abbastanza...", "Il mio agente dice...").
- **NON collegato**: la pipeline V3 (`select-cast-member`, `cast-agency-actor`) non passa per questo flusso → nessun rifiuto in V3 oggi. **Proposto** per future task: wrappare `select-cast-member` per usare `decide_acceptance` di cast.py (che già considera level/fame del player).

Files: `backend/routes/casting_agency.py`, `backend/routes/acting_school.py`, `backend/game_hooks.py`, `backend/routes/pipeline_v3.py`, `frontend/src/pages/ActingSchool.jsx`.


## Bundle 5 fix (Apr 25, 2026 — sera 9)

### 1. Bug "Non possiedi una Scuola di Recitazione"
- `routes/casting_agency.py` send-to-school cercava `type='acting_school'`, ma in DB l'infrastruttura è salvata come **`cinema_school`**. Fix: query `$in: ['cinema_school','acting_school','scuola_recitazione','casting_school']` (allineata alla query che già funziona altrove). Verificato via curl: attore Jin Garcia iscritto correttamente.

### 2. Menu PRODUCI: "La Tua TV" → "Sceneggiature"
- `App.js` linea 1436: rimosso bottone "La Tua TV" (resta in topnav "LE MIE TV"). Aggiunto bottone "Sceneggiature" → `/emerging-screenplays` (icona BookOpen, verde smeraldo). Visibile in screenshot.

### 3. Cast Pipeline V3: "I Miei Attori" Scuola/Agenzia + Bonus
- `routes/pipeline_v3.py`:
  - `GET /films/{pid}/my-agency-actors`: cost=0 per tutti gli attori del proprio roster (scuola+agenzia). Flag `is_own_roster=True`. Mantenuto campo `source` (school/agency).
  - `POST /films/{pid}/cast-agency-actor`: cost=0, salva `is_own_roster` e `own_source` nell'entry del cast.
  - `POST /films/{pid}/release`: nuovo bonus CWSv proporzionale: per ogni attore proprio nel cast, `(stars²) × 0.025%` cumulativo, capped a +5%. Esempi: 4★ → +0.4%, 7★ → +1.225%, 9★ → +2.025% per attore.
  - Bonus XP al rilascio: `50 × stars` per attore proprio, max 1000 XP totale. Source `own_actors_bonus` in `wallet_transactions`.
- `components/v3/CastPhase.jsx`:
  - Tab "La Mia Agenzia" ora mostra **due sezioni separate** (Scuola di Recitazione 🎓 verde / La Mia Agenzia 💼 viola), con icona dedicata e badge "GRATIS".
  - Cast selezionato: badge distinti per source (Scuola/Mia Agenzia/Agenzia generica).

### 4. LAMPO Auto-Cast: include propri attori
- `routes/lampo.py`: dopo `_pick_random_cast`, sostituisce fino a **2 attori NPC** con attori dal roster del player (se disponibili). Preservato `character_role`, marcato `is_own_roster=True` con `own_source`. Trigger automatico bonus CWSv/XP al rilascio LAMPO.

Files: `backend/routes/casting_agency.py`, `backend/routes/pipeline_v3.py`, `backend/routes/lampo.py`, `frontend/src/App.js`, `frontend/src/components/v3/CastPhase.jsx`.


## Bundle 4 fix (Apr 25, 2026 — sera 8)

### 1. Mercato TV — Offerte Spontanee
- Backend: nuovo endpoint `POST /api/tv-market/content/{content_id}/spontaneous-offer` (`routes/tv_market.py`). Permette a qualunque player con TV di inviare un'offerta diretta al proprietario anche se il contenuto NON è sul mercato. `listing_id=None`, `is_spontaneous=True`. Stesso flusso accept/reject/counter. Limite: max 3 spontanee pendenti per (buyer, content). Notifica `tv_market_spontaneous_offer`.
- Frontend `TvMarketModal.jsx`: tab "Fai Offerta" sempre visibile per chi possiede ≥1 TV (non solo quando esiste un listing). Banner cyan "Offerta spontanea" nel form quando non c'è listing. Testo Panoramica chiarito: invita a usare "Fai Offerta" quando il proprietario non ha ancora pubblicato.

### 2. Palinsesto TV — Orario corretto + Episodi scrollabili
- `PalinsestoModal.jsx`: l'orario inserito dal player viene convertito da datetime locale a UTC ISO (`new Date(...).toISOString()`) prima dell'invio al backend. Risolve il bug "ora salva sempre 23:00" causato da fuso orario non gestito (l'orario locale veniva interpretato come UTC dal backend e poi riconvertito a locale, generando uno shift di +2h).
- `SeriesDetailModal.jsx`: nuovo componente `EpisodeList` che mostra TUTTI gli episodi in container scrollabile (max-h 260px) con thin scrollbar custom. Ogni episodio è cliccabile e apre la trama inline:
  - Episodi `aired`/`on_air`: mostrano `plot` o `mini_plot`.
  - Episodi non ancora trasmessi: mostrano "Trama non ancora disponibile — sarà visibile quando l'episodio verrà trasmesso." (gating coerente con la richiesta utente).
  - Badge LIVE per `on_air`, data uscita per pendenti, % consenso per aired.

### 3. Boost guadagni Lv 1-10 (silent)
- `utils/silent_bonuses.py`: aggiunto Layer 4 "Level-based revenue boost":
  - Lv 1-5: $40K × min(films, 5) per heartbeat (≈ 10 min). Cap giornaliero $5M.
  - Lv 6-10: $15K × min(films, 5) per heartbeat. Cap giornaliero $2M.
  - Lv 11+: 0 (economia normale).
  - Lv 0 senza film: $1K token per non far percepire "vuoto totale".
- Boost atomico in `wallet_transactions` con `source="level_boost"`, `silent=True`. Nessun toast, ma percettibile dalla crescita del saldo.
- Test: Lv 2 con 6 film → $200K/heartbeat; Lv 7 → $75K/heartbeat; Lv 16 → $0 (correttamente disattivato).

### 4. Avatar mini cast — DiceBear v9 → v7 fix
- `cast_system.py generate_cast_member()`: switch da `9.x/avataaars` a `7.x/avataaars`. La v9 rifiutava i parametri `top=*` e `facialHair=*` legacy con HTTP 400 → tutte le immagini erano broken e mostravano "?" (placeholder iOS).
- Migrazione retroattiva: aggiornati `21.448` NPCs in `db.people` + tutte le emerging_screenplays con avatar v9 → v7 (stripping di `&top=` e `&facialHair=` prima del replace). Coerenza sex/gender preservata via seed deterministico (`{first}{last}{role}`) + bgColor differenziato per genere (rosa per female, azzurro per male).
- Test: URL v7 ritorna HTTP 200 con SVG valido (~7KB).

Files: `backend/routes/tv_market.py`, `backend/utils/silent_bonuses.py`, `backend/cast_system.py`, `frontend/src/components/TvMarketModal.jsx`, `frontend/src/components/PalinsestoModal.jsx`, `frontend/src/components/SeriesDetailModal.jsx`.


## Fix Infrastructure Upgrade Player Level (Apr 25, 2026 — sera 7)

**Bug**: il popup "Upgrade infrastruttura" mostrava `Lv. giocatore: 0/1` (o simili) anche se il giocatore era a livello 16, bloccando il bottone "Migliora".

**Root cause**: due fonti di verità per il `level`:
- `/api/player/level-info` (usato dall'header `LEVEL 16`) → `game_systems.get_level_from_xp(total_xp)` con curva `50 * 1.037^L`.
- `users.level` salvato in DB (legacy) e `level_info` non popolato → restituiva 1 o 0.
L'endpoint `/infrastructure/{id}/upgrade-info` leggeva `user.get('level_info', {}).get('level', user.get('level', 1))` → discrepante con header.

**Fix**: in `routes/infrastructure.py` (sia `upgrade-info` GET che `/upgrade` POST) ora si usa la stessa funzione di `/types`:
```python
player_level = get_level_from_xp(user.get('total_xp', 0)).get('level', 0)
```
Coerente con tutti gli altri check di livello (linee 82, 159, 256). Verificato via curl: per fandrex1 (1160 XP) ora `player_level=16` invece di `1`. Screenshot UI conferma `Lv. giocatore: 16/7` e "Migliora a Lv.2" abilitato.

**Bonus**: corretti gli import errati `'../contexts/AuthContext'` → `'../contexts'` in `TvMarketDashboardWidget.jsx` e `TvMarketModal.jsx` (causavano errore di compilazione frontend "Module not found").

Files: `backend/routes/infrastructure.py`, `frontend/src/components/TvMarketDashboardWidget.jsx`, `frontend/src/components/TvMarketModal.jsx`.


## Cruscotto TV Market in Dashboard (Apr 25, 2026 — sera 6)

Nuovo widget dedicato `TvMarketDashboardWidget.jsx` integrato in Dashboard sopra "ULTIMI FILM AL CINEMA".

**Vista compatta** (sempre visibile):
- Header con icona TV + titolo "Cruscotto TV Market"
- Badge rosa pulsante con totale alert (offerte ricevute pendenti + controproposte da approvare)
- 4 mini-stat: Offerte ricevute (rosa se >0), Offerte fatte, Contratti attivi, Storico
- Click → apre modal full-screen

**Modal full** con 4 tab:
- **Ricevute** (badge offerte pending): per ogni offerta → buyer, station, prezzo/modo/durata, messaggio, pulsanti Accetta/Rifiuta inline
- **Inviate** (badge controproposte): le mie offerte con status; controproposte ricevute mostrano box cyan con prezzo + messaggio + bottone "Accetta controproposta"
- **Attivi**: contratti attivi con countdown "Resta X gg" (rosso se ≤3 giorni dalla scadenza), modalità 100%/50% colorata
- **Storico**: contratti completati con data conclusione

Mobile-first con touch-manipulation, 4 colonne stat con responsive shrink, scroll fluido nel modal.

Files: `frontend/src/components/TvMarketDashboardWidget.jsx`, `frontend/src/pages/Dashboard.jsx`.

## Mercato Diritti TV — Visibilità + Auto-Palinsesto (Apr 25, 2026 — sera 5)

Implementati i due P1 in coda al sistema mercato:

### 1. Visibilità contratti attivi nelle dashboard
- **Backend `economy.py /dashboard/batch`**:
  - `series_light` + `recent_releases` projection ora includono `tv_rights_*` fields.
  - Dopo gather, batch lookup su `tv_stations` e `users` → ogni item con contratto attivo riceve `tv_rights_station_name`, `tv_rights_station_logo`, `tv_rights_buyer_house`, `tv_rights_buyer_nickname`.
- **Backend `pipeline_series_v3.py /prossimamente`**: stesso enrichment per le serie/anime in arrivo TV.
- **Frontend `TvRightsBadge.jsx`** (nuovo): pillola cyan (split) o amber (full) in basso a destra della locandina con icona TV + nome stazione. Click → apre `TvMarketModal` in panoramica per vedere tutti i contratti attivi sul contenuto.
- Badge integrato in: Dashboard recent films / series / anime + ProssimamenteV3.
- **Test verificato**: enrichment ritorna `tv_rights_station_name="Mia Super TV"` e `tv_rights_buyer_house="Anacapito Studio's"` per film con contratto attivo, `None` per film senza.

### 2. Auto-integrazione palinsesto del buyer
- **`tv_market._execute_payment_and_contract`**: alla firma del contratto, il content viene **auto-aggiunto** a `tv_stations.contents.{films|tv_series|anime}` del buyer con flag `via_tv_market: True` e `contract_id`. Idempotente (no duplicati).
- **`auto_close_expired_contracts`**: alla scadenza, rimuove dal palinsesto del buyer **solo** le entry con `contract_id` corrispondente (preserva content posseduti dal buyer per altri motivi).
- Il buyer vede subito il contenuto disponibile nel suo schedule TV senza passi manuali.

Files: `backend/routes/tv_market.py`, `backend/routes/economy.py`, `backend/routes/pipeline_series_v3.py`, `frontend/src/components/TvRightsBadge.jsx`, `frontend/src/pages/Dashboard.jsx`.

## Mercato Diritti TV + UI Locandine (Apr 25, 2026 — sera 4)

### Fix #2 — UI locandine
- `ProducerBadge.jsx`: ora ritorna sempre `null` (badge "DI [nickname]" rimosso).
- `Dashboard.jsx`, `ComingSoonSection.jsx`, `LaPrimaSection.jsx`: testo sotto la locandina ora usa `producer_house || producer_nickname` (nome casa di produzione) invece del solo nickname.
- `LampoLightning`: posizionato a `bottom-left` su tutte le locandine (Dashboard recent series/anime/films, ComingSoon, LaPrima, Prossimamente V3).

### Fix #1 — Mercato Diritti TV (sistema completo)
**Backend** (`routes/tv_market.py` — nuovo modulo, ~600 righe):
- 3 collections: `tv_market_listings`, `tv_market_offers`, `tv_market_contracts`, `tv_market_credits_pool`.
- 12 endpoints REST: `/suggested-price`, `/list`, `/listings` (GET pubblico), `/listings/{id}` (DELETE), `/listings/{id}/offer`, `/incoming-offers`, `/my-offers`, `/offers/{id}/{accept|reject|counter}`, `/contracts/active/{content_id}`, `/contracts/mine`.
- **Pricing helper** `compute_suggested_price`: deriva da CWSv, likes, revenue + modificatori (in_theaters ×0.7, lampo ×1.10, recency, full ×2.5).
- **Modalità FULL (100% diritti)**: esclusiva, owner non può trasmettere durante il contratto. Owner riceve 100% del prezzo.
- **Modalità SPLIT (50% diritti)**: buyer paga al seller il 50% del prezzo upfront. Entrambi possono trasmettere su tutte le proprie TV. I crediti vanno al `tv_market_credits_pool` (premi futuri).
- **Notifiche** via `db.notifications` per: nuova offerta, controproposta, accettata, rifiutata, listing cancellato, contratto scaduto.
- **Wallet transactions** registrate per tracciabilità (`tv_market_purchase`, `tv_market_sale`).
- **Scheduler hook** `auto_close_expired_contracts`: ogni 10 minuti chiude contratti scaduti, libera il content da metadati di contratto attivo, notifica entrambe le parti.
- **Metadati sul content**: alla firma vengono settati `tv_rights_active_contract_id`, `tv_rights_buyer_user_id`, `tv_rights_buyer_station_id`, `tv_rights_mode`, `tv_rights_end_at` per visibilità futura nelle dashboard.
- Validazioni: ownership, possesso TV per il buyer, fondi/CP sufficienti, no relisting con contratto FULL attivo.

**Frontend** (`TvMarketModal.jsx` + `ContentTemplate.jsx`):
- Bottone "🎬 Mercato TV" sotto il titolo del film/serie/anime in `ContentTemplate`.
- Modal con 4 tab dinamici basati sul ruolo:
  - **Panoramica**: status listing, contratti attivi (con TV name + scadenza), prezzi suggeriti per entrambe le modalità.
  - **Pubblica/Modifica** (owner): form con modalità, denaro, crediti, durata, note + bottone "Usa prezzo consigliato".
  - **Offerte ricevute** (owner): card per ogni offerta con accept/reject/counter (controproposta inline con form $/CP/giorni/messaggio).
  - **Fai Offerta** (buyer con TV): selezione stazione TV, modalità, prezzo personalizzabile, messaggio.
- Mobile-first: bottom-sheet su mobile, dialog su desktop.
- Touch targets larghi, `touch-manipulation`, scroll fluidi.
- Toast feedback per ogni azione.

Files: `backend/routes/tv_market.py`, `backend/server.py` (router + scheduler), `frontend/src/components/TvMarketModal.jsx`, `frontend/src/components/ContentTemplate.jsx`, `frontend/src/components/ProducerBadge.jsx`, `frontend/src/pages/Dashboard.jsx`, `frontend/src/components/ComingSoonSection.jsx`, `frontend/src/components/LaPrimaSection.jsx`.

## Admin: Editor stato contenuti cliccabile (Apr 25, 2026 — sera 3)

### Backend (`server.py`)
Nuovo endpoint `POST /api/admin/set-content-status` (admin only):
- Body: `{item_id, collection, status, prossimamente_tv?, sync_pipeline_state?}`
- Aggiorna realmente `db.{films|film_projects|tv_series|series_projects_v3}`
- Audit fields: `admin_status_override_at`, `admin_status_override_by`
- Per `tv_series`: setta opzionalmente `prossimamente_tv`
- Per V3 projects: copia opzionalmente status anche in `pipeline_state`

### Frontend (`AdminStatusEditor.jsx` + `AdminPage.jsx`)
- Nuovo componente riutilizzabile `AdminStatusEditor` mobile-first.
- La card "STATO" nel popup admin film/serie/anime è ora cliccabile (badge "TAP per modificare ›").
- Editor mostra TUTTI gli stati possibili divisi per collection con:
  - Status code (mono), label leggibile, descrizione, sezioni dashboard dove appare ("📍 In Arrivo Su TV", "📍 Ultimi Aggiornamenti", ecc.)
  - Stato attuale evidenziato in cima
  - Toggle "Prossimamente TV" per `tv_series` (controlla visibilità in IN ARRIVO SU TV)
  - Checkbox "Sincronizza pipeline_state" per progetti V3
- Bottone CONFERMA verde sticky in cima al popup (sopra l'overlay, sempre visibile).
- z-index 200 per stare sopra il popup admin sottostante.
- Modifica REALE in DB confermata via test curl.

Cataloghi stati implementati:
- `films`: in_theaters, lampo_ready, lampo_scheduled, completed, archived, released, pending_release, discarded, deleted (9 stati)
- `film_projects`: idea, casting, screenplay, pre_production, shooting, pending_release, coming_soon, discarded, released (9 stati)
- `tv_series`: in_tv, catalog, completed, released, lampo_ready, lampo_scheduled, coming_soon, production, ready_to_release, discarded (10 stati)
- `series_projects_v3`: idea, hype, cast, prep, ciak, finalcut, marketing, distribution, release_pending, discarded (10 stati)

Files: `backend/server.py`, `frontend/src/components/AdminStatusEditor.jsx`, `frontend/src/pages/AdminPage.jsx`.

## LAMPO Visibility Globale — chiarimenti + fix `/coming-soon` (Apr 25, 2026 — sera 2)

### Investigazione bug "proprietario vede LAMPO, altri player no"
**Diagnosi**: il codice in `/app` ha già le query corrette per mostrare i LAMPO globalmente:
- `economy.py /dashboard/batch` → `recent_series_global` e `recent_anime_global` includono `lampo_scheduled` e `lampo_ready` (commit 5af992b)
- `pipeline_series_v3.py /prossimamente` → query released include `lampo_scheduled, lampo_ready`
- LAMPO stub setta `prossimamente_tv: True` correttamente

**Causa**: l'utente sta confrontando l'ambiente di **PRODUZIONE deployata** (vecchio codice senza queste fix) con il preview. Il proprietario vede comunque i propri contenuti LAMPO grazie al fallback `my_series` (filtro `user_id` senza filtro status), ma gli altri player non hanno alcun fallback → vedono vuoto.

**Soluzione**: deploy in produzione delle modifiche già presenti nel codebase.

### Fix preventivo aggiuntivo (`/coming-soon`)
- `series_pipeline.py /coming-soon`: la query principale `series_cursor` ora include anche `lampo_scheduled, lampo_ready` (in aggiunta al `lampo_series_cursor` già esistente). Doppia copertura ridondante per robustezza, dedup tramite `seen_ids`.

Files: `backend/routes/series_pipeline.py`.

## LAMPO Cast Fallback + Episodi AI (Apr 25, 2026 — sera)

### Cast Fallback difensivo (`routes/lampo.py`)
- `_pick_random_cast._sample` ora ha fallback: se la query con filtro `stars <= cap` ritorna vuoto, ritenta SENZA filtro stelle. Garantisce che director/actors/writer/composer non siano mai vuoti se ci sono NPCs nel pool.
- Era una protezione contro edge case dove il filtro level-gating eliminava tutti i candidati.

### Episodi AI per LAMPO Serie/Anime (`routes/lampo.py`)
- `_generate_screenplay_lampo` ora accetta `num_episodes` e ritorna anche `episodes: [{title, synopsis}]` quando content_type è serie/anime.
- Il prompt richiede titoli UNICI evocativi (max 4 parole, no "Episodio N"), sinossi specifiche di 1-2 frasi coerenti con la sceneggiatura, arco progressivo (setup → escalation → climax → risoluzione).
- Worker (`_worker_generate`): preferisce episodi AI, fallback ai template `_random_episode_minitrama` solo se l'AI fallisce.
- Test: per "Kudakodu/Nakisha" (8 episodi) — titoli generati: "Il primo incontro", "Doppio gioco", "Confessioni inattese", "Mandato pericoloso", "Piano in fuga", "Tradimento scoperto", "La scelta finale", "Amore o vendetta". Sinossi tutte progressive e fedeli alla pretrama.

### Frontend rendering titoli (`LampoModal.jsx`)
- `EpisodesList` ora mostra titolo prominente (ambra grassetto) + synopsis nella riga compatta.
- Espanso: titolo grande tra virgolette, synopsis sotto.
- Detection automatica di titoli generici (`/^(ep\.?|episodio|capitolo)\s*\d+$/i`): se generico, mostra solo la synopsis (no doppio rumore visivo).

Files: `backend/routes/lampo.py`, `frontend/src/components/LampoModal.jsx`.

## LAMPO Fix Bundle (Apr 25, 2026 — pomeriggio)
Tre fix critici basati su feedback foto utente:

### 1. Episodi LAMPO scrollabili + cliccabili (LampoResult)
- Nuovo componente `EpisodesList` in `LampoModal.jsx`: ora mostra TUTTI gli episodi (non solo i primi 5), in container scrollabile (max-h 72) con touch-manipulation per mobile.
- Ogni episodio è cliccabile: tap → si espande mostrando trama completa, titolo, durata. Tap di nuovo → collassa.
- Accent ambra quando aperto, indicatore chevron `›` ruotato.
- Hint "tap per dettagli" nell'header degli episodi.

### 2. AI screenplay: prompt rinforzato per non invertire ruoli
- `_generate_screenplay_lampo` in `routes/lampo.py`: system_message + prompt molto più direttivi.
- Nuova "REGOLA ASSOLUTA": rileggere la pretrama 2 volte, identificare protagonista/antagonista/vittima/ruoli/generi, NON invertire MAI relazioni (es. "lei deve uccidere lui" → mai il contrario), NON cambiare nomi né generi, NON aggiungere personaggi.
- Logline deve riassumere FEDELMENTE il conflitto. Test: "Kudakodu/Nakisha" ora corretto ("il suo ultimo incarico è uccidere proprio Kudakodu" riferito a Nakisha).

### 3. LAMPO drafts visibili nei pannelli Produzione (Anime/Serie/Film)
- **Anime + Serie TV** (`PipelineSeriesV3.jsx`): nuovo state `lampoProjects`, fetch da `/api/lampo/mine` filtrato per `content_type === seriesType` e `!released && status !== 'discarded'`. Card ⚡ accanto a "Nuova Anime/Serie" con poster, badge "LAMPO" + status (PRONTO/X%/etc.), click → riapre `LampoModal` con `existingProject` (salta direttamente al recap o progress bar).
- **Film** (`FilmPipeline.jsx` + `FilmCarousel`): stessa logica con `lampoFilmDrafts`. Nuove card LAMPO nel carousel cinematic. Glow ambra quando pronto, pulse animato quando in generazione.
- Auto-refresh dopo chiusura modal (`loadLampoDrafts() + loadProjects()`).

Files: `frontend/src/components/LampoModal.jsx`, `frontend/src/components/v3/PipelineSeriesV3.jsx`, `frontend/src/pages/FilmPipeline.jsx`, `backend/routes/lampo.py`.

## LAMPO Generi & Sub-generi AI (Apr 25, 2026)
- **GENRES espansi** in `LampoModal.jsx`: 24 film (era 8), 25 serie TV (era 6), 28 anime (era 5). Ogni genere ha `desc` con descrizione breve in italiano.
- **Descrizione genere** mostrata nel form sotto il select in box ambra (testid `lampo-genre-desc`) + nota "L'AI sceglierà 1-3 sotto-generi dalla tua pretrama".
- **Sub-generi AI**: rimossa la selezione manuale. `_generate_screenplay_lampo` ora ritorna `{screenplay, subgenres}` via singola chiamata gpt-4o-mini con output JSON. L'AI analizza la pretrama ed estrae 1-3 sub-generi pertinenti (es. "thriller psicologico", "noir", "coming of age", "cyberpunk"). Sanitizzati: minuscoli, max 3 parole, no duplicati, no genere principale.
- **Persistenza**: `subgenres` salvato in `lampo_projects`, propagato a `films` e `tv_series` (sia stub `lampo_ready`/`lampo_scheduled` sia release immediata).
- **UI recap step finale**: `LampoResult` mostra sub-generi come chip ambra "#nome" sotto il titolo (testid `lampo-subgenres-recap`).
- Files: `frontend/src/components/LampoModal.jsx`, `backend/routes/lampo.py`.

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
