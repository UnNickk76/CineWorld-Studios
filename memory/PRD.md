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
- Rimossi: blocchi operativi e "I Miei" dalla dashboard
- Tutte le sezioni con scroll orizzontale

#### Bottone Menu → Griglia Azioni (Vecchio Stile)
- Click su "Menu" in fondo alla dashboard apre la griglia:
  - PRODUCI! (full width, gold)
  - MERCATO + SCENEGGIATURE (2 colonne)
  - CONTEST + MINIGIOCHI+SFIDE (2 colonne)
  - ARENA + FESTIVAL (2 colonne)
  - LE MIE TV! (full width, rosso)

#### SideMenu Laterale Sinistro
- Menu slide-in da sinistra (25% larghezza)
- 9 voci: Produci, Sceneggiature, Mercato, Le mie TV, Infrastrutture, Minigiochi+Sfide, Contest, Arena, Festival
- Trigger: CIACK (logo Clapperboard in alto sx) quando si è già in dashboard
- Se si è in altre pagine, CIACK porta a dashboard senza aprire menu
- Overlay scuro con chiusura al click esterno

#### Glow Animato Sezioni
- .glow-gold per LaPrima e eventi LEGGENDARIO
- .glow-blue per Prossimamente
- .glow-purple per Ultimi Aggiornamenti e eventi EPICO
- Animazioni lente 4s solo sui container

#### Fix Infrastrutture - Emittente TV
- Aggiunta EMITTENTE TV nel tab STUDI della pagina Infrastrutture
- Corrette categorie CATEGORIES per match con backend types:
  - cinema → cinema, drive_in, vip_cinema
  - commerciale → multiplex_small, multiplex_medium, multiplex_large
  - studi → production_studio, studio_serie_tv, studio_anime, emittente_tv
  - agenzie → cinema_school, talent_scout_actors, talent_scout_screenwriters
  - strategico → pvp_operative, pvp_investigative, pvp_legal
  - speciale (NUOVA) → cinema_museum, film_festival_venue, theme_park

#### Sistema TV Refactoring
- TVStationPage → puro stile Netflix (solo caroselli + locandine)
- TVMenuModal (4 tab): Contenuti, Palinsesto, Pubblicità, Statistiche
- SeriesDetailModal + PalinsestoModal integrati
- Menu button in alto a destra nella TV Station page

### Sessioni Precedenti
- Pipeline Film V2, Serie TV, Anime
- Sistema Marketplace (Fase 1 e 2)
- PvP Arena con sfide e divisioni
- Minigiochi, Festival, Tour del Cinema, Contest
- Infrastrutture con upgrade
- Sistema Social CineBoard + Amici
- Chat di gruppo, Leaderboard + Classifiche
- Notifiche Globali + ConfirmDialog custom

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
