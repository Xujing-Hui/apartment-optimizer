"""
optimizer.py
------------
Main pipeline for the Apartment Commute Optimizer.

Pipeline
--------
1. Load data from the three JSON files.
2. Build the weighted transit graph (graph.py).
3. Pre-compute shortest paths FROM NEU (used by chain-trip scoring).
4. For each apartment that passes the constraint filters:
     a. Run Dijkstra from the apartment to all 66 nodes.
     b. Compute chain_cost = min over k { d(apt, Sk) + d(Sk, NEU) }
     c. Compute best-of-6 cost for Costco, Trader Joe's, and Gym.
     d. Compute weighted score = 3×chain + 1×costco + 2×TJ + 4×gym
5. Sort apartments by score (ascending) and print ranked results.

Objective function
------------------
    score(apt) = 3 × chain_cost
               + 1 × min d(apt → Costco_k)
               + 2 × min d(apt → TJ_k)
               + 4 × min d(apt → Gym_k)

    chain_cost = min over k { d(apt, Starbucks_k) + d(Starbucks_k, NEU) }

    All distances d(·,·) are shortest-path times in minutes computed
    over the multi-modal transit graph by Dijkstra's algorithm.

Visit weights: Chain(NEU+SB)=3, Costco=1, Trader Joe's=2, Gym=4
"""

import sys
import os

# Allow running from the src/ directory directly
sys.path.insert(0, os.path.dirname(__file__))

from graph     import load_data, build_graph
from dijkstra  import dijkstra, reconstruct_path

# ── Destination ID lists by category ─────────────────────────────────────────
STARBUCKS_IDS = ["S1", "S2", "S3", "S4", "S5", "S6"]
COSTCO_IDS    = ["C1", "C2", "C3", "C4", "C5", "C6"]
TJ_IDS        = ["T1", "T2", "T3", "T4", "T5", "T6"]
GYM_IDS       = ["G1", "G2", "G3", "G4", "G5", "G6"]

# Visit weights (matches weekly_visits in destinations_json.json)
WEIGHT_CHAIN  = 3   # Starbucks + NEU combined (3 visits/week)
WEIGHT_COSTCO = 1
WEIGHT_TJ     = 2
WEIGHT_GYM    = 4


# ── Helpers ───────────────────────────────────────────────────────────────────
def _best_of(dist_apt: dict, candidate_ids: list) -> tuple[float, str]:
    """
    Return (min_distance, best_id) for a set of candidate destination IDs
    using pre-computed distances from one Dijkstra run.
    """
    best_dist = float("inf")
    best_id   = None
    for cid in candidate_ids:
        d = dist_apt.get(cid, float("inf"))
        if d < best_dist:
            best_dist = d
            best_id   = cid
    return best_dist, best_id


def _chain_trip(dist_apt: dict, dist_neu: dict,
                starbucks_ids: list) -> tuple[float, str]:
    """
    Compute the chain-trip cost:
        chain_cost = min over k { dist_apt[Sk] + dist_neu[Sk] }

    Using the pre-computed dist_neu array (Dijkstra run from NEU once)
    avoids recomputing the Starbucks → NEU leg for every apartment.

    Returns (chain_cost, best_starbucks_id).
    """
    best_chain = float("inf")
    best_sb    = None
    for sid in starbucks_ids:
        d_apt_sb = dist_apt.get(sid, float("inf"))
        d_sb_neu = dist_neu.get(sid, float("inf"))
        chain    = d_apt_sb + d_sb_neu
        if chain < best_chain:
            best_chain = chain
            best_sb    = sid
    return best_chain, best_sb


# ── Constraint filter ─────────────────────────────────────────────────────────
def passes_constraints(apt: dict, constraints: dict) -> bool:
    """
    Return True if the apartment satisfies all hard constraints:
      - Monthly rent ≤ max_monthly_rent
      - Walk to nearest station ≤ max_walk_min_to_station
    """
    return (apt["monthly_rent"]        <= constraints["max_monthly_rent"] and
            apt["walk_min_to_station"] <= constraints["max_walk_min_to_station"])


# ── Main optimizer ────────────────────────────────────────────────────────────
def run_optimizer(verbose: bool = True) -> list[dict]:
    """
    Execute the full optimization pipeline and return a sorted list of
    result dicts.

    Parameters
    ----------
    verbose : bool
        If True, print a formatted ranking table to stdout.

    Returns
    -------
    list[dict]  sorted by score ascending, each dict contains:
        apt, score, chain, best_sb, sb_to_apt, sb_to_neu,
        costco, best_costco, tj, best_tj, gym, best_gym
    """
    # Step 1: Load data
    apartments, destinations, stations, constraints, categories = load_data()

    # Step 2: Build graph
    G = build_graph(apartments, destinations, stations)

    # Build lookup: id → name
    dest_name = {d["id"]: d["name"] for d in destinations}

    # Step 3: Pre-compute distances from NEU (used by chain-trip scoring)
    dist_neu, _ = dijkstra(G, "NEU_SV")

    results: list[dict] = []

    # Step 4: Score each apartment
    for apt in apartments:

        # 4a. Constraint filter
        if not passes_constraints(apt, constraints):
            if verbose:
                print(f"FILTERED: {apt['name']}  "
                      f"(rent=${apt['monthly_rent']}, "
                      f"walk={apt['walk_min_to_station']} min)")
            continue

        # 4b. Single Dijkstra run from this apartment
        dist_apt, prev_apt = dijkstra(G, apt["id"])

        # 4c. Chain trip: Apt → Starbucks* → NEU
        chain_cost, best_sb = _chain_trip(dist_apt, dist_neu, STARBUCKS_IDS)

        # 4d. Independent categories: pick best of 6 candidates
        costco_cost, best_costco = _best_of(dist_apt, COSTCO_IDS)
        tj_cost,     best_tj     = _best_of(dist_apt, TJ_IDS)
        gym_cost,    best_gym    = _best_of(dist_apt, GYM_IDS)

        # 4e. Weighted score
        score = (WEIGHT_CHAIN  * chain_cost  +
                 WEIGHT_COSTCO * costco_cost +
                 WEIGHT_TJ     * tj_cost     +
                 WEIGHT_GYM    * gym_cost)

        results.append({
            "apt"       : apt,
            "score"     : round(score, 1),
            "chain"     : round(chain_cost, 1),
            "best_sb"   : best_sb,
            "sb_to_apt" : round(dist_apt.get(best_sb, float("inf")), 1),
            "sb_to_neu" : round(dist_neu.get(best_sb, float("inf")), 1),
            "costco"    : round(costco_cost, 1),
            "best_costco": best_costco,
            "tj"        : round(tj_cost, 1),
            "best_tj"   : best_tj,
            "gym"       : round(gym_cost, 1),
            "best_gym"  : best_gym,
            "dist_apt"  : dist_apt,   # full distance map (for path queries)
            "prev_apt"  : prev_apt,   # predecessor map  (for path queries)
        })

    # Step 5: Sort by score ascending
    results.sort(key=lambda r: r["score"])

    # Optional: print formatted output
    if verbose:
        _print_results(results, dest_name)

    return results


# ── Pretty-print ──────────────────────────────────────────────────────────────
def _print_results(results: list[dict], dest_name: dict) -> None:
    """Print a formatted ranking table."""
    SEP = "=" * 78
    print(f"\n{SEP}")
    print("  APARTMENT COMMUTE OPTIMIZER — FINAL RANKING")
    print(f"{SEP}")
    print(f"  Objective: 3×chain + 1×Costco + 2×TJ + 4×Gym  (min/week)")
    print(f"  Walk fallback cap: 30 min\n")

    for rank, r in enumerate(results, start=1):
        apt = r["apt"]
        print(f"  #{rank}  {apt['name']}  ({apt['area']})")
        print(f"       Rent: ${apt['monthly_rent']:,}   "
              f"Walk to station: {apt['walk_min_to_station']} min")
        print(f"       Chain  (×{WEIGHT_CHAIN}={3*r['chain']:.1f}): "
              f"apt→{r['best_sb']}={r['sb_to_apt']}min + "
              f"{r['best_sb']}→NEU={r['sb_to_neu']}min = {r['chain']} min")
        print(f"       Costco (×{WEIGHT_COSTCO}={r['costco']:.1f}): "
              f"{r['best_costco']} — {dest_name.get(r['best_costco'],'?')}")
        print(f"       TJ     (×{WEIGHT_TJ}={2*r['tj']:.1f}): "
              f"{r['best_tj']} — {dest_name.get(r['best_tj'],'?')}")
        print(f"       Gym    (×{WEIGHT_GYM}={4*r['gym']:.1f}): "
              f"{r['best_gym']} — {dest_name.get(r['best_gym'],'?')}")
        print(f"       >>> TOTAL SCORE: {r['score']} min/week")
        print()

    print(SEP)
    print(f"  Winner: {results[0]['apt']['name']}  "
          f"({results[0]['score']} min/week)")
    print(SEP)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    run_optimizer(verbose=True)
