# 🏠 Apartment Commute Optimizer

A graph-based tool that helps students find the optimal apartment by minimizing **total weekly commute time** across all daily destinations — not just distance to one location.

---

## 🧠 Problem Statement

Housing decisions are among the most consequential choices for students entering the workforce in the San Francisco Bay Area. When selecting an apartment, renters typically weigh rent, commute time, and proximity to transit — but these factors are often evaluated informally and independently.

As students transitioning into full-time roles in the Bay Area, we face exactly this tradeoff: an apartment may appear affordable, but its true cost emerges through daily commuting across multiple destinations — campus, employer, grocery stores, and beyond. Apartment choice directly shapes daily routine, time management, and quality of life.

This tool replaces vague intuition with a rigorous algorithmic framework: **which feasible apartment minimizes total weekly commute time to a fixed set of destinations, subject to rent and transit accessibility constraints?**

---

## 🗺️ How It Works

### Graph Structure
| Node Type | Examples |
|---|---|
| Candidate apartments | Apt A, Apt B, Apt C... |
| Daily destinations | Northeastern, internship company, grocery store... |
| Transit nodes | Caltrain stations, bus stops |

**Edges** represent routes between nodes, weighted by travel time (walking + riding + waiting).

### Definitions

| Term | Definition |
|------|------------|
| Apartment *a* | Defined by monthly rent and geographic location |
| Destination *d_j* | Defined by location and weekly visit frequency |
| Feasibility | Rent ≤ *B* **and** walk time to nearest transit stop ≤ *X* minutes |

### Objective Function

For each feasible apartment *a*:

```
Total Weekly Commute Time(a) = Σ travel_time(a, d_j) × visit_count(d_j)
```

where `travel_time(a, d_j)` is the shortest-path travel time via the public transit network.

**Goal:** Rank all feasible apartments by this score and identify the one with the minimum total weekly commute time.

---

## 📁 Project Structure

```
apartment-optimizer/
├── README.md
├── docs/
│   ├── report1.pdf
│   ├── report2.pdf
│   ├── final_report.pdf
│   └── pseudocode.pdf
├── presentation/
│   └── final_presentation.pptx
├── data/
│   ├── apartments.json       # Candidate apartment data
│   ├── destinations.json     # Daily destination data
│   └── stations.json         # Transit station data
├── src/
│   ├── graph.py              # Graph construction logic
│   ├── dijkstra.py           # Dijkstra's algorithm implementation
│   ├── optimizer.py          # Main pipeline: filter → score → rank
│   ├── utils.py              # Helper functions (distance calculation, etc.)
│   └── visualize.py          # Result visualization (optional)
├── tests/
│   ├── test_basic.py         # Basic correctness tests
│   ├── test_edge_cases.py    # Edge case tests
│   └── test_scale.py         # Scale tests (50 vs 100 apartments)
└── results/
    ├── ranking_output.txt    # Program output: apartment rankings
    └── runtime_comparison.png  # Dijkstra vs Bellman-Ford performance chart
```

---

## 🚀 Getting Started

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run the Optimizer
```bash
python src/optimizer.py
```

### Run Tests
```bash
python -m pytest tests/
```

---

## ⚙️ Algorithm

We use **Dijkstra's algorithm with a min-heap** to find shortest paths from each candidate apartment to every destination through the transit network.

**Why Dijkstra over Bellman-Ford?**
- All edge weights (travel times) are non-negative
- Dijkstra runs in **O((V + E) log V)** with a min-heap, which is faster than Bellman-Ford's O(VE) for this use case
- Transit graphs are typically sparse, making Dijkstra well-suited

**Pipeline:**
```
Build Graph → Run Dijkstra per apartment → Compute weighted commute score → Filter constraints → Rank & output
```

---

## 📊 Sample Output

| Rank | Apartment | Weekly Commute (hrs) | Monthly Rent |
|------|-----------|----------------------|--------------|
| 1 | Apt C | 4.2 | $2,800 |
| 2 | Apt A | 5.1 | $2,600 |
| 3 | Apt B | 6.8 | $2,500 |

---

## ⚠️ Limitations

- Does not account for real-time traffic or transit delays
- Transit graph is static (no schedule variation by time of day)
- Does not factor in subjective living experience (noise, neighborhood, amenities)
- Walking speed assumed constant

---

## 👥 Team

| Member | Responsibilities |
|--------|-----------------|
| Jiaxin Liu | Data collection, graph construction (`graph.py`) |
| Fanchao Yu & Xujing Hui | Dijkstra implementation, testing (`dijkstra.py`, `tests/`) |
| All of the Members | Report writing, GitHub management, presentation |
