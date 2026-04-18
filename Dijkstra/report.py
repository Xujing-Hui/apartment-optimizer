"""Human-readable and JSON reports for scoring results."""

import json
from pathlib import Path
from typing import Any, Dict, List, Union

from Dijkstra.walk_estimate import MAX_STRAIGHT_LINE_WALK_MINUTES


def _fmt_minutes(x: float) -> str:
    return f"{x:.1f}" if x != float("inf") else "inf"


def _append_path_leg_lines(lines: List[str], legs: List[Dict[str, Any]], prefix: str = "      ") -> None:
    if not legs:
        return
    lines.append(f"{prefix}By segment (minutes, mode):")
    for leg in legs:
        m = leg.get("minutes")
        if m is None:
            ms = "?"
        elif isinstance(m, float) and m == float("inf"):
            ms = "inf"
        else:
            ms = _fmt_minutes(float(m))
        mode = leg.get("mode", "?")
        lines.append(f"{prefix}  {leg['from']} → {leg['to']}: {ms} min ({mode})")


def _json_safe(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, float):
        if x == float("inf"):
            return None
        return round(x, 6) if x != int(x) else int(x)
    if isinstance(x, dict):
        return {k: _json_safe(v) for k, v in x.items()}
    if isinstance(x, list):
        return [_json_safe(v) for v in x]
    return x


def build_scores_document(
    ranked: List[Dict[str, Any]],
    *,
    nodes: int,
    undirected_edges: int,
    data_paths: Dict[str, str],
) -> Dict[str, Any]:
    """Top-level object written to scores.json."""
    return {
        "metadata": {
            "nodes": nodes,
            "undirected_edges": undirected_edges,
            "input_files": data_paths,
        },
        "rankings": _json_safe(ranked),
    }


def write_scores_json(path: Union[str, Path], doc: Dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2, ensure_ascii=False)


def format_ranking_report(
    ranked: List[Dict[str, Any]],
    *,
    nodes: int,
    undirected_edges: int,
) -> str:
    """Detailed plain-text report."""
    lines: List[str] = []
    sep = "=" * 72
    lines.append(sep)
    lines.append("  TRANSIT-WEIGHTED APARTMENT SCORING (Dijkstra v2)")
    lines.append(sep)
    lines.append("")
    lines.append(f"Graph: {nodes} nodes, {undirected_edges} undirected edges (from JSON topology).")
    lines.append("Objective: minimize total weekly minutes (lower is better).")
    lines.append(
        "Each leg uses min(transit shortest path, Haversine straight-line / 80 m/min), "
        f"with straight-line only if <= {MAX_STRAIGHT_LINE_WALK_MINUTES:g} min "
        "(avoids fake reachability when transit is missing)."
    )
    lines.append("")
    if not ranked:
        lines.append("No apartments scored.")
        return "\n".join(lines)

    best = ranked[0]
    tw = best["total_minutes_per_week"]
    tw_s = f"{tw:.1f}" if tw != float("inf") else "unreachable"
    lines.append("--- Executive summary ---")
    lines.append(f"Best apartment: {best['apartment_id']} — {best['apartment_name']}")
    lines.append(f"Total weekly transit time: {tw_s} minutes")
    lines.append("")

    lines.append("--- Rankings (all apartments) ---")
    lines.append(f"{'Rank':<5}{'ID':<22}{'Weekly min':>14}{'Rent':>10}")
    lines.append("-" * 72)
    for i, r in enumerate(ranked, 1):
        t = r["total_minutes_per_week"]
        ts = f"{t:.1f}" if t != float("inf") else "inf"
        rent = r.get("monthly_rent")
        rs = f"${rent}" if rent is not None else "—"
        lines.append(f"{i:<5}{r['apartment_id']:<22}{ts:>14}{rs:>10}")
    lines.append("")

    cat_labels = {
        "starbucks_neu_chain": "Starbucks → NEU chain (3× one-way chain trip)",
        "costco": "Costco (1× best one-way)",
        "trader_joes": "Trader Joe's (2× best one-way)",
        "gym_24hf": "24 Hour Fitness (4× best one-way)",
    }

    for r in ranked:
        lines.append(sep)
        lines.append(f"  {r['apartment_name']}  [{r['apartment_id']}]")
        if r.get("area"):
            lines.append(f"  Area: {r['area']}")
        lines.append(sep)
        tt = r["total_minutes_per_week"]
        lines.append(f"  TOTAL weekly minutes: {tt:.1f}" if tt != float("inf") else "  TOTAL weekly minutes: unreachable")
        lines.append("")

        cats = r["categories"]
        ch = cats["starbucks_neu_chain"]
        lines.append(f"  [{cat_labels['starbucks_neu_chain']}]")
        lines.append(
            f"    Weekly visits: {ch['weekly_visits']}  |  Endpoint: {ch['chain_endpoint_id']} ({ch['chain_endpoint_name']})"
        )
        if ch.get("reachable"):
            lines.append(
                f"    Optimal Starbucks: {ch['optimal_starbucks_id']} — {ch['optimal_starbucks_name']}"
            )
            lines.append(
                f"    One chain trip: {ch['one_trip_minutes']:.1f} min →  "
                f"{ch['weekly_visits']} × {ch['one_trip_minutes']:.1f} = {ch['weekly_weighted_minutes']:.1f} min/week"
            )
            lines.append(
                f"    Optimal legs: Apt→S* {ch.get('optimal_leg1_mode', '?')}, "
                f"S*→NEU {ch.get('optimal_leg2_mode', '?')}"
            )
            if ch.get("path_apartment_to_optimal_starbucks"):
                lines.append(
                    f"    Path Apt → S*: {' → '.join(ch['path_apartment_to_optimal_starbucks'])}"
                )
                _append_path_leg_lines(lines, ch.get("path_apartment_to_optimal_starbucks_legs") or [], "      ")
            if ch.get("path_optimal_starbucks_to_neu"):
                lines.append(
                    f"    Path S* → NEU: {' → '.join(ch['path_optimal_starbucks_to_neu'])}"
                )
                _append_path_leg_lines(lines, ch.get("path_optimal_starbucks_to_neu_legs") or [], "      ")
        else:
            lines.append("    ** Not reachable ** (infinite distance on some chain leg)")
        lines.append("    All Starbucks candidates (effective minutes per chain trip; tr=transit, sl=straight-line):")
        for row in ch["per_starbucks"]:
            mark = " *" if row["starbucks_id"] == ch.get("optimal_starbucks_id") else ""
            d1 = row["minutes_apt_to_starbucks"]
            d2 = row["minutes_starbucks_to_neu"]
            tot = row["minutes_one_chain_trip"]
            t1_tr = row.get("minutes_apt_to_starbucks_transit", d1)
            t1_sl = row.get("minutes_apt_to_starbucks_walk_straight_line", float("inf"))
            t2_tr = row.get("minutes_starbucks_to_neu_transit", d2)
            t2_sl = row.get("minutes_starbucks_to_neu_walk_straight_line", float("inf"))
            d1s = f"{d1:.1f}" if d1 != float("inf") else "inf"
            d2s = f"{d2:.1f}" if d2 != float("inf") else "inf"
            tots = f"{tot:.1f}" if tot != float("inf") else "inf"
            l1 = row.get("leg1_mode", "?")
            l2 = row.get("leg2_mode", "?")
            lines.append(
                f"      {row['starbucks_id']}  apt→S eff {d1s} (tr {_fmt_minutes(t1_tr)}, sl {_fmt_minutes(t1_sl)}, {l1})"
                f"  +  S→NEU eff {d2s} (tr {_fmt_minutes(t2_tr)}, sl {_fmt_minutes(t2_sl)}, {l2})  =  {tots}{mark}"
            )
        lines.append("")

        for key in ("costco", "trader_joes", "gym_24hf"):
            blk = cats[key]
            lines.append(f"  [{cat_labels[key]}]")
            lines.append(f"    Weekly visits: {blk['weekly_visits']}")
            if blk.get("reachable"):
                lines.append(
                    f"    Best: {blk['best_candidate_id']} — {blk['best_candidate_name']}"
                )
                otr = blk.get("one_way_minutes_transit")
                osl = blk.get("one_way_minutes_walk_straight_line")
                mode = "straight_line_walk" if blk.get("used_straight_line_walk") else "transit"
                if otr is not None and osl is not None:
                    lines.append(
                        f"    One-way effective: {blk['one_way_minutes']:.1f} min "
                        f"(transit {_fmt_minutes(float(otr))}, straight-line {_fmt_minutes(float(osl))}) — using {mode}"
                    )
                else:
                    lines.append(
                        f"    One-way effective: {blk['one_way_minutes']:.1f} min — using {mode}"
                    )
                lines.append(
                    f"    Weekly: {blk['weekly_visits']} × {blk['one_way_minutes']:.1f} = {blk['weekly_weighted_minutes']:.1f} min/week"
                )
                if blk.get("path_apartment_to_best"):
                    lines.append(f"    Path: {' → '.join(blk['path_apartment_to_best'])}")
                    _append_path_leg_lines(lines, blk.get("path_apartment_to_best_legs") or [], "      ")
            else:
                lines.append("    ** Not reachable **")
            lines.append("    All candidates (effective; tr/sl = transit / straight-line):")
            for cm in blk["candidates_minutes"]:
                m = cm["minutes"]
                ms = f"{m:.1f}" if m != float("inf") else "inf"
                tr = cm.get("transit_minutes", float("inf"))
                sl = cm.get("walk_straight_line_minutes", float("inf"))
                trs = f"{tr:.1f}" if tr != float("inf") else "inf"
                sls = f"{sl:.1f}" if sl != float("inf") else "inf"
                um = cm.get("used_straight_line_walk", False)
                star = " *" if cm["id"] == blk.get("best_candidate_id") else ""
                lines.append(
                    f"      {cm['id']}: eff {ms} (tr {trs}, sl {sls}, "
                    f"{'sl' if um else 'tr'}){star}"
                )
            lines.append("")

    lines.append(sep)
    lines.append("End of report")
    lines.append(sep)
    return "\n".join(lines)


def write_ranking_report(path: Union[str, Path], text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
