# calc_adv.py — Advertising campaign calculation logic
# Extracted from film_engagement.py for modular architecture


AD_PLATFORMS = [
    {"id": "social_media", "name": "Social Media", "name_it": "Social Media", "reach_multiplier": 1.2, "cost_per_day": 6000},
    {"id": "tv_spots", "name": "TV Commercials", "name_it": "Spot TV", "reach_multiplier": 2.0, "cost_per_day": 60000},
    {"id": "billboards", "name": "Billboards", "name_it": "Cartelloni", "reach_multiplier": 1.5, "cost_per_day": 24000},
    {"id": "streaming_ads", "name": "Streaming Ads", "name_it": "Pubblicità Streaming", "reach_multiplier": 1.8, "cost_per_day": 36000},
    {"id": "influencers", "name": "Influencer Campaign", "name_it": "Campagna Influencer", "reach_multiplier": 1.6, "cost_per_day": 30000},
    {"id": "premiere_event", "name": "Red Carpet Premiere", "name_it": "Premiere Red Carpet", "reach_multiplier": 2.5, "cost_per_day": 120000},
]


def calculate_adv_cost(platform_ids: list, days: int) -> dict:
    """Calculate total advertising campaign cost and expected boost."""
    total_cost = 0
    total_multiplier = 1.0
    selected = []

    for pid in platform_ids:
        platform = next((p for p in AD_PLATFORMS if p["id"] == pid), None)
        if platform:
            platform_cost = platform["cost_per_day"] * days
            total_cost += platform_cost
            total_multiplier *= platform["reach_multiplier"]
            selected.append(platform)

    return {
        "total_cost": total_cost,
        "total_multiplier": round(total_multiplier, 2),
        "platforms": selected,
        "days": days,
    }


def calculate_adv_revenue_boost(film: dict, total_multiplier: float, days: int) -> int:
    """Calculate the revenue boost from an advertising campaign."""
    opening_day = film.get("opening_day_revenue", 100000) or 100000
    quality_mult = (film.get("quality_score") or 50) / 100
    daily_boost = opening_day * quality_mult * total_multiplier * 0.5
    boosted = int(daily_boost * days)
    max_boost = opening_day * 10
    return min(boosted, max_boost)
