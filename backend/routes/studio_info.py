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
    """Return quota info for all 3 production studios of this user."""
    types = ["production_studio", "studio_serie_tv", "studio_anime"]
    results = {}
    for t in types:
        results[t] = await get_studio_quota_info(db, user["id"], t)
    return {"quotas": results}


@router.get("/studio/quota/{studio_type}")
async def get_one_quota(studio_type: str, user: dict = Depends(get_current_user)):
    return await get_studio_quota_info(db, user["id"], studio_type)


# ─────────────────────────────────────────────────────────────────
# Infrastructure info catalogue (tooltip "i")
# ─────────────────────────────────────────────────────────────────

INFRA_INFO = {
    "production_studio": {
        "title": "Studio di Produzione",
        "short": "Il cuore cinematografico del tuo impero. Produce film di qualsiasi genere.",
        "what_it_does": [
            "Consente la produzione di film con pipeline completa",
            "Livello determina qualità CGI/VFX e tipologie sbloccate",
            "Riduce cooldown tra una produzione e l'altra",
            "Aumenta slot di progetti in parallelo"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Disponibile di default • 1 progetto/5 giorni • CGI base"},
            {"level": 3, "label": "2 progetti in parallelo"},
            {"level": 6, "label": "3 progetti • cooldown 3 giorni"},
            {"level": 15, "label": "CGI avanzata • 8 progetti in parallelo"},
            {"level": 20, "label": "Sblocca biografie e film storici"},
            {"level": 35, "label": "Sblocca kolossal epici"},
            {"level": 50, "label": "VFX cinematografici • franchise/saga automatici"},
            {"level": 200, "label": "Progetti illimitati • 0 cooldown"},
        ],
        "roi": "Più livelli = più film all'anno, più qualità, più spettatori.",
    },
    "studio_serie_tv": {
        "title": "Studio Serie TV",
        "short": "Produce serie TV multi-stagione con pipeline dedicata.",
        "what_it_does": [
            "Abilita la pipeline Serie TV (V3)",
            "Livello = progetti paralleli + cooldown ridotto",
            "Sblocca formati lunghi (13-26 episodi) e maratone",
            "Aumenta la qualità base delle serie"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Sblocca produzione serie • 1 in parallelo • cooldown 5gg"},
            {"level": 3, "label": "2 serie in parallelo"},
            {"level": 6, "label": "Formati Maratona e Lunga"},
            {"level": 15, "label": "Serie Prestige/Premium • 8 in parallelo"},
            {"level": 50, "label": "Serie internazionali • produzioni di punta"},
            {"level": 200, "label": "Illimitato"},
        ],
        "roi": "Stream annuale ricorrente: più serie in catalogo = più spettatori fedeli ogni settimana.",
    },
    "studio_anime": {
        "title": "Studio Anime",
        "short": "Produce anime in stili unici: Shonen, Seinen, Shojo, Mecha, Isekai.",
        "what_it_does": [
            "Abilita la pipeline Anime (V3)",
            "Accesso a disegnatori specializzati (animatori illustratori)",
            "Livello = progetti paralleli + cooldown ridotto",
            "Sblocca stili di animazione premium"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Stili base Shonen e Shojo • 1 anime in parallelo"},
            {"level": 3, "label": "Seinen + Mecha"},
            {"level": 6, "label": "Isekai + 3 anime in parallelo"},
            {"level": 15, "label": "Animazione cinematografica 4K"},
            {"level": 200, "label": "Illimitato"},
        ],
        "roi": "Gli anime hanno una fan base ultra-dedita: più episodi = più likes/commenti virali.",
    },
    "tv_station": {
        "title": "Emittente TV",
        "short": "Il tuo canale TV: trasmetti film, serie TV e anime sul palinsesto.",
        "what_it_does": [
            "Ti consente di trasmettere i tuoi contenuti a spettatori globali",
            "Slot per tipo (Film/Serie/Anime) = livello della station",
            "Permette di affittare diritti (TV Rights) da altri player",
            "Auto-adoption: serie V3 'Prossimamente TV' senza station specifica vanno qui"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "1 slot per tipo (1 film + 1 serie + 1 anime)"},
            {"level": 2, "label": "2 slot per tipo"},
            {"level": 5, "label": "5 slot per tipo • boost revenue"},
            {"level": 10, "label": "10 slot • co-produzioni internazionali"},
            {"level": 200, "label": "Slot illimitati"},
        ],
        "roi": "Ogni contenuto in palinsesto = revenue ricorrente + fama della station.",
    },
    "cinema": {
        "title": "Multisala Cinema",
        "short": "Una sala cinematografica fisica che ospita film in uscita.",
        "what_it_does": [
            "Guadagna sul box office dei film proiettati",
            "Livello = capienza e comfort (biglietti più cari)",
            "Può ospitare film propri o di altri player"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "Sala base • 200 posti"},
            {"level": 5, "label": "Sala premium • 500 posti • concessions bar"},
            {"level": 15, "label": "IMAX • 1000 posti • biglietti premium"},
        ],
        "roi": "Ingresso fisso per ogni spettatore che guarda un film nella tua sala.",
    },
    "agency": {
        "title": "Agenzia Talenti",
        "short": "Gestisce contratti esclusivi con attori/registi.",
        "what_it_does": [
            "Firma contratti esclusivi con NPC per ridurre i costi cast",
            "Accesso a pool di talenti premium",
            "Livello = numero di contratti attivi simultanei"
        ],
        "unlocks_by_level": [
            {"level": 1, "label": "3 contratti attivi"},
            {"level": 5, "label": "10 contratti + talenti 4★"},
            {"level": 15, "label": "Esclusive di top player • talenti 5★"},
        ],
        "roi": "Un'esclusiva con un talento superstar riduce drasticamente i costi di ogni suo ruolo.",
    },
}


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
