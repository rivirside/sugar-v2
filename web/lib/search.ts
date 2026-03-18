import Fuse from "fuse.js";
import type { Compound } from "./types";

let fuseInstance: Fuse<Compound> | null = null;

export function initSearch(compounds: Compound[]): Fuse<Compound> {
  if (fuseInstance) return fuseInstance;
  fuseInstance = new Fuse(compounds, {
    keys: [
      { name: "id", weight: 2 },
      { name: "name", weight: 2 },
      { name: "aliases", weight: 1 },
    ],
    threshold: 0.3,
    includeScore: true,
  });
  return fuseInstance;
}

export function searchCompounds(
  query: string,
  compounds: Compound[],
  limit: number = 10
): Compound[] {
  const fuse = initSearch(compounds);
  return fuse.search(query, { limit }).map((r) => r.item);
}
