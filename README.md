# CS5800 — Apartment Commute Optimizer
**Group 7 — Xujing Hui, Fanchao Yu, Jiaxin Liu — Spring 2026**

GitHub: https://github.com/Xujing-Hui/apartment-optimizer

---

## What This Project Does

Given 5 candidate apartments in the San Jose metropolitan area, this program finds the one that minimizes a student's **total weekly transit commute time** across all habitual destinations: NEU campus (via a Starbucks chain stop), Costco, Trader Joe's, and 24 Hour Fitness.

The transit network is modeled as a **weighted undirected graph** (66 nodes, ~94 edges) covering Caltrain, VTA bus routes, and Milpitas BART. The primary solver is **Dijkstra's algorithm** with a min-heap. Bellman-Ford is included for cross-validation.

---

## Requirements

- **Python 3.10 or later** (no other version tested)
- **No external libraries** — standard library only (`heapq`, `math`, `json`, `os`, `sys`)
- Nothing to install or pip-install

---

## Quick Start — Run in 3 Steps

> All commands assume you are in the **root folder** of the unzipped project
> (the folder that contains `src/`, `data/`, `pseudocode/`, `results/`, `README.md`).

### Step 1 — Unzip the submitted file

```
ReportHuiLiuYu.zip
```

You should see this structure after unzipping:

```
ReportHuiLiuYu/
├── data/
│   ├── apartments_json.json
│   ├── destinations_json.json
│   └── stations_json_v2.json
├── src/
│   ├── utils.py
│   ├── graph.py
│   ├── dijkstra.py
│   ├── optimizer.py
│   ├── test_graph.py
│   ├── test_dijkstra.py
│   └── test_optimizer.py
├── pseudocode/
│   ├── pseudocode_1_build_graph.txt
│   ├── pseudocode_2_dijkstra.txt
│   └── pseudocode_3_optimizer.txt
├── results/
│   ├── ranking_output.txt
│   └── test_output.txt
└── README.md
```

### Step 2 — Run the optimizer (main result)

```bash
cd src
python optimizer.py
```

**Expected output:**

```
==============================================================================
  APARTMENT COMMUTE OPTIMIZER — FINAL RANKING
==============================================================================
  Objective: 3×chain + 1×Costco + 2×TJ + 4×Gym  (min/week)
  Walk fallback cap: 30 min

  #1  Villas on the Boulevard  (Santa Clara)
       Rent: $3,465   Walk to station: 4 min
       Chain  (×3=135.6): apt→S2=4.6min + S2→NEU=40.6min = 45.2 min
       Costco (×1=29.0): C1 — Costco Sunnyvale
       TJ     (×2=39.2): T1 — Trader Joe's Sunnyvale (El Camino Real)
       Gym    (×4=18.4): G2 — 24 Hour Fitness Santa Clara (ECR Super-Sport)
       >>> TOTAL SCORE: 222.2 min/week

  #2  Murphy Station  (Sunnyvale)
       ...
       >>> TOTAL SCORE: 238.1 min/week

  #3  The Verdant Apartments  (North San Jose)
       ...
       >>> TOTAL SCORE: 272.5 min/week

  #4  Cannery Park by Windsor  (Downtown San Jose)
       ...
       >>> TOTAL SCORE: 294.0 min/week

  #5  The Harlowe  (Milpitas)
       ...
       >>> TOTAL SCORE: 338.4 min/week

==============================================================================
  Winner: Villas on the Boulevard  (222.2 min/week)
==============================================================================
```

The full output (with all paths) is also saved in `results/ranking_output.txt`.

### Step 3 — Run all unit tests (optional but recommended)

```bash
cd src
python test_graph.py
python test_dijkstra.py
python test_optimizer.py
```

**Expected output for each file:**

```
# test_graph.py
Running 6 graph tests...

PASS  test_node_count  (66 nodes)
PASS  test_edge_bidirectionality
PASS  test_walk_fallback_edges_present  (5 pairs)
PASS  test_walk_fallback_cap_respected  (cap=30.0 min)
PASS  test_apartments_connected_to_stations
PASS  test_destinations_connected_to_stations

6/6 tests passed.
```

```
# test_dijkstra.py
Running 8 Dijkstra tests...

PASS  test_source_distance_is_zero
PASS  test_known_distances_simple_graph
PASS  test_unreachable_node_is_infinity
PASS  test_dijkstra_bellman_ford_agree  (5 apartments cross-validated)
PASS  test_path_reconstruction_correct  (path=['A', 'B', 'C', 'D'], cost=6)
PASS  test_path_source_to_self
PASS  test_unreachable_path_is_none
PASS  test_real_graph_neu_distances

8/8 tests passed.
```

```
# test_optimizer.py
Running 8 optimizer tests...

PASS  test_all_apartments_pass_constraints  (5/5 pass)
PASS  test_result_count
PASS  test_winner_is_villas  (score=222.2 min/week)
PASS  test_last_place_is_harlowe  (score=338.4 min/week)
PASS  test_scores_strictly_ascending
PASS  test_expected_scores  (tolerance=0.5 min)
PASS  test_chain_trip_starbucks_winners
PASS  test_villas_gym_uses_walk_fallback  (gym=4.6 min)

8/8 tests passed.
```

**Total: 22/22 tests pass.**

---

## Troubleshooting

**"ModuleNotFoundError" or "No module named X"**
→ Make sure you are running from inside the `src/` directory:
```bash
cd src          # ← required
python optimizer.py
```

**"FileNotFoundError: apartments_json.json"**
→ The data files must be in `../data/` relative to `src/`. Check that `data/` is at the same level as `src/` after unzipping.

**"python: command not found"**
→ Try `python3` instead of `python`:
```bash
python3 optimizer.py
```

---

## How the Algorithm Works

### 1. Build Graph

Three JSON files are loaded and merged into a single adjacency-list graph:

```
apartments_json.json   →  5 apartment nodes
                           each connected by a walk edge to its nearest station

stations_json_v2.json  →  36 transit nodes (Caltrain, VTA bus, BART)
                           connected by schedule-time edges

destinations_json.json →  25 destination nodes
                           each connected by a walk edge to its nearest station
```

An additional **walk-fallback edge** is added between any (apartment, destination) pair where the straight-line walking time ≤ 30 min. This lets Dijkstra choose walking over transit when it is genuinely faster (e.g., Villas on the Boulevard → Gym G2: 4.6 min walk vs. 13 min by bus).

### 2. Run Dijkstra

One Dijkstra run per apartment (5 total) plus one pre-computed run from NEU. Each run returns shortest travel times to all 66 nodes simultaneously.

```
Time complexity:  O(A × (V+E) log V)   A=5 apartments, V=66 nodes, E≈94 edges
Space complexity: O(V + E)
```

Dijkstra is preferred over Bellman-Ford because all edge weights are non-negative (travel times cannot be negative). Bellman-Ford is implemented in `dijkstra.py` for cross-validation only.

### 3. Score Each Apartment

```
Score(apt) = 3 × chain_cost
           + 1 × min{ d(apt, Costco_k) }
           + 2 × min{ d(apt, TJ_k) }
           + 4 × min{ d(apt, Gym_k) }

chain_cost = min over k { d(apt, Starbucks_k) + d(Starbucks_k, NEU) }
```

The **chain trip** (Starbucks → NEU) models the real behavior: every school visit starts with a Starbucks stop, so both legs are one journey. The algorithm tries all 6 Starbucks candidates and picks the one that minimizes the combined two-leg time — not necessarily the nearest one.

Visit weights: Chain=3, Costco=1, Trader Joe's=2, Gym=4 (matches weekly_visits in data).

### 4. Rank and Output

Apartments are sorted by score ascending. Lower score = less total weekly transit time.

---

## Final Results

| Rank | Apartment | Area | Rent | Total Score |
|------|-----------|------|------|-------------|
| #1 | Villas on the Boulevard | Santa Clara | $3,465 | **222.2 min/week** |
| #2 | Murphy Station | Sunnyvale | $3,817 | 238.1 min/week |
| #3 | The Verdant Apartments | North San Jose | $3,292 | 272.5 min/week |
| #4 | Cannery Park by Windsor | Downtown SJ | $3,359 | 294.0 min/week |
| #5 | The Harlowe | Milpitas | $3,300 | 338.4 min/week |

Walk-fallback edges used (≤30 min): Villas↔S2 (4.6 min), Villas↔G2 (4.6 min),
Murphy↔S1 (6.1 min), Murphy↔T1 (6.7 min), Verdant↔S4 (1.7 min).

---

## Source Files

| File | Purpose |
|------|---------|
| `src/utils.py` | Haversine great-circle distance; walking time estimate |
| `src/graph.py` | Loads 3 JSON files; builds weighted adjacency list; adds walk-fallback edges |
| `src/dijkstra.py` | Dijkstra with min-heap; Bellman-Ford (verification); path reconstruction |
| `src/optimizer.py` | Main pipeline: constraint filter → chain trip scoring → rank → print |
| `src/test_graph.py` | 6 unit tests for graph construction |
| `src/test_dijkstra.py` | 8 unit tests for Dijkstra correctness |
| `src/test_optimizer.py` | 8 end-to-end optimizer tests |

---

## Algorithm Complexity

| Component | Time | Space |
|-----------|------|-------|
| Build graph | O(V + E + A×D) | O(V + E) |
| NEU precompute (1 run) | O((V+E) log V) | O(V) |
| Dijkstra per apartment | O((V+E) log V) | O(V) |
| Full pipeline (5 apartments) | O(A × (V+E) log V) | O(V+E) |
| Bellman-Ford (verification) | O(V × E) | O(V) |

For V=66, E≈94, A=5: all 6 Dijkstra runs complete in **under 10 milliseconds** total.

---

## Libraries Used

| Library | Module | Why |
|---------|--------|-----|
| `heapq.heappush` / `heapq.heappop` | Python stdlib | Binary min-heap for Dijkstra's priority queue; enables O((V+E) log V) vs O(V²) with a plain array |
| `math.radians`, `math.sin`, `math.cos`, `math.asin`, `math.sqrt` | Python stdlib | Haversine formula — great-circle distance between two lat/lng coordinates |
| `json.load` | Python stdlib | Parse the three JSON input data files at startup |

No pip-installable packages are required.

---

## Data Sources

| File | Source | Date |
|------|--------|------|
| `apartments_json.json` | Zillow, Apartments.com | March 2026 |
| `destinations_json.json` | Google Maps, Yelp, official store locators | March 2026 |
| `stations_json_v2.json` | Caltrain schedule Jan 2026, VTA route map 2025, Google Maps, Moovit | March 2026 |

---

## Visualization (by Jiaxin Liu)

Interactive Kepler.gl map — 10 point layers + 5 per-apartment path layers:

```
https://kepler.gl/demo/map?mapUrl=https://dl.dropboxusercontent.com/scl/fi/
6pxc1x2l7tevax9aa426o/keplergl_18ojc6l.json?rlkey=yqgusvky902iklxy9ib2pp44q&dl=0
```

---

## Team

| Member | Contributions |
|--------|--------------|
| **Xujing Hui** (#002339163) | Dijkstra + Bellman-Ford implementation, algorithm design, complexity analysis, testing, report writing |
| **Jiaxin Liu** (#003169274) | Data collection (all 3 JSON files), graph builder, walk-fallback edges, chain-trip model, Kepler.gl visualization, report writing |
| **Fanchao Yu** (#001601606) | Main optimizer pipeline, scoring, report writing, presentation slides, pseudocode, algorithm design |
