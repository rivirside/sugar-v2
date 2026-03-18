import type { Reaction } from "./types";

export interface Edge {
  reactionId: string;
  target: string;
  weight: number;
}

export type AdjacencyList = Map<string, Edge[]>;

export function buildGraph(reactions: Reaction[]): AdjacencyList {
  const adj: AdjacencyList = new Map();
  for (const r of reactions) {
    if (r.substrates.length !== 1 || r.products.length !== 1) continue;
    const source = r.substrates[0];
    const target = r.products[0];
    if (!adj.has(source)) adj.set(source, []);
    adj.get(source)!.push({ reactionId: r.id, target, weight: r.cost_score });
  }
  return adj;
}
