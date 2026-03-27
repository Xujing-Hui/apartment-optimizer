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

### Shared
- Report writing and presentation preparation (all members)
- GitHub repository management (Xujing + Fanchao)

## Repository

https://github.com/Xujing-Hui/apartment-optimizer
