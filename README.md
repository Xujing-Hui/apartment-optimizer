# NEU Student Apartment Commute Optimizer

**CS 5800 — Algorithms | Final Project | Spring 2026**

Apartment optimization using Dijkstra's shortest path algorithm on the San Jose VTA Light Rail network.

## Problem

> Among candidate apartments in San Jose, which feasible apartment minimizes total weekly commute time to a fixed set of destinations, while satisfying rent and transit-access constraints?

## How It Works

1. **Build Graph** — Apartments, destinations, and VTA Light Rail stations are modeled as nodes in a weighted graph. Walking edges connect apartments/destinations to nearby stations; transit edges connect adjacent stations.
2. **Run Dijkstra** — For each feasible apartment, compute shortest travel time to every destination using Dijkstra's algorithm with a min-heap.
3. **Compute Score** — Total weekly commute = Σ (shortest time × weekly visits) across all destinations.
4. **Rank** — Filter by constraints (rent ≤ $1,700, walk to station ≤ 15 min), sort by score, output ranking.

## Results

| Rank | Apartment | Rent | Weekly Commute | Best Path to NEU |
|------|-----------|------|----------------|------------------|
| #1 | A3 (Tamien) | $1,500 | 126.0 min | A3 → S5 → S4 → S3 → S2 → D1 |
| #2 | A4 (Capitol) | $1,400 | 139.0 min | A4 → S7 → S6 → S5 → S4 → S3 → S2 → D1 |
| #3 | A5 (Branham) | $1,350 | 149.2 min | A5 → S8 → S7 → S6 → S5 → S4 → S3 → S2 → D1 |

A1 (Downtown, $2,200) and A2 (Japantown, $1,800) were filtered out by the rent constraint.

## Data

- **5 candidate apartments** along the VTA Blue Line (Downtown SJ to Branham)
- **3 fixed destinations**: NEU Campus (5x/week), Walmart Neighborhood Market (2x/week), Planet Fitness (3x/week)
- **8 VTA Light Rail stations** (Blue Line, St. James to Branham)

## Project Structure

```
apartment-optimizer/
├── README.md
├── data/
│   ├── apartments.json         # 5 candidate apartments with coordinates & rent
│   ├── destinations.json       # 3 destinations with coordinates & visit frequency
│   └── stations.json           # 8 VTA Blue Line stations
├── src/
│   ├── utils.py                # Haversine distance & walking time calculation
│   ├── graph.py                # Graph construction from JSON data
│   ├── dijkstra.py             # Dijkstra (min-heap) & Bellman-Ford
│   └── optimizer.py            # Main pipeline: filter → score → rank → output
├── tests/
│   ├── test_basic.py           # Dijkstra correctness & distance tests (5 tests)
│   ├── test_edge_cases.py      # Edge cases: budget, disconnected nodes, walk vs transit (5 tests)
│   └── test_scale.py           # Dijkstra vs Bellman-Ford performance comparison (5 sizes)
├── results/
│   └── ranking_output.txt      # Program output with ranked apartments & paths
├── docs/
│   ├── report1.pdf
│   └── final_report.pdf
└── presentation/
    └── final_presentation.pptx
```

## How to Run

```bash
cd src
python optimizer.py
```

```bash
cd tests
python test_basic.py
python test_edge_cases.py
python test_scale.py
```

Requires Python 3.8+. No external libraries needed.

## Algorithm Complexity

| Component | Time | Space |
|-----------|------|-------|
| Dijkstra (single source, min-heap) | O((V+E) log V) | O(V) |
| Full pipeline (A apartments) | O(A × (V+E) log V) | O(V+E) + O(A×D) |
| Bellman-Ford (comparison) | O(V × E) | O(V) |

Performance test result (from `test_scale.py`):

| Stations | Nodes | Dijkstra (ms) | Bellman-Ford (ms) | Speedup |
|----------|-------|---------------|-------------------|---------|
| 10 | 18 | 0.099 | 0.247 | 2.5x |
| 50 | 58 | 0.231 | 1.538 | 6.7x |
| 200 | 208 | 0.725 | 17.486 | 24.1x |


## Team & Contributions

**Jiaxin Liu** — Data collection: apartments, destinations, and VTA station coordinates & rent data (`data/` files)

**Xujing Hui** — Algorithm design & core implementation: `optimizer.py`, `graph.py`, `utils.py`; GitHub repo setup

**Fanchao Yu** — Algorithm implementation & testing: `dijkstra.py` (Dijkstra + Bellman-Ford); all test cases (`tests/`)

**Shared** — Report writing, presentation, GitHub management


## Repository

https://github.com/Xujing-Hui/apartment-optimizer

---

## Extension: South Bay transit model (Dijkstra v2)

### Why we rebuilt this from scratch

After submitting the initial prototype, we identified three fundamental problems that made the original results largely meaningless as a real decision tool:

1. **Imprecise apartment data.** The first version used rough, manually-estimated coordinates — sometimes just a city centroid — and rent numbers that did not match real listings. Because Haversine walking times and station connectivity depend entirely on exact coordinates, even small position errors caused the graph to connect apartments to the wrong stations and produce unreliable scores.

2. **All five apartments were in the same corridor.** Every candidate in v1 sat along a single VTA Blue Line stretch in downtown San Jose. When the apartments are geographically clustered like this, Dijkstra produces nearly identical scores for all of them. There is no meaningful differentiation, and the algorithm reduces to a tie-breaker rather than an actual decision aid. We needed candidates spread across genuinely different transit corridors.

3. **The transit network was too thin to reflect reality.** The original graph contained only 8 light-rail stations on the Blue Line. Real South Bay commuting involves transfers between Caltrain, multiple VTA bus routes, and BART. A stripped-down rail-only graph systematically underestimates travel time to any destination that requires a bus transfer, which distorts every score.

We addressed all three issues by rebuilding the data layer and the graph model completely. The legacy `src/` and `data/` files are preserved unchanged; everything new lives under `Dijkstra/`, `Data/*_v2.json`, `results_v2/`, and `tests_v2/`.

---

### New data layer (`Data/*_v2.json`)

We collected all three v2 files from Zillow, Apartments.com, Google Maps, and official transit schedules (April 2026). Every coordinate was verified against a street address rather than estimated.

#### `apartments_json_v2.json` — 5 apartments across distinct South Bay sub-areas

Each apartment entry contains:

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Unique node ID used throughout the graph |
| `name`, `address` | string | Human-readable labels for reports |
| `lat`, `lng` | float (WGS84) | Exact street-level coordinates for Haversine walk estimates |
| `monthly_rent` | int (USD) | Verified from current listings; displayed in output |
| `area` | string | Sub-area label (Sunnyvale / Santa Clara / Downtown SJ / North SJ / Milpitas) |
| `nearest_station_id` | string | The one transit node this apartment connects to in the graph |
| `walk_min_to_station` | float | Timed walking minutes; becomes the apartment–station edge weight |

We deliberately spread the five apartments across **different transit corridors**: Sunnyvale (Caltrain-adjacent), Santa Clara (VTA 22/522 corridor), Downtown San Jose (bus hub proximity), North San Jose (VTA 72 / Rapid 500), and Milpitas (VTA 20 / BART). This ensures the graph has to do real work — no two apartments are close enough for Dijkstra to produce trivially similar scores.

Each apartment connects to the graph through exactly **one walk edge** to its `nearest_station_id`. We chose not to add multiple access edges per apartment because the JSON already captures the primary transit access point for each building, and adding more would require subjective cutoff choices we could not verify rigorously.

#### `stations_json_v2.json` — 36 transit nodes across 4 types

| Node type | Count | Why we included it |
|---|---|---|
| `caltrain` | 7 | Backbone for Sunnyvale–San Jose express corridors |
| `bus_stop` | 19 | Local VTA stops serving intermediate destinations |
| `bus_hub` | 9 | Transfer points (Diridon, Sunnyvale TC, Santa Clara TC, Milpitas BART…) |
| `bart` | 1 | Milpitas BART — the only intermodal option for The Harlowe apartment |

Each station entry contains:

| Field | Type | Purpose |
|---|---|---|
| `id` | string | Node ID, referenced by `nearest_station_id` in apartments and destinations |
| `name`, `type`, `address` | string | Labels and routing metadata |
| `lat`, `lng` | float | For sanity-checking; not used as edge weights |
| `neighbors` | list | Direct connections, each `{ id, travel_min, mode }` |

The `neighbors.mode` field (`caltrain`, `bus`, `bart`, `walk`) is the key design addition over v1. We store mode as the **third element** of every adjacency triple `(neighbor_id, weight, mode)`. This means Dijkstra can still relax edges using only the second element (weight), but `report.py` can later annotate every path leg with how it is actually traveled — not just a raw minute count. Undirected pairs are deduplicated at build time so each edge appears once in the canonical pair set, then both directions are inserted into the adjacency list with the same weight and mode.

#### `destinations_json_v2.json` — 25 destinations across 5 categories

| Category | Candidates | `weekly_visits` | Scoring rule |
|---|---|---|---|
| `starbucks_neu_chain` | S1–S6 | 3 | Chain trip: `min_S [dist(apt,S) + dist(S,NEU)]` |
| `costco` | C1–C6 | 1 | `min` over 6 candidates |
| `trader_joes` | T1–T6 | 2 | `min` over 6 candidates |
| `gym_24hf` | G1–G6 | 4 | `min` over 6 candidates |
| `school_chain_endpoint` | NEU_SV (fixed) | — | Chain endpoint only; never scored standalone |

Each destination entry mirrors the apartment schema (`id`, `lat`, `lng`, `nearest_station_id`, `walk_min_from_station`) so graph construction is symmetric: both apartments and destinations attach to the graph through a single walk edge to their nearest station, and `build_graph` handles both with the same code path.

The `categories` block at the bottom of the file is the **single source of truth** for candidate ID lists and visit counts. `scoring.py` reads it directly, so changing a visit frequency or swapping in a new candidate requires editing only the JSON, not the Python.

The Starbucks category is modeled as a **chain endpoint** rather than a standalone destination. Every trip to NEU starts with a Starbucks stop: `Apartment → S* → NEU`. We score it as `3 × min_S [dist(apt,S) + dist(S,NEU)]` rather than as two independent `3×` terms. This correctly captures the reality that you do not choose the closest Starbucks in isolation — you choose whichever one makes the combined two-leg trip shortest.

---

### Pipeline architecture (`Dijkstra/`)

```
Data/*_v2.json
      │
      ▼
graph_builder.py   walk_estimate.py
      │                   │
      └────────┬───────────┘
               ▼
        shortest_path.py   (Dijkstra, lookup_edge, path_leg_breakdown)
               │
               ▼
          scoring.py        (NEU Dijkstra + per-apt Dijkstra, chain rule, min per category)
               │
               ▼
          report.py         (scores.json + ranking_report.txt with per-leg modes)
```

- **`graph_builder.build_graph`** — Produces the adjacency dict as triples. Station–station edges carry the JSON `mode`; apartment and destination walk edges use `"walk"`.
- **`shortest_path.dijkstra`** — Standard min-heap implementation; ignores the third tuple element during relaxation (only weight matters). `lookup_edge(graph, u, v)` retrieves `(weight, mode)` for any edge; `path_leg_breakdown(graph, path)` turns a list of node IDs into a list of `{from, to, minutes, mode}` dicts.
- **`walk_estimate`** — Haversine straight-line at 80 m/min, capped at **45 minutes** (`MAX_STRAIGHT_LINE_WALK_MINUTES`). Above the cap the function returns `inf`, preventing a missing transit edge from being masked by an implausible multi-hour walk and producing a fake "reachable" result.
- **`scoring.compute_apartment_scores`** — Runs one Dijkstra from `NEU_SV` (result reused for all apartments via the undirected property: `dist(NEU,S) = dist(S,NEU)`), then one Dijkstra per apartment. For each leg it takes `min(transit_time, straight_line_walk)` and records which mode was used. Chain scoring iterates over S1–S6 and picks the `S*` that minimizes the combined two-leg time. Path legs are stored as `path_*_legs` lists so the report can display each hop with its mode.
- **`report`** — Writes `results_v2/scores.json` (machine-readable, `inf` serialized as `null`) and `results_v2/ranking_report.txt` (long-form narrative). The text report prints each path segment as `A → B: 8.0 min (walk)`, `B → C: 13.0 min (caltrain)`, and so on.

### How we run it

From the **repository root** (so `Data/` resolves correctly):

```bash
python -m Dijkstra
```

Optional flags: `--apartments`, `--stations`, `--destinations`, `--out-dir`.

`__main__.py` is the glue that ties everything together. It imports `pathlib.Path` for cross-platform path handling, then calls the internal package functions in sequence: `load_json_records` to read the three JSON files, `run_full_pipeline` to build the graph and produce ranked results, `graph_edge_stats` to pull node/edge counts for the report header, and finally `build_scores_document` + `write_scores_json` for the machine-readable output and `format_ranking_report` + `write_ranking_report` for the human-readable text file. None of these are external dependencies — they all live in the `Dijkstra/` package we wrote.

### Tests we added

```bash
python -m unittest discover -s tests_v2
```

We cover: Dijkstra correctness on triple-weighted graphs; `lookup_edge` and `path_leg_breakdown`; graph construction from v2-shaped JSON including mode assertions (`x[2] == "bus"` for station edges, `x[2] == "walk"` for apartment/destination edges); the Starbucks–NEU chain rule including the case where the closest Starbucks to the apartment is **not** the chain-optimal choice; Haversine cap behavior (long distances return `inf` by default, finite when cap is disabled); straight-line walk shortcut (same-coordinate pair gives 0 min and overrides expensive transit); and a full integration run on `Data/*_v2.json` verifying all 5 apartments return finite scores with all required JSON keys present.

### Complexity note

The asymptotic cost is **one** Dijkstra from the chain endpoint plus **one** per apartment: **O((V+E) log V × (1 + A))**, where V = 66 nodes (5 apartments + 36 stations + 25 destinations), E = total undirected edges, and A = 5 apartments. This is the same min-heap implementation as in `Dijkstra/shortest_path.py`, unchanged from v1.

---

## Libraries we used

One thing we were actually pretty happy about: this entire project — both the original v1 pipeline and the v2 South Bay model — runs on **pure Python standard library**. We never needed to install anything. Here is what we actually reached for and why.

### `heapq` — [docs.python.org/3/library/heapq.html](https://docs.python.org/3/library/heapq.html)

This is the core of our Dijkstra implementation. Python's `heapq` gives us a min-heap (priority queue) through simple list operations — `heappush` to insert and `heappop` to extract the minimum. Every time we relax an edge and find a shorter path, we push `(new_distance, node)` onto the heap. This keeps the next node to process always at the front of the queue, which is exactly what makes Dijkstra run in O((V+E) log V) rather than O(V²). We use it in both `src/Dijkstra.py` (v1) and `Dijkstra/shortest_path.py` (v2).

### `json` — [docs.python.org/3/library/json.html](https://docs.python.org/3/library/json.html)

All of our data lives in JSON files, so `json` is everywhere. We use `json.load()` in `graph_builder.py` to read the three v2 data files at startup, and `json.dump()` in `report.py` to write `results_v2/scores.json`. One small thing we had to handle: Python's `float('inf')` is not valid JSON, so we wrote a small `_json_safe()` helper that converts any `inf` to `null` before serializing — otherwise the output file would crash any downstream tool that tried to parse it.

### `math` — [docs.python.org/3/library/math.html](https://docs.python.org/3/library/math.html)

We use `math.radians`, `math.sin`, `math.cos`, and `math.atan2` to implement the Haversine formula in `walk_estimate.py`. Given two latitude/longitude pairs, Haversine gives us the great-circle distance in kilometers, which we then divide by our walking speed (80 m/min) to get an estimated straight-line walk time. It is not perfectly accurate for city blocks, but it is a reasonable lower-bound estimate and it does not require any external geocoding service.

### `pathlib` — [docs.python.org/3/library/pathlib.html](https://docs.python.org/3/library/pathlib.html)

We use `pathlib.Path` anywhere we need to work with file paths — loading data files, writing output directories, resolving the repo root from `__file__`. It is a lot cleaner than string concatenation with `os.path.join`, and it handles Windows vs. Unix path separators automatically, which mattered since we were running and testing on different machines.

### `argparse` — [docs.python.org/3/library/argparse.html](https://docs.python.org/3/library/argparse.html)

`__main__.py` uses `argparse` to expose optional CLI flags (`--apartments`, `--stations`, `--destinations`, `--out-dir`) so we can override the default `Data/` paths without editing the source. The defaults point to the v2 JSON files so `python -m Dijkstra` just works from the repo root, but having flags made testing with modified data files much easier.

### `typing` — [docs.python.org/3/library/typing.html](https://docs.python.org/3/library/typing.html)

We used `Dict`, `List`, `Tuple`, `Optional`, `Union`, and `Any` from `typing` throughout the v2 codebase to annotate function signatures. This was partly for clarity — it is a lot easier to understand `Dict[str, List[Tuple[str, float, str]]]` than just `dict` when you are looking at the graph adjacency type — and partly because it helped us catch the places where we had accidentally kept the old two-element tuple format when the rest of the code had already moved to triples.

### `collections.defaultdict` — [docs.python.org/3/library/collections.html](https://docs.python.org/3/library/collections.html)

Only used in the legacy `src/graph.py` (v1). We replaced it with a plain `dict` and an explicit `ensure_node` helper in v2 because `defaultdict` can silently create keys on access, which made it harder to catch missing station IDs early. The explicit check also lets us raise a clear `ValueError` when a `nearest_station_id` does not exist in the stations list.
