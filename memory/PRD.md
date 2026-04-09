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

#### Dashboard Refactor + SideMenu + Glow + Menu Hamburger
(come precedentemente implementato)

## Distinzione Prossimamente
| Sezione | Dove | Cosa mostra |
|---|---|---|
| Prossimamente Dashboard | Dashboard globale | Contenuti di TUTTI i giocatori in sviluppo |
| Prossimamente Emittente TV | TVMenuModal → Contenuti | Contenuti programmati per la propria emittente con timer |

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
