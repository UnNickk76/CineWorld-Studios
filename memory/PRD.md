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
- Solo 8 sezioni: LaPrima, Eventi WOW, Prossimamente/Ultimi per Film, Serie TV, Anime
- Glow animato (gold/blue/purple) su tutte le sezioni, 4s
- Rimossi blocchi operativi e "I Miei" dalla dashboard

#### Bottone Menu → Griglia Azioni (Vecchio Stile)
- PRODUCI!, MERCATO, SCENEGGIATURE, CONTEST, MINIGIOCHI+SFIDE, ARENA, FESTIVAL, LE MIE TV!

#### SideMenu Laterale Sinistro
- Slide-in 25% con 9 voci navigazione
- Trigger: CIACK logo (top-left) quando su dashboard
- X button in alto per chiudere
- Overlay scuro per chiusura al tap esterno
- **Navbar (top+bottom) traslano** insieme al contenuto quando menu è aperto
- Body attribute `data-sidemenu="open"` + CSS class `sidemenu-translate`

#### Fix Infrastrutture
- Emittente TV ripristinata nel tab STUDI
- Categorie corrette per match backend types
- Nuova categoria SPECIALE (cinema_museum, film_festival_venue, theme_park)

#### Sistema TV Refactoring
- TVStationPage Netflix puro + TVMenuModal 4 tab
- SeriesDetailModal + PalinsestoModal integrati
- Notifiche Globali + ConfirmDialog custom

### Sessioni Precedenti
- Pipeline Film V2, Serie TV, Anime, Marketplace, PvP Arena
- Minigiochi, Festival, Tour, Contest, Infrastrutture
- Social CineBoard, Amici, Chat, Leaderboard

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
