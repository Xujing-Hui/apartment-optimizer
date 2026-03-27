"""
Dijkstra's shortest path algorithm using a min-heap (priority queue).

Time complexity:  O((V + E) log V)
Space complexity: O(V + E)

"""
import heapq

def dijkstra(graph, source):
    """Shortest paths from source to all nodes. O((V+E) log V) with min-heap

    Args:
        graph: dict of { node_id: [(neighbor_id, weight), ...] }
        source: starting node ID
    """
    dist = {node: float("inf") for node in graph}
    prev = {node: None for node in graph}
    dist[source] = 0
    heap = [(0, source)]
    visited = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited: continue
        visited.add(u)
        for v, w in graph.get(u, []):
            if v not in visited and d + w < dist.get(v, float("inf")):
                dist[v] = d + w
                prev[v] = u
                heapq.heappush(heap, (dist[v], v))

    return dist, prev

def reconstruct_path(prev, source, target):
    """Trace back the shortest path from source to target.
    
        Args:
        prev: dict from dijkstra() containing previous nodes
        source: starting node ID
        target: ending node ID
    """
    path, cur = [], target
    while cur is not None:
        path.append(cur)
        if cur == source: break
        cur = prev.get(cur)
    else:
        return []
    path.reverse()
    return path

def bellman_ford(graph, source):
    """Bellman-Ford shortest paths. O(V*E). For performance comparison.
        Args:
        graph: dict of { node_id: [(neighbor_id, weight), ...] }
        source: starting node ID
        
        Time complexity:  O(V * E)
        Space complexity: O(V)
        
    """
    dist = {node: float("inf") for node in graph}
    dist[source] = 0
    edges = [(u, v, w) for u in graph for v, w in graph[u]]
    for _ in range(len(graph) - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return dist
