# CineWorld Studio's - PRD

## Problema Originale
Gioco browser di simulazione cinematografica con produzione film, serie TV, anime, sistema TV con palinsesto, marketplace, PvP arena, minigiochi e social features.

## Architettura
- **Frontend**: React + TailwindCSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Auth**: JWT-based con bcrypt

## Cosa è stato implementato

### Sessione Corrente (Apr 2026)

#### Tab Contenuti Rifattorizzato (TVMenuModal)
- Card "+" come PRIMO elemento inline a sinistra per ogni sezione (Film=giallo, Serie TV=blu, Anime=arancione)
- Eliminato bottone "+ Aggiungi" a destra
- Scroll orizzontale su tutte le righe
- Freccia ➡️ del colore sezione se scroll necessario (20+ items)

#### Sezione Prossimamente Emittente TV (NUOVA)
- Sezione nel tab Contenuti dedicata alla programmazione futura della propria emittente
- Card "+" → picker contenuti (film/serie/anime, ANCHE in produzione/sviluppo)
- Timer popup: 6 ore | 12 ore | 24 ore | 2 giorni | 4 giorni | 6 giorni
- Film: scade timer → va in onda automaticamente
- Serie/Anime con episodi: dopo timer → apre PalinsestoModal per scheduling episodi
- Serie/Anime SENZA episodi: resta CONGELATA (icona fiocco neve), si sblocca quando definiti
- Auto-transizione in `_auto_advance_broadcasts`
- Backend endpoints: add-upcoming, get upcoming, remove-upcoming, available-upcoming

#### Rifattorizzazione Sistema Infrastrutture (Apr 2026)
- Creata /strutture (gestione cinema, film, prezzi, revenue)
- Creata /agenzia (4 tab: Attori, Scuola, Scout, Sceneggiature)
- Creata /strategico (divisioni PvP con stats e upgrade)
- SideMenu con visibilità condizionale (API /infrastructure/owned-categories)
- InfrastructurePage semplificata a solo Shop + Upgrade (1574→779 righe)
- Rimosso tab Agenzia Casting da ProductionStudioPanel
- Formula cinema migliorata: gradimento, durata, compatibilità genere, prezzi, food

#### Rifinitura Prossimamente Gestionale (Apr 2026)
- Click su locandina nel "Prossimamente" → apre popup dettaglio gestione (SeriesDetailModal/FilmDetailPopup) invece del cestino
- Bottone "Elimina dalla programmazione" esplicito sotto ogni locandina
- Merge vecchi contenuti schedulati (`scheduled_for_tv`) con nuovi (`upcoming_content`) nella lista Prossimamente
- Fix overlay click-through su FilmDetailPopup (e.stopPropagation su backdrop)

#### Click Gestionale su TUTTE le sezioni TVMenuModal (Apr 2026)
- Click su locandina in Film/Serie TV/Anime apre il gestionale (SeriesDetailModal o FilmDetailPopup)
- Bottone "Elimina" esplicito sotto ogni locandina in tutte le sezioni
- Rimosso trash overlay on hover (sostituito da bottone esplicito)

#### Eventi WOW — Animazione Cinematica (Apr 2026)
- Click su card "Eventi WOW" in Dashboard ora apre l'animazione cinematica VelionCinematicEvent
- Rimossa navigazione diretta a `/films/{id}`

#### Velion — Rimozione notifica revenue automatica (Apr 2026)
- Rimosso tipo `revenue` da HIGH_PRIORITY_TYPES in VelionOverlay
- La notifica "botteghino da incassare" non appare più (processo automatico)

#### Dashboard Refactor + SideMenu + Glow + Menu Hamburger
(come precedentemente implementato)

## Distinzione Prossimamente
| Sezione | Dove | Cosa mostra |
|---|---|---|
| Prossimamente Dashboard | Dashboard globale | Contenuti di TUTTI i giocatori in sviluppo |
| Prossimamente Emittente TV | TVMenuModal → Contenuti | Contenuti programmati per la propria emittente con timer |

#### UX Migliorata Strutture/Cinema (Apr 2026)
- Badge performance film visuale (Ottimo verde / Medio giallo / Flop rosso) con icone
- Box "Perché stai guadagnando così?" con fattori positivi/negativi/neutri
- Differenziazione tipo struttura con label e bonus genere
- Dettagli noleggio film (durata restante, % ricavi, costo pagato)
- Barra gradimento pubblico animata con colori dinamici
- Micro feedback toast contestuali su ogni azione (prezzi, aggiunta/rimozione film)
- Statistiche griglia (Affluenza, Occupazione, Schermi)

#### FASE 3 — Mondo Vivo (Apr 2026)
- **Sistema Citta Dinamiche (Invisibile)**: 47 citta con generi attivi e valori nascosti (0-100), timer random 5-25 giorni, update asincrono via scheduler
- **Sistema Hype Film**: Campo hype (0-100) per ogni film, decadimento nel tempo, influenza su affluenza/food/rendimento cinema
- **Impatto Citta su LaPrima**: Boost forte su premiere basato su affinita citta-genere, max +15%/-5%
- **Impatto Citta post-uscita**: Leggero su revenue cinema via scheduler
- **Notifiche Impatto Film**: Generate ogni 3h per film attivi, ~40 parole descrittive (4 tier), MAI numeri esposti
- **Velion LaPrima Suggestion**: ~40% probabilita, suggerisce 2-4 citta (60-70% buone, 30-40% sbagliate), UI con fade e glow
- **Collegamento Eventi-Hype**: Eventi positivi → hype/gradimento +, negativi → hype/gradimento -
- Backend: `/app/backend/routes/city_dynamics.py`, scheduler jobs in `scheduler_tasks.py`

#### Sistema Tutorial PRO (Apr 2026)
- **Backend model**: `tutorial_config` collection MongoDB con template statico/velion/guest
- **Admin Tutorial Manager**: 3 card con 2 pulsanti ciascuna (Da DB + Con AI = 6 azioni totali)
- **Generazione AI**: GPT-4.1-mini via Emergent LLM Key, genera contenuti JSON strutturati per ogni tipo tutorial
  - Prompt dedicati per statico (8 blocchi), velion (6 step interattivi), guest (7 step pipeline)
  - Parsing JSON automatico, gestione errori, versioning incrementale
- **Background task non bloccante**: Processing → Generazione → Salvataggio → Completato con polling 1.5s
- **Progress bar differenziata**: colore verde per AI, giallo per DB, badge tipo (es. "static (AI)")
- **Frozen Sections**: "Note di Rilascio" e "Note di Sistema" freezate con badge "In aggiornamento"
  - Pagine sostituite con layout freeze (icona lucchetto, messaggio, box AI futuro)
  - Menu grid: opacita ridotta, badge "SOSPESO", click disabilitato
  - Nessun fetch vecchi contenuti, nessun errore console
- **Tutorial Page**: Legge contenuti da DB (`/api/tutorial/content`), versioning visibile
- **Preparazione riattivazione futura**: Struttura DB pronta per AI/Admin Panel
- Backend: `/app/backend/routes/tutorial.py`, model: `/app/backend/models/tutorial.py`
- Endpoints AI: `POST /api/admin/tutorial/update-ai/{type}` (static/velion/guest)

#### Restyling UI Pagina Dettaglio + Sistema Durata (Apr 2026)
- **ContentTemplate.jsx riscritto**: Layout a flusso mobile-first (rimosso overlay PNG con positioning assoluto)
- **Nuovo ordine UI**: Status bar → Poster+Trama breve → Titolo → Regia+Cast → Barra dati (IMDb/Durata) → Box giornali → Box pubblico/eventi → Sceneggiatura scrollabile → Trailer placeholder
- **5 stati dinamici**: LaPrima! (glow oro), Prossimamente, Al Cinema (verde), In TV! (blu), In Catalogo
- **Box giornali verdi**: VARIETY/EMPIRE/HOLLYWOOD R. (film) o IGN/COLLIDER/ENTERTAINMENT W. (serie)
- **Box celeste pubblico+eventi**: Percezione pubblica + headline news_events
- **Sistema Durata backend**: 5 categorie film (Cortometraggio→Kolossal, 20-280 min) + 5 categorie serie (Breve→Kolossal Seriale, 15-110 min/ep)
- **Calcolo deterministico**: Basato su genere, lunghezza trama, bias controllato
- **short_plot**: Generato automaticamente dalla sceneggiatura (max 500 char), salvato una volta
- **Retrocompatibilita assoluta**: Nessuna migrazione DB, fallback sicuri per tutti i campi opzionali
- **Impatto gameplay durata**: quality_mod, revenue_mult, cost_mult per categoria
- Endpoints: `POST /api/pipeline-v2/films/{pid}/set-duration`, `POST /api/series-pipeline/{id}/set-duration`, `GET .../duration-categories`
- File: `ContentTemplate.jsx`, `content-template.css`, `pipeline_v2.py`, `series_pipeline.py`, `films.py`

#### Sistema Trend Dinamico (Apr 2026)
- **Scheduler `update_trend_scores()`**: Calcolo batch ogni 6h per tutti film+serie attivi
- **Formula**: quality*15 + hype*20 + attendance + likes + cinemas + status_boost - age_decay - flop_penalty, range 0-10000
- **Ranking**: Posizione globale ordinata per trend_score DESC
- **Delta**: Differenza posizione tra calcoli (es: +12 = in salita, -5 = in calo)
- **Frontend**: Integrato nella barra dati fucsia: `🔥 #9 ↑+12` con colore verde/rosso/grigio
- **Eventi automatici**: Notifica "Trend in Salita!" (delta>+20) o "Interesse in Calo" (delta<-20)
- **Retrocompatibilita**: Campi opzionali con fallback a 0/null, nessuna migrazione
- **Performance**: Query batch, no loop pesanti, aggiornamento ogni 6h
- File: `scheduler_tasks.py`, `server.py`, `ContentTemplate.jsx`, `content-template.css`, `films.py`, `series_pipeline.py`

#### Navigazione Mobile Gesture-Based (Apr 2026)
- **TopNavbar riorganizzata**: CIACK (toggle side menu) → HOME (dashboard) → BACK (solo quando serve), rimosso `?` tutorial
- **Side Menu Globale**: Spostato da Dashboard a AppLayout, funziona da qualsiasi pagina
- **Swipe Navigator**: Gesture touch tra pagine bottom-nav (/films, /marketplace, /infrastructure, /pvp-arena, /my-tv)
- **Dashboard swipe speciale**: Destra → apre menu, Sinistra → prima pagina di gioco
- **Anti-conflitto scroll**: Ignora swipe se il touch parte dentro elementi con scrollWidth > clientWidth
- **Vibrazione**: `navigator.vibrate()` su apertura/chiusura menu e cambio pagina
- **z-index corretto**: Menu (z-40/z-48) sotto navbar (z-50), CIACK sempre cliccabile
- File: `App.js`, `Dashboard.jsx`

#### Navbar Definitiva + Comandi Rapidi (Apr 2026)
- **Top navbar**: 8 icone fisse (CIACK, HOME, PRODUCI, ARENA, LE MIE TV, MAJOR, CHAT, NOTIFICHE) + fondi compatti. Rimosso hamburger menu, CineBoard dropdown, tutorial, online users.
- **Bottom navbar**: 11 item (HOME, I MIEI, PRODUCI, CINEBOARD, CLASSIFICHE, FESTIVAL, CINEJOURNAL, MERCATO, MINIGIOCHI, EVENTI, RAPIDI). Icona Zap per Comandi Rapidi.
- **Comandi Rapidi**: Panel popup dalla bottom nav con 8 scorciatoie (Sceneggiature, Le mie TV, Infrastrutture, Arena, Contest, Saghe, Stelle, Profilo)
- **Side menu**: Icone Lucide React (giallo/gold) al posto di emoji — stile identico alle navbar
- **Swipe semplificato**: Solo dashboard swipe destro → apre menu. Rimosso swipe tra pagine.
- File: `App.js`, `Dashboard.jsx`

#### Fase 2: Mercato Auto + Prossimamente Fix + Placeholder (Apr 2026)
- **Mercato auto-listing**: Film scartati (`discard_film_v2`) entrano automaticamente nel marketplace con prezzo proporzionale (40-60% investito, min $10K). Split 50/50 (50% venditore, 50% rimosso dal sistema)
- **Prossimamente fix**: V2 detail ora ha bottone "Vedi Dettaglio" → naviga a ContentTemplate. Campi mancanti mostrano spazio vuoto (no "non disponibile")
- **ContentTemplate cleanup**: Rimossi tutti i placeholder "Trama non disponibile", "Durata non disponibile" — spazio vuoto se dato assente
- **Popup conferma**: ConfirmDialog personalizzato CineWorld (Velion/CineOx) gia presente ovunque, nessun `window.confirm` nel codice
- File: `pipeline_v2.py`, `film_pipeline.py`, `ContentTemplate.jsx`, `ComingSoonSection.jsx`

#### Menu Laterale Pellicola Cinematografica (Apr 2026)
- **Effetto pellicola animata CSS-only**: Background con bande scure + gradient dorato + perforazioni laterali, animazione verticale 20s loop infinito
- **Frame dorati**: Ogni voce menu stilizzata come frame pellicola con bordo gold, glow sottile, sfondo semi-trasparente
- **Performance**: Solo CSS (will-change: transform), nessuna immagine, nessun repaint pesante
- File: `App.js`, `styles/film-strip-menu.css`

## Backlog

### P1
- Fase 3 Mercato: vendita serie/anime

### P2
- Sfida della Settimana

### P3
- Previsioni Festival, Marketplace diritti TV/Anime
- Velion Mood, Chat Evolution, CinePass+Stripe, Livelli

## Credenziali Test
- Email: fandrex1@gmail.com
- Password: Fandrel2776
- Nickname: NeoMorpheus
