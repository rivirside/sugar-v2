"use client";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { useCallback, useMemo } from "react";
import type { EvidenceTier } from "./types";

export type { EvidenceTier };
export const ALL_TIERS: EvidenceTier[] = [
  "validated",
  "predicted",
  "inferred",
  "hypothetical",
];

export function useEvidenceFilter() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const activeTiers = useMemo<EvidenceTier[]>(() => {
    const param = searchParams.get("evidence");
    if (!param) return ALL_TIERS;
    return param
      .split(",")
      .filter((t): t is EvidenceTier =>
        ALL_TIERS.includes(t as EvidenceTier)
      );
  }, [searchParams]);

  const setTiers = useCallback(
    (tiers: EvidenceTier[]) => {
      const params = new URLSearchParams(searchParams.toString());
      if (tiers.length === ALL_TIERS.length) {
        params.delete("evidence");
      } else {
        params.set("evidence", tiers.join(","));
      }
      const qs = params.toString();
      router.replace(qs ? `${pathname}?${qs}` : pathname);
    },
    [searchParams, router, pathname]
  );

  const toggleTier = useCallback(
    (tier: EvidenceTier) => {
      const next = activeTiers.includes(tier)
        ? activeTiers.filter((t) => t !== tier)
        : [...activeTiers, tier];
      setTiers(next);
    },
    [activeTiers, setTiers]
  );

  return { activeTiers, setTiers, toggleTier };
}
