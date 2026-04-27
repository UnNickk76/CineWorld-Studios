"""
Routes per esporre info studio quota + descrizioni infrastrutture (tooltip i).
"""
from fastapi import APIRouter, Depends
from database import db
from auth_utils import get_current_user
from utils.studio_quota import get_studio_quota_info

router = APIRouter(prefix="/api", tags=["studio"])


@router.get("/studio/quota")
async def get_all_quotas(user: dict = Depends(get_current_user)):
    """Return quota info for all 3 production studios of this user (classic + LAMPO)."""
    types = ["production_studio", "studio_serie_tv", "studio_anime"]
    results = {}
    for t in types:
        results[t] = {
            "classic": await get_studio_quota_info(db, user["id"], t, mode="classic"),
            "lampo": await get_studio_quota_info(db, user["id"], t, mode="lampo"),
        }
    return {"quotas": results}


@router.get("/studio/quota/{studio_type}")
async def get_one_quota(studio_type: str, user: dict = Depends(get_current_user)):
    return {
        "classic": await get_studio_quota_info(db, user["id"], studio_type, mode="classic"),
        "lampo": await get_studio_quota_info(db, user["id"], studio_type, mode="lampo"),
    }


# ─────────────────────────────────────────────────────────────────
# Infrastructure info catalogue (tooltip "i")
# ─────────────────────────────────────────────────────────────────

INFRA_INFO = {
    # ═══════════ STUDI ═══════════
    "production_studio": {
        "title": "Studio di Produzione",
        "short": "Il cuore del tuo impero cinematografico. Gratuito di default (Lv 0) — produce film di ogni genere.",
        "what_it_does": [
            "Sblocca la pipeline di produzione film completa",
            "Livello = qualità CGI/VFX + tipologie di film disponibili",
            "Riduce il cooldown tra una produzione e l'altra",
            "Aumenta gli slot di progetti in parallelo",
            "Abilita anche la produzione LAMPO (pipeline ultra-rapida da 2 min)"
        ],
        "unlocks_by_level": [
            {"level": 0, "label": "Gratuito di default • 1 progetto attivo • cooldown 5 giorni • CGI base"},
            {"level": 3, "label": "2 progetti paralleli"},
            {"level": 6, "label": "3 progetti • cooldown 3 giorni"},
            {"level": 15, "label": "CGI avanzata • 8 progetti paralleli"},
            {"level": 20, "label": "Sblocca biografie e film storici"},
            {"level": 35, "label": "Sblocca kolossal epici"},
            {"level": 50, "label": "VFX cinematografici • franchise/saga automatici"},
            {"level": 200, "label": "Progetti illimitati • zero cooldown"},
        ],
        "roi": "Più livelli = più film all'anno, più qualità, più spettatori, più box-office.",
    },
    "studio_serie_tv": {
        "title": "Studio Serie TV",
        "short": "Produce serie TV multi-stagione con pipeline dedicata (fino a 26 episodi).",
        "what_it_does": [
            "Abilita la pipeline Serie TV V3",
            "Livello = progetti paralleli + cooldown ridotto",
            "Sblocca formati lunghi (maratone, miniserie, saghe)",
            "Aumenta la qualità base delle serie prodotte"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Sblocca produzione serie • 1 in parallelo • cooldown 5gg"},
            {"level": 3, "label": "2 serie in parallelo"},
            {"level": 6, "label": "Formati Maratona e Lunga • 3 in parallelo"},
            {"level": 15, "label": "Serie Prestige/Premium • 8 in parallelo"},
            {"level": 50, "label": "Serie internazionali • produzioni di punta"},
            {"level": 200, "label": "Illimitato"},
        ],
        "roi": "Le serie generano revenue ricorrente settimanale: più serie in catalogo = più spettatori fedeli.",
    },
    "studio_anime": {
        "title": "Studio Anime",
        "short": "Produce anime negli stili Shonen, Seinen, Shojo, Mecha, Isekai.",
        "what_it_does": [
            "Abilita la pipeline Anime V3",
            "Accesso ad animatori illustratori specializzati",
            "Livello = progetti paralleli + cooldown ridotto",
            "Sblocca stili di animazione premium (4K, cell-shading, rotoscopio)"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Stili base Shonen e Shojo • 1 anime in parallelo"},
            {"level": 3, "label": "Stili Seinen e Mecha"},
            {"level": 6, "label": "Isekai + 3 anime in parallelo"},
            {"level": 15, "label": "Animazione cinematografica 4K"},
            {"level": 200, "label": "Illimitato"},
        ],
        "roi": "Gli anime hanno una fan base ultra-dedicata: più episodi = più likes, commenti virali, merchandise.",
    },
    "emittente_tv": {
        "title": "Emittente TV",
        "short": "Il tuo canale TV: trasmetti film, serie e anime sul palinsesto globale.",
        "what_it_does": [
            "Trasmette i tuoi contenuti a spettatori di tutto il mondo",
            "Slot per tipo (Film/Serie/Anime) = livello della station",
            "Affitta TV Rights da altri player per ampliare il palinsesto",
            "Auto-adoption: le serie V3 'Prossimamente TV' senza target vanno qui",
            "Puoi possederne più di una (costo esponenziale)"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "1 slot per tipo (1 film + 1 serie + 1 anime)"},
            {"level": 2, "label": "2 slot per tipo"},
            {"level": 5, "label": "5 slot per tipo • boost revenue"},
            {"level": 10, "label": "10 slot • co-produzioni internazionali"},
            {"level": 200, "label": "Slot illimitati"},
        ],
        "roi": "Ogni contenuto in palinsesto genera revenue ricorrente + fama della station = brand forte.",
    },
    # Compatibilità: vecchio id 'tv_station' usato altrove
    "tv_station": {
        "title": "Emittente TV",
        "short": "Il tuo canale TV: trasmetti film, serie e anime sul palinsesto globale.",
        "what_it_does": [
            "Trasmette i tuoi contenuti a spettatori di tutto il mondo",
            "Slot per tipo (Film/Serie/Anime) = livello della station",
            "Affitta TV Rights da altri player per ampliare il palinsesto",
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "1 slot per tipo"},
            {"level": 5, "label": "5 slot per tipo • boost revenue"},
            {"level": 200, "label": "Slot illimitati"},
        ],
        "roi": "Revenue ricorrente da ogni contenuto in palinsesto.",
    },

    # ═══════════ CINEMA / STRUTTURE ═══════════
    "cinema": {
        "title": "Cinema",
        "short": "Sala cinematografica fisica: ospita film in uscita e genera box-office ogni ora.",
        "what_it_does": [
            "Guadagna sul box office dei film proiettati",
            "Livello = numero di sale e capienza posti",
            "Può ospitare film propri o film affittati da altri player",
            "Vende biglietti, popcorn, bevande, combo e altri prodotti food"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "4 sale • 100 posti/sala • prodotti base (biglietto, popcorn, combo)"},
            {"level": 3, "label": "+6 sale • sblocca Hot Dog"},
            {"level": 5, "label": "Gelato + Merchandising + Lounge VIP"},
            {"level": 7, "label": "Proiezioni Premium 3D"},
            {"level": 10, "label": "Cocktail bar + massima capienza"},
        ],
        "roi": "Incasso orario costante: il cinema è la tua fonte di reddito passivo principale.",
    },
    "drive_in": {
        "title": "Drive-In",
        "short": "Cinema all'aperto in stile retrò. Bonus generi action/horror.",
        "what_it_does": [
            "Proiezione di film dal tuo parcheggio gigante",
            "+25% incassi per film horror • +20% action",
            "Atmosfera vintage attira nostalgici e famiglie",
            "Costi di gestione ridotti rispetto al cinema classico"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "50 postazioni auto • generi compatibili boostati"},
            {"level": 5, "label": "100 postazioni + snack bar"},
        ],
        "roi": "Entry-level per nuovi player: basso costo iniziale, bonus genere molto redditizi.",
    },
    "vip_cinema": {
        "title": "Cinema VIP",
        "short": "Sala esclusiva per film drama/premium: biglietti a prezzo alto, clientela elitaria.",
        "what_it_does": [
            "Poltrone reclinabili, servizio al posto, champagne incluso",
            "+30% incassi su film drama/storici • +20% su romance",
            "Clientela ad alta spesa per food&beverage"
        ],
        "unlocks_by_level": [
            {"level": 5, "label": "2 sale • 60 posti/sala • biglietti premium"},
            {"level": 10, "label": "4 sale • concierge dedicato"},
        ],
        "roi": "Pochi spettatori, ma revenue-per-spettatore altissimo. Ideale per produzioni d'autore.",
    },
    "multiplex_small": {
        "title": "Multiplex Piccolo",
        "short": "Cinema multisala di quartiere: 6 sale, pubblico familiare.",
        "what_it_does": [
            "6 sale • ampia offerta di film in contemporanea",
            "Bar snack + merchandising base",
            "Bilanciato tra costi e ricavi"
        ],
        "unlocks_by_level": [
            {"level": 3, "label": "6 sale • 150 posti/sala"},
            {"level": 8, "label": "Sale aggiornate + concessions"},
        ],
        "roi": "Scalabile: se lo porti a livello alto rivaleggia con i grandi multiplex.",
    },
    "multiplex_medium": {
        "title": "Multiplex Medio",
        "short": "Multisala urbana: 10 sale, boost su film commerciali.",
        "what_it_does": [
            "10 sale • food court interno",
            "+15% incassi su film action/adventure",
            "Capacità di ospitare anche anteprime ed eventi"
        ],
        "unlocks_by_level": [
            {"level": 8, "label": "10 sale • 200 posti/sala"},
            {"level": 15, "label": "IMAX + 3D + merchandising premium"},
        ],
        "roi": "Sweet-spot tra volumi e qualità: il più versatile dei cinema.",
    },
    "multiplex_large": {
        "title": "Multiplex Gigante",
        "short": "Cattedrale cinematografica: 16 sale, IMAX, parco tematico integrato.",
        "what_it_does": [
            "16 sale • IMAX + 4DX + Dolby Atmos",
            "+15% incassi su action/sci-fi/adventure",
            "Food court, arcade, merchandising, cinema museum incluso",
            "Consumo elevato, ma rendimenti scalabili massimi"
        ],
        "unlocks_by_level": [
            {"level": 15, "label": "16 sale • 300 posti/sala"},
            {"level": 25, "label": "IMAX Premium + eventi red carpet"},
        ],
        "roi": "Il top del segmento cinema: richiede budget ma rende moltissimo con film blockbuster.",
    },
    "cinema_museum": {
        "title": "Museo del Cinema",
        "short": "Spazio culturale che valorizza la storia del cinema. Bonus su film storici.",
        "what_it_does": [
            "Retrospettive e proiezioni classiche attirano cinefili",
            "+30% incassi su film storici • +25% documentari",
            "Visite guidate e mostre con entrate extra",
            "Aumenta la fama del tuo studio"
        ],
        "unlocks_by_level": [
            {"level": 10, "label": "Esposizione base + 1 sala proiezione"},
            {"level": 20, "label": "Archivio 4K + partnership festival"},
        ],
        "roi": "Revenue media ma enorme boost di fama e reputazione: sblocca contratti cast più rari.",
    },
    "film_festival_venue": {
        "title": "Sede Festival",
        "short": "Location dedicata ai festival cinematografici. +fama per ogni evento ospitato.",
        "what_it_does": [
            "Ospita festival (mensili) con film nominati",
            "+20% incassi su film indie/foreign/drama",
            "Ogni festival = bonus fama e cascate di premi",
            "Attrattivo per VIP e registi premium"
        ],
        "unlocks_by_level": [
            {"level": 15, "label": "Festival locale • 3 giorni di eventi"},
            {"level": 25, "label": "Festival internazionale • red carpet"},
        ],
        "roi": "Moltiplicatore fama: i tuoi film vincono più premi, aumenta il valore di tutto il catalogo.",
    },
    "theme_park": {
        "title": "Parco Tematico",
        "short": "Disney-like: giostre basate sui tuoi franchise. Revenue altissima, investimento enorme.",
        "what_it_does": [
            "Attrazioni e merchandising basati sui tuoi film più celebri",
            "+30% incassi su action/adventure/animation",
            "Revenue giornaliera indipendente dai film in sala",
            "Boost di fama permanente"
        ],
        "unlocks_by_level": [
            {"level": 25, "label": "Parco base • 5 attrazioni"},
            {"level": 50, "label": "Parco globale • hotel annesso"},
        ],
        "roi": "La vera monetizzazione end-game: un parco paga per anni anche senza nuovi film.",
    },

    # ═══════════ AGENZIE ═══════════
    "cinema_school": {
        "title": "Scuola di Recitazione",
        "short": "Forma attori giovani ★1-3 e li trasforma in talenti personali esclusivi.",
        "what_it_does": [
            "Iscrive studenti fino a un cap (max_students = livello × 5)",
            "Giornate di training aumentano skill • motivazione da monitorare",
            "Studenti formati diventano 'attori personali' (solo tuoi)",
            "Più livello = più studenti + training speed più alto"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "10 studenti • training base"},
            {"level": 5, "label": "25 studenti • skill avanzati"},
            {"level": 10, "label": "50 studenti • diplomi accelerati"},
        ],
        "roi": "Attori personali = cast gratis o scontati per TUTTI i tuoi film futuri.",
    },
    "talent_scout_actors": {
        "title": "Agenzia Talent Scout",
        "short": "Agenzia unica che recluta attori, registi, compositori e disegnatori NPC.",
        "what_it_does": [
            "Sblocca tutti e 4 i ruoli nel Mercato Talenti: attori, registi, compositori, disegnatori",
            "La quota visibile per ogni ruolo è ridistribuita in base al livello",
            "Sblocca pre-ingaggi e contratti esclusivi cross-ruolo",
            "Sceneggiatori restano sull'infrastruttura dedicata"
        ],
        "unlocks_by_level": [
            {"level": 3, "label": "Proposte ★1-3 • 3 al giorno"},
            {"level": 10, "label": "Proposte ★4 • contratti esclusivi"},
            {"level": 20, "label": "Proposte ★5 superstar"},
        ],
        "roi": "Risparmi tempo e denaro: cast sempre disponibili senza grind del marketplace.",
    },
    "talent_scout_screenwriters": {
        "title": "Talent Scout Sceneggiatori",
        "short": "Ti fornisce sceneggiatori pronti a scrivere trame e pre-plot per i tuoi progetti.",
        "what_it_does": [
            "Proposte giornaliere di sceneggiatori NPC",
            "Livello = qualità delle sceneggiature (impatta CWSv)",
            "Sblocca scrittori specializzati per genere",
            "Contratti multi-progetto con sconto volume"
        ],
        "unlocks_by_level": [
            {"level": 3, "label": "Sceneggiatori ★1-3"},
            {"level": 10, "label": "Sceneggiatori ★4 • generi di nicchia"},
            {"level": 20, "label": "Top writer ★5 • premi garantiti"},
        ],
        "roi": "Sceneggiature migliori → CWSv più alto → film di successo più probabili.",
    },

    # ═══════════ STRATEGICO (PvP) ═══════════
    "pvp_investigative": {
        "title": "Divisione Investigativa",
        "short": "Spia altri player: scopri i loro progetti in corso, cast, budget.",
        "what_it_does": [
            "Azioni di spionaggio su rivali (con cooldown)",
            "Rivela info sensibili: film in produzione, budget, cast segreto",
            "Prerequisito per attivare la Divisione Legale",
            "Livello = numero di azioni giornaliere + successo"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "1 spionaggio al giorno • basic intel"},
            {"level": 5, "label": "3 azioni/giorno • intel dettagliato"},
            {"level": 15, "label": "Spionaggio stealth • impossibile da rilevare"},
        ],
        "roi": "Informazione = potere: sabotare o anticipare i rivali ti fa risparmiare milioni.",
    },
    "pvp_operative": {
        "title": "Divisione Operativa",
        "short": "Esegue sabotaggi: blocca uscite rivali, ritarda produzioni nemiche.",
        "what_it_does": [
            "Attacchi ai cinema/studi dei rivali (danneggia revenue)",
            "Può 'rubare' contratti cast dai rivali",
            "Sabotaggio marketing: abbassa hype di film nemici in uscita",
            "Livello = potenza attacchi + durata effetti"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Sabotaggio base • 1 al giorno"},
            {"level": 5, "label": "Attacchi multi-target"},
            {"level": 15, "label": "Sabotaggi critici (blocca un'uscita rivale)"},
        ],
        "roi": "Arma offensiva PvP: blocca un rivale sul più bello e scalate la leaderboard.",
    },
    "pvp_legal": {
        "title": "Divisione Legale",
        "short": "Difesa + cause: blocca attacchi nemici, fai causa per copyright, recupera danni.",
        "what_it_does": [
            "Protegge le tue infrastrutture dagli attacchi operativi",
            "Avvia cause per plagio/copyright contro rivali (risarcimento $$$)",
            "Richiede la Divisione Investigativa Lv 1+",
            "Livello = ampiezza della difesa + probabilità vittoria cause"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Difesa base • 1 causa attiva"},
            {"level": 5, "label": "3 cause parallele • scudo anti-spionaggio"},
            {"level": 15, "label": "Studio legale globale • immunità su asset top"},
        ],
        "roi": "Scudo + generatore di risarcimenti: i rivali che ti attaccano pagano caro.",
    },
}

# Alias agency → talent_scout_actors per retro-compat
INFRA_INFO["agency"] = INFRA_INFO["talent_scout_actors"]


@router.get("/infrastructure/info/{infra_type}")
async def get_infra_info(infra_type: str):
    """Return description, unlocks, ROI for an infrastructure type (for tooltip 'i')."""
    info = INFRA_INFO.get(infra_type)
    if not info:
        return {"title": infra_type.replace("_", " ").title(), "short": "", "what_it_does": [], "unlocks_by_level": [], "roi": ""}
    return info


@router.get("/infrastructure/info")
async def get_all_infra_info():
    """Full catalogue for the tooltip system."""
    return INFRA_INFO
