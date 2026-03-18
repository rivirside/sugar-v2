"use client";

import { useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import { reactions, compoundMap } from "@/lib/data";
import { EvidenceBadge } from "@/components/evidence-badge";
import { formatYield } from "@/lib/utils";
import type { ReactionType, EvidenceTier } from "@/lib/types";
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from "@/components/ui/table";
import { Search, ArrowRight } from "lucide-react";

const ALL_REACTION_TYPES: ReactionType[] = [
  "epimerization",
  "isomerization",
  "reduction",
  "oxidation",
  "phosphorylation",
  "dephosphorylation",
  "mutase",
  "lactonization",
  "aldol",
  "hydrolysis",
  "condensation",
  "transamination",
  "nucleotidyltransfer",
  "multi_epimerization",
];

const EVIDENCE_TIERS: EvidenceTier[] = [
  "validated",
  "predicted",
  "inferred",
  "hypothetical",
];

export default function ReactionBrowserPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<Set<ReactionType>>(new Set());
  const [evidenceFilter, setEvidenceFilter] = useState<Set<EvidenceTier>>(
    new Set()
  );

  const filtered = useMemo(() => {
    return reactions.filter((r) => {
      // Text search (by substrate/product names or reaction ID)
      if (query) {
        const q = query.toLowerCase();
        const substrateNames = r.substrates
          .map((s) => compoundMap.get(s)?.name ?? s)
          .join(" ")
          .toLowerCase();
        const productNames = r.products
          .map((p) => compoundMap.get(p)?.name ?? p)
          .join(" ")
          .toLowerCase();
        const matchesId = r.id.toLowerCase().includes(q);
        if (
          !substrateNames.includes(q) &&
          !productNames.includes(q) &&
          !matchesId
        )
          return false;
      }

      // Type filter
      if (typeFilter.size > 0 && !typeFilter.has(r.reaction_type)) return false;

      // Evidence filter
      if (evidenceFilter.size > 0 && !evidenceFilter.has(r.evidence_tier))
        return false;

      return true;
    });
  }, [query, typeFilter, evidenceFilter]);

  function toggleType(type: ReactionType) {
    setTypeFilter((prev) => {
      const next = new Set(prev);
      if (next.has(type)) next.delete(type);
      else next.add(type);
      return next;
    });
  }

  function toggleEvidence(tier: EvidenceTier) {
    setEvidenceFilter((prev) => {
      const next = new Set(prev);
      if (next.has(tier)) next.delete(tier);
      else next.add(tier);
      return next;
    });
  }

  return (
    <div className="flex flex-1 flex-col px-4 py-6 sm:px-6">
      <div className="mx-auto w-full max-w-5xl">
        <h1 className="text-2xl font-bold text-zinc-100">Reactions</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Browse {reactions.length} enzymatic reactions
        </p>

        {/* Search + Filters */}
        <div className="mt-6 space-y-4">
          <div className="flex items-center gap-2 rounded-lg border border-zinc-800 bg-zinc-900/80 px-3 py-2">
            <Search className="h-4 w-4 text-zinc-500" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search by compound name or reaction ID..."
              className="w-full bg-transparent text-sm text-zinc-100 placeholder:text-zinc-500 outline-none"
            />
          </div>

          <div className="flex flex-wrap gap-4">
            {/* Type filter */}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-xs text-zinc-500">Type:</span>
              {ALL_REACTION_TYPES.map((type) => (
                <button
                  key={type}
                  onClick={() => toggleType(type)}
                  className={`rounded-full border px-2 py-0.5 text-xs capitalize transition-colors ${
                    typeFilter.has(type)
                      ? "border-zinc-600 bg-zinc-800 text-zinc-200"
                      : "border-zinc-800 text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {type.replace("_", " ")}
                </button>
              ))}
            </div>

            {/* Evidence filter */}
            <div className="flex items-center gap-2">
              <span className="text-xs text-zinc-500">Evidence:</span>
              {EVIDENCE_TIERS.map((tier) => (
                <button
                  key={tier}
                  onClick={() => toggleEvidence(tier)}
                  className={`rounded-full border px-2 py-0.5 text-xs capitalize transition-colors ${
                    evidenceFilter.has(tier)
                      ? "border-zinc-600 bg-zinc-800 text-zinc-200"
                      : "border-zinc-800 text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  {tier}
                </button>
              ))}
            </div>
          </div>
        </div>

        <p className="mt-4 text-xs text-zinc-500">{filtered.length} results</p>

        {/* Table */}
        <div className="mt-2">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Substrate</TableHead>
                <TableHead className="w-8"></TableHead>
                <TableHead>Product</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Evidence</TableHead>
                <TableHead>Yield</TableHead>
                <TableHead>Cost</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((r) => {
                const substrate = compoundMap.get(r.substrates[0]);
                const product = compoundMap.get(r.products[0]);
                return (
                  <TableRow
                    key={r.id}
                    className="cursor-pointer"
                    onClick={() => router.push(`/reaction/${r.id}`)}
                  >
                    <TableCell className="text-zinc-200">
                      {substrate?.name ?? r.substrates[0]}
                    </TableCell>
                    <TableCell>
                      <ArrowRight className="h-3 w-3 text-zinc-600" />
                    </TableCell>
                    <TableCell className="text-zinc-200">
                      {product?.name ?? r.products[0]}
                    </TableCell>
                    <TableCell className="text-xs capitalize text-zinc-400">
                      {r.reaction_type.replace("_", " ")}
                    </TableCell>
                    <TableCell>
                      <EvidenceBadge tier={r.evidence_tier} />
                    </TableCell>
                    <TableCell className="text-zinc-400">
                      {formatYield(r.yield)}
                    </TableCell>
                    <TableCell className="text-zinc-400">
                      {r.cost_score.toFixed(2)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </div>
    </div>
  );
}
