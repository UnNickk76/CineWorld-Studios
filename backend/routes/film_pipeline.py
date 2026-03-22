# CineWorld - Film Pipeline System
# Multi-step film creation with proposals, casting agents, and progression

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timezone, timedelta
import random
import uuid
import os
import logging
import asyncio

from database import db
from auth_utils import get_current_user
import poster_storage
from game_systems import (
    calculate_imdb_rating, generate_ai_interactions, calculate_film_tier,
    generate_critic_reviews, calculate_fame_change, get_level_from_xp,
    XP_REWARDS
)

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')

router = APIRouter()

# === VALID STATE TRANSITIONS ===
VALID_FILM_STATUSES = {'draft', 'proposed', 'coming_soon', 'ready_for_casting', 'casting', 'screenplay', 'pre_production', 'shooting', 'completed', 'released', 'discarded', 'abandoned'}

VALID_FILM_TRANSITIONS = {
    'draft': {'proposed', 'discarded'},
    'proposed': {'coming_soon', 'casting', 'discarded'},
    'coming_soon': {'ready_for_casting', 'casting', 'completed', 'discarded'},
    'ready_for_casting': {'casting', 'discarded'},
    'casting': {'screenplay', 'discarded'},
    'screenplay': {'pre_production', 'discarded'},
    'pre_production': {'shooting', 'discarded'},
    'shooting': {'completed', 'released', 'discarded'},
    'completed': {'released'},
    'released': set(),
    'discarded': set(),
    'abandoned': set(),
}

def validate_film_transition(current_status: str, target_status: str) -> bool:
    """Check if a status transition is valid."""
    if current_status not in VALID_FILM_STATUSES:
        return False
    allowed = VALID_FILM_TRANSITIONS.get(current_status, set())
    return target_status in allowed

# === ROLE VALUES - Impact on film quality and actor growth ===
ROLE_VALUES = {
    'Protagonista': {'quality_weight': 1.5, 'growth_rate': 1.2, 'label': 'Protagonista'},
    'Co-Protagonista': {'quality_weight': 1.2, 'growth_rate': 1.0, 'label': 'Co-Protagonista'},
    'Antagonista': {'quality_weight': 1.3, 'growth_rate': 1.1, 'label': 'Antagonista'},
    'Supporto': {'quality_weight': 0.7, 'growth_rate': 0.6, 'label': 'Supporto'},
    'Cameo': {'quality_weight': 0.3, 'growth_rate': 0.2, 'label': 'Cameo'},
}

# === EXTRAS (Comparse) - Genre fit affects quality ===
# Optimal ranges per genre: going below wastes money, going above can hurt quality
EXTRAS_OPTIMAL = {
    'action': {'min': 200, 'max': 700, 'sweet': 400},
    'comedy': {'min': 50, 'max': 300, 'sweet': 150},
    'drama': {'min': 50, 'max': 250, 'sweet': 120},
    'horror': {'min': 100, 'max': 500, 'sweet': 250},
    'sci_fi': {'min': 150, 'max': 800, 'sweet': 400},
    'romance': {'min': 50, 'max': 150, 'sweet': 80},
    'thriller': {'min': 50, 'max': 300, 'sweet': 150},
    'animation': {'min': 50, 'max': 200, 'sweet': 100},
    'documentary': {'min': 50, 'max': 100, 'sweet': 50},
    'fantasy': {'min': 200, 'max': 800, 'sweet': 500},
    'musical': {'min': 100, 'max': 500, 'sweet': 300},
    'western': {'min': 100, 'max': 400, 'sweet': 200},
    'war': {'min': 300, 'max': 1000, 'sweet': 600},
    'noir': {'min': 50, 'max': 200, 'sweet': 100},
    'adventure': {'min': 150, 'max': 600, 'sweet': 350},
    'biographical': {'min': 50, 'max': 300, 'sweet': 150},
}
EXTRAS_COST_PER_PERSON = 500  # $500 per extra


# === EQUIPMENT PACKAGES ===
EQUIPMENT_PACKAGES = [
    {'id': 'basic_cam', 'name': 'Telecamere Base', 'desc': 'Kit telecamere HD standard per produzioni indipendenti', 'base_cost': 50000, 'quality_bonus': 1.5, 'tier': 'base'},
    {'id': 'pro_cam', 'name': 'Telecamere Professionali', 'desc': 'RED Komodo 6K + set di ottiche Zeiss cinematografiche', 'base_cost': 150000, 'quality_bonus': 3.5, 'tier': 'pro'},
    {'id': 'lighting_std', 'name': 'Illuminazione Standard', 'desc': 'Kit luci LED Arri Skypanel + diffusori e bandiere', 'base_cost': 40000, 'quality_bonus': 1.0, 'tier': 'base'},
    {'id': 'lighting_pro', 'name': 'Illuminazione Cinematografica', 'desc': 'Sistema HMI 18K + Fresnel Tungsten + Kino Flo per ogni set', 'base_cost': 120000, 'quality_bonus': 2.5, 'tier': 'pro'},
    {'id': 'audio_std', 'name': 'Audio Standard', 'desc': 'Microfoni boom Sennheiser + mixer portatile', 'base_cost': 30000, 'quality_bonus': 1.0, 'tier': 'base'},
    {'id': 'audio_dolby', 'name': 'Audio Dolby Atmos', 'desc': 'Registrazione Dolby Atmos completa con 128 tracce + foley studio', 'base_cost': 200000, 'quality_bonus': 4.0, 'tier': 'premium'},
    {'id': 'steadicam', 'name': 'Steadicam & Gimbal', 'desc': 'DJI Ronin 4D + Steadicam Archer per riprese fluide', 'base_cost': 80000, 'quality_bonus': 2.0, 'tier': 'pro'},
    {'id': 'crane_drone', 'name': 'Gru e Droni Cinematografici', 'desc': 'Gru Technocrane 50ft + DJI Inspire 3 per riprese aeree mozzafiato', 'base_cost': 180000, 'quality_bonus': 3.0, 'tier': 'premium'},
    {'id': 'green_screen', 'name': 'Studio Green Screen', 'desc': 'Cyclorama 360° con tracking markers per compositing perfetto', 'base_cost': 100000, 'quality_bonus': 2.5, 'tier': 'pro'},
    {'id': 'imax_rig', 'name': 'Rig IMAX 70mm', 'desc': 'Telecamere IMAX proprietarie per la massima risoluzione e impatto visivo', 'base_cost': 500000, 'quality_bonus': 6.0, 'tier': 'premium'},
]

# === SPONSORS ===
SPONSORS = [
    {'id': 'sip_cola', 'name': 'SipCola', 'fame': 95, 'logo_color': '#E31937', 'category': 'beverage'},
    {'id': 'nexus_auto', 'name': 'Nexus Automotive', 'fame': 90, 'logo_color': '#1A3D7C', 'category': 'automotive'},
    {'id': 'royal_air', 'name': 'Royal Air Lines', 'fame': 85, 'logo_color': '#003366', 'category': 'travel'},
    {'id': 'volt_tech', 'name': 'VoltTech Electronics', 'fame': 88, 'logo_color': '#00C9FF', 'category': 'tech'},
    {'id': 'bella_moda', 'name': 'Bella Moda', 'fame': 82, 'logo_color': '#FF69B4', 'category': 'fashion'},
    {'id': 'aurora_bank', 'name': 'Aurora Bank', 'fame': 78, 'logo_color': '#DAA520', 'category': 'finance'},
    {'id': 'titan_sport', 'name': 'Titan Sport', 'fame': 75, 'logo_color': '#FF4500', 'category': 'sport'},
    {'id': 'sapore_italiano', 'name': 'Sapore Italiano', 'fame': 70, 'logo_color': '#228B22', 'category': 'food'},
    {'id': 'golden_watch', 'name': 'Golden Watch Co.', 'fame': 92, 'logo_color': '#B8860B', 'category': 'luxury'},
    {'id': 'planet_green', 'name': 'Planet Green Energy', 'fame': 65, 'logo_color': '#32CD32', 'category': 'energy'},
    {'id': 'star_mobile', 'name': 'StarMobile', 'fame': 80, 'logo_color': '#6A0DAD', 'category': 'tech'},
    {'id': 'domina_hotels', 'name': 'Domina Hotels', 'fame': 72, 'logo_color': '#8B4513', 'category': 'hospitality'},
    {'id': 'viaggio_cruise', 'name': 'Viaggio Cruise', 'fame': 68, 'logo_color': '#4169E1', 'category': 'travel'},
    {'id': 'ferro_costruzioni', 'name': 'Ferro Costruzioni', 'fame': 55, 'logo_color': '#708090', 'category': 'construction'},
    {'id': 'natura_cosmetici', 'name': 'Natura Cosmetici', 'fame': 60, 'logo_color': '#DDA0DD', 'category': 'beauty'},
    {'id': 'blitz_energy', 'name': 'Blitz Energy Drink', 'fame': 50, 'logo_color': '#00FF00', 'category': 'beverage'},
    {'id': 'omega_pharma', 'name': 'Omega Pharma', 'fame': 73, 'logo_color': '#20B2AA', 'category': 'health'},
    {'id': 'cinema_world', 'name': 'Cinema World Magazine', 'fame': 45, 'logo_color': '#FF6347', 'category': 'media'},
    {'id': 'velox_logistics', 'name': 'Velox Logistics', 'fame': 40, 'logo_color': '#FF8C00', 'category': 'logistics'},
    {'id': 'primo_assicurazioni', 'name': 'Primo Assicurazioni', 'fame': 58, 'logo_color': '#4682B4', 'category': 'insurance'},
]

# === CGI PACKAGES by Genre ===
CGI_PACKAGES = {
    'horror': [
        {'id': 'horror_creatures', 'name': 'Mostri e Creature', 'cost': 500000, 'quality_bonus': 3.5, 'desc': 'Creature terrificanti in CGI'},
        {'id': 'horror_haunted', 'name': 'Ambienti Infestati', 'cost': 350000, 'quality_bonus': 2.5, 'desc': 'Case infestate, cimiteri oscuri'},
        {'id': 'horror_gore', 'name': 'Effetti Sangue & Gore', 'cost': 250000, 'quality_bonus': 2.0, 'desc': 'Effetti splatter realistici'},
        {'id': 'horror_demons', 'name': 'Demoni e Fantasmi', 'cost': 450000, 'quality_bonus': 3.0, 'desc': 'Entita soprannaturali'},
        {'id': 'horror_undead', 'name': 'Zombie e Non-Morti', 'cost': 400000, 'quality_bonus': 2.8, 'desc': 'Orde di zombie in CGI'},
        {'id': 'horror_transform', 'name': 'Trasformazioni', 'cost': 600000, 'quality_bonus': 4.0, 'desc': 'Licantropi, mutazioni, possessioni'},
    ],
    'sci_fi': [
        {'id': 'scifi_ships', 'name': 'Astronavi', 'cost': 700000, 'quality_bonus': 4.0, 'desc': 'Flotte spaziali e caccia stellari'},
        {'id': 'scifi_planets', 'name': 'Pianeti e Galassie', 'cost': 600000, 'quality_bonus': 3.5, 'desc': 'Mondi alieni e nebulose'},
        {'id': 'scifi_robots', 'name': 'Robot e Androidi', 'cost': 500000, 'quality_bonus': 3.0, 'desc': 'Intelligenze artificiali e mech'},
        {'id': 'scifi_portals', 'name': 'Portali e Wormhole', 'cost': 400000, 'quality_bonus': 2.5, 'desc': 'Varchi dimensionali e teletrasporto'},
        {'id': 'scifi_aliens', 'name': 'Alieni', 'cost': 550000, 'quality_bonus': 3.2, 'desc': 'Razze aliene e creature extraterrestri'},
        {'id': 'scifi_weapons', 'name': 'Armi Futuristiche', 'cost': 350000, 'quality_bonus': 2.0, 'desc': 'Laser, blaster, scudi energetici'},
        {'id': 'scifi_cities', 'name': 'Citta del Futuro', 'cost': 650000, 'quality_bonus': 3.8, 'desc': 'Megalopoli futuristiche e cyberpunk'},
    ],
    'action': [
        {'id': 'action_explosions', 'name': 'Esplosioni Massive', 'cost': 400000, 'quality_bonus': 3.0, 'desc': 'Esplosioni cinematografiche'},
        {'id': 'action_vehicles', 'name': 'Veicoli Militari', 'cost': 500000, 'quality_bonus': 3.2, 'desc': 'Tank, elicotteri, jet da combattimento'},
        {'id': 'action_destruction', 'name': 'Crolli e Distruzione', 'cost': 600000, 'quality_bonus': 3.5, 'desc': 'Edifici che crollano, tsunami di detriti'},
        {'id': 'action_chase', 'name': 'Inseguimenti Epici', 'cost': 350000, 'quality_bonus': 2.5, 'desc': 'Inseguimenti ad alta velocita'},
        {'id': 'action_stunts', 'name': 'Acrobazie Impossibili', 'cost': 300000, 'quality_bonus': 2.0, 'desc': 'Salti, cadute, combattimenti'},
        {'id': 'action_weapons', 'name': 'Arsenale Hi-Tech', 'cost': 250000, 'quality_bonus': 1.8, 'desc': 'Armi speciali e gadget'},
    ],
    'fantasy': [
        {'id': 'fantasy_dragons', 'name': 'Draghi e Creature', 'cost': 700000, 'quality_bonus': 4.0, 'desc': 'Draghi, fenici, grifoni'},
        {'id': 'fantasy_magic', 'name': 'Magie e Incantesimi', 'cost': 400000, 'quality_bonus': 2.8, 'desc': 'Effetti magici e sortilegi'},
        {'id': 'fantasy_kingdoms', 'name': 'Castelli e Regni', 'cost': 550000, 'quality_bonus': 3.2, 'desc': 'Regni fantastici e fortezze'},
        {'id': 'fantasy_forests', 'name': 'Boschi Incantati', 'cost': 350000, 'quality_bonus': 2.5, 'desc': 'Foreste magiche e rovine antiche'},
        {'id': 'fantasy_portals', 'name': 'Portali Dimensionali', 'cost': 400000, 'quality_bonus': 2.8, 'desc': 'Varchi tra mondi e dimensioni'},
        {'id': 'fantasy_artifacts', 'name': 'Armi e Artefatti', 'cost': 300000, 'quality_bonus': 2.0, 'desc': 'Spade leggendarie e reliquie'},
    ],
    'adventure': [
        {'id': 'adv_environments', 'name': 'Ambienti Esotici', 'cost': 400000, 'quality_bonus': 2.8, 'desc': 'Giungle, deserti, oceani'},
        {'id': 'adv_temples', 'name': 'Templi e Rovine', 'cost': 350000, 'quality_bonus': 2.5, 'desc': 'Templi antichi e trappole'},
        {'id': 'adv_creatures', 'name': 'Creature Selvagge', 'cost': 450000, 'quality_bonus': 3.0, 'desc': 'Animali giganti e bestie mitiche'},
        {'id': 'adv_underwater', 'name': 'Mondi Sottomarini', 'cost': 500000, 'quality_bonus': 3.2, 'desc': 'Citta sottomarine e abissi'},
        {'id': 'adv_sky', 'name': 'Volo e Paracadutismo', 'cost': 300000, 'quality_bonus': 2.0, 'desc': 'Scene aeree mozzafiato'},
        {'id': 'adv_treasure', 'name': 'Tesori e Reliquie', 'cost': 250000, 'quality_bonus': 1.8, 'desc': 'Tesori nascosti e mappe antiche'},
    ],
    'war': [
        {'id': 'war_battles', 'name': 'Battaglie Epiche', 'cost': 700000, 'quality_bonus': 4.0, 'desc': 'Scontri su larga scala'},
        {'id': 'war_aircraft', 'name': 'Aerei e Bombardieri', 'cost': 500000, 'quality_bonus': 3.0, 'desc': 'Combattimenti aerei'},
        {'id': 'war_naval', 'name': 'Battaglie Navali', 'cost': 600000, 'quality_bonus': 3.5, 'desc': 'Navi da guerra e sommergibili'},
        {'id': 'war_trenches', 'name': 'Trincee e Bunker', 'cost': 350000, 'quality_bonus': 2.5, 'desc': 'Ambienti di guerra'},
        {'id': 'war_tanks', 'name': 'Corazzati e Artiglieria', 'cost': 450000, 'quality_bonus': 2.8, 'desc': 'Tank e pezzi di artiglieria'},
        {'id': 'war_aftermath', 'name': 'Devastazione Bellica', 'cost': 400000, 'quality_bonus': 2.5, 'desc': 'Citta distrutte e rovine'},
    ],
}
# Default CGI for genres not listed
CGI_DEFAULT = [
    {'id': 'default_environments', 'name': 'Ambientazioni Digitali', 'cost': 300000, 'quality_bonus': 2.0, 'desc': 'Set virtuali e sfondi'},
    {'id': 'default_crowd', 'name': 'Folla Digitale', 'cost': 250000, 'quality_bonus': 1.5, 'desc': 'Folle simulate in CGI'},
    {'id': 'default_weather', 'name': 'Meteo Estremo', 'cost': 200000, 'quality_bonus': 1.2, 'desc': 'Tempeste, tornado, tsunami'},
    {'id': 'default_vehicles', 'name': 'Veicoli', 'cost': 350000, 'quality_bonus': 2.0, 'desc': 'Auto, moto, aerei'},
    {'id': 'default_fire', 'name': 'Fuoco e Fiamme', 'cost': 200000, 'quality_bonus': 1.5, 'desc': 'Incendi e esplosioni piccole'},
    {'id': 'default_digital', 'name': 'Ritocco Digitale', 'cost': 150000, 'quality_bonus': 1.0, 'desc': 'Pulizia e miglioramento digitale'},
]

# === VFX PACKAGES by Genre ===
VFX_PACKAGES = {
    'horror': [
        {'id': 'vfx_horror_atmo', 'name': 'Atmosfera Oscura', 'cost': 150000, 'quality_bonus': 1.5, 'desc': 'Nebbia, ombre, distorsioni'},
        {'id': 'vfx_horror_jump', 'name': 'Jump Scare FX', 'cost': 100000, 'quality_bonus': 1.0, 'desc': 'Effetti shock e tensione'},
        {'id': 'vfx_horror_decay', 'name': 'Decomposizione', 'cost': 200000, 'quality_bonus': 1.8, 'desc': 'Invecchiamento, decomposizione'},
        {'id': 'vfx_horror_vision', 'name': 'Visioni e Allucinazioni', 'cost': 180000, 'quality_bonus': 1.5, 'desc': 'Effetti psichedelici'},
    ],
    'sci_fi': [
        {'id': 'vfx_scifi_holo', 'name': 'Ologrammi', 'cost': 200000, 'quality_bonus': 1.8, 'desc': 'Display olografici e interfacce'},
        {'id': 'vfx_scifi_shield', 'name': 'Scudi Energetici', 'cost': 180000, 'quality_bonus': 1.5, 'desc': 'Barriere e campi di forza'},
        {'id': 'vfx_scifi_teleport', 'name': 'Teletrasporto', 'cost': 150000, 'quality_bonus': 1.2, 'desc': 'Effetti di materializzazione'},
        {'id': 'vfx_scifi_hyper', 'name': 'Iperspazio', 'cost': 250000, 'quality_bonus': 2.0, 'desc': 'Salto nell\'iperspazio e velocita luce'},
    ],
    'action': [
        {'id': 'vfx_action_slow', 'name': 'Slow Motion', 'cost': 120000, 'quality_bonus': 1.2, 'desc': 'Rallenti cinematografici'},
        {'id': 'vfx_action_impact', 'name': 'Effetti Impatto', 'cost': 150000, 'quality_bonus': 1.5, 'desc': 'Shockwave e onde d\'urto'},
        {'id': 'vfx_action_fire', 'name': 'Fuoco e Fiamme', 'cost': 180000, 'quality_bonus': 1.5, 'desc': 'Incendi ed effetti pirotecnici'},
        {'id': 'vfx_action_debris', 'name': 'Detriti e Polvere', 'cost': 100000, 'quality_bonus': 1.0, 'desc': 'Particelle, polvere, frammenti'},
    ],
    'fantasy': [
        {'id': 'vfx_fantasy_glow', 'name': 'Aura Magica', 'cost': 150000, 'quality_bonus': 1.5, 'desc': 'Effetti luminosi e particelle magiche'},
        {'id': 'vfx_fantasy_morph', 'name': 'Metamorfosi', 'cost': 200000, 'quality_bonus': 1.8, 'desc': 'Trasformazioni e shape-shifting'},
        {'id': 'vfx_fantasy_elemental', 'name': 'Elementi Naturali', 'cost': 180000, 'quality_bonus': 1.5, 'desc': 'Fuoco magico, ghiaccio, fulmini'},
        {'id': 'vfx_fantasy_enchant', 'name': 'Incantesimi', 'cost': 160000, 'quality_bonus': 1.2, 'desc': 'Rune, cerchi magici, evocazioni'},
    ],
}
VFX_DEFAULT = [
    {'id': 'vfx_default_color', 'name': 'Color Grading Pro', 'cost': 100000, 'quality_bonus': 1.0, 'desc': 'Correzione colore cinematografica'},
    {'id': 'vfx_default_composite', 'name': 'Compositing', 'cost': 150000, 'quality_bonus': 1.2, 'desc': 'Integrazione effetti e green screen'},
    {'id': 'vfx_default_particle', 'name': 'Particelle', 'cost': 120000, 'quality_bonus': 1.0, 'desc': 'Pioggia, neve, scintille'},
    {'id': 'vfx_default_cleanup', 'name': 'Pulizia Digitale', 'cost': 80000, 'quality_bonus': 0.8, 'desc': 'Rimozione cavi, correzioni'},
]

# ==================== MODELS ====================

class FilmProposalRequest(BaseModel):
    title: str
    genre: str
    subgenres: List[str]  # Up to 3 subgenres
    pre_screenplay: str  # 100-500 chars
    locations: List[str]  # Multiple locations
    purchased_screenplay_id: Optional[str] = None  # If using a purchased screenplay
    release_type: str = 'immediate'  # immediate or coming_soon

class CastSpeedUpRequest(BaseModel):
    role_type: str  # director, screenwriter, actors, composer

class SelectCastRequest(BaseModel):
    role_type: str
    proposal_id: str
    actor_role: Optional[str] = None  # Protagonista, Co-Protagonista, Antagonista, Supporto, Cameo

class ScreenplaySubmitRequest(BaseModel):
    mode: str  # 'ai', 'pre_only', 'manual'
    manual_text: Optional[str] = None

class RemasterRequest(BaseModel):
    pass

class ProductionSetupRequest(BaseModel):
    extras_count: int = 50  # 50-1000
    cgi_packages: List[str] = []  # list of CGI package IDs
    vfx_packages: List[str] = []  # list of VFX package IDs

class SpeedUpShootingRequest(BaseModel):
    option: str  # 'fast' (50%), 'faster' (80%), 'instant'

class BuzzVoteRequest(BaseModel):
    vote: str  # 'high', 'medium', 'low'

# ==================== CONSTANTS ====================

# Max simultaneous films based on level
def get_max_films(level: int) -> int:
    if level >= 10: return 6
    if level >= 5: return 4
    return 2

# CinePass cost per step
STEP_CINEPASS = {
    'creation': 1,
    'proposal': 1,
    'casting': 2,
    'screenplay': 2,
    'pre_production': 3,
    'shooting': 3
}

# Genre-location affinity bonuses for pre-IMDb
GENRE_LOCATION_BONUS = {
    'horror': ['Gothic Castle', 'Transylvania Forest', 'Abandoned Hospital', 'Catacombs Paris'],
    'romance': ['Paris Streets', 'Amalfi Coast', 'Santorini', 'Venice Canals'],
    'action': ['New York City', 'Dubai Marina', 'Hong Kong Neon', 'Tokyo District'],
    'sci_fi': ['Tokyo District', 'Dubai Marina', 'Shanghai Bund', 'Iceland Landscape'],
    'western': ['Monument Valley', 'Texas Ranch', 'Mexican Desert'],
    'war': ['Normandy Beaches', 'Berlino', 'Moscow'],
    'noir': ['Los Angeles', 'Chicago', 'New York City'],
    'adventure': ['Amazon Rainforest', 'Sahara Desert', 'Himalaya'],
}

# Genre combo rarity bonus (rare genre+subgenre combos score higher potential)
RARE_COMBOS = {
    ('horror', 'Gothic'): 0.6,
    ('sci_fi', 'Cyberpunk'): 0.5,
    ('noir', 'Tech-Noir'): 0.7,
    ('western', 'Spaghetti Western'): 0.6,
    ('animation', 'Adult Animation'): 0.5,
    ('documentary', 'True Crime'): 0.4,
    ('musical', 'Rock Musical'): 0.4,
}


# ==================== PRE-IMDB CALCULATION ====================

def calculate_pre_imdb(title: str, genre: str, subgenres: list, pre_screenplay: str, locations: list) -> dict:
    """Calculate pre-IMDb score based on film proposal quality."""
    base = 4.0 + random.uniform(0, 1.5)
    factors = {}

    # Genre popularity
    popular_genres = ['action', 'comedy', 'thriller', 'horror', 'sci_fi']
    if genre in popular_genres:
        bonus = 0.4
        factors['genere_popolare'] = f'+{bonus}'
        base += bonus

    # Rare genre+subgenre combo
    subgenre_str = ' '.join(subgenres) if subgenres else ''
    for (g, sg), bonus in RARE_COMBOS.items():
        if genre == g and sg.lower() in subgenre_str.lower():
            factors['combo_rara'] = f'+{bonus}'
            base += bonus
            break

    # Multiple subgenres bonus
    if len(subgenres) >= 2:
        bonus = 0.3
        factors['multi_sottogenere'] = f'+{bonus}'
        base += bonus

    # Pre-screenplay quality (length factor)
    screenplay_len = len(pre_screenplay.strip())
    if screenplay_len >= 400:
        bonus = 0.8
    elif screenplay_len >= 250:
        bonus = 0.5
    elif screenplay_len >= 150:
        bonus = 0.3
    else:
        bonus = 0.0
    if bonus > 0:
        factors['qualita_sinossi'] = f'+{bonus}'
        base += bonus

    # Location fit - check all locations
    location_genres = GENRE_LOCATION_BONUS.get(genre, [])
    loc_match = any(loc_g.lower() in loc_name.lower() for loc_name in locations for loc_g in location_genres)
    if loc_match:
        bonus = 0.5
        factors['location_perfetta'] = f'+{bonus}'
        base += bonus

    # Multiple locations bonus
    if len(locations) >= 2:
        bonus = 0.2 * min(len(locations) - 1, 3)
        factors['location_multiple'] = f'+{bonus}'
        base += bonus

    # Title quality (longer/creative titles score slightly better)
    if len(title) > 15:
        bonus = 0.2
        factors['titolo_evocativo'] = f'+{bonus}'
        base += bonus

    # Hidden random factor ±1.5
    hidden = round(random.uniform(-1.5, 1.5), 1)
    factors['fattore_nascosto'] = '???'
    base += hidden

    # Clamp to 1.0-10.0
    score = round(max(1.0, min(10.0, base)), 1)

    return {
        'score': score,
        'factors': factors,
        'hidden_factor': hidden  # stored but not shown to player
    }


# ==================== CAST PROPOSAL GENERATOR ====================


async def _generate_guest_star_proposals(film_project: dict, user_id: str) -> list:
    """Generate guest star vocal proposals for animation films.
    Only famous/superstar actors, high cost, optional but give bonus.
    """
    famous_actors = await db.people.aggregate([
        {'$match': {'type': 'actor', 'fame_category': {'$in': ['famous', 'superstar']}}},
        {'$sample': {'size': 30}},
        {'$project': {'_id': 0, 'id': 1, 'name': 1, 'skills': 1, 'fame_score': 1,
                       'fame_category': 1, 'cost_per_film': 1, 'avatar_url': 1,
                       'imdb_rating': 1, 'films_count': 1,
                       'gender': 1, 'age': 1, 'nationality': 1,
                       'strong_genres': 1, 'adaptable_genre': 1,
                       'strong_genres_names': 1, 'adaptable_genre_name': 1,
                       'skill_caps': 1, 'hidden_talent': 1, 'stars': 1}}
    ]).to_list(30)

    for person in famous_actors:
        fc = person.get('fame_category', 'famous')
        person['fame_label'] = 'Superstar' if fc == 'superstar' else 'Famoso'
        person['growth_trend'] = 'stable'
        person['has_worked_with_player'] = False
        person['is_guest_star'] = True

    agent_names = ["Voice Stars Agency", "Dubbing Elite", "Celebrity Voices", "Star Voice Mgmt"]
    proposals = []
    for i, person in enumerate(famous_actors[:8]):
        base_cost = person.get('cost_per_film', 500000)
        guest_cost = int(base_cost * 2.5)  # Guest stars cost 2.5x
        delay = random.randint(5, 25) + i * random.randint(2, 5)
        proposals.append({
            'id': str(uuid.uuid4()),
            'person': person,
            'agent_name': random.choice(agent_names),
            'delay_minutes': delay,
            'available_at': None,
            'status': 'pending',
            'cost': guest_cost,
            'negotiable': False,
            'is_guest_star': True,
        })
    return proposals


async def generate_cast_proposals(film_project: dict, role_type: str) -> list:
    """Generate cast proposals from agents for a specific role.
    For animation films, actors are Guest Star Vocali (famous only, optional).
    """
    pre_imdb = film_project.get('pre_imdb_score', 5.0)
    genre = film_project.get('genre', 'drama')
    user_id = film_project['user_id']
    is_animation = genre == 'animation'

    # For animation films, actors become guest star vocali
    if is_animation and role_type == 'actors':
        return await _generate_guest_star_proposals(film_project, user_id)

    # Get user info for proposal quality and dynamic casting
    user = await db.users.find_one({'id': user_id}, {'_id': 0, 'fame': 1, 'total_xp': 1})
    fame = user.get('fame', 50) if user else 50

    # Number of agents varies per role (variable, not fixed!)
    # DOUBLED base for actors to provide more choices
    base_agents = 1 + int(pre_imdb / 4) + int(fame / 150)
    role_bonus = {'directors': random.randint(0, 2), 'screenwriters': random.randint(0, 2),
                  'actors': random.randint(2, 5), 'composers': random.randint(0, 2)}
    num_agents = base_agents + role_bonus.get(role_type, 0)
    num_agents = max(2, min(num_agents, 7))

    # Each agent brings 1-4 candidates (doubled for actors)
    total_candidates = 0
    agent_batches = []
    for _ in range(num_agents):
        candidates_per_agent = random.randint(2, 4) if role_type == 'actors' else random.randint(1, 3)
        agent_batches.append(candidates_per_agent)
        total_candidates += candidates_per_agent
    total_candidates = min(total_candidates, 16)  # Doubled max from 8 to 16

    # Determine people type
    people_type = role_type
    if role_type == 'actors':
        people_type = 'actor'
    elif role_type == 'screenwriters':
        people_type = 'screenwriter'
    elif role_type == 'directors':
        people_type = 'director'
    elif role_type == 'composers':
        people_type = 'composer'

    # === DYNAMIC CASTING: Fame-based candidate selection ===
    # Low-fame players get more unknown/rising talent
    # High-fame players get better access to stars
    fame_filters = []
    if fame < 30:
        # Mostly unknowns and rising stars
        fame_filters = [
            {'$match': {'type': people_type, 'fame_category': {'$in': ['unknown', 'rising']}}},
        ]
        sample_size = total_candidates * 3
        # Also fetch a few famous for variety
        famous_sample = 2
    elif fame < 60:
        fame_filters = [
            {'$match': {'type': people_type, 'fame_category': {'$in': ['unknown', 'rising', 'famous']}}},
        ]
        sample_size = total_candidates * 3
        famous_sample = 0
    else:
        # High fame: full access
        fame_filters = [
            {'$match': {'type': people_type}},
        ]
        sample_size = total_candidates * 3
        famous_sample = 0

    # Get people with full details including gender, age, nationality, fame info
    people = await db.people.aggregate([
        *fame_filters,
        {'$sample': {'size': sample_size}},
        {'$project': {'_id': 0, 'id': 1, 'name': 1, 'skills': 1, 'fame_score': 1, 'fame': 1,
                       'category': 1, 'fame_category': 1,
                       'cost_per_film': 1, 'avatar_url': 1, 'rejection_rate': 1,
                       'imdb_rating': 1, 'films_count': 1,
                       'gender': 1, 'age': 1, 'nationality': 1,
                       'films_worked': 1, 'skill_changes': 1,
                       'strong_genres': 1, 'adaptable_genre': 1,
                       'strong_genres_names': 1, 'adaptable_genre_name': 1,
                       'skill_caps': 1, 'hidden_talent': 1, 'stars': 1, 'agency_name': 1}}
    ]).to_list(sample_size)

    # For low-fame players, also add a couple of famous people for aspiration
    if famous_sample > 0 and fame < 30:
        famous_people = await db.people.aggregate([
            {'$match': {'type': people_type, 'fame_category': {'$in': ['famous', 'superstar']}}},
            {'$sample': {'size': famous_sample}},
            {'$project': {'_id': 0, 'id': 1, 'name': 1, 'skills': 1, 'fame_score': 1, 'fame': 1,
                           'category': 1, 'fame_category': 1,
                           'cost_per_film': 1, 'avatar_url': 1, 'rejection_rate': 1,
                           'imdb_rating': 1, 'films_count': 1,
                           'gender': 1, 'age': 1, 'nationality': 1,
                           'films_worked': 1, 'skill_changes': 1,
                           'strong_genres': 1, 'adaptable_genre': 1,
                           'strong_genres_names': 1, 'adaptable_genre_name': 1,
                           'skill_caps': 1, 'hidden_talent': 1, 'stars': 1, 'agency_name': 1}}
        ]).to_list(famous_sample)
        people.extend(famous_people)

    # Enrich person data: determine fame label, growth trend, worked-with
    user_films = await db.films.find(
        {'owner_id': user_id}, {'_id': 0, 'cast': 1}
    ).to_list(200)
    worked_with_ids = set()
    for film in user_films:
        cast = film.get('cast', {})
        if isinstance(cast, list):
            for member in cast:
                if isinstance(member, dict) and member.get('id'):
                    worked_with_ids.add(member['id'])
            continue
        for actor in cast.get('actors', []):
            if actor.get('id'):
                worked_with_ids.add(actor['id'])
        for role_key in ['director', 'screenwriter', 'composer']:
            p = cast.get(role_key, {})
            if p and p.get('id'):
                worked_with_ids.add(p['id'])

    for person in people:
        # Fame label
        fc = person.get('fame_category', 'unknown')
        fame_labels = {
            'unknown': 'Sconosciuto', 'rising': 'Emergente',
            'famous': 'Famoso', 'superstar': 'Superstar'
        }
        person['fame_label'] = fame_labels.get(fc, 'Sconosciuto')

        # Growth trend from skill_changes
        sc = person.get('skill_changes', {})
        if sc:
            total_change = sum(sc.values())
            if total_change > 5:
                person['growth_trend'] = 'rising'
            elif total_change < -3:
                person['growth_trend'] = 'declining'
            else:
                person['growth_trend'] = 'stable'
        else:
            person['growth_trend'] = 'stable'

        # Has worked with player before
        person['has_worked_with_player'] = person.get('id') in worked_with_ids

        # Clean up fields not needed in frontend
        person.pop('skill_changes', None)
        person.pop('films_worked', None)

    # Sort by fame score and take appropriate number
    people.sort(key=lambda p: p.get('fame_score', p.get('fame', 0)), reverse=True)

    # Higher IMDb films attract better candidates
    if pre_imdb >= 8:
        selected = people[:total_candidates]
    elif pre_imdb >= 6:
        selected = people[1:total_candidates + 1]
    else:
        selected = people[total_candidates:][:total_candidates]

    if not selected:
        selected = people[:total_candidates]

    # Generate proposal timing - grouped by agent
    agent_names = [
        "Agenzia Stella", "Management Rossa", "Talent Milano", "Star Agency",
        "Cinema Partners", "Golden Cast", "Elite Agents", "Silver Screen Mgmt",
        "Agenzia del Cinema", "World Talent Group", "Cinecittà Talent", "Roma Casting"
    ]
    proposals = []
    candidate_idx = 0
    for agent_idx, batch_size in enumerate(agent_batches):
        # Base delay per agent
        base_minutes = max(3, (10 - pre_imdb) * 6)
        agent_delay = int(base_minutes + random.uniform(0, base_minutes * 0.4) + agent_idx * random.randint(5, 20))

        agent_name = random.choice(agent_names)

        for j in range(batch_size):
            if candidate_idx >= len(selected):
                break
            person = selected[candidate_idx]
            candidate_idx += 1

            proposals.append({
                'id': str(uuid.uuid4()),
                'person': person,
                'agent_name': agent_name,
                'delay_minutes': agent_delay + j * random.randint(0, 3),
                'available_at': None,
                'status': 'pending',
                'cost': person.get('cost_per_film', 50000),
                'negotiable': random.random() < 0.3,
            })

    return proposals


# ==================== ENDPOINTS ====================

@router.get("/film-pipeline/counts")
async def get_pipeline_counts(user: dict = Depends(get_current_user)):
    """Get film counts per pipeline phase for badge display."""
    pipeline = [
        {'$match': {'user_id': user['id'], 'status': {'$nin': ['discarded', 'abandoned']}}},
        {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
    ]
    results = await db.film_projects.aggregate(pipeline).to_list(20)
    counts = {r['_id']: r['count'] for r in results}

    # Also count films in shooting (from films collection)
    shooting_count = await db.films.count_documents({
        'owner_id': user['id'],
        'status': {'$in': ['shooting', 'in_production']}
    })

    from server import get_level_from_xp
    level = get_level_from_xp(user.get('total_xp', 0))['level']

    return {
        'creation': counts.get('draft', 0),
        'proposed': counts.get('proposed', 0) + counts.get('coming_soon', 0) + counts.get('ready_for_casting', 0),
        'casting': counts.get('casting', 0),
        'screenplay': counts.get('screenplay', 0),
        'pre_production': counts.get('pre_production', 0),
        'shooting': shooting_count,
        'max_simultaneous': get_max_films(level),
        'total_active': sum(counts.values())
    }


@router.post("/film-pipeline/create")
async def create_film_proposal(req: FilmProposalRequest, user: dict = Depends(get_current_user)):
    """Step 1: Create a film proposal with title, genre, subgenre, pre-screenplay, location."""
    # Validate
    if len(req.pre_screenplay.strip()) < 100:
        raise HTTPException(status_code=400, detail="La pre-sceneggiatura deve essere di almeno 100 caratteri")
    if len(req.pre_screenplay.strip()) > 500:
        raise HTTPException(status_code=400, detail="La pre-sceneggiatura non può superare i 500 caratteri")
    if not req.title.strip():
        raise HTTPException(status_code=400, detail="Il titolo è obbligatorio")

    # Check max simultaneous films
    from server import get_level_from_xp
    level = get_level_from_xp(user.get('total_xp', 0))['level']
    max_films = get_max_films(level)
    active = await db.film_projects.count_documents({
        'user_id': user['id'],
        'status': {'$nin': ['discarded', 'abandoned', 'completed']}
    })
    if active >= max_films:
        raise HTTPException(status_code=400, detail=f"Puoi avere massimo {max_films} film in lavorazione (livello {level})")

    # CinePass cost
    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['creation']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Fund cost for creation step
    creation_cost = 25000 + random.randint(0, 15000)
    if user.get('funds', 0) < creation_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${creation_cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -creation_cost}})

    # Calculate pre-IMDb
    imdb_result = calculate_pre_imdb(req.title, req.genre, req.subgenres, req.pre_screenplay, req.locations)

    # Find location data for all selected locations
    from server import LOCATIONS
    selected_locations = []
    for loc_name in req.locations:
        loc = next((l for l in LOCATIONS if l['name'] == loc_name), {'name': loc_name, 'cost_per_day': 50000, 'category': 'other'})
        selected_locations.append(loc)

    project = {
        'id': str(uuid.uuid4()),
        'user_id': user['id'],
        'status': 'proposed',
        'release_type': req.release_type if req.release_type in ('immediate', 'coming_soon') else 'immediate',
        'title': req.title.strip(),
        'genre': req.genre,
        'subgenres': req.subgenres,
        'subgenre': req.subgenres[0] if req.subgenres else '',
        'pre_screenplay': req.pre_screenplay.strip(),
        'locations': selected_locations,
        'location': selected_locations[0] if selected_locations else {},
        'location_name': req.locations[0] if req.locations else '',
        'pre_imdb_score': imdb_result['score'],
        'pre_imdb_factors': imdb_result['factors'],
        'hidden_factor': imdb_result['hidden_factor'],
        'cast': {'director': None, 'screenwriter': None, 'actors': [], 'composer': None},
        'cast_proposals': {},
        'costs_paid': {'creation': creation_cost},
        'cinepass_paid': {'creation': cp_cost},
        'hype_score': 0,
        'scheduled_release_at': None,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

    # If using a purchased screenplay, mark it as used and add bonus
    if req.purchased_screenplay_id:
        ps = await db.purchased_screenplays.find_one(
            {'id': req.purchased_screenplay_id, 'user_id': user['id'], 'used': False}
        )
        if ps:
            await db.purchased_screenplays.update_one(
                {'id': req.purchased_screenplay_id}, {'$set': {'used': True, 'used_in_film': project['id']}}
            )
            project['from_purchased_screenplay'] = True
            project['purchased_screenplay_quality'] = ps.get('quality', 50)
            project['purchased_screenplay_writer'] = ps.get('writer_name', '')

    await db.film_projects.insert_one(project)
    project.pop('_id', None)

    return {
        'success': True,
        'message': f'"{req.title}" proposto! Pre-valutazione IMDb: {imdb_result["score"]}',
        'project': project
    }


@router.get("/film-pipeline/proposals")
async def get_proposals(user: dict = Depends(get_current_user)):
    """Step 2: Get all user's proposed films + coming_soon pre-casting + ready_for_casting films."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': {'$in': ['proposed', 'coming_soon', 'ready_for_casting']},
         '$or': [
             {'coming_soon_type': {'$exists': False}},
             {'coming_soon_type': 'pre_casting'},
             {'status': 'proposed'},
             {'status': 'ready_for_casting'}
         ]},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)
    return {'proposals': projects}


COMING_SOON_TIERS = {
    'short':  {'min_h': 2, 'max_h': 6,  'speedup_cap': 0.20, 'label': 'Breve'},
    'medium': {'min_h': 6, 'max_h': 18, 'speedup_cap': 0.40, 'label': 'Medio'},
    'long':   {'min_h': 18, 'max_h': 48, 'speedup_cap': 0.60, 'label': 'Lungo'},
}


class LaunchComingSoonRequest(BaseModel):
    tier: str = 'short'  # short, medium, long
    hours: float = 4     # within tier range


def _apply_quality_modifier(hours: float, pre_imdb: float) -> tuple:
    """Apply small quality modifier. Returns (modified_hours, modifier_pct)."""
    if pre_imdb >= 8.0:
        mod = 0.20
    elif pre_imdb >= 7.0:
        mod = 0.10
    elif pre_imdb >= 5.0:
        mod = 0.0
    elif pre_imdb >= 3.5:
        mod = -0.10
    else:
        mod = -0.10
    modified = hours * (1 + mod)
    return round(modified, 2), round(mod * 100)


@router.post("/film-pipeline/{project_id}/launch-coming-soon")
async def launch_film_coming_soon(project_id: str, req: LaunchComingSoonRequest, user: dict = Depends(get_current_user)):
    """Launch a proposed film into Coming Soon phase. Requires poster."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'proposed'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(404, "Film non trovato o non in fase Proposte")
    if not project.get('poster_url'):
        raise HTTPException(400, "Devi generare la locandina prima di lanciare il Coming Soon")

    tier = COMING_SOON_TIERS.get(req.tier)
    if not tier:
        raise HTTPException(400, "Tier non valido. Usa: short, medium, long")

    base_hours = max(tier['min_h'], min(tier['max_h'], req.hours))
    pre_imdb = project.get('pre_imdb_score', 5.0)
    final_hours, quality_mod_pct = _apply_quality_modifier(base_hours, pre_imdb)
    final_hours = max(tier['min_h'], min(tier['max_h'] * 1.2, final_hours))

    now = datetime.now(timezone.utc)
    release_at = now + timedelta(hours=final_hours)

    initial_event = {
        'text': f"Coming Soon lanciato! Durata: {final_hours:.1f}h",
        'type': 'neutral',
        'effect_hours': 0,
        'created_at': now.isoformat()
    }
    if quality_mod_pct != 0:
        sign = '+' if quality_mod_pct > 0 else ''
        initial_event['text'] += f" (qualita' {sign}{quality_mod_pct}%)"

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'coming_soon',
            'coming_soon_type': 'pre_casting',
            'coming_soon_tier': req.tier,
            'coming_soon_base_hours': base_hours,
            'coming_soon_final_hours': final_hours,
            'coming_soon_quality_mod_pct': quality_mod_pct,
            'coming_soon_speedup_used': 0.0,
            'coming_soon_speedup_cap': tier['speedup_cap'],
            'coming_soon_min_hours': final_hours * (1 - tier['speedup_cap']),
            'coming_soon_started_at': now.isoformat(),
            'scheduled_release_at': release_at.isoformat(),
            'news_events': [initial_event],
            'updated_at': now.isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'"{project["title"]}" e\' ora in Coming Soon!',
        'tier': req.tier,
        'base_hours': base_hours,
        'quality_mod_pct': quality_mod_pct,
        'final_hours': final_hours,
        'scheduled_release_at': release_at.isoformat(),
        'speedup_cap': tier['speedup_cap']
    }


@router.post("/film-pipeline/{project_id}/discard")
async def discard_film(project_id: str, user: dict = Depends(get_current_user)):
    """Discard a film - it becomes available for other users to buy."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project['status'] in ('completed', 'discarded'):
        raise HTTPException(status_code=400, detail="Non puoi scartare questo film")

    total_spent = sum(project.get('costs_paid', {}).values())
    sale_price = int(total_spent * 0.7)

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'discarded',
            'status_before_discard': project['status'],
            'discarded_at': datetime.now(timezone.utc).isoformat(),
            'discarded_by': user['id'],
            'discarded_by_nickname': user.get('nickname', 'Unknown'),
            'sale_price': sale_price,
            'available_for_purchase': True
        }}
    )

    return {
        'message': f'"{project["title"]}" scartato. Sarà disponibile per altri giocatori a ${sale_price:,}',
        'sale_price': sale_price
    }


@router.post("/film-pipeline/{project_id}/advance-to-casting")
async def advance_to_casting(project_id: str, user: dict = Depends(get_current_user)):
    """Move a proposed/coming_soon/ready_for_casting film to casting phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': {'$in': ['proposed', 'coming_soon', 'ready_for_casting']}},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non in fase Proposte")

    # If coming_soon (pre_casting), check timer expired
    if project['status'] == 'coming_soon':
        if project.get('coming_soon_type') != 'pre_casting':
            raise HTTPException(400, "Questo film non puo' avanzare al casting da questo stato")
        sra = project.get('scheduled_release_at')
        if sra:
            release_dt = datetime.fromisoformat(sra.replace('Z', '+00:00'))
            if release_dt.tzinfo is None:
                release_dt = release_dt.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) < release_dt:
                raise HTTPException(400, "Il periodo Coming Soon non e' ancora terminato")
    # ready_for_casting: timer already expired via scheduler, proceed directly

    # CinePass cost for casting
    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['casting']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Generate cast proposals for all roles
    now = datetime.now(timezone.utc)
    cast_proposals = {}
    for role in ['directors', 'screenwriters', 'actors', 'composers']:
        proposals = await generate_cast_proposals(project, role)
        for p in proposals:
            p['available_at'] = (now + __import__('datetime').timedelta(minutes=p['delay_minutes'])).isoformat()
        cast_proposals[role] = proposals

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'casting',
            'cast_proposals': cast_proposals,
            'casting_started_at': now.isoformat(),
            'cinepass_paid.casting': cp_cost,
            'updated_at': now.isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'"{project["title"]}" in fase Casting! Gli agenti stanno proponendo candidati.',
        'cast_proposals': cast_proposals
    }


@router.get("/film-pipeline/casting")
async def get_casting_films(user: dict = Depends(get_current_user)):
    """Step 3: Get all films in casting phase with proposal status."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    ).sort('casting_started_at', -1).to_list(50)

    now = datetime.now(timezone.utc)

    # Filter out corrupted projects (missing essential casting data)
    valid_projects = []
    for p in projects:
        if not p.get('cast_proposals') and not p.get('cast', {}).get('proposals'):
            # Auto-fix: reset corrupted project to proposed
            await db.film_projects.update_one(
                {'id': p['id']},
                {'$set': {'status': 'proposed', 'reset_reason': 'auto_fix_missing_cast', 'updated_at': now.isoformat()}}
            )
            logging.getLogger(__name__).warning(f"Auto-reset corrupted film {p['id']} ({p.get('title')}) from casting to proposed")
            continue
        valid_projects.append(p)
    projects = valid_projects

    now = datetime.now(timezone.utc)

    # Collect all person IDs to enrich with latest data from people collection
    all_person_ids = set()
    for p in projects:
        for role, proposals in p.get('cast_proposals', {}).items():
            for prop in proposals:
                person = prop.get('person', {})
                pid = person.get('id')
                if pid and not person.get('strong_genres'):
                    all_person_ids.add(pid)

    # Batch-fetch missing rich data
    rich_data_map = {}
    if all_person_ids:
        rich_people = await db.people.find(
            {'id': {'$in': list(all_person_ids)}},
            {'_id': 0, 'id': 1, 'strong_genres': 1, 'adaptable_genre': 1,
             'strong_genres_names': 1, 'adaptable_genre_name': 1,
             'skill_caps': 1, 'hidden_talent': 1, 'agency_name': 1}
        ).to_list(len(all_person_ids))
        for rp in rich_people:
            rich_data_map[rp['id']] = rp

    for p in projects:
        # Update proposal availability + enrich person data
        updated = False
        for role, proposals in p.get('cast_proposals', {}).items():
            for prop in proposals:
                if prop.get('status') == 'pending' and prop.get('available_at'):
                    avail_at = datetime.fromisoformat(prop['available_at'].replace('Z', '+00:00'))
                    if now >= avail_at:
                        prop['status'] = 'available'
                        updated = True
                # Enrich person with rich data if missing
                person = prop.get('person', {})
                pid = person.get('id')
                if pid and pid in rich_data_map and not person.get('strong_genres'):
                    rd = rich_data_map[pid]
                    person['strong_genres'] = rd.get('strong_genres', [])
                    person['adaptable_genre'] = rd.get('adaptable_genre', '')
                    person['strong_genres_names'] = rd.get('strong_genres_names', [])
                    person['adaptable_genre_name'] = rd.get('adaptable_genre_name', '')
                    person['skill_caps'] = rd.get('skill_caps', {})
                    person['hidden_talent'] = rd.get('hidden_talent', 0.5)
                    person['agency_name'] = rd.get('agency_name', '')
        # Persist updated statuses to DB
        if updated:
            await db.film_projects.update_one(
                {'id': p['id']},
                {'$set': {'cast_proposals': p['cast_proposals']}}
            )

    return {'casting_films': projects}


@router.post("/film-pipeline/{project_id}/speed-up-casting")
async def speed_up_casting(project_id: str, req: CastSpeedUpRequest, user: dict = Depends(get_current_user)):
    """Pay credits to make all pending proposals for a role immediately available."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    proposals = project.get('cast_proposals', {}).get(req.role_type, [])
    pending = [p for p in proposals if p.get('status') == 'pending']

    if not pending:
        return {'message': 'Nessuna proposta in attesa', 'cost': 0}

    # Cost: reduced proportional to number of pending
    cost = len(pending) * 5000
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")

    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    # Make all pending proposals available now
    now = datetime.now(timezone.utc).isoformat()
    for prop in proposals:
        if prop.get('status') == 'pending':
            prop['status'] = 'available'
            prop['available_at'] = now

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            f'cast_proposals.{req.role_type}': proposals,
            f'costs_paid.casting_speedup_{req.role_type}': cost,
            'updated_at': now
        }}
    )

    return {
        'message': f'Proposte per {req.role_type} sbloccate! Costo: ${cost:,}',
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/select-cast")
async def select_cast_member(project_id: str, req: SelectCastRequest, user: dict = Depends(get_current_user)):
    """Select a cast member from proposals."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    proposals = project.get('cast_proposals', {}).get(req.role_type, [])
    proposal = next((p for p in proposals if p['id'] == req.proposal_id), None)

    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    if proposal.get('status') != 'available':
        raise HTTPException(status_code=400, detail="Questa proposta non è ancora disponibile")

    # Check rejection (using existing rejection rate)
    rejection_rate = proposal.get('person', {}).get('rejection_rate', 0)
    if random.random() < rejection_rate:
        # Mark as rejected
        proposal['status'] = 'rejected'
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {f'cast_proposals.{req.role_type}': proposals}}
        )
        return {
            'accepted': False,
            'message': f"{proposal['person']['name']} ha rifiutato! Prova con un altro candidato."
        }

    # Accept - set cast member
    person = proposal['person']
    cast_key = req.role_type
    if req.role_type == 'directors':
        cast_key = 'director'
    elif req.role_type == 'screenwriters':
        cast_key = 'screenwriter'
    elif req.role_type == 'composers':
        cast_key = 'composer'

    # Pay cost
    cost = proposal.get('cost', 0)
    if cost > 0 and user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti per ingaggiare. Servono ${cost:,}")
    if cost > 0:
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    # Mark proposal as accepted
    # For actors: keep other proposals available so user can hire more
    # For other roles: mark others as passed (only one allowed)
    for p in proposals:
        if p['id'] == req.proposal_id:
            p['status'] = 'accepted'
        elif cast_key != 'actors' and p.get('status') not in ('rejected',):
            p['status'] = 'passed'

    # Update cast
    if cast_key == 'actors':
        person_with_role = {**person, 'role_in_film': req.actor_role or 'Supporto'}
        actors = project.get('cast', {}).get('actors', [])
        actors.append(person_with_role)
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.actors': actors,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.{cast_key}': person,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )

    # Check if casting is complete
    updated = await db.film_projects.find_one({'id': project_id}, {'_id': 0, 'cast': 1})
    cast = updated.get('cast', {})
    casting_complete = (
        cast.get('director') is not None and
        cast.get('screenwriter') is not None and
        cast.get('composer') is not None and
        len(cast.get('actors', [])) >= 1
    )

    return {
        'accepted': True,
        'message': f"{person['name']} ingaggiato come {cast_key}!",
        'person': person,
        'cost': cost,
        'casting_complete': casting_complete
    }


class RenegotiateRequest(BaseModel):
    role_type: str
    proposal_id: str
    actor_role: str = None

@router.post("/film-pipeline/{project_id}/renegotiate")
async def renegotiate_cast(project_id: str, req: RenegotiateRequest, user: dict = Depends(get_current_user)):
    """Renegotiate with a rejected cast member by offering more money."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    proposals = project.get('cast_proposals', {}).get(req.role_type, [])
    proposal = next((p for p in proposals if p['id'] == req.proposal_id), None)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposta non trovata")
    if proposal.get('status') != 'rejected':
        raise HTTPException(status_code=400, detail="Puoi rinegoziare solo con chi ha rifiutato")

    # Renegotiation: 30% cost increase, lower rejection rate
    original_cost = proposal.get('cost', 0)
    renegotiate_increase = int(original_cost * 0.3)
    new_cost = original_cost + renegotiate_increase
    new_rejection_rate = max(0.05, proposal.get('person', {}).get('rejection_rate', 0.3) - 0.2)

    if user.get('funds', 0) < new_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${new_cost:,} per rinegoziare")

    # Try again with lower rejection rate
    if random.random() < new_rejection_rate:
        proposal['status'] = 'rejected'
        proposal['renegotiate_count'] = proposal.get('renegotiate_count', 0) + 1
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {f'cast_proposals.{req.role_type}': proposals}}
        )
        return {
            'accepted': False,
            'message': f"{proposal['person']['name']} ha rifiutato ancora! Il prezzo sale a ${new_cost:,}.",
            'new_cost': new_cost
        }

    # Accepted!
    proposal['status'] = 'accepted'
    proposal['cost'] = new_cost
    person = proposal['person']

    # Pay
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -new_cost}})

    cast_key = req.role_type
    if req.role_type == 'directors': cast_key = 'director'
    elif req.role_type == 'screenwriters': cast_key = 'screenwriter'
    elif req.role_type == 'composers': cast_key = 'composer'

    if cast_key == 'actors':
        person_with_role = {**person, 'role_in_film': req.actor_role or 'Supporto'}
        actors = project.get('cast', {}).get('actors', [])
        actors.append(person_with_role)
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.actors': actors,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': new_cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )
    else:
        for p in proposals:
            if p['id'] != req.proposal_id and p.get('status') not in ('rejected',):
                p['status'] = 'passed'
        await db.film_projects.update_one(
            {'id': project_id},
            {'$set': {
                f'cast.{cast_key}': person,
                f'cast_proposals.{req.role_type}': proposals,
                f'costs_paid.cast_{person["id"]}': new_cost,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }}
        )

    updated = await db.film_projects.find_one({'id': project_id}, {'_id': 0, 'cast': 1})
    cast = updated.get('cast', {})
    casting_complete = (
        cast.get('director') is not None and
        cast.get('screenwriter') is not None and
        cast.get('composer') is not None and
        len(cast.get('actors', [])) >= 1
    )

    return {
        'accepted': True,
        'message': f"{person['name']} ha accettato la rinegoziazione! Costo: ${new_cost:,}",
        'person': person,
        'cost': new_cost,
        'casting_complete': casting_complete
    }


@router.post("/film-pipeline/{project_id}/advance-to-screenplay")
async def advance_to_screenplay(project_id: str, user: dict = Depends(get_current_user)):
    """Move from casting to screenplay phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'casting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    cast = project.get('cast', {})
    is_full_package = project.get('from_emerging_screenplay') and project.get('emerging_option') == 'full_package'
    
    # Full package films have pre-filled cast, relaxed validation
    if is_full_package:
        if not cast.get('director'):
            raise HTTPException(status_code=400, detail="Il cast del pacchetto non include un regista")
    else:
        if not cast.get('director') or not cast.get('screenwriter') or not cast.get('composer') or not cast.get('actors'):
            raise HTTPException(status_code=400, detail="Devi completare il casting prima di procedere")

    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['screenplay']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    update_fields = {
        'status': 'screenplay',
        'cinepass_paid.screenplay': cp_cost,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    # Auto-fill screenplay for full_package films
    if is_full_package and not project.get('screenplay'):
        update_fields['screenplay'] = project.get('pre_screenplay', '')
        update_fields['screenplay_mode'] = 'full_package'

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': update_fields}
    )

    return {'success': True, 'message': f'"{project["title"]}" in fase Sceneggiatura!'}


@router.get("/film-pipeline/all")
async def get_all_projects(user: dict = Depends(get_current_user)):
    """Get all active film projects for this user."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': {'$nin': ['discarded', 'abandoned', 'completed']}},
        {'_id': 0}
    ).sort('created_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    safe_projects = []
    for p in projects:
        # Validate project status is known
        if p.get('status') not in VALID_FILM_STATUSES:
            continue
        try:
            if p.get('status') == 'casting':
                for role, proposals in (p.get('cast_proposals') or {}).items():
                    for prop in (proposals or []):
                        if prop.get('status') == 'pending' and prop.get('available_at'):
                            avail_at = datetime.fromisoformat(prop['available_at'].replace('Z', '+00:00'))
                            if now >= avail_at:
                                prop['status'] = 'available'
            safe_projects.append(p)
        except Exception:
            continue

    return {'projects': safe_projects}


@router.get("/film-pipeline/marketplace")
async def get_marketplace(user: dict = Depends(get_current_user)):
    """Get all discarded films. Own films are visible but not buyable."""
    films = await db.film_projects.find(
        {'available_for_purchase': True},
        {'_id': 0, 'hidden_factor': 0}
    ).sort('discarded_at', -1).to_list(50)
    # Mark which films belong to the current user (can view but not buy)
    for f in films:
        f['is_own'] = f.get('discarded_by') == user['id']
    return {'films': films}


@router.post("/film-pipeline/marketplace/buy/{project_id}")
async def buy_discarded_film(project_id: str, user: dict = Depends(get_current_user)):
    """Buy a discarded film from the marketplace."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'available_for_purchase': True},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non disponibile")
    if project.get('discarded_by') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi comprare un film che hai scartato tu")

    price = project.get('sale_price', 0)
    if user.get('funds', 0) < price:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${price:,}")

    # Transfer funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -price}})
    await db.users.update_one({'id': project['discarded_by']}, {'$inc': {'funds': price}})

    # Determine which phase to place the film in
    buyer_status = project.get('status_before_discard', 'proposed')
    valid_statuses = ['proposed', 'casting', 'screenplay', 'pre_production', 'shooting']
    if buyer_status not in valid_statuses:
        buyer_status = 'proposed'
    
    # If film was in proposed phase, auto-advance to casting (buyer already paid)
    now_dt = datetime.now(timezone.utc)
    cast_proposals = project.get('cast_proposals', {})
    if buyer_status == 'proposed':
        buyer_status = 'casting'
        cast_proposals = {}
        for role in ['directors', 'screenwriters', 'actors', 'composers']:
            proposals = await generate_cast_proposals(project, role)
            for p in proposals:
                p['available_at'] = (now_dt + timedelta(minutes=p['delay_minutes'])).isoformat()
            cast_proposals[role] = proposals

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'user_id': user['id'],
            'status': buyer_status,
            'available_for_purchase': False,
            'bought_from': project.get('discarded_by'),
            'bought_at': now_dt.isoformat(),
            'purchase_price': price,
            'cast_proposals': cast_proposals,
            'casting_started_at': now_dt.isoformat(),
            'updated_at': now_dt.isoformat()
        }}
    )

    # Notify seller
    from server import create_notification
    notif = create_notification(
        project['discarded_by'], 'marketplace',
        'Film Venduto!',
        f'Il tuo film "{project["title"]}" è stato acquistato! Hai ricevuto ${price:,}.',
        {'film_title': project['title'], 'price': price}
    )
    await db.notifications.insert_one(notif)

    return {
        'success': True,
        'message': f'Hai acquistato "{project["title"]}" per ${price:,}!',
        'project_id': project_id,
        'new_status': buyer_status
    }



# ==================== PHASE 2: SCREENPLAY ====================

@router.get("/film-pipeline/screenplay")
async def get_screenplay_films(user: dict = Depends(get_current_user)):
    """Get films in screenplay phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    ).sort('updated_at', -1).to_list(50)
    return {'films': projects}


@router.post("/film-pipeline/{project_id}/write-screenplay")
async def write_screenplay(project_id: str, req: ScreenplaySubmitRequest, user: dict = Depends(get_current_user)):
    """Submit screenplay for a film: AI-generated, pre-only, or manual."""
    import os, logging
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato o non in fase Sceneggiatura")

    # Validate required fields exist
    genre = project.get('genre', 'Drammatico')
    subgenre = project.get('subgenre', '')
    pre_screenplay = project.get('pre_screenplay', project.get('plot', ''))
    if not pre_screenplay:
        raise HTTPException(status_code=400, detail="Manca la sinossi del film. Torna alla fase Proposte.")

    screenplay_text = ""
    quality_modifier = 0

    if req.mode == 'ai':
        # Generate AI screenplay based on pre-screenplay
        EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
        if EMERGENT_LLM_KEY:
            try:
                from emergentintegrations.llm.chat import LlmChat, UserMessage
                chat = LlmChat(
                    api_key=EMERGENT_LLM_KEY,
                    session_id=f"pipeline-screenplay-{uuid.uuid4()}",
                    system_message="Sei uno sceneggiatore cinematografico professionista. Scrivi sceneggiature in italiano, concise ma d'impatto."
                ).with_model("openai", "gpt-4o-mini")

                prompt = f"""Scrivi una sceneggiatura breve (max 400 parole) per un film {genre} ({subgenre}) intitolato "{project['title']}".

Basati su questa sinossi del produttore:
"{pre_screenplay}"

Location: {project.get('location', {}).get('name', 'N/A')}

Includi:
- Logline (1-2 frasi)
- Conflitto principale
- 4-5 punti chiave della trama
- Climax e risoluzione
- Note su atmosfera e tono

Scrivi TUTTO in italiano."""

                response = await chat.send_message(UserMessage(text=prompt))
                screenplay_text = response
                quality_modifier = 10  # AI bonus
            except Exception as e:
                logging.error(f"AI screenplay error: {e}")
                screenplay_text = f"[Sceneggiatura AI] Basata su: {pre_screenplay}"
                quality_modifier = 5
        else:
            screenplay_text = f"[Sceneggiatura AI non disponibile] Basata su: {pre_screenplay}"
            quality_modifier = 5

        # AI screenplay costs more
        cost = 80000
        if user.get('funds', 0) < cost:
            raise HTTPException(status_code=400, detail=f"Fondi insufficienti per la sceneggiatura AI. Servono ${cost:,}")
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    elif req.mode == 'pre_only':
        # Keep only pre-screenplay (quality malus)
        screenplay_text = pre_screenplay
        quality_modifier = -15  # Malus for no full screenplay
        cost = 0

    elif req.mode == 'manual':
        if not req.manual_text or len(req.manual_text.strip()) < 100:
            raise HTTPException(status_code=400, detail="La sceneggiatura manuale deve essere di almeno 100 caratteri")
        screenplay_text = req.manual_text.strip()
        # Manual quality depends on length
        if len(screenplay_text) >= 500:
            quality_modifier = 8
        elif len(screenplay_text) >= 300:
            quality_modifier = 4
        else:
            quality_modifier = 0
        cost = 20000
        if user.get('funds', 0) < cost:
            raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
        await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})
    else:
        raise HTTPException(status_code=400, detail="Modalita' non valida. Usa 'ai', 'pre_only' o 'manual'")

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'screenplay': screenplay_text,
            'screenplay_mode': req.mode,
            'screenplay_quality_modifier': quality_modifier,
            f'costs_paid.screenplay': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Sceneggiatura {"AI" if req.mode == "ai" else "manuale" if req.mode == "manual" else "base"} completata!',
        'screenplay': screenplay_text,
        'quality_modifier': quality_modifier,
        'cost': cost
    }



# === EQUIPMENT ENDPOINTS ===
@router.get("/film-pipeline/{project_id}/equipment-options")
async def get_equipment_options(project_id: str, user: dict = Depends(get_current_user)):
    """Get available equipment packages with costs scaled by pre-IMDb."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    pre_imdb = project.get('pre_imdb_score', 5.0)
    # Scale costs: higher pre-IMDb = more expensive equipment available
    cost_multiplier = 0.7 + (pre_imdb / 10) * 0.6  # 0.7x to 1.3x
    options = []
    for eq in EQUIPMENT_PACKAGES:
        scaled_cost = int(eq['base_cost'] * cost_multiplier)
        options.append({
            'id': eq['id'], 'name': eq['name'], 'desc': eq['desc'],
            'cost': scaled_cost, 'tier': eq['tier']
        })
    already_selected = project.get('equipment', [])
    return {'options': options, 'selected': already_selected}

class EquipmentSelect(BaseModel):
    equipment_ids: List[str]

@router.post("/film-pipeline/{project_id}/select-equipment")
async def select_equipment(project_id: str, req: EquipmentSelect, user: dict = Depends(get_current_user)):
    """Select equipment packages for a film in casting."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project['status'] != 'casting':
        raise HTTPException(status_code=400, detail="Le attrezzature si scelgono durante il casting")
    pre_imdb = project.get('pre_imdb_score', 5.0)
    cost_multiplier = 0.7 + (pre_imdb / 10) * 0.6
    selected = []
    total_cost = 0
    total_bonus = 0.0
    for eq_id in req.equipment_ids:
        eq = next((e for e in EQUIPMENT_PACKAGES if e['id'] == eq_id), None)
        if not eq:
            continue
        cost = int(eq['base_cost'] * cost_multiplier)
        selected.append({'id': eq['id'], 'name': eq['name'], 'cost': cost, 'tier': eq['tier']})
        total_cost += cost
        total_bonus += eq['quality_bonus']
    # Check funds
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'funds': 1})
    if (u.get('funds', 0)) < total_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti! Servono ${total_cost:,}")
    # Deduct and save
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {'equipment': selected, 'equipment_cost': total_cost, 'equipment_bonus': total_bonus},
         '$inc': {'costs_paid.equipment': total_cost}}
    )
    return {'success': True, 'equipment': selected, 'total_cost': total_cost, 'message': f'Attrezzature selezionate! Costo: ${total_cost:,}'}

# === SPONSOR ENDPOINTS ===
@router.get("/film-pipeline/{project_id}/sponsor-offers")
async def get_sponsor_offers(project_id: str, user: dict = Depends(get_current_user)):
    """Get sponsor offers based on film value and player fame."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'fame': 1, 'nickname': 1})
    player_fame = u.get('fame', 50) if u else 50
    pre_imdb = project.get('pre_imdb_score', 5.0)
    total_cost = sum(project.get('costs_paid', {}).values())
    # Max sponsors based on player fame
    max_sponsors = 1 + int(player_fame / 20)  # 1-6
    max_sponsors = min(max_sponsors, 6)
    # Generate offers - higher film value = better offers
    film_value_factor = (pre_imdb / 10) * (1 + total_cost / 2000000)
    offers = []
    for sp in SPONSORS:
        # Only sponsors with fame <= player_fame + 20 will approach
        if sp['fame'] > player_fame + 25:
            continue
        # Offer amount: exponential based on film value and sponsor fame
        base_offer = int(sp['fame'] * 1000 * film_value_factor)
        offer_amount = int(base_offer * (1 + random.random() * 0.3))
        # Revenue share %: higher fame sponsors take less %
        rev_share = round(max(5, 25 - (sp['fame'] / 10) + random.uniform(-3, 3)), 1)
        # Attendance boost: based on sponsor fame (up to 30% total from all sponsors)
        attendance_boost = round(sp['fame'] / 100 * 8, 1)  # 3-8% per sponsor
        offers.append({
            'id': sp['id'], 'name': sp['name'], 'fame': sp['fame'],
            'logo_color': sp['logo_color'], 'category': sp['category'],
            'offer_amount': offer_amount, 'revenue_share_pct': rev_share,
            'attendance_boost_pct': attendance_boost
        })
    # Sort by offer amount desc
    offers.sort(key=lambda x: x['offer_amount'], reverse=True)
    already_selected = project.get('sponsors', [])
    return {'offers': offers, 'selected': already_selected, 'max_sponsors': max_sponsors}

class SponsorSelect(BaseModel):
    sponsor_ids: List[str]

@router.post("/film-pipeline/{project_id}/select-sponsors")
async def select_sponsors(project_id: str, req: SponsorSelect, user: dict = Depends(get_current_user)):
    """Select sponsors for a film in pre-production."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project['status'] != 'pre_production':
        raise HTTPException(status_code=400, detail="Gli sponsor si scelgono in pre-produzione")
    u = await db.users.find_one({'id': user['id']}, {'_id': 0, 'fame': 1})
    player_fame = u.get('fame', 50) if u else 50
    max_sponsors = min(1 + int(player_fame / 20), 6)
    if len(req.sponsor_ids) > max_sponsors:
        raise HTTPException(status_code=400, detail=f"Puoi scegliere massimo {max_sponsors} sponsor con la tua fama attuale")
    pre_imdb = project.get('pre_imdb_score', 5.0)
    total_cost = sum(project.get('costs_paid', {}).values())
    film_value_factor = (pre_imdb / 10) * (1 + total_cost / 2000000)
    selected = []
    total_sponsor_money = 0
    total_rev_share = 0.0
    total_attendance_boost = 0.0
    for sp_id in req.sponsor_ids:
        sp = next((s for s in SPONSORS if s['id'] == sp_id), None)
        if not sp:
            continue
        base_offer = int(sp['fame'] * 1000 * film_value_factor)
        offer_amount = int(base_offer * (1 + random.random() * 0.3))
        rev_share = round(max(5, 25 - (sp['fame'] / 10) + random.uniform(-3, 3)), 1)
        attendance_boost = round(sp['fame'] / 100 * 8, 1)
        selected.append({
            'id': sp['id'], 'name': sp['name'], 'fame': sp['fame'],
            'logo_color': sp['logo_color'], 'category': sp['category'],
            'offer_amount': offer_amount, 'revenue_share_pct': rev_share,
            'attendance_boost_pct': attendance_boost
        })
        total_sponsor_money += offer_amount
        total_rev_share += rev_share
        total_attendance_boost += attendance_boost
    # Cap total attendance boost at 30%
    total_attendance_boost = min(total_attendance_boost, 30.0)
    # Give sponsor money to player immediately
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': total_sponsor_money}})
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'sponsors': selected,
            'sponsor_money': total_sponsor_money,
            'sponsor_rev_share_pct': round(total_rev_share, 1),
            'sponsor_attendance_boost_pct': round(total_attendance_boost, 1)
        }}
    )
    return {
        'success': True, 'sponsors': selected,
        'total_money': total_sponsor_money,
        'total_rev_share': round(total_rev_share, 1),
        'total_attendance_boost': round(total_attendance_boost, 1),
        'message': f'{len(selected)} sponsor selezionati! Ricevi ${total_sponsor_money:,} in sponsorizzazioni!'
    }

class PosterRequest(BaseModel):
    mode: str  # 'ai_auto', 'ai_custom', 'classic'
    custom_prompt: Optional[str] = None
    classic_style: Optional[str] = None  # 'noir', 'vintage', 'action', 'romance', 'horror', 'scifi'

CLASSIC_POSTER_STYLES = {
    'noir': 'Classic film noir style poster with dramatic shadows, black and white with gold accents, fedora silhouette, venetian blinds light',
    'vintage': 'Vintage 1960s Italian cinema poster, warm colors, hand-painted style, dramatic typography space',
    'action': 'Explosive Hollywood action movie poster, fire and explosions, intense orange and blue color grading, hero silhouette',
    'romance': 'Romantic drama poster, soft golden hour lighting, two silhouettes, dreamy bokeh, pastel colors',
    'horror': 'Horror movie poster, dark atmospheric, single light source, eerie fog, dramatic red accents on black',
    'scifi': 'Science fiction movie poster, neon lights, futuristic cityscape, cyberpunk aesthetic, blue and purple tones',
    'comedy': 'Bright colorful comedy movie poster, fun playful style, bold saturated colors, cheerful lighting',
    'drama': 'Dramatic cinema poster, contemplative mood, muted earth tones, artistic composition, award-winning film style'
}

@router.post("/film-pipeline/{project_id}/generate-poster")
async def generate_poster(project_id: str, req: PosterRequest, user: dict = Depends(get_current_user)):
    """Generate or set a movie poster for the film project."""
    project = await db.film_projects.find_one({'id': project_id, 'user_id': user['id']}, {'_id': 0})
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project['status'] not in ('proposed', 'screenplay'):
        raise HTTPException(status_code=400, detail="La locandina si crea durante la fase proposta o sceneggiatura")

    poster_url = None
    genre_name = project.get('genre', 'drama').replace('_', ' ').title()

    if req.mode == 'ai_auto':
        # Generate from screenplay automatically
        screenplay = project.get('screenplay', project.get('pre_screenplay', ''))
        prompt = f"Professional cinematic movie poster for '{project['title']}', a {genre_name} film. {screenplay[:200]}. Dramatic lighting, high quality, no text. Style: modern Hollywood movie poster."
    elif req.mode == 'ai_custom':
        if not req.custom_prompt:
            raise HTTPException(status_code=400, detail="Scrivi un prompt personalizzato")
        prompt = f"Professional cinematic movie poster: {req.custom_prompt}. Title: '{project['title']}'. No text overlay. High quality."
    elif req.mode == 'classic':
        style = CLASSIC_POSTER_STYLES.get(req.classic_style, CLASSIC_POSTER_STYLES['drama'])
        prompt = f"{style}. Movie title: '{project['title']}', genre: {genre_name}. No text overlay on image. High quality cinematic poster."
    else:
        raise HTTPException(status_code=400, detail="Modalita non valida: usa 'ai_auto', 'ai_custom' o 'classic'")

    # Generate poster via AI
    try:
        if not EMERGENT_LLM_KEY:
            raise HTTPException(status_code=500, detail="Chiave AI non configurata")

        import base64
        from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
        img_gen = OpenAIImageGeneration(api_key=EMERGENT_LLM_KEY)
        images = await img_gen.generate_images(
            prompt=prompt,
            model="gpt-image-1",
            number_of_images=1
        )
        if images and len(images) > 0:
            filename = f"proj_{project_id}.png"
            await poster_storage.save_poster(filename, images[0], 'image/png')
            poster_url = f"/api/posters/{filename}"
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Poster generation error: {e}")
        raise HTTPException(status_code=500, detail=f"Errore generazione poster: {str(e)}")

    if not poster_url:
        raise HTTPException(status_code=500, detail="Impossibile generare la locandina")

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'poster_url': poster_url,
            'poster_prompt': prompt,
            'poster_mode': req.mode,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'poster_url': poster_url,
        'message': 'Locandina generata con successo!'
    }



@router.post("/film-pipeline/{project_id}/advance-to-preproduction")
async def advance_to_preproduction(project_id: str, user: dict = Depends(get_current_user)):
    """Move from screenplay to pre-production phase."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'screenplay'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    
    # Full package films use pre_screenplay as their screenplay
    is_full_package = project.get('from_emerging_screenplay') and project.get('emerging_option') == 'full_package'
    if not project.get('screenplay') and not is_full_package:
        raise HTTPException(status_code=400, detail="Devi prima completare la sceneggiatura")
    
    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['pre_production']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Auto-set screenplay from pre_screenplay for full_package
    update_fields = {
        'status': 'pre_production',
        'cinepass_paid.pre_production': cp_cost,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    if is_full_package and not project.get('screenplay'):
        update_fields['screenplay'] = project.get('pre_screenplay', '')
        update_fields['screenplay_mode'] = 'full_package'

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': update_fields}
    )
    return {'success': True, 'message': f'"{project["title"]}" in Pre-Produzione!'}


# ==================== PHASE 2: PRE-PRODUCTION ====================

# Remaster duration based on pre-IMDb score (higher = faster)
def get_remaster_duration_minutes(pre_imdb: float) -> int:
    base = max(5, int((10 - pre_imdb) * 6))  # 5-50 minutes
    return base + random.randint(0, 10)

# Remaster quality boost
def get_remaster_boost() -> int:
    return random.randint(5, 15)


@router.get("/film-pipeline/pre-production")
async def get_preproduction_films(user: dict = Depends(get_current_user)):
    """Get films in pre-production phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    ).sort('updated_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    for p in projects:
        if p.get('remaster_started_at') and not p.get('remaster_completed'):
            started = datetime.fromisoformat(p['remaster_started_at'].replace('Z', '+00:00'))
            duration = p.get('remaster_duration_minutes', 30)
            end_time = started + __import__('datetime').timedelta(minutes=duration)
            if now >= end_time:
                # Auto-complete remaster
                boost = p.get('remaster_boost', get_remaster_boost())
                await db.film_projects.update_one(
                    {'id': p['id']},
                    {'$set': {
                        'remaster_completed': True,
                        'remaster_quality_boost': boost,
                        'updated_at': now.isoformat()
                    }}
                )
                p['remaster_completed'] = True
                p['remaster_quality_boost'] = boost
            else:
                remaining = (end_time - now).total_seconds() / 60
                p['remaster_remaining_minutes'] = round(remaining, 1)

    return {'films': projects}


@router.post("/film-pipeline/{project_id}/remaster")
async def start_remaster(project_id: str, user: dict = Depends(get_current_user)):
    """Start remastering a film in pre-production."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('remaster_started_at'):
        raise HTTPException(status_code=400, detail="Rimasterizzazione già avviata")

    # Check if user has production studio
    studio = await db.infrastructure.find_one({'owner_id': user['id'], 'type': 'production_studio'}, {'_id': 0})
    if not studio:
        raise HTTPException(status_code=400, detail="Devi possedere uno Studio di Produzione per rimasterizzare")

    cost = 50000 + random.randint(0, 30000)
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    duration = get_remaster_duration_minutes(project.get('pre_imdb_score', 5))
    boost = get_remaster_boost()

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'remaster_started_at': datetime.now(timezone.utc).isoformat(),
            'remaster_duration_minutes': duration,
            'remaster_boost': boost,
            'remaster_completed': False,
            f'costs_paid.remaster': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Rimasterizzazione avviata! Durata: ~{duration} minuti',
        'duration_minutes': duration,
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/speed-up-remaster")
async def speed_up_remaster(project_id: str, user: dict = Depends(get_current_user)):
    """Pay to instantly complete remastering."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if not project.get('remaster_started_at') or project.get('remaster_completed'):
        raise HTTPException(status_code=400, detail="Nessuna rimasterizzazione in corso")

    cost = 40000
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    boost = project.get('remaster_boost', get_remaster_boost())
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'remaster_completed': True,
            'remaster_quality_boost': boost,
            f'costs_paid.remaster_speedup': cost,
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Rimasterizzazione completata! Qualita +{boost}%',
        'quality_boost': boost,
        'cost': cost
    }


@router.post("/film-pipeline/{project_id}/start-shooting")
async def start_shooting(project_id: str, user: dict = Depends(get_current_user)):
    """Move from pre-production to shooting ('Ciak! Si Gira!')."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'pre_production'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('remaster_started_at') and not project.get('remaster_completed'):
        raise HTTPException(status_code=400, detail="Attendi il completamento della rimasterizzazione")

    from routes.cinepass import spend_cinepass
    cp_cost = STEP_CINEPASS['shooting']
    await spend_cinepass(user['id'], cp_cost, user.get('cinepass', 0))

    # Calculate shooting duration (days) based on pre-IMDb + quality modifiers
    base_days = random.randint(3, 7)
    now = datetime.now(timezone.utc)

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'shooting',
            'shooting_started_at': now.isoformat(),
            'shooting_days': base_days,
            'shooting_day_current': 0,
            'shooting_completed': False,
            'cinepass_paid.shooting': cp_cost,
            'updated_at': now.isoformat()
        }}
    )

    return {
        'success': True,
        'message': f'Ciak! Si Gira! "{project["title"]}" in ripresa per {base_days} giorni!',
        'shooting_days': base_days
    }


# ==================== PHASE 2: SHOOTING ====================

@router.get("/film-pipeline/shooting")
async def get_shooting_films(user: dict = Depends(get_current_user)):
    """Get films in shooting phase."""
    projects = await db.film_projects.find(
        {'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    ).sort('shooting_started_at', -1).to_list(50)

    now = datetime.now(timezone.utc)
    for p in projects:
        if p.get('shooting_started_at') and not p.get('shooting_completed'):
            started = datetime.fromisoformat(p['shooting_started_at'].replace('Z', '+00:00'))
            total_days = p.get('shooting_days', 5)
            # 1 real hour = 1 shooting day (accelerated for gameplay)
            hours_elapsed = (now - started).total_seconds() / 3600
            current_day = min(int(hours_elapsed), total_days)
            p['shooting_day_current'] = current_day
            p['shooting_hours_remaining'] = max(0, total_days - hours_elapsed)

            if current_day >= total_days:
                p['shooting_completed'] = True

    return {'films': projects}


@router.post("/film-pipeline/{project_id}/speed-up-shooting")
async def speed_up_shooting(project_id: str, req: SpeedUpShootingRequest, user: dict = Depends(get_current_user)):
    """Speed up shooting with credits. Options: fast (50%), faster (80%), instant."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")
    if project.get('shooting_completed'):
        raise HTTPException(status_code=400, detail="Riprese già completate")

    costs = {'fast': 50000, 'faster': 90000, 'instant': 150000}
    reductions = {'fast': 0.5, 'faster': 0.8, 'instant': 1.0}

    if req.option not in costs:
        raise HTTPException(status_code=400, detail="Opzione non valida")

    cost = costs[req.option]
    if user.get('funds', 0) < cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${cost:,}")
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -cost}})

    reduction = reductions[req.option]
    started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
    total_days = project.get('shooting_days', 5)
    hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    remaining_hours = max(0, total_days - hours_elapsed)
    new_remaining = remaining_hours * (1 - reduction)

    # Adjust the started time to simulate faster progress
    new_started = datetime.now(timezone.utc) - __import__('datetime').timedelta(hours=(total_days - new_remaining))

    updates = {
        'shooting_started_at': new_started.isoformat(),
        f'costs_paid.shooting_speedup': cost,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    if req.option == 'instant':
        updates['shooting_completed'] = True

    await db.film_projects.update_one({'id': project_id}, {'$set': updates})

    labels = {'fast': 'Velocizzato 50%', 'faster': 'Velocizzato 80%', 'instant': 'Riprese completate!'}
    return {
        'success': True,
        'message': f'{labels[req.option]} Costo: ${cost:,}',
        'cost': cost
    }



# ==================== DYNAMIC RELEASE EVENTS ====================

RELEASE_EVENTS = [
    # POSITIVE EVENTS (quality + revenue boost)
    {
        'id': 'viral_tiktok', 'name': 'Successo Virale sui Social',
        'type': 'positive', 'rarity': 'common',
        'description': 'Una scena del film diventa virale su TikTok e Instagram. Milioni di visualizzazioni in poche ore generano un enorme passaparola!',
        'quality_modifier': 5, 'revenue_modifier': 25,
    },
    {
        'id': 'celebrity_endorsement', 'name': 'Endorsement di una Celebrity',
        'type': 'positive', 'rarity': 'common',
        'description': 'Una celebrità internazionale twitta entusiasticamente del film, spingendo milioni di fan a comprare il biglietto.',
        'quality_modifier': 3, 'revenue_modifier': 20,
    },
    {
        'id': 'festival_selection', 'name': 'Selezione a un Festival',
        'type': 'positive', 'rarity': 'uncommon',
        'description': 'Il film viene selezionato per un prestigioso festival internazionale! La critica e il pubblico ne parlano ovunque.',
        'quality_modifier': 8, 'revenue_modifier': 15,
    },
    {
        'id': 'critics_rave', 'name': 'Recensioni Entusiastiche',
        'type': 'positive', 'rarity': 'uncommon',
        'description': 'I critici più influenti al mondo sono unanimi: il film è un capolavoro. Le recensioni a 5 stelle piovono da ogni testata.',
        'quality_modifier': 10, 'revenue_modifier': 20,
    },
    {
        'id': 'cultural_phenomenon', 'name': 'Fenomeno Culturale',
        'type': 'positive', 'rarity': 'rare',
        'description': 'Il film trascende il cinema e diventa un fenomeno culturale. Citazioni, meme, merchandising: tutti ne parlano!',
        'quality_modifier': 14, 'revenue_modifier': 40,
    },
    {
        'id': 'award_buzz', 'name': 'Candidatura ai Premi',
        'type': 'positive', 'rarity': 'uncommon',
        'description': "Gli esperti dell'industria inseriscono il film tra i favoriti per i prossimi premi cinematografici. L'hype cresce!",
        'quality_modifier': 7, 'revenue_modifier': 15,
    },
    {
        'id': 'surprise_hit', 'name': 'Sorpresa al Botteghino',
        'type': 'positive', 'rarity': 'common',
        'description': 'Il film supera ogni aspettativa al botteghino del primo weekend. Il passaparola è esplosivo!',
        'quality_modifier': 4, 'revenue_modifier': 30,
    },
    {
        'id': 'soundtrack_charts', 'name': 'Colonna Sonora in Classifica',
        'type': 'positive', 'rarity': 'common',
        'description': 'La colonna sonora del film scala le classifiche musicali, portando nuova attenzione e pubblico nelle sale.',
        'quality_modifier': 3, 'revenue_modifier': 18,
    },
    # NEGATIVE EVENTS (quality + revenue penalty)
    {
        'id': 'scandal', 'name': 'Scandalo sul Set',
        'type': 'negative', 'rarity': 'common',
        'description': "Emerge uno scandalo legato alla produzione del film. I media si scatenano e il pubblico si divide sull'opportunità di vederlo.",
        'quality_modifier': -6, 'revenue_modifier': -15,
    },
    {
        'id': 'bad_timing', 'name': 'Tempismo Sfortunato',
        'type': 'negative', 'rarity': 'common',
        'description': 'Il film esce nello stesso weekend di un blockbuster molto atteso. Le sale sono piene... per il film concorrente.',
        'quality_modifier': -2, 'revenue_modifier': -25,
    },
    {
        'id': 'leak', 'name': 'Leak Online',
        'type': 'negative', 'rarity': 'uncommon',
        'description': "Una copia del film viene diffusa online prima dell'uscita. Molti lo guardano gratis, devastando gli incassi.",
        'quality_modifier': -3, 'revenue_modifier': -30,
    },
    {
        'id': 'controversy', 'name': 'Polemica Pubblica',
        'type': 'negative', 'rarity': 'uncommon',
        'description': 'Il film genera una forte polemica per i suoi contenuti. Alcuni gruppi chiedono il boicottaggio.',
        'quality_modifier': -8, 'revenue_modifier': -15,
    },
    {
        'id': 'technical_issues', 'name': 'Problemi Tecnici nelle Sale',
        'type': 'negative', 'rarity': 'common',
        'description': "Problemi tecnici alla proiezione rovinano l'esperienza nelle sale principali. Le recensioni dei primi spettatori sono negative.",
        'quality_modifier': -5, 'revenue_modifier': -10,
    },
    {
        'id': 'actor_controversy', 'name': 'Scandalo di un Attore',
        'type': 'negative', 'rarity': 'uncommon',
        'description': "Uno degli attori protagonisti viene coinvolto in uno scandalo mediatico. L'attenzione si sposta dal film alla polemica.",
        'quality_modifier': -7, 'revenue_modifier': -20,
    },
    {
        'id': 'public_flop', 'name': 'Flop al Primo Weekend',
        'type': 'negative', 'rarity': 'rare',
        'description': "Il film delude clamorosamente al botteghino. Le sale si svuotano dopo il primo giorno e i media parlano di 'disastro'.",
        'quality_modifier': -12, 'revenue_modifier': -35,
    },
    # NEUTRAL/MIXED EVENTS
    {
        'id': 'polarizing', 'name': 'Film Polarizzante',
        'type': 'neutral', 'rarity': 'common',
        'description': 'Il pubblico si divide nettamente: chi lo ama e chi lo odia. Le discussioni accese sui social generano comunque attenzione.',
        'quality_modifier': -2, 'revenue_modifier': 10,
    },
    {
        'id': 'cult_following', 'name': 'Cult Following Immediato',
        'type': 'neutral', 'rarity': 'uncommon',
        'description': 'Il film non conquista il grande pubblico ma sviluppa immediatamente un seguito di fan accaniti che lo vedono più volte.',
        'quality_modifier': 2, 'revenue_modifier': 5,
    },
    {
        'id': 'nothing_special', 'name': 'Uscita Tranquilla',
        'type': 'neutral', 'rarity': 'common',
        'description': "Il film esce senza particolari scossoni. Nessun evento degno di nota accompagna l'uscita in sala.",
        'quality_modifier': 0, 'revenue_modifier': 0,
    },
]

# Weighted by rarity
EVENT_WEIGHTS = {'common': 5, 'uncommon': 3, 'rare': 1}


def generate_release_event(project, cast, quality_score, genre):
    """Generate a dynamic release event based on film context."""
    # Quality-based bias: better films have slightly higher chance of positive events
    positive_events = [e for e in RELEASE_EVENTS if e['type'] == 'positive']
    negative_events = [e for e in RELEASE_EVENTS if e['type'] == 'negative']
    neutral_events = [e for e in RELEASE_EVENTS if e['type'] == 'neutral']

    # Base chances: positive 35%, negative 30%, neutral 35%
    # Quality modifies: high quality films get +10% positive, low quality -10%
    quality_bias = (quality_score - 50) / 200  # ±0.25 range
    pos_chance = 0.35 + quality_bias
    neg_chance = 0.30 - quality_bias
    neutral_chance = 1 - pos_chance - neg_chance

    roll = random.random()
    if roll < pos_chance:
        pool = positive_events
    elif roll < pos_chance + neg_chance:
        pool = negative_events
    else:
        pool = neutral_events

    # Weighted random selection by rarity
    weights = [EVENT_WEIGHTS.get(e['rarity'], 3) for e in pool]
    event_template = random.choices(pool, weights=weights, k=1)[0]

    # Personalize the description with film data
    title = project.get('title', 'Il film')
    director_name = cast.get('director', {}).get('name', 'il regista')
    lead_actor = cast.get('actors', [{}])[0].get('name', 'il protagonista') if cast.get('actors') else 'il protagonista'

    description = event_template['description']
    description = description.replace('il film', f'"{title}"').replace('Il film', f'"{title}"')

    # Scale modifiers slightly by rarity for variance
    quality_mod = event_template['quality_modifier']
    revenue_mod = event_template['revenue_modifier']
    # Add small random variance (±20%)
    quality_mod = round(quality_mod * random.uniform(0.8, 1.2))
    revenue_mod = round(revenue_mod * random.uniform(0.8, 1.2))

    return {
        'id': event_template['id'],
        'name': event_template['name'],
        'type': event_template['type'],
        'rarity': event_template['rarity'],
        'description': description,
        'quality_modifier': quality_mod,
        'revenue_modifier': revenue_mod,
    }



async def _generate_film_ai_content(film_id, title, genre_name, director_name, actor_names, screenplay_text, has_poster):
    """Background task: generate AI synopsis and poster for a released film."""
    key = os.environ.get('EMERGENT_LLM_KEY', '')
    if not key:
        return

    # 1. Generate AI synopsis
    try:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        chat = LlmChat(
            api_key=key,
            session_id=f"synopsis-{film_id}",
            system_message="Sei uno scrittore di sinossi cinematografiche. Scrivi riassunti avvincenti e drammatici."
        ).with_model("openai", "gpt-4o-mini")
        cast_str = ", ".join(actor_names) if actor_names else "cast internazionale"
        prompt = f"""Crea una sinossi avvincente per un film {genre_name}.
Titolo: {title}
Regista: {director_name}
Cast: {cast_str}
Sceneggiatura: {screenplay_text[:500]}
Scrivi 2-3 paragrafi in italiano. Massimo 150 parole. Sii drammatico e coinvolgente."""
        result = await chat.send_message(UserMessage(text=prompt))
        if result:
            await db.films.update_one({'id': film_id}, {'$set': {'synopsis': result.strip()}})
            logging.info(f"AI synopsis generated for film {film_id}")
    except Exception as e:
        logging.error(f"Background synopsis error for {film_id}: {e}")

    # 2. Generate poster if not already present
    if not has_poster:
        try:
            import base64
            from PIL import Image
            import io
            from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
            img_gen = OpenAIImageGeneration(api_key=key)
            poster_prompt = f"Professional cinematic movie poster for '{title}', a {genre_name} film. Dramatic lighting, high quality, no text overlay. Style: modern Hollywood movie poster."
            images = await img_gen.generate_images(
                prompt=poster_prompt,
                model="gpt-image-1",
                number_of_images=1
            )
            if images:
                img_data = images[0]
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((400, 600), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, 'PNG', optimize=True)
                png_bytes = buf.getvalue()

                filename = f"{film_id}.png"
                await poster_storage.save_poster(filename, png_bytes, 'image/png')
                await db.films.update_one({'id': film_id}, {'$set': {'poster_url': f"/api/posters/{filename}"}})
                logging.info(f"AI poster generated for film {film_id}")
        except Exception as e:
            logging.error(f"Background poster error for {film_id}: {e}")



@router.post("/film-pipeline/{project_id}/release")
async def release_film(project_id: str, user: dict = Depends(get_current_user)):
    """Release a completed film to theaters. Shows cost summary."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id'], 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Progetto non trovato")

    # Check shooting is complete
    if not project.get('shooting_completed'):
        started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
        total_days = project.get('shooting_days', 5)
        hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        if hours_elapsed < total_days:
            raise HTTPException(status_code=400, detail="Le riprese non sono ancora completate")

    # Calculate final quality score
    pre_imdb = project.get('pre_imdb_score', 5.0)
    hidden_factor = project.get('hidden_factor', 0)
    screenplay_mod = project.get('screenplay_quality_modifier', 0)
    remaster_boost = project.get('remaster_quality_boost', 0)

    # Buzz influence
    buzz_votes = project.get('buzz_votes', {})
    total_votes = sum(buzz_votes.values()) if buzz_votes else 0
    buzz_influence = 0
    if total_votes > 0:
        high_pct = buzz_votes.get('high', 0) / total_votes
        low_pct = buzz_votes.get('low', 0) / total_votes
        buzz_influence = (high_pct - low_pct) * 10  # ±10% influence

    # Cast quality
    cast = project.get('cast', {})
    cast_skills = []
    for role in ['director', 'screenwriter']:
        person = cast.get(role, {})
        if person and person.get('skills'):
            avg = sum(person['skills'].values()) / max(1, len(person['skills']))
            cast_skills.append(avg)
    for actor in cast.get('actors', []):
        if actor.get('skills'):
            avg = sum(actor['skills'].values()) / max(1, len(actor['skills']))
            cast_skills.append(avg)
    cast_quality = sum(cast_skills) / max(1, len(cast_skills)) if cast_skills else 30

    # Soundtrack quality (from composer skills)
    composer = cast.get('composer', {})
    soundtrack_score = 0
    if composer and composer.get('skills'):
        composer_avg = sum(composer['skills'].values()) / max(1, len(composer['skills']))
        soundtrack_score = round(composer_avg * 0.08, 1)  # 0-8 points based on composer skill avg (0-100)

    # Production setup bonuses (extras, CGI, VFX)
    prod_setup = project.get('production_setup', {})
    extras_count = prod_setup.get('extras_count', 100)
    cgi_bonus = prod_setup.get('cgi_bonus', 0)
    vfx_bonus = prod_setup.get('vfx_bonus', 0)

    # Extras fit bonus/penalty
    genre = project.get('genre', 'drama')
    optimal = EXTRAS_OPTIMAL.get(genre, {'min': 50, 'max': 500, 'sweet': 200})
    if optimal['min'] <= extras_count <= optimal['max']:
        # Good range - bonus based on closeness to sweet spot
        extras_bonus = 2.0 - abs(extras_count - optimal['sweet']) / max(1, optimal['max'] - optimal['min']) * 2.0
        extras_bonus = max(0.5, round(extras_bonus, 1))
    elif extras_count > optimal['max']:
        # Too many extras - penalty proportional to excess
        excess_ratio = (extras_count - optimal['max']) / optimal['max']
        extras_bonus = -round(excess_ratio * 3.0, 1)
    else:
        extras_bonus = 0.0

    # Role-weighted cast quality
    role_weighted_quality = 0
    for actor in cast.get('actors', []):
        if actor.get('skills'):
            avg_skill = sum(actor['skills'].values()) / max(1, len(actor['skills']))
            role_weight = ROLE_VALUES.get(actor.get('role_in_film', 'Supporto'), {}).get('quality_weight', 0.7)
            role_weighted_quality += avg_skill * role_weight
    if cast.get('actors'):
        role_weighted_quality = role_weighted_quality / len(cast['actors'])

    # Equipment bonus
    equipment_bonus = project.get('equipment_bonus', 0)

    # === QUALITY SCORE CALCULATION v2 ===
    # Philosophy: Cinema is ALCHEMY, not chemistry.
    # Great ingredients help, but the result is NEVER guaranteed.
    # Even $200M blockbusters can flop, and low-budget gems become classics.
    # Investments set the floor (~65 max), but the ceiling comes from luck and vision.

    # --- FOUNDATION (max ~65 with perfect inputs) ---
    base_quality = pre_imdb * 4.8  # 0-48 range (balanced between old 5.5 and v2's 4.0)

    # Cast with heavier diminishing returns (max ~7)
    if cast_quality > 70:
        cast_contrib = 70 * 0.08 + (cast_quality - 70) * 0.03
    else:
        cast_contrib = cast_quality * 0.08

    # Role-weighted quality (max ~4.5)
    if role_weighted_quality > 60:
        role_contrib = 60 * 0.05 + (role_weighted_quality - 60) * 0.02
    else:
        role_contrib = role_weighted_quality * 0.05

    # Soundtrack (capped at 4)
    soundtrack_contrib = min(soundtrack_score, 4)

    # Equipment/CGI/VFX with heavy diminishing returns (capped at 5)
    tech_bonus = cgi_bonus + vfx_bonus + equipment_bonus
    tech_contrib = min(tech_bonus, 3) + max(0, tech_bonus - 3) * 0.2
    tech_contrib = min(tech_contrib, 5)

    # Deterministic score (max ~65 with perfect everything)
    deterministic = (base_quality + screenplay_mod + remaster_boost + buzz_influence +
                     cast_contrib + role_contrib + soundtrack_contrib +
                     tech_contrib + extras_bonus)

    quality_score = deterministic

    # === THE ALCHEMY - Unpredictability System v2 ===
    # No amount of money can control these factors.
    advanced_factors = {}

    # 1. DIRECTOR VISION - The single most impactful random factor
    # A visionary director finds angles nobody expected. A mismatch ruins everything.
    director_skills = cast.get('director', {}).get('skills', {})
    director_avg = sum(director_skills.values()) / max(1, len(director_skills)) if director_skills else 40
    director_mean = (director_avg - 50) * 0.08  # slight advantage for great directors
    director_vision = round(max(-22, min(22, random.gauss(director_mean, 9))), 1)
    if director_vision != 0:
        if director_vision >= 15:
            advanced_factors['visione_regista'] = f'+{director_vision} (Visione geniale del regista!)'
        elif director_vision >= 8:
            advanced_factors['visione_regista'] = f'+{director_vision} (Regia ispirata)'
        elif director_vision <= -15:
            advanced_factors['visione_regista'] = f'{director_vision} (Regia completamente sbagliata!)'
        elif director_vision <= -8:
            advanced_factors['visione_regista'] = f'{director_vision} (Regia sottotono)'
        else:
            advanced_factors['visione_regista'] = f'{director_vision:+}'
    quality_score += director_vision

    # 2. Audience Reception - the crowd is unpredictable
    audience_roll = round(max(-20, min(20, random.gauss(0, 8))), 1)
    if audience_roll != 0:
        if audience_roll >= 12:
            advanced_factors['pubblico'] = f'+{audience_roll} (Il pubblico impazzisce!)'
        elif audience_roll >= 6:
            advanced_factors['pubblico'] = f'+{audience_roll} (Ben accolto)'
        elif audience_roll <= -12:
            advanced_factors['pubblico'] = f'{audience_roll} (Il pubblico non gradisce!)'
        elif audience_roll <= -6:
            advanced_factors['pubblico'] = f'{audience_roll} (Tiepida accoglienza)'
        else:
            advanced_factors['pubblico'] = f'{audience_roll:+}'
    quality_score += audience_roll

    # 3. Cast Chemistry - synergy between actors
    chemistry = random.choice([-5, -3, -2, -1, 0, 0, 0, 1, 2, 3, 4, 6])
    if chemistry != 0:
        advanced_factors['chimica_cast'] = f'{chemistry:+}'
        quality_score += chemistry

    # 4. Genre Trend - market appetite for this genre
    trend_genres = {'action': 1, 'horror': -1, 'comedy': 1, 'drama': 0, 'sci_fi': 2, 'thriller': 0, 'romance': -1, 'animation': 1}
    genre_trend = trend_genres.get(project.get('genre', ''), 0) + random.choice([-3, -2, -1, 0, 0, 0, 0, 1, 2, 3])
    if genre_trend != 0:
        advanced_factors['trend_genere'] = f'{genre_trend:+}'
        quality_score += genre_trend

    # 5. Critical Reception - critics can make or break
    critic_roll = random.choice([-8, -5, -3, -1, 0, 0, 0, 1, 2, 4, 6, 10])
    if critic_roll != 0:
        if critic_roll >= 6:
            advanced_factors['critica'] = f'+{critic_roll} (Acclamato dalla critica!)'
        elif critic_roll <= -5:
            advanced_factors['critica'] = f'{critic_roll} (Stroncato dalla critica!)'
        else:
            advanced_factors['critica'] = f'{critic_roll:+}'
        quality_score += critic_roll

    # 6. Market Timing
    timing = random.choice([-4, -2, -1, 0, 0, 0, 0, 1, 3, 5])
    if timing != 0:
        advanced_factors['tempismo_mercato'] = f'{timing:+}'
        quality_score += timing

    # 7. DYNAMIC RELEASE EVENT - narrative event that affects the film
    release_event = generate_release_event(project, cast, quality_score, genre)
    if release_event:
        quality_score += release_event['quality_modifier']
        advanced_factors['evento_rilascio'] = f"{release_event['quality_modifier']:+} ({release_event['name']})"

    # Final clamp
    quality_score = max(10, min(100, quality_score))
    quality_score = round(quality_score, 1)

    # Determine tier
    if quality_score >= 85:
        tier = 'masterpiece'
    elif quality_score >= 70:
        tier = 'excellent'
    elif quality_score >= 55:
        tier = 'good'
    elif quality_score >= 40:
        tier = 'mediocre'
    else:
        tier = 'bad'

    # Cost summary
    costs_paid = project.get('costs_paid', {})
    total_cost = sum(costs_paid.values())
    cinepass_paid = project.get('cinepass_paid', {})
    total_cinepass = sum(cinepass_paid.values())

    # Calculate opening day revenue based on quality, budget, cast fame
    avg_cast_fame = 0
    all_cast_fame = []
    for role_key in ['director', 'screenwriter', 'composer']:
        p = cast.get(role_key)
        if p and p.get('fame'):
            all_cast_fame.append(p['fame'])
    for a in cast.get('actors', []):
        if a.get('fame'):
            all_cast_fame.append(a['fame'])
    if all_cast_fame:
        avg_cast_fame = sum(all_cast_fame) / len(all_cast_fame)
    opening_day_revenue = int((quality_score * 2000) + (avg_cast_fame * 500) + (total_cost * 0.1) + random.randint(10000, 100000))
    # Apply sponsor attendance boost (up to 30%)
    sponsor_boost = project.get('sponsor_attendance_boost_pct', 0) / 100
    opening_day_revenue = int(opening_day_revenue * (1 + sponsor_boost))
    # Apply release event revenue modifier
    if release_event and release_event.get('revenue_modifier', 0) != 0:
        opening_day_revenue = int(opening_day_revenue * (1 + release_event['revenue_modifier'] / 100))

    # Calculate audience satisfaction
    audience_satisfaction = max(20, min(100, quality_score + random.randint(-10, 15)))

    # Create the actual film in the films collection (fully featured)
    film_id = str(uuid.uuid4())
    genre_val = project.get('genre', 'drama')
    now_str = datetime.now(timezone.utc).isoformat()

    film_doc = {
        'id': film_id,
        'owner_id': user['id'],
        'user_id': user['id'],
        'title': project['title'],
        'genre': genre_val,
        'subgenre': project.get('subgenre', ''),
        'subgenres': project.get('subgenres', []),
        'status': 'in_theaters',
        'quality_score': quality_score,
        'tier': tier,
        'budget': total_cost,
        'total_budget': total_cost,
        'total_revenue': 0,
        'opening_day_revenue': opening_day_revenue,
        'day_in_theaters': 0,
        'max_days': max(14, int(quality_score / 3) + random.randint(7, 21)),
        'cast': cast.get('actors', []),
        'director': cast.get('director', {}),
        'screenwriter': cast.get('screenwriter', {}),
        'screenwriters': [cast.get('screenwriter', {})] if cast.get('screenwriter') else [],
        'composer': cast.get('composer'),
        'locations': [l if isinstance(l, str) else l.get('name', str(l)) for l in project.get('locations', [])],
        'location': (project.get('locations', [''])[0] if isinstance(project.get('locations', [''])[0], str) else project.get('locations', [{}])[0].get('name', '')) if project.get('locations') else '',
        'screenplay': project.get('screenplay', project.get('pre_screenplay', '')),
        'pre_imdb_score': pre_imdb,
        'audience_satisfaction': audience_satisfaction,
        'buzz_votes': buzz_votes,
        'buzz_influence': buzz_influence,
        'remaster_boost': remaster_boost,
        'soundtrack_score': soundtrack_score,
        'production_setup': prod_setup,
        'advanced_factors': advanced_factors,
        'pipeline_project_id': project_id,
        'likes_count': 0,
        'liked_by': [],
        'virtual_likes': random.randint(100, 5000),
        'cumulative_attendance': 0,
        'daily_revenues': [],
        'box_office': {},
        'extras_count': prod_setup.get('extras_count', 100),
        'extras_cost': prod_setup.get('extras_cost', 0),
        'created_at': now_str,
        'released_at': now_str,
        'release_date': now_str[:10],
        'distribution_zone': 'national',
        'distribution_cost': 0,
        'current_cinemas': random.randint(50, 200),
        'current_attendance': 0,
        'avg_attendance_per_cinema': 0,
        'cinema_distribution': [
            {'country_code': 'IT', 'country_name': 'Italia', 'cinemas': random.randint(30, 120), 'total_attendance': 0},
        ],
        'attendance_history': [],
        'total_screenings': 0,
        'equipment': project.get('equipment', []),
        'sponsors': project.get('sponsors', []),
        'sponsor_rev_share_pct': project.get('sponsor_rev_share_pct', 0),
        'sponsor_attendance_boost_pct': project.get('sponsor_attendance_boost_pct', 0),
        'production_house': user.get('nickname', user.get('email', 'Studio').split('@')[0]),
        'agency_actors_count': project.get('agency_actors_count', 0),
        'release_event': release_event,
    }

    # Calculate IMDb rating
    film_doc['imdb_rating'] = calculate_imdb_rating(film_doc)

    # Generate AI interactions (reviews from public)
    film_doc['ai_interactions'] = generate_ai_interactions(film_doc, 0)
    film_doc['ratings'] = {'user_ratings': [], 'ai_ratings': film_doc['ai_interactions']}

    # Calculate film tier (Masterpiece, Epic, etc.)
    tier_result = calculate_film_tier(film_doc)
    film_doc['film_tier'] = tier_result['tier']
    film_doc['tier_score'] = tier_result['score']
    film_doc['tier_bonuses'] = tier_result.get('bonuses', {})

    # Apply immediate tier bonus
    if tier_result.get('triggered') and tier_result.get('tier_info'):
        immediate_bonus = tier_result['tier_info'].get('immediate_bonus', 0)
        if immediate_bonus != 0:
            bonus_amount = int(opening_day_revenue * immediate_bonus)
            film_doc['opening_day_revenue'] += bonus_amount
            film_doc['tier_opening_bonus'] = bonus_amount

    # Generate critic reviews
    try:
        critic_data = generate_critic_reviews(film_doc, user.get('language', 'it'))
        if isinstance(critic_data, dict):
            film_doc['critic_reviews'] = critic_data.get('reviews', [])
            film_doc['critic_effects'] = critic_data.get('total_effects', {})
        elif isinstance(critic_data, list):
            film_doc['critic_reviews'] = critic_data
            film_doc['critic_effects'] = {}
    except Exception as e:
        logging.error(f"Critic reviews error: {e}")
        film_doc['critic_reviews'] = []
        film_doc['critic_effects'] = {}

    # Generate synopsis from screenplay (background - non-blocking)
    screenplay_text = project.get('screenplay', project.get('pre_screenplay', ''))
    genre_name = genre_val.replace('_', ' ').title()
    director_name = cast.get('director', {}).get('name', 'Regista')
    actor_names = [a.get('name', '') for a in cast.get('actors', [])[:3]]
    film_doc['synopsis'] = f"Un avvincente {genre_name} diretto da {director_name}. {project['title']} racconta una storia che vi terrà col fiato sospeso."

    # Generate poster - use existing or defer to background
    existing_poster = project.get('poster_url')
    if existing_poster:
        film_doc['poster_url'] = existing_poster
    else:
        film_doc['poster_url'] = None

    # Soundtrack info from composer
    if cast.get('composer') and cast['composer'].get('skills'):
        comp_skills = cast['composer']['skills']
        soundtrack_rating = sum(comp_skills.values()) / max(1, len(comp_skills))
        film_doc['soundtrack_rating'] = round(soundtrack_rating, 1)
        film_doc['soundtrack_boost'] = {
            'day_1_multiplier': round(1.0 + (soundtrack_rating / 100) * 1.5, 2),
            'day_2_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.8, 2),
            'day_3_multiplier': round(1.0 + (soundtrack_rating / 100) * 0.3, 2),
        }

    await db.films.insert_one(film_doc)
    film_doc.pop('_id', None)

    # Launch AI tasks in background (synopsis + poster) - non-blocking
    asyncio.create_task(_generate_film_ai_content(
        film_id, project['title'], genre_name, director_name,
        actor_names, screenplay_text, existing_poster
    ))

    # Update project status
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'completed',
            'film_id': film_id,
            'final_quality': quality_score,
            'final_tier': tier,
            'completed_at': now_str
        }}
    )

    # Award XP and fame
    xp_gain = int(quality_score * 2)
    if quality_score >= 90:
        xp_gain += XP_REWARDS.get('film_blockbuster', 500)
    elif quality_score >= 80:
        xp_gain += XP_REWARDS.get('film_hit', 250)

    # Agency actors bonus
    agency_actors_count = project.get('agency_actors_count', 0)
    if agency_actors_count == 0:
        # Count from cast data
        agency_actors_count = sum(1 for a in cast.get('actors', []) if a.get('is_agency_actor'))
    agency_xp_mult, agency_fame_mult, agency_quality_bonus = 1.0, 1.0, 0
    if agency_actors_count > 0:
        from routes.casting_agency import calculate_agency_bonus, update_agency_actors_after_film
        agency_xp_mult, agency_fame_mult, agency_quality_bonus = calculate_agency_bonus(agency_actors_count, quality_score)
        xp_gain = int(xp_gain * agency_xp_mult)

    current_fame = user.get('fame', 50)
    fame_change = calculate_fame_change(quality_score, opening_day_revenue, current_fame)
    if agency_actors_count > 0:
        fame_change = int(fame_change * agency_fame_mult)
    new_fame = max(0, min(100, current_fame + fame_change))

    await db.users.update_one(
        {'id': user['id']},
        {'$set': {'fame': new_fame},
         '$inc': {'total_xp': xp_gain}}
    )

    # Update agency actors' skills after film
    if agency_actors_count > 0:
        try:
            await update_agency_actors_after_film(film_doc, user['id'])
        except Exception as e:
            logging.error(f"Agency actor update error: {e}")

    # Notification
    from server import create_notification
    tier_labels = {'masterpiece': 'Capolavoro!', 'excellent': 'Eccellente!', 'good': 'Buono', 'mediocre': 'Mediocre', 'bad': 'Scarso'}
    notif = create_notification(user['id'], 'film_release', 'Film Rilasciato!',
        f'"{project["title"]}" e al cinema! Qualita: {quality_score} ({tier_labels.get(tier, tier)})',
        {'film_id': film_id, 'quality': quality_score, 'tier': tier})
    await db.notifications.insert_one(notif)

    # Determine release outcome based on quality
    if quality_score < 55:
        release_outcome = 'flop'
        release_image = '/assets/release/cinema_flop.jpg'
    elif quality_score <= 75:
        release_outcome = 'normal'
        release_image = '/assets/release/cinema_normal.jpg'
    else:
        release_outcome = 'success'
        release_image = '/assets/release/cinema_success.jpg'

    # Extract screenplay scenes for visual trailer
    screenplay_text = project.get('screenplay', project.get('pre_screenplay', ''))
    screenplay_scenes = []
    if screenplay_text and len(screenplay_text) > 50:
        # Split into 3-5 meaningful segments
        sentences = [s.strip() for s in screenplay_text.replace('\n', '. ').split('.') if len(s.strip()) > 15]
        if len(sentences) >= 5:
            step = len(sentences) // 5
            screenplay_scenes = [sentences[i * step] + '.' for i in range(5)]
        elif len(sentences) >= 3:
            step = max(1, len(sentences) // 3)
            screenplay_scenes = [sentences[i * step] + '.' for i in range(min(3, len(sentences)))]
        else:
            screenplay_scenes = [s + '.' for s in sentences[:3]]

    # Calculate hype level from buzz and other factors
    hype_level = min(100, max(0, int(buzz_influence * 10 + (soundtrack_score or 0) * 2 + len(project.get('sponsors', [])) * 5)))

    return {
        'success': True,
        'film_id': film_id,
        'title': project['title'],
        'quality_score': quality_score,
        'tier': tier,
        'tier_label': tier_labels.get(tier, tier),
        'imdb_rating': film_doc.get('imdb_rating', 0),
        'poster_url': film_doc.get('poster_url'),
        'sponsors': project.get('sponsors', []),
        'release_outcome': release_outcome,
        'release_image': release_image,
        'screenplay_scenes': screenplay_scenes,
        'hype_level': hype_level,
        'opening_day_revenue': opening_day_revenue,
        'total_revenue': film_doc.get('total_revenue', 0),
        'cost_summary': {
            'total_money': total_cost,
            'total_cinepass': total_cinepass,
            'breakdown': costs_paid,
            'cinepass_breakdown': cinepass_paid
        },
        'modifiers': {
            'pre_imdb': pre_imdb,
            'screenplay': screenplay_mod,
            'remaster': remaster_boost,
            'buzz': round(buzz_influence, 1),
            'cast_quality': round(cast_quality, 1),
            'role_weighted': round(role_weighted_quality, 1),
            'soundtrack': soundtrack_score,
            'cgi': cgi_bonus,
            'vfx': vfx_bonus,
            'extras': extras_bonus,
            'extras_count': extras_count,
            'advanced_factors': advanced_factors
        },
        'xp_gained': xp_gain,
        'release_event': release_event,
    }


# ==================== BUZZ SYSTEM ====================


# ==================== PRODUCTION SETUP (Extras, CGI, VFX) ====================

@router.get("/film-pipeline/production-options/{genre}")
async def get_production_options(genre: str, user: dict = Depends(get_current_user)):
    """Get CGI, VFX packages and extras info for a genre."""
    cgi = CGI_PACKAGES.get(genre, CGI_DEFAULT)
    vfx = VFX_PACKAGES.get(genre, VFX_DEFAULT)
    extras_info = EXTRAS_OPTIMAL.get(genre, {'min': 50, 'max': 500, 'sweet': 200})
    return {
        'cgi_packages': cgi,
        'vfx_packages': vfx,
        'extras_optimal': extras_info,
        'extras_cost_per_person': EXTRAS_COST_PER_PERSON,
        'role_values': ROLE_VALUES
    }

@router.post("/film-pipeline/{project_id}/production-setup")
async def set_production_setup(project_id: str, req: ProductionSetupRequest, user: dict = Depends(get_current_user)):
    """Set extras, CGI and VFX for a film in pre-production."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if project['status'] != 'pre_production':
        raise HTTPException(status_code=400, detail="Il film deve essere in pre-produzione")

    # Validate extras
    extras_count = max(50, min(1000, req.extras_count))
    genre = project.get('genre', 'drama')

    # Calculate CGI cost
    available_cgi = CGI_PACKAGES.get(genre, CGI_DEFAULT)
    cgi_ids = {p['id'] for p in available_cgi}
    selected_cgi = [p for p in available_cgi if p['id'] in req.cgi_packages and p['id'] in cgi_ids]
    cgi_cost = sum(p['cost'] for p in selected_cgi)
    cgi_bonus = sum(p['quality_bonus'] for p in selected_cgi)

    # Calculate VFX cost
    available_vfx = VFX_PACKAGES.get(genre, VFX_DEFAULT)
    vfx_ids = {p['id'] for p in available_vfx}
    selected_vfx = [p for p in available_vfx if p['id'] in req.vfx_packages and p['id'] in vfx_ids]
    vfx_cost = sum(p['cost'] for p in selected_vfx)
    vfx_bonus = sum(p['quality_bonus'] for p in selected_vfx)

    # Extras cost
    extras_cost = extras_count * EXTRAS_COST_PER_PERSON

    total_cost = cgi_cost + vfx_cost + extras_cost

    if user.get('funds', 0) < total_cost:
        raise HTTPException(status_code=400, detail=f"Fondi insufficienti. Servono ${total_cost:,}")

    # Deduct funds
    await db.users.update_one({'id': user['id']}, {'$inc': {'funds': -total_cost}})

    # Save production setup
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'production_setup': {
                'extras_count': extras_count,
                'extras_cost': extras_cost,
                'cgi_packages': [{'id': p['id'], 'name': p['name'], 'cost': p['cost'], 'quality_bonus': p['quality_bonus']} for p in selected_cgi],
                'cgi_cost': cgi_cost,
                'cgi_bonus': cgi_bonus,
                'vfx_packages': [{'id': p['id'], 'name': p['name'], 'cost': p['cost'], 'quality_bonus': p['quality_bonus']} for p in selected_vfx],
                'vfx_cost': vfx_cost,
                'vfx_bonus': vfx_bonus,
                'total_cost': total_cost,
                'setup_completed': True
            }
        }}
    )

    return {
        'success': True,
        'message': f'Setup produzione completato! Costo totale: ${total_cost:,}',
        'total_cost': total_cost,
        'extras_count': extras_count,
        'cgi_count': len(selected_cgi),
        'vfx_count': len(selected_vfx)
    }

@router.get("/film-pipeline/buzz")
async def get_buzz_films(user: dict = Depends(get_current_user)):
    """Get films in shooting that can be voted on (excluding user's own)."""
    films = await db.film_projects.find(
        {'status': 'shooting', 'user_id': {'$ne': user['id']}},
        {'_id': 0, 'hidden_factor': 0, 'cast_proposals': 0}
    ).to_list(20)

    # Filter out films already voted by this user
    result = []
    for f in films:
        voters = f.get('buzz_voters', [])
        if user['id'] not in voters:
            result.append({
                'id': f['id'],
                'title': f['title'],
                'genre': f['genre'],
                'subgenre': f.get('subgenre', ''),
                'pre_imdb_score': f.get('pre_imdb_score', 5),
                'pre_screenplay': f.get('pre_screenplay', '')[:150] + '...',
                'owner_nickname': f.get('owner_nickname', ''),
                'buzz_votes': f.get('buzz_votes', {}),
                'total_votes': sum(f.get('buzz_votes', {}).values())
            })

    # Get owner nicknames
    owner_ids = list(set(f.get('user_id', '') for f in films))
    if owner_ids:
        owners = await db.users.find({'id': {'$in': owner_ids}}, {'_id': 0, 'id': 1, 'nickname': 1}).to_list(50)
        owner_map = {o['id']: o['nickname'] for o in owners}
        for f_orig, f_result in zip(films, result):
            f_result['owner_nickname'] = owner_map.get(f_orig.get('user_id', ''), 'Sconosciuto')

    return {'films': result}


@router.post("/film-pipeline/{project_id}/buzz-vote")
async def buzz_vote(project_id: str, req: BuzzVoteRequest, user: dict = Depends(get_current_user)):
    """Vote on a film's buzz (hype level)."""
    if req.vote not in ('high', 'medium', 'low'):
        raise HTTPException(status_code=400, detail="Voto non valido. Usa 'high', 'medium' o 'low'")

    project = await db.film_projects.find_one(
        {'id': project_id, 'status': 'shooting'},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Film non trovato")
    if project.get('user_id') == user['id']:
        raise HTTPException(status_code=400, detail="Non puoi votare il tuo film")
    if user['id'] in project.get('buzz_voters', []):
        raise HTTPException(status_code=400, detail="Hai già votato per questo film")

    # Update votes
    await db.film_projects.update_one(
        {'id': project_id},
        {
            '$inc': {f'buzz_votes.{req.vote}': 1},
            '$push': {'buzz_voters': user['id']}
        }
    )

    # Reward voter with 1-2 CinePass
    cp_reward = random.choice([1, 1, 2])
    await db.users.update_one({'id': user['id']}, {'$inc': {'cinepass': cp_reward}})

    vote_labels = {'high': 'Hype alto!', 'medium': 'Interessante', 'low': 'Meh...'}
    return {
        'success': True,
        'message': f'Voto registrato: {vote_labels[req.vote]} +{cp_reward} CP',
        'cp_reward': cp_reward
    }


# ==================== FILM COMING SOON + RELEASE STRATEGY ====================

class ReleaseStrategyRequest(BaseModel):
    strategy: str  # 'auto' or 'manual'
    hours: int = 24  # Only for manual: 6, 12, 24, 48

@router.post("/film-pipeline/{project_id}/choose-release-strategy")
async def choose_release_strategy(project_id: str, req: ReleaseStrategyRequest, user: dict = Depends(get_current_user)):
    """Choose release strategy for a Coming Soon film after shooting completes."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(404, "Film non trovato")
    if project.get('release_type') != 'coming_soon':
        raise HTTPException(400, "Solo i film 'Coming Soon' possono usare la strategia di uscita")
    if project['status'] not in ('shooting',):
        raise HTTPException(400, "Il film non e' nella fase giusta")
    # Check shooting is complete
    if not project.get('shooting_completed'):
        started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
        total_days = project.get('shooting_days', 5)
        hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        if hours_elapsed < total_days:
            raise HTTPException(400, "Le riprese non sono ancora completate")

    if req.strategy not in ('auto', 'manual'):
        raise HTTPException(400, "Strategia non valida")

    now = datetime.now(timezone.utc)
    pre_imdb = project.get('pre_imdb_score', 5.0)
    hype = project.get('hype_score', 0)
    competition = await db.film_projects.count_documents({'status': 'coming_soon'})
    perfect_timing = False
    bonus_pct = 0.0

    if req.strategy == 'auto':
        # System calculates optimal release time
        if pre_imdb >= 7.5:
            base_hours = 48
        elif pre_imdb >= 5.5:
            base_hours = 24
        else:
            base_hours = 12
        if competition > 5:
            base_hours += 12
        if hype > 30:
            base_hours = max(6, base_hours - 6)
        hours = max(6, min(72, base_hours))
        bonus_pct = 3.0

    else:  # manual
        if req.hours not in (6, 12, 24, 48):
            raise HTTPException(400, "Durata non valida. Scegli tra 6, 12, 24, 48 ore")
        hours = req.hours
        # Calculate perfect timing
        if pre_imdb >= 7.5 and hours >= 24:
            perfect_timing = True
        elif 5.5 <= pre_imdb < 7.5 and 12 <= hours <= 24:
            perfect_timing = True
        elif pre_imdb < 5.5 and hours <= 12:
            perfect_timing = True
        if hype > 30 and hours <= 12:
            perfect_timing = True
        if competition > 5 and hours >= 48:
            perfect_timing = True
        bonus_pct = 8.0 if perfect_timing else 0.0

    release_at = now + timedelta(hours=hours)

    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'coming_soon',
            'release_strategy': req.strategy,
            'release_strategy_hours': hours,
            'release_strategy_bonus_pct': bonus_pct,
            'release_strategy_perfect': perfect_timing,
            'scheduled_release_at': release_at.isoformat(),
            'coming_soon_started_at': now.isoformat(),
            'updated_at': now.isoformat()
        }}
    )

    return {
        "status": "coming_soon",
        "strategy": req.strategy,
        "hours_until_release": hours,
        "scheduled_release_at": release_at.isoformat(),
        "bonus_pct": bonus_pct,
        "perfect_timing": perfect_timing
    }


class ScheduleFilmReleaseRequest(BaseModel):
    release_hours: int = 24

@router.post("/film-pipeline/{project_id}/schedule-release")
async def schedule_film_release(project_id: str, req: ScheduleFilmReleaseRequest, user: dict = Depends(get_current_user)):
    """Legacy schedule endpoint - redirects to strategy system."""
    project = await db.film_projects.find_one(
        {'id': project_id, 'user_id': user['id']},
        {'_id': 0}
    )
    if not project:
        raise HTTPException(404, "Film non trovato")
    if project.get('release_type') != 'coming_soon':
        raise HTTPException(400, "Solo i film 'Coming Soon' possono essere programmati")
    if project['status'] != 'shooting':
        raise HTTPException(400, "Il film non e' pronto per la programmazione")
    if not project.get('shooting_completed'):
        started = datetime.fromisoformat(project['shooting_started_at'].replace('Z', '+00:00'))
        total_days = project.get('shooting_days', 5)
        hours_elapsed = (datetime.now(timezone.utc) - started).total_seconds() / 3600
        if hours_elapsed < total_days:
            raise HTTPException(400, "Le riprese non sono ancora completate")
    
    hours = max(1, min(168, req.release_hours))
    release_at = datetime.now(timezone.utc) + timedelta(hours=hours)
    
    await db.film_projects.update_one(
        {'id': project_id},
        {'$set': {
            'status': 'coming_soon',
            'scheduled_release_at': release_at.isoformat(),
            'coming_soon_started_at': datetime.now(timezone.utc).isoformat(),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {
        "status": "coming_soon",
        "scheduled_release_at": release_at.isoformat(),
        "hours_until_release": hours
    }
