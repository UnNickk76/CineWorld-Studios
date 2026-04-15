"""
calc_production_cost.py — Calcolo costo totale produzione film

Range: $1M - $200M denaro, 5-30 CP crediti
Rientro sponsor sottratto dal costo denaro.
Velocizzazioni GIA scalate al momento -> NON nel totale.
"""


# Base cost by format
FORMAT_BASE_COST = {
    "cortometraggio": 1_000_000,
    "medio": 5_000_000,
    "standard": 15_000_000,
    "epico": 50_000_000,
    "kolossal": 120_000_000,
}

FORMAT_BASE_CP = {
    "cortometraggio": 5,
    "medio": 8,
    "standard": 12,
    "epico": 18,
    "kolossal": 25,
}

# Cast cost multipliers by star rating
CAST_STAR_COST = {
    1: 50_000,
    2: 150_000,
    3: 400_000,
    4: 1_000_000,
    5: 3_000_000,
}

# Equipment costs
EQUIPMENT_COSTS = {
    "steadicam": 100_000,
    "drone": 200_000,
    "crane": 350_000,
    "underwater": 500_000,
    "anamorphic": 150_000,
}

CGI_COSTS = {
    "basic_cgi": 500_000,
    "advanced_cgi": 2_000_000,
    "full_cgi": 5_000_000,
}

VFX_COSTS = {
    "explosions": 800_000,
    "creatures": 3_000_000,
    "environments": 1_500_000,
    "de_aging": 2_000_000,
}

# Marketing package costs (same as in pipeline)
MARKETING_COSTS = {
    "Teaser Digitale": 20_000,
    "Campagna Social": 40_000,
    "Campagna Social Virale": 40_000,
    "Stampa e TV": 60_000,
    "Tour Cast": 80_000,
    "Tour del Cast": 80_000,
    "Mega Globale": 150_000,
    "Mega Campagna Globale": 150_000,
}

# Extras cost per 100
EXTRAS_COST_PER_100 = 80_000


def calculate_production_cost(project: dict) -> dict:
    """Calcola il costo totale di produzione.
    
    Returns breakdown + totals.
    """
    film_format = project.get("film_format", "standard")
    
    # === DENARO ===
    breakdown = []
    
    # 1. Base production cost
    base = FORMAT_BASE_COST.get(film_format, 15_000_000)
    breakdown.append({"id": "base", "label": "Produzione base", "category": "base", "funds": base, "editable": False})
    
    # 2. Cast
    cast = project.get("cast") or {}
    cast_cost = 0
    for role in ["director", "composer"]:
        member = cast.get(role)
        if member and isinstance(member, dict):
            stars = member.get("stars", 1) or 1
            cast_cost += CAST_STAR_COST.get(stars, 50_000)
    for member in (cast.get("actors") or []):
        if isinstance(member, dict):
            stars = member.get("stars", 1) or 1
            cast_cost += CAST_STAR_COST.get(stars, 50_000)
    for member in (cast.get("screenwriters") or []):
        if isinstance(member, dict):
            stars = member.get("stars", 1) or 1
            cast_cost += CAST_STAR_COST.get(stars, 50_000) * 0.5
    if cast_cost > 0:
        breakdown.append({"id": "cast", "label": "Cast & Troupe", "category": "cast", "funds": round(cast_cost), "editable": True})
    
    # 3. Equipment
    equip_cost = sum(EQUIPMENT_COSTS.get(e, 0) for e in (project.get("prep_equipment") or []))
    if equip_cost > 0:
        breakdown.append({"id": "equipment", "label": "Attrezzature", "category": "equipment", "funds": equip_cost, "editable": True})
    
    # 4. CGI
    cgi_cost = sum(CGI_COSTS.get(c, 0) for c in (project.get("prep_cgi") or []))
    if cgi_cost > 0:
        breakdown.append({"id": "cgi", "label": "CGI", "category": "cgi", "funds": cgi_cost, "editable": True})
    
    # 5. VFX
    vfx_cost = sum(VFX_COSTS.get(v, 0) for v in (project.get("prep_vfx") or []))
    if vfx_cost > 0:
        breakdown.append({"id": "vfx", "label": "VFX", "category": "vfx", "funds": vfx_cost, "editable": True})
    
    # 6. Extras
    extras = project.get("prep_extras", 0) or 0
    extras_cost = (extras // 100) * EXTRAS_COST_PER_100
    if extras_cost > 0:
        breakdown.append({"id": "extras", "label": f"Comparse ({extras})", "category": "extras", "funds": extras_cost, "editable": True})
    
    # 7. Shooting days factor
    shooting_days = project.get("shooting_days", 14) or 14
    shoot_cost = max(0, (shooting_days - 5)) * 200_000
    if shoot_cost > 0:
        breakdown.append({"id": "shooting", "label": f"Riprese ({shooting_days}gg)", "category": "shooting", "funds": shoot_cost, "editable": False})
    
    # 8. Marketing
    mkt_cost = sum(MARKETING_COSTS.get(p, 0) for p in (project.get("marketing_packages") or []))
    if mkt_cost > 0:
        breakdown.append({"id": "marketing", "label": "Marketing", "category": "marketing", "funds": mkt_cost, "editable": True})
    
    # 9. Distribution
    dist_cost_data = project.get("distribution_cost") or {}
    dist_funds = dist_cost_data.get("total_funds", 0)
    if dist_funds > 0:
        breakdown.append({"id": "distribution", "label": "Distribuzione", "category": "distribution", "funds": dist_funds, "editable": True})
    
    # Total funds
    total_funds = sum(b["funds"] for b in breakdown)
    
    # 10. Sponsor offset
    sponsor_offset = project.get("sponsors_total_offer", 0) or 0
    if sponsor_offset > 0:
        breakdown.append({"id": "sponsors", "label": "Rientro Sponsor", "category": "sponsors", "funds": -sponsor_offset, "editable": False})
        total_funds -= sponsor_offset
    
    total_funds = max(1_000_000, total_funds)
    
    # === CREDITI (max 30) ===
    base_cp = FORMAT_BASE_CP.get(film_format, 12)
    # Add CP for complexity
    complexity_cp = 0
    if len(project.get("prep_cgi") or []) > 1:
        complexity_cp += 2
    if len(project.get("prep_vfx") or []) > 1:
        complexity_cp += 2
    if len((cast.get("actors") or [])) >= 4:
        complexity_cp += 1
    dist_cp = (dist_cost_data.get("total_cp", 0) or 0)
    
    total_cp = min(30, base_cp + complexity_cp + dist_cp)
    
    return {
        "breakdown": breakdown,
        "total_funds": total_funds,
        "total_cp": total_cp,
        "sponsor_offset": sponsor_offset,
    }


def calculate_savings_options(project: dict, current_cost: dict) -> list:
    """Calcola 5-6 opzioni di risparmio reali."""
    options = []
    
    cast = project.get("cast") or {}
    actors = cast.get("actors") or []
    
    # 1. Riduci Cast (remove most expensive actor)
    if len(actors) > 2:
        expensive = max(actors, key=lambda a: a.get("stars", 1) if isinstance(a, dict) else 1) if actors else None
        if expensive and isinstance(expensive, dict):
            savings = CAST_STAR_COST.get(expensive.get("stars", 1), 50_000)
            options.append({
                "id": "reduce_cast",
                "label": "Riduci Cast",
                "description": f"Rimuovi l'attore piu costoso ({expensive.get('name', '?')})",
                "savings_funds": savings,
                "savings_cp": 0,
            })
    
    # 2. Riduci Attrezzature
    equipment = project.get("prep_equipment") or []
    if len(equipment) > 1:
        most_expensive = max(equipment, key=lambda e: EQUIPMENT_COSTS.get(e, 0))
        savings = EQUIPMENT_COSTS.get(most_expensive, 0)
        options.append({
            "id": "reduce_equipment",
            "label": "Riduci Attrezzature",
            "description": f"Rimuovi {most_expensive.replace('_', ' ')}",
            "savings_funds": savings,
            "savings_cp": 0,
        })
    
    # 3. Riduci CGI/VFX
    cgi = project.get("prep_cgi") or []
    vfx = project.get("prep_vfx") or []
    all_fx = [(c, CGI_COSTS.get(c, 0), "cgi") for c in cgi] + [(v, VFX_COSTS.get(v, 0), "vfx") for v in vfx]
    if len(all_fx) > 0:
        most_expensive = max(all_fx, key=lambda x: x[1])
        options.append({
            "id": "reduce_fx",
            "label": "Riduci Effetti",
            "description": f"Rimuovi {most_expensive[0].replace('_', ' ')}",
            "savings_funds": most_expensive[1],
            "savings_cp": 1 if most_expensive[1] > 1_000_000 else 0,
        })
    
    # 4. Riduci Marketing
    mkt = project.get("marketing_packages") or []
    if len(mkt) > 0:
        most_expensive = max(mkt, key=lambda p: MARKETING_COSTS.get(p, 0))
        savings = MARKETING_COSTS.get(most_expensive, 0)
        options.append({
            "id": "reduce_marketing",
            "label": "Riduci Marketing",
            "description": f"Rimuovi {most_expensive}",
            "savings_funds": savings,
            "savings_cp": 0,
        })
    
    # 5. Riduci Distribuzione
    dist = project.get("distribution_cost") or {}
    if dist.get("total_funds", 0) > 30000:
        savings = round(dist["total_funds"] * 0.4)
        options.append({
            "id": "reduce_distribution",
            "label": "Riduci Distribuzione",
            "description": "Dimezza le zone di distribuzione",
            "savings_funds": savings,
            "savings_cp": max(1, dist.get("total_cp", 0) // 3),
        })
    
    # 6. Riduci Comparse
    extras = project.get("prep_extras", 0) or 0
    if extras > 200:
        reduction = extras // 2
        savings = (reduction // 100) * EXTRAS_COST_PER_100
        options.append({
            "id": "reduce_extras",
            "label": "Riduci Comparse",
            "description": f"Dimezza comparse ({extras} -> {extras - reduction})",
            "savings_funds": savings,
            "savings_cp": 0,
        })
    
    return options


def calculate_velion_savings(project: dict, current_cost: dict) -> dict:
    """Velion auto-ottimizza: lima piccole quantita da piu voci."""
    total_funds = current_cost.get("total_funds", 0)
    total_cp = current_cost.get("total_cp", 0)
    
    # Velion saves 8-15% on funds, 1-3 CP
    import random
    pct = random.uniform(0.08, 0.15)
    funds_saved = round(total_funds * pct, -3)
    cp_saved = min(3, max(1, total_cp // 8))
    
    changes = []
    # Small cuts across categories
    for b in current_cost.get("breakdown", []):
        if b.get("editable") and b["funds"] > 0:
            cut = round(b["funds"] * random.uniform(0.03, 0.10), -3)
            if cut > 0:
                changes.append(f"{b['label']}: -${cut:,.0f}")
    
    return {
        "savings_funds": int(funds_saved),
        "savings_cp": cp_saved,
        "savings_pct": round(pct * 100, 1),
        "changes": changes,
    }
