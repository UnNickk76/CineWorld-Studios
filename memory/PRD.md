# CineWorld Studio's - PRD

## Problema Originale
Gioco browser di simulazione cinematografica con produzione film, serie TV, anime, sistema TV con palinsesto, marketplace, PvP arena, minigiochi e social features.

## Architettura
- **Frontend**: React + TailwindCSS + Shadcn UI + Framer Motion
- **Backend**: FastAPI + MongoDB
- **Auth**: JWT-based con bcrypt

## Cosa è stato implementato

### Sessione Corrente (Apr 2026)

#### Dashboard Refactor (VETRINA MOBILE-FIRST)
- Dashboard completamente rifattorizzata con solo 8 sezioni in ordine:
  1. LaPrima (glow-gold)
  2. Eventi WOW (EPICO/LEGGENDARIO, max 3, derivati da film di alta qualità)
  3. Prossimamente FILM (glow-blue)
  4. Ultimi Aggiornamenti FILM (glow-purple)
  5. Prossimamente SERIE TV (glow-blue)
  6. Ultimi Aggiornamenti SERIE TV (glow-purple)
  7. Prossimamente ANIME (glow-blue)
  8. Ultimi Aggiornamenti ANIME (glow-purple)
- Rimossi: blocchi operativi (produci, mercato ecc), sezioni I Miei film/serie/anime
- Tutte le sezioni con scroll orizzontale (overflow-x-auto)

#### SideMenu Laterale Sinistro
- Menu slide-in da sinistra (25% larghezza)
- 9 voci: Produci, Sceneggiature, Mercato, Le mie TV, Infrastrutture, Minigiochi+Sfide, Contest, Arena, Festival
- Trigger: bottone Menu in fondo dashboard + CIACK dalla bottom nav (quando già su dashboard)
- Overlay scuro con chiusura al click esterno

#### Glow Animato Sezioni
- `.glow-gold` per LaPrima e eventi LEGGENDARIO
- `.glow-blue` per sezioni Prossimamente
- `.glow-purple` per sezioni Ultimi Aggiornamenti e eventi EPICO
- Animazioni lente (4s) solo sui container

#### Sistema TV Refactoring
- TVStationPage → puro stile Netflix (solo caroselli + locandine, nessun bottone gestionale)
- TVMenuModal (4 tab): Contenuti, Palinsesto, Pubblicità, Statistiche
- SeriesDetailModal: dettaglio serie/anime con "Gestisci Palinsesto"
- PalinsestoModal: gestione episodi con schedulazione calendario reale
- Menu button in alto a destra nella TV Station page
- Integrazione in MyFilms.jsx per aprire SeriesDetailModal da "I Miei"

#### Notifiche Globali + ConfirmDialog
- Sistema NotificationProvider con raggruppamento anti-spam
- ConfirmDialog custom al posto di window.confirm

### Sessioni Precedenti
- Pipeline Film V2, Serie TV, Anime
- Sistema Marketplace (Fase 1 e 2)
- PvP Arena con sfide e divisioni
- Minigiochi (IndovinaIncasso, TriviaCinema, etc.)
- Festival, Tour del Cinema, Contest
- Infrastrutture con upgrade
- Sistema Social CineBoard + Amici
- Chat di gruppo
- Leaderboard + Classifiche

## Backlog Prioritizzato

### P1
- Fase 3 Mercato: vendita serie/anime con distribuzione a chi acquista

### P2
- Sfida della Settimana (minigioco rotante con premi extra)

### P3
- Previsioni Festival
- Marketplace diritti TV/Anime
- Velion Mood Indicator, Chat Evolution, CinePass+Stripe, Livelli

## Credenziali Test
- Email: fandrex1@gmail.com
- Password: Fandrel2776
- Nickname: NeoMorpheus
