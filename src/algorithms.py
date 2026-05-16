"""
multiware_algorithms.py
========================
Multi-Warehouse Distribution System
All 4 core algorithms — clean, readable, fully commented.

Run:
    python multiware_algorithms.py
"""

import heapq
import math


# ─────────────────────────────────────────────────────────────
# DATA STRUCTURES
# ─────────────────────────────────────────────────────────────

class MinHeap:
    """
    Binary min-heap used by Dijkstra.
    Each item is [priority, value].
    """
    def __init__(self):
        self._data = []

    def push(self, item):
        heapq.heappush(self._data, item)

    def pop(self):
        return heapq.heappop(self._data)

    def is_empty(self):
        return len(self._data) == 0


class UnionFind:
    """
    Disjoint Set Union with path compression + union by rank.
    Used by Kruskal to detect cycles in O(α(n)) per operation.
    """
    def __init__(self, nodes):
        self.parent = {n: n for n in nodes}
        self.rank   = {n: 0  for n in nodes}

    def find(self, x):
        # Path compression
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, x, y):
        px, py = self.find(x), self.find(y)
        if px == py:
            return False   # Already connected — adding edge would create a cycle
        # Union by rank
        if self.rank[px] < self.rank[py]:
            self.parent[px] = py
        elif self.rank[px] > self.rank[py]:
            self.parent[py] = px
        else:
            self.parent[py] = px
            self.rank[px] += 1
        return True

    def connected(self, x, y):
        return self.find(x) == self.find(y)


# ─────────────────────────────────────────────────────────────
# ALGORITHM 1 — DIJKSTRA'S SHORTEST PATH
# ─────────────────────────────────────────────────────────────

def dijkstra(graph, source):
    """
    Find shortest path from source to all other nodes.

    Args:
        graph  : dict { node_id: [(neighbor_id, cost), ...] }
        source : starting node id

    Returns:
        dist : dict { node_id: min_cost }
        prev : dict { node_id: previous_node } — for path reconstruction

    Complexity: O((V + E) log V)
    """
    dist = {node: math.inf for node in graph}
    prev = {}
    dist[source] = 0

    heap = MinHeap()
    heap.push([0, source])

    visited = set()

    while not heap.is_empty():
        d, u = heap.pop()

        if u in visited:
            continue           # Stale entry — a shorter path was already found
        visited.add(u)

        for v, weight in graph.get(u, []):
            new_dist = dist[u] + weight
            if new_dist < dist[v]:           # Relaxation step
                dist[v] = new_dist
                prev[v] = u
                heap.push([new_dist, v])

    return dist, prev


def build_cost_matrix(warehouses, customers, graph):
    """
    Run Dijkstra once per warehouse to build the full cost matrix.

    Returns:
        cost_matrix[warehouse_id][customer_id] = min shipping cost
    """
    cost_matrix = {}
    for wh in warehouses:
        dist, _ = dijkstra(graph, wh)
        cost_matrix[wh] = {}
        for cu in customers:
            cost_matrix[wh][cu] = dist[cu] if math.isfinite(dist[cu]) else 9999
        print(f"  Dijkstra from {wh}: {cost_matrix[wh]}")
    return cost_matrix


# ─────────────────────────────────────────────────────────────
# ALGORITHM 2 — KRUSKAL'S MST
# ─────────────────────────────────────────────────────────────

def kruskal(nodes, edges):
    """
    Build the Minimum Spanning Tree connecting all warehouse nodes.

    Args:
        nodes : list of warehouse node ids
        edges : list of (cost, node_a, node_b)

    Returns:
        mst        : list of edges in the MST
        total_cost : total MST cost
        pruned     : edges that were rejected (would create cycles)

    Complexity: O(E log E)
    """
    sorted_edges = sorted(edges, key=lambda e: e[0])   # Sort by cost ascending
    uf = UnionFind(nodes)
    mst, pruned = [], []
    total_cost = 0

    for cost, u, v in sorted_edges:
        if uf.connected(u, v):
            # Adding this edge would create a cycle — skip it
            pruned.append((cost, u, v))
            print(f"  PRUNE  {u}–{v}  ${cost}  (would form cycle)")
        else:
            # Safe to add — merges two components
            uf.union(u, v)
            mst.append((cost, u, v))
            total_cost += cost
            print(f"  ADD    {u}–{v}  ${cost}  (MST total: ${total_cost})")

            if len(mst) == len(nodes) - 1:
                break   # MST complete — V-1 edges

    return mst, total_cost, pruned


# ─────────────────────────────────────────────────────────────
# ALGORITHM 3 — DP ASSIGNMENT (EXACT, OPTIMAL)
# ─────────────────────────────────────────────────────────────

def dp_assign(orders, warehouses, cost_matrix):
    """
    Optimally assign each order to a warehouse using Dynamic Programming.

    State:
        dp[i][stock_vector] = minimum total cost to fulfill orders 0..i-1
        with the given remaining stock at each warehouse.

    Transition:
        For order i, try assigning it to each warehouse w:
        if stock[w] >= order.units:
            new_cost = dp[i][s] + cost_matrix[w][order.customer]
            update dp[i+1][s with s[w] -= units]

    Uses a sparse dictionary to avoid allocating a full multi-dimensional array.

    Complexity: O(n × |states| × W)  where |states| grows with stock variety
    """
    n = len(orders)
    W = len(warehouses)
    init_stocks = tuple(w['stock'] for w in warehouses)

    # dp[i] maps stock_key → {cost, prev}
    dp = [dict() for _ in range(n + 1)]
    dp[0][init_stocks] = {'cost': 0, 'prev': None}

    for i, order in enumerate(orders):
        for stock_key, state in dp[i].items():
            stocks = list(stock_key)
            cur_cost = state['cost']

            for w in range(W):
                if stocks[w] < order['units']:
                    continue   # Not enough stock at this warehouse

                ship_cost = cost_matrix[warehouses[w]['id']][order['customer']]
                new_cost  = cur_cost + ship_cost

                new_stocks = stocks[:]
                new_stocks[w] -= order['units']
                new_key = tuple(new_stocks)

                existing = dp[i + 1].get(new_key)
                if existing is None or new_cost < existing['cost']:
                    dp[i + 1][new_key] = {
                        'cost': new_cost,
                        'prev': {
                            'stock_key': stock_key,
                            'w': w,
                            'ship_cost': ship_cost,
                            'order_id': order['id']
                        }
                    }

    # Find the optimal final state (minimum cost)
    best_key  = min(dp[n], key=lambda k: dp[n][k]['cost'])
    best_cost = dp[n][best_key]['cost']

    # Traceback to recover the assignment decisions
    assignment = [None] * n
    trace = []
    sk = best_key

    for i in range(n, 0, -1):
        p = dp[i][sk]['prev']
        assignment[i - 1] = p['w']
        trace.insert(0, {
            'order': p['order_id'],
            'warehouse': warehouses[p['w']]['id'],
            'cost': p['ship_cost']
        })
        sk = p['stock_key']

    return assignment, best_cost, trace


def greedy_assign(orders, warehouses, cost_matrix):
    """
    Greedy assignment — at each step, pick the cheapest warehouse with stock.
    Fast but NOT globally optimal.

    Complexity: O(n × W)
    """
    stocks = [w['stock'] for w in warehouses]
    assignment = []
    total_cost = 0

    for order in orders:
        best_w, best_cost = -1, math.inf

        for w in range(len(warehouses)):
            if stocks[w] >= order['units']:
                c = cost_matrix[warehouses[w]['id']][order['customer']]
                if c < best_cost:
                    best_cost = c
                    best_w = w

        if best_w < 0:
            raise Exception(f"Cannot fulfill {order['id']} — no stock")

        stocks[best_w] -= order['units']
        assignment.append(best_w)
        total_cost += best_cost

    return assignment, total_cost


# ─────────────────────────────────────────────────────────────
# ALGORITHM 4 — BIN PACKING
# ─────────────────────────────────────────────────────────────

def next_fit_pack(orders, assignment, warehouses, max_weight=500, max_vol=3.0):
    """
    Next-Fit greedy bin packing.
    Sort orders by (warehouse, region), then fill current bin until full,
    then open a new one.

    Complexity: O(n log n) for sorting + O(n) for packing
    Guarantee:  uses at most 2× the optimal number of bins
    """
    REGION_ORDER = {'North': 0, 'West': 1, 'Central': 2, 'East': 3, 'South': 4}

    items = sorted(
        [{'order': o, 'wi': assignment[i]} for i, o in enumerate(orders)],
        key=lambda x: (x['wi'], REGION_ORDER.get(x['order']['region'], 9))
    )

    bins, cur = [], None

    for item in items:
        o, wi = item['order'], item['wi']
        fits = (
            cur is not None
            and cur['wi'] == wi
            and cur['weight'] + o['weight'] <= max_weight
            and cur['vol']    + o['vol']    <= max_vol
        )
        if not fits:
            if cur: bins.append(cur)
            cur = {'id': f"SHP-{len(bins)+1:03d}", 'wi': wi,
                   'wid': warehouses[wi]['id'], 'orders': [], 'weight': 0, 'vol': 0}

        cur['orders'].append(o)
        cur['weight'] += o['weight']
        cur['vol']    += o['vol']

    if cur: bins.append(cur)
    return bins


def ffd_pack(orders, assignment, warehouses, max_weight=500, max_vol=3.0):
    """
    First-Fit Decreasing (FFD) bin packing.
    Sort by weight descending, then fit each order into the first bin it fits.
    Generally produces fewer bins than Next-Fit.

    Complexity: O(n log n) + O(n²) worst case for fitting
    """
    by_wh = {}
    for i, o in enumerate(orders):
        wi = assignment[i]
        by_wh.setdefault(wi, []).append(o)

    all_bins = []
    for wi, items in by_wh.items():
        items.sort(key=lambda o: o['weight'], reverse=True)   # Heaviest first
        wh_bins = []
        for o in items:
            placed = False
            for b in wh_bins:
                if b['weight'] + o['weight'] <= max_weight and b['vol'] + o['vol'] <= max_vol:
                    b['orders'].append(o)
                    b['weight'] += o['weight']
                    b['vol']    += o['vol']
                    placed = True
                    break
            if not placed:
                wh_bins.append({'id': f"FFD-{len(all_bins)+len(wh_bins)+1:03d}",
                                'wi': wi, 'wid': warehouses[wi]['id'],
                                'orders': [o], 'weight': o['weight'], 'vol': o['vol']})
        all_bins.extend(wh_bins)

    return all_bins


def theoretical_min(orders, assignment, warehouses, max_weight=500):
    """Lower bound on bin count: ⌈total_weight_per_warehouse / max_weight⌉"""
    by_wh = {}
    for i, o in enumerate(orders):
        wi = assignment[i]
        by_wh[wi] = by_wh.get(wi, 0) + o['weight']
    return sum(math.ceil(w / max_weight) for w in by_wh.values())


# ─────────────────────────────────────────────────────────────
# DEMO — runs all 4 algorithms and prints results
# ─────────────────────────────────────────────────────────────

if __name__ == '__main__':

    # ── Graph definition ──────────────────────────────────────
    # Nodes: W1, W2, W3 = warehouses | C1-C8 = customers
    # Edges: directed, asymmetric costs

    graph = {
        'W1': [('W2',180),('W3',220),('C1',62),('C2',45),('C3',78),('C4',95),('C5',110),('C6',130),('C7',145),('C8',98)],
        'W2': [('W1',195),('W3',160),('C1',88),('C2',92),('C3',105),('C4',55),('C5',48),('C6',75),('C7',120),('C8',140)],
        'W3': [('W2',170),('W1',235),('C1',130),('C2',118),('C3',95),('C4',88),('C5',72),('C6',72),('C7',88),('C8',66)],
        'C1':[],'C2':[],'C3':[],'C4':[],'C5':[],'C6':[],'C7':[],'C8':[],
    }

    warehouses = [
        {'id':'W1', 'name':'Cairo Hub',       'stock':120},
        {'id':'W2', 'name':'Alexandria Port',  'stock':90},
        {'id':'W3', 'name':'Giza Logistics',   'stock':110},
    ]

    customers = ['C1','C2','C3','C4','C5','C6','C7','C8']

    wh_edges = [(180,'W1','W2'),(195,'W2','W1'),(160,'W2','W3'),(170,'W3','W2'),(220,'W1','W3'),(235,'W3','W1')]

    orders = [
        {'id':'ORD-001','customer':'C1','region':'North',  'weight':12,'vol':.08,'units':1},
        {'id':'ORD-002','customer':'C2','region':'North',  'weight':8, 'vol':.05,'units':1},
        {'id':'ORD-003','customer':'C3','region':'West',   'weight':22,'vol':.15,'units':2},
        {'id':'ORD-004','customer':'C4','region':'Central','weight':15,'vol':.10,'units':1},
        {'id':'ORD-005','customer':'C5','region':'East',   'weight':18,'vol':.12,'units':2},
        {'id':'ORD-006','customer':'C6','region':'East',   'weight':10,'vol':.07,'units':1},
        {'id':'ORD-007','customer':'C7','region':'South',  'weight':25,'vol':.18,'units':2},
        {'id':'ORD-008','customer':'C8','region':'South',  'weight':14,'vol':.09,'units':1},
        {'id':'ORD-009','customer':'C1','region':'North',  'weight':9, 'vol':.06,'units':1},
        {'id':'ORD-010','customer':'C5','region':'East',   'weight':11,'vol':.07,'units':1},
        {'id':'ORD-011','customer':'C6','region':'East',   'weight':7, 'vol':.05,'units':1},
        {'id':'ORD-012','customer':'C8','region':'South',  'weight':19,'vol':.13,'units':2},
    ]

    print("=" * 55)
    print("  MULTIWARE — Algorithm Demo")
    print("=" * 55)

    # 1. Dijkstra
    print("\n[1] DIJKSTRA — Building cost matrix")
    cost_matrix = build_cost_matrix(['W1','W2','W3'], customers, graph)

    # 2. Kruskal
    print("\n[2] KRUSKAL — Warehouse backbone MST")
    mst, mst_cost, pruned = kruskal(['W1','W2','W3'], wh_edges)
    print(f"  MST total cost: ${mst_cost}")
    print(f"  Pruned edges:   {len(pruned)}")

    # 3. DP Assignment
    print("\n[3] DP ASSIGNMENT — Optimal order allocation")
    dp_assign_result, dp_cost, trace = dp_assign(orders, warehouses, cost_matrix)
    print(f"  DP total cost: ${dp_cost}")
    print(f"\n  {'Order':<10} {'Warehouse':<12} {'Cost'}")
    print(f"  {'-'*35}")
    for t in trace:
        print(f"  {t['order']:<10} {t['warehouse']:<12} ${t['cost']}")

    # 4. Greedy Assignment
    print("\n[4] GREEDY ASSIGNMENT — Heuristic comparison")
    gr_assign_result, gr_cost = greedy_assign(orders, warehouses, cost_matrix)
    print(f"  Greedy total cost: ${gr_cost}")

    # 5. Bin Packing
    print("\n[5] BIN PACKING — Shipment consolidation")
    nf_bins  = next_fit_pack(orders, dp_assign_result, warehouses)
    ffd_bins = ffd_pack(orders, dp_assign_result, warehouses)
    theory   = theoretical_min(orders, dp_assign_result, warehouses)
    print(f"  Next-Fit bins : {len(nf_bins)}")
    print(f"  FFD bins      : {len(ffd_bins)}")
    print(f"  Theory min    : {theory}")

    # Summary
    print("\n" + "=" * 55)
    print("  COMPARISON SUMMARY")
    print("=" * 55)
    print(f"  DP cost        : ${dp_cost}  (globally optimal)")
    print(f"  Greedy cost    : ${gr_cost}  (heuristic)")
    print(f"  DP saves       : ${gr_cost - dp_cost}  ({(gr_cost-dp_cost)/gr_cost*100:.1f}%)")
    print(f"  MST backbone   : ${mst_cost}")
    print(f"  Next-Fit bins  : {len(nf_bins)}  (FFD: {len(ffd_bins)}, theory: {theory})")
    print("=" * 55)
