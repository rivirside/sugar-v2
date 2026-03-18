import type { AdjacencyList, Edge } from "./graph";

export interface PathResult {
  nodes: string[];
  reactionIds: string[];
  totalCost: number;
}

// ---------------------------------------------------------------------------
// Dijkstra with step-count tracking
// Uses composite key `${node}:${step}` to correctly enforce maxSteps and
// prevent the algorithm from re-visiting the same (node, depth) pair.
// ---------------------------------------------------------------------------

export function dijkstra(
  adj: AdjacencyList,
  start: string,
  end: string,
  maxSteps: number = 20,
  blockedNodes: Set<string> = new Set(),
  blockedEdges: Set<string> = new Set()
): PathResult | null {
  // Priority queue entries: [cost, node, step, path, reactionIds]
  type PQEntry = [number, string, number, string[], string[]];

  const pq: PQEntry[] = [[0, start, 0, [start], []]];
  const visited = new Map<string, number>(); // key -> best cost

  while (pq.length > 0) {
    // Simple linear scan min-heap (sufficient for small graphs)
    let minIdx = 0;
    for (let i = 1; i < pq.length; i++) {
      if (pq[i][0] < pq[minIdx][0]) minIdx = i;
    }
    const [cost, node, step, path, reactionIds] = pq.splice(minIdx, 1)[0];

    if (node === end) {
      return { nodes: path, reactionIds, totalCost: cost };
    }

    if (step >= maxSteps) continue;

    const key = `${node}:${step}`;
    const prevCost = visited.get(key);
    if (prevCost !== undefined && prevCost <= cost) continue;
    visited.set(key, cost);

    const edges: Edge[] = adj.get(node) ?? [];
    for (const edge of edges) {
      if (blockedNodes.has(edge.target)) continue;
      if (blockedEdges.has(edge.reactionId)) continue;
      if (path.includes(edge.target)) continue; // no cycles

      pq.push([
        cost + edge.weight,
        edge.target,
        step + 1,
        [...path, edge.target],
        [...reactionIds, edge.reactionId],
      ]);
    }
  }

  return null;
}

// ---------------------------------------------------------------------------
// Yen's K-Shortest Paths algorithm
// ---------------------------------------------------------------------------

export interface YenOptions {
  maxSteps?: number;
  timeoutMs?: number;
}

export function findKShortestPaths(
  adj: AdjacencyList,
  start: string,
  end: string,
  k: number = 5,
  options: YenOptions = {}
): PathResult[] {
  const { maxSteps = 20, timeoutMs = 5000 } = options;
  const deadline = Date.now() + timeoutMs;

  // A* list: confirmed k-shortest paths
  const A: PathResult[] = [];
  // Candidate list
  const B: PathResult[] = [];

  const firstPath = dijkstra(adj, start, end, maxSteps);
  if (!firstPath) return [];
  A.push(firstPath);

  for (let ki = 1; ki < k; ki++) {
    if (Date.now() > deadline) break;

    const prevPath = A[ki - 1];

    for (let i = 0; i < prevPath.nodes.length - 1; i++) {
      if (Date.now() > deadline) break;

      const spurNode = prevPath.nodes[i];
      const rootPath = prevPath.nodes.slice(0, i + 1);
      const rootReactions = prevPath.reactionIds.slice(0, i);

      const blockedEdges = new Set<string>();
      const blockedNodes = new Set<string>();

      // Block edges that have been used by existing A-paths with the same root
      for (const path of A) {
        if (path.nodes.length > i && arraysEqual(path.nodes.slice(0, i + 1), rootPath)) {
          blockedEdges.add(path.reactionIds[i]);
        }
      }

      // Block root nodes to prevent loops
      for (const n of rootPath.slice(0, -1)) {
        blockedNodes.add(n);
      }

      const spurPath = dijkstra(adj, spurNode, end, maxSteps - i, blockedNodes, blockedEdges);

      if (spurPath) {
        const totalNodes = [...rootPath.slice(0, -1), ...spurPath.nodes];
        const totalReactions = [...rootReactions, ...spurPath.reactionIds];
        const totalCost = spurPath.totalCost + prevPath.totalCost - prevPath.totalCost +
          // recalculate root cost
          rootReactions.reduce<number>((acc, rId, idx) => {
            // We need the edge cost from adj; stored implicitly in path costs.
            // Simpler: just use the cost difference between nodes in prevPath.
            return acc;
          }, 0);

        // Simpler cost: recompute from scratch using the reaction edges
        let recomputedCost = 0;
        for (let j = 0; j < totalNodes.length - 1; j++) {
          const from = totalNodes[j];
          const rId = totalReactions[j];
          const edges = adj.get(from) ?? [];
          const edge = edges.find((e) => e.reactionId === rId);
          if (edge) recomputedCost += edge.weight;
        }

        const candidate: PathResult = {
          nodes: totalNodes,
          reactionIds: totalReactions,
          totalCost: recomputedCost,
        };

        // Only add if not already in B or A
        const isDuplicate =
          B.some((p) => arraysEqual(p.reactionIds, candidate.reactionIds)) ||
          A.some((p) => arraysEqual(p.reactionIds, candidate.reactionIds));

        if (!isDuplicate) {
          B.push(candidate);
        }
      }
    }

    if (B.length === 0) break;

    // Pick the lowest-cost candidate
    B.sort((a, b) => a.totalCost - b.totalCost);
    A.push(B.shift()!);
  }

  return A;
}

function arraysEqual(a: string[], b: string[]): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) {
    if (a[i] !== b[i]) return false;
  }
  return true;
}
