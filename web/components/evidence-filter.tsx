"use client";

import { Suspense } from "react";
import { useEvidenceFilter, ALL_TIERS } from "@/lib/evidence-filter";
import type { EvidenceTier } from "@/lib/types";

// Color classes per tier (border + text for active; muted for inactive)
const TIER_ACTIVE: Record<EvidenceTier, string> = {
  validated: "border-green-500 bg-green-500/15 text-green-400",
  predicted: "border-blue-500 bg-blue-500/15 text-blue-400",
  inferred: "border-amber-500 bg-amber-500/15 text-amber-400",
  hypothetical: "border-zinc-500 bg-zinc-500/15 text-zinc-400",
};

const TIER_INACTIVE: Record<EvidenceTier, string> = {
  validated: "border-zinc-800 text-zinc-600 hover:border-green-800 hover:text-green-600",
  predicted: "border-zinc-800 text-zinc-600 hover:border-blue-800 hover:text-blue-600",
  inferred: "border-zinc-800 text-zinc-600 hover:border-amber-800 hover:text-amber-600",
  hypothetical: "border-zinc-800 text-zinc-600 hover:border-zinc-600 hover:text-zinc-500",
};

function EvidenceFilterInner() {
  const { activeTiers, toggleTier } = useEvidenceFilter();

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-zinc-500">Evidence:</span>
      {ALL_TIERS.map((tier) => {
        const active = activeTiers.includes(tier);
        return (
          <button
            key={tier}
            onClick={() => toggleTier(tier)}
            className={`rounded-full border px-2 py-0.5 text-xs capitalize transition-colors ${
              active ? TIER_ACTIVE[tier] : TIER_INACTIVE[tier]
            }`}
          >
            {tier}
          </button>
        );
      })}
    </div>
  );
}

// Wrap in Suspense because useSearchParams requires it in Next.js app router
export function EvidenceFilter() {
  return (
    <Suspense>
      <EvidenceFilterInner />
    </Suspense>
  );
}
