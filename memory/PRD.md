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
- **Admin Tutorial Manager**: 3 pulsanti aggiornamento (statico, velion, guest) con progress bar live
- **Background task non bloccante**: Processing → Generazione → Salvataggio → Completato con polling 1.5s
- **Frozen Sections**: "Note di Rilascio" e "Note di Sistema" freezate con badge "In aggiornamento"
  - Pagine sostituite con layout freeze (icona lucchetto, messaggio, box AI futuro)
  - Menu grid: opacita ridotta, badge "SOSPESO", click disabilitato
  - Nessun fetch vecchi contenuti, nessun errore console
- **Tutorial Page**: Legge contenuti da DB (`/api/tutorial/content`), versioning visibile
- **Preparazione riattivazione futura**: Struttura DB pronta per AI/Admin Panel
- Backend: `/app/backend/routes/tutorial.py`, model: `/app/backend/models/tutorial.py`

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
