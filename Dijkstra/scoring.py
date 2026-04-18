"""Apartment scores: Dijkstra from NEU_SV + one run per apartment; chain + category mins."""

from typing import Any, Dict, List, Optional, Tuple

from Dijkstra.shortest_path import Graph, dijkstra, path_leg_breakdown, reconstruct_path
from Dijkstra.walk_estimate import build_coord_map, walk_minutes_between_ids

CHAIN_KEY = "starbucks_neu_chain"
OTHER_CATEGORIES = ("costco", "trader_joes", "gym_24hf")

MODE_TRANSIT = "transit"
MODE_STRAIGHT_LINE_WALK = "straight_line_walk"


def _node_lookup(apartments: List[dict], destinations: List[dict]) -> Dict[str, str]:
    names = {}
    for a in apartments:
        names[a["id"]] = a.get("name", a["id"])
    for d in destinations:
        names[d["id"]] = d.get("name", d["id"])
    return names


def _min_with_tiebreak(
    items: List[Tuple[str, float]],
) -> Tuple[Optional[str], float]:
    """Argmin by distance, then by id for stability."""
    finite = [(i, d) for i, d in items if d != float("inf")]
    if not finite:
        return None, float("inf")
    return min(finite, key=lambda x: (x[1], x[0]))


def _effective_transit_vs_walk(t_transit: float, t_walk: float) -> Tuple[float, bool]:
    """Return (effective_minutes, used_straight_line_walk).

    Tie (equal finite): prefer transit for path richness.
    """
    if t_walk == float("inf"):
        return t_transit, False
    if t_transit == float("inf"):
        return t_walk, True
    if t_walk < t_transit:
        return t_walk, True
    return t_transit, False


def _leg_mode(used_walk: bool) -> str:
    return MODE_STRAIGHT_LINE_WALK if used_walk else MODE_TRANSIT


def _path_legs(
    graph: Graph,
    path: List[str],
    used_straight_line: bool,
    straight_line_minutes: float,
) -> List[Dict[str, Any]]:
    """Graph leg breakdown, or one synthetic leg for Haversine shortcut."""
    if len(path) < 2:
        return []
    if used_straight_line:
        return [
            {
                "from": path[0],
                "to": path[-1],
                "minutes": straight_line_minutes,
                "mode": MODE_STRAIGHT_LINE_WALK,
            }
        ]
    return path_leg_breakdown(graph, path)


def compute_apartment_scores(
    graph: Graph,
    apartments: List[dict],
    destinations: List[dict],
    categories: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Return one result dict per apartment (unsorted)."""
    chain_cfg = categories[CHAIN_KEY]
    chain_endpoint: str = chain_cfg["chain_endpoint"]
    starbucks_ids: List[str] = list(chain_cfg["candidates"])
    chain_visits = int(chain_cfg["weekly_visits"])

    if chain_endpoint not in graph:
        raise ValueError(f"Chain endpoint {chain_endpoint!r} not in graph")

    coord_map = build_coord_map(apartments, destinations)
    dist_neu, prev_neu = dijkstra(graph, chain_endpoint)
    names = _node_lookup(apartments, destinations)

    results: List[Dict[str, Any]] = []
    for apt in apartments:
        aid = apt["id"]
        dist_apt, prev_apt = dijkstra(graph, aid)

        # --- Starbucks → NEU chain ---
        per_sb: List[Dict[str, Any]] = []
        for sid in starbucks_ids:
            t1_tr = dist_apt.get(sid, float("inf"))
            t1_wk = walk_minutes_between_ids(aid, sid, coord_map)
            eff1, walk1 = _effective_transit_vs_walk(t1_tr, t1_wk)

            t2_tr = dist_neu.get(sid, float("inf"))
            t2_wk = walk_minutes_between_ids(chain_endpoint, sid, coord_map)
            eff2, walk2 = _effective_transit_vs_walk(t2_tr, t2_wk)

            total = eff1 + eff2 if eff1 != float("inf") and eff2 != float("inf") else float("inf")
            row = {
                "starbucks_id": sid,
                "starbucks_name": names.get(sid, sid),
                "minutes_apt_to_starbucks_transit": t1_tr,
                "minutes_apt_to_starbucks_walk_straight_line": t1_wk,
                "minutes_apt_to_starbucks": eff1,
                "leg1_used_straight_line_walk": walk1,
                "leg1_mode": _leg_mode(walk1),
                "minutes_starbucks_to_neu_transit": t2_tr,
                "minutes_starbucks_to_neu_walk_straight_line": t2_wk,
                "minutes_starbucks_to_neu": eff2,
                "leg2_used_straight_line_walk": walk2,
                "leg2_mode": _leg_mode(walk2),
                "minutes_one_chain_trip": total,
            }
            per_sb.append(row)

        chain_totals = [(r["starbucks_id"], r["minutes_one_chain_trip"]) for r in per_sb]
        opt_s, one_chain = _min_with_tiebreak(chain_totals)
        chain_weekly = chain_visits * one_chain if one_chain != float("inf") else float("inf")

        path_apt_s: List[str] = []
        path_s_neu: List[str] = []
        legs_apt_s: List[Dict[str, Any]] = []
        legs_s_neu: List[Dict[str, Any]] = []
        leg1_mode_opt = MODE_TRANSIT
        leg2_mode_opt = MODE_TRANSIT
        if opt_s is not None and one_chain != float("inf"):
            row_opt = next(r for r in per_sb if r["starbucks_id"] == opt_s)
            leg1_mode_opt = row_opt["leg1_mode"]
            leg2_mode_opt = row_opt["leg2_mode"]
            if row_opt["leg1_used_straight_line_walk"]:
                path_apt_s = [aid, opt_s]
            else:
                path_apt_s = reconstruct_path(prev_apt, aid, opt_s)
            if row_opt["leg2_used_straight_line_walk"]:
                path_s_neu = [opt_s, chain_endpoint]
            else:
                neu_to_s = reconstruct_path(prev_neu, chain_endpoint, opt_s)
                path_s_neu = list(reversed(neu_to_s)) if neu_to_s else []
            legs_apt_s = _path_legs(
                graph,
                path_apt_s,
                row_opt["leg1_used_straight_line_walk"],
                float(row_opt["minutes_apt_to_starbucks"]),
            )
            legs_s_neu = _path_legs(
                graph,
                path_s_neu,
                row_opt["leg2_used_straight_line_walk"],
                float(row_opt["minutes_starbucks_to_neu"]),
            )

        chain_block: Dict[str, Any] = {
            "category_key": CHAIN_KEY,
            "weekly_visits": chain_visits,
            "chain_endpoint_id": chain_endpoint,
            "chain_endpoint_name": names.get(chain_endpoint, chain_endpoint),
            "one_trip_minutes": one_chain,
            "weekly_weighted_minutes": chain_weekly,
            "optimal_starbucks_id": opt_s,
            "optimal_starbucks_name": names.get(opt_s, opt_s) if opt_s else None,
            "optimal_leg1_mode": leg1_mode_opt,
            "optimal_leg2_mode": leg2_mode_opt,
            "per_starbucks": per_sb,
            "path_apartment_to_optimal_starbucks": path_apt_s,
            "path_apartment_to_optimal_starbucks_legs": legs_apt_s,
            "path_optimal_starbucks_to_neu": path_s_neu,
            "path_optimal_starbucks_to_neu_legs": legs_s_neu,
            "reachable": opt_s is not None and one_chain != float("inf"),
        }

        category_blocks: Dict[str, Any] = {CHAIN_KEY: chain_block}
        total_weekly = chain_weekly if chain_weekly != float("inf") else float("inf")

        for cat_key in OTHER_CATEGORIES:
            cfg = categories[cat_key]
            cands: List[str] = list(cfg["candidates"])
            visits = int(cfg["weekly_visits"])

            cand_details: List[Dict[str, Any]] = []
            pairs: List[Tuple[str, float]] = []
            for c in cands:
                t_tr = dist_apt.get(c, float("inf"))
                t_wk = walk_minutes_between_ids(aid, c, coord_map)
                eff, u_w = _effective_transit_vs_walk(t_tr, t_wk)
                cand_details.append(
                    {
                        "id": c,
                        "minutes": eff,
                        "transit_minutes": t_tr,
                        "walk_straight_line_minutes": t_wk,
                        "used_straight_line_walk": u_w,
                    }
                )
                pairs.append((c, eff))

            best_id, best_d = _min_with_tiebreak(pairs)
            wmin = visits * best_d if best_d != float("inf") else float("inf")
            if wmin != float("inf") and total_weekly != float("inf"):
                total_weekly += wmin
            elif wmin == float("inf"):
                total_weekly = float("inf")

            path_best: List[str] = []
            best_detail = next((x for x in cand_details if x["id"] == best_id), None)
            best_used_walk = bool(best_detail and best_detail["used_straight_line_walk"])
            best_t_tr = best_detail["transit_minutes"] if best_detail else float("inf")
            best_t_wk = best_detail["walk_straight_line_minutes"] if best_detail else float("inf")

            if best_id is not None and best_d != float("inf"):
                if best_used_walk:
                    path_best = [aid, best_id]
                else:
                    path_best = reconstruct_path(prev_apt, aid, best_id)

            path_best_legs = _path_legs(graph, path_best, best_used_walk, float(best_d))

            category_blocks[cat_key] = {
                "category_key": cat_key,
                "weekly_visits": visits,
                "best_candidate_id": best_id,
                "best_candidate_name": names.get(best_id, best_id) if best_id else None,
                "one_way_minutes": best_d,
                "one_way_minutes_transit": best_t_tr,
                "one_way_minutes_walk_straight_line": best_t_wk,
                "used_straight_line_walk": best_used_walk,
                "weekly_weighted_minutes": wmin,
                "path_apartment_to_best": path_best,
                "path_apartment_to_best_legs": path_best_legs,
                "reachable": best_id is not None and best_d != float("inf"),
                "candidates_minutes": cand_details,
            }

        results.append(
            {
                "apartment_id": aid,
                "apartment_name": apt.get("name", aid),
                "monthly_rent": apt.get("monthly_rent"),
                "area": apt.get("area"),
                "total_minutes_per_week": total_weekly,
                "categories": category_blocks,
            }
        )

    return results


def rank_apartments(scored: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort by total ascending; tie-break by apartment_id."""
    return sorted(
        scored,
        key=lambda r: (
            r["total_minutes_per_week"] if r["total_minutes_per_week"] != float("inf") else float("inf"),
            r["apartment_id"],
        ),
    )


def run_full_pipeline(
    apartments: List[dict],
    stations: List[dict],
    dest_doc: Dict[str, Any],
) -> Tuple[Graph, List[Dict[str, Any]]]:
    """Build graph and return (graph, ranked_results)."""
    from Dijkstra.graph_builder import build_graph

    destinations = dest_doc["destinations"]
    categories = dest_doc["categories"]
    graph = build_graph(apartments, stations, destinations)
    raw = compute_apartment_scores(graph, apartments, destinations, categories)
    ranked = rank_apartments(raw)
    return graph, ranked


def graph_edge_stats(graph: Graph) -> Tuple[int, int]:
    """Undirected edge count (each edge counted once)."""
    nodes = len(graph)
    directed = sum(len(v) for v in graph.values())
    edges = directed // 2
    return nodes, edges
