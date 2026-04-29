"""
calc_speedup.py — Sistema costi velocizzazione unificato

Il costo diminuisce esponenzialmente in base al progresso attuale.
Piu sei avanti, meno costa velocizzare.

Usato da: Hype, Ciak, FinalCut, La Prima
"""

# Costi base CP per percentuale
BASE_COSTS = {25: 10, 50: 15, 75: 20, 100: 25}
# Costi capped per Film TV (max 5 CP)
BASE_COSTS_TV = {25: 1, 50: 3, 75: 4, 100: 5}


def get_speedup_cost(percentage: int, current_progress: float, is_tv_movie: bool = False) -> int:
    """Calcola il costo in CinePass per una velocizzazione.

    Il costo scala inversamente con il progresso:
    - A 0% progresso: costo pieno
    - A 90% progresso: costo quasi nullo

    Per i Film TV (is_tv_movie=True) usa una scala ridotta (max 5 CP a 100%).
    """
    base_table = BASE_COSTS_TV if is_tv_movie else BASE_COSTS
    base = base_table.get(percentage, 3 if is_tv_movie else 15)
    remaining_ratio = max(0.0, (100.0 - current_progress) / 100.0)
    return max(1, round(base * remaining_ratio))


def calculate_speedup_gain(percentage: int, current_progress: float) -> float:
    """Calcola il guadagno effettivo in punti percentuali.
    
    Il guadagno e' applicato sul RIMANENTE, non sull'intero.
    Es: a 80%, con 100% speedup -> guadagno = 20% (il rimanente)
    Es: a 80%, con 50% speedup -> guadagno = 10% (50% del rimanente)
    """
    remaining = 100.0 - current_progress
    return remaining * (percentage / 100.0)
