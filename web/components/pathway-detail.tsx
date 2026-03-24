"use client";

import { useState } from "react";
import Link from "next/link";
import { EvidenceBadge } from "@/components/evidence-badge";
import { CoverageBadge } from "@/components/coverage-badge";
import { compoundMap } from "@/lib/data";
import { formatYield, cumulativeYield } from "@/lib/utils";
import type { PathResult } from "@/lib/pathfinding";
import type { Reaction } from "@/lib/types";
import { ArrowRight, ChevronDown, ChevronRight } from "lucide-react";

interface PathwayDetailProps {
  pathway: PathResult;
  reactionMap: Map<string, Reaction>;
}

function SimilarityBar({ value, label }: { value: number; label: string }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-2">
      <span className="w-20 shrink-0 text-xs text-zinc-500">{label}</span>
      <div className="h-1.5 flex-1 rounded-full bg-zinc-800">
        <div
          className="h-1.5 rounded-full bg-zinc-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="w-8 text-right text-xs text-zinc-500">{pct}%</span>
    </div>
  );
}

function CandidatePanel({ reaction }: { reaction: Reaction }) {
  const candidates = reaction.cross_substrate_candidates;
  if (!candidates || candidates.length === 0) {
    return (
      <div className="mt-2 rounded-md border border-zinc-800 bg-zinc-900/40 p-3 text-xs text-zinc-500">
        No cross-substrate enzyme candidates found for this step.
      </div>
    );
  }

  return (
    <div className="mt-2 flex flex-col gap-2">
      {candidates.slice(0, 5).map((c, i) => {
        const knownSubstrate = compoundMap.get(c.known_substrate_id);
        return (
          <div
            key={i}
            className="rounded-md border border-zinc-800 bg-zinc-900/40 p-3"
          >
            <div className="flex items-start justify-between">
              <div>
                <span className="text-xs font-medium text-zinc-300">
                  {c.ec_number}
                </span>
                {c.enzyme_name && (
                  <span className="ml-2 text-xs text-zinc-500">
                    {c.enzyme_name}
                  </span>
                )}
              </div>
              <span
                className={`rounded-full px-1.5 py-0.5 text-xs ${
                  c.matching_layer === 1
                    ? "bg-green-400/10 text-green-400"
                    : c.matching_layer === 2
                      ? "bg-amber-400/10 text-amber-400"
                      : "bg-orange-400/10 text-orange-400"
                }`}
              >
                Layer {c.matching_layer}
              </span>
            </div>

            <div className="mt-2 text-xs text-zinc-500">
              Works on:{" "}
              <Link
                href={`/compound/${c.known_substrate_id}`}
                className="text-zinc-300 hover:text-white"
              >
                {knownSubstrate?.name ?? c.known_substrate_id}
              </Link>
              {c.organism && (
                <span className="ml-2 italic text-zinc-600">
                  ({c.organism})
                </span>
              )}
            </div>

            <div className="mt-2 flex flex-col gap-1">
              <SimilarityBar
                value={c.similarity.overall}
                label="Overall"
              />
              {c.similarity.stereocenter_distance > 0 && (
                <div className="text-xs text-zinc-600">
                  Stereocenters differ: {c.similarity.stereocenter_distance}
                </div>
              )}
              {c.similarity.carbon_count_distance > 0 && (
                <div className="text-xs text-zinc-600">
                  Carbon count differs by: {c.similarity.carbon_count_distance}
                </div>
              )}
              {c.similarity.modification_distance > 0 && (
                <div className="text-xs text-zinc-600">
                  Modification difference: {Math.round(c.similarity.modification_distance * 100)}%
                </div>
              )}
              {c.similarity.type_distance > 0 && (
                <div className="text-xs text-zinc-600">
                  Type difference: {Math.round(c.similarity.type_distance * 100)}%
                </div>
              )}
            </div>

            {c.pdb_ids.length > 0 && (
              <div className="mt-2 text-xs text-zinc-500">
                PDB:{" "}
                {c.pdb_ids.map((pdb, j) => (
                  <span key={j}>
                    {j > 0 && ", "}
                    <a
                      href={`https://www.rcsb.org/structure/${pdb}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-400 hover:text-blue-300"
                    >
                      {pdb}
                    </a>
                  </span>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

function StepCard({
  reaction,
  fromId,
  toId,
  stepNumber,
}: {
  reaction: Reaction;
  fromId: string;
  toId: string;
  stepNumber: number;
}) {
  const [expanded, setExpanded] = useState(false);
  const from = compoundMap.get(fromId);
  const to = compoundMap.get(toId);
  const hasCandidates =
    reaction.enzyme_coverage === "cross_substrate" ||
    reaction.enzyme_coverage === "none";
  const engScore = reaction.engineerability_score;

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-3">
      <div className="flex items-center gap-2 text-xs text-zinc-500">
        <span className="font-medium">Step {stepNumber}</span>
        <span className="capitalize">
          {reaction.reaction_type.replace("_", " ")}
        </span>
        <EvidenceBadge tier={reaction.evidence_tier} />
        <CoverageBadge coverage={reaction.enzyme_coverage} />
        {engScore != null && (
          <span
            className="ml-auto text-xs text-zinc-600"
            title="Engineerability score (0 = easy, 1 = hard)"
          >
            eng: {engScore.toFixed(2)}
          </span>
        )}
      </div>

      <div className="mt-2 flex items-center gap-2">
        <Link
          href={`/compound/${fromId}`}
          className="text-sm font-medium text-zinc-200 hover:text-white"
        >
          {from?.name ?? fromId}
        </Link>
        <ArrowRight className="h-3.5 w-3.5 text-zinc-600" />
        <Link
          href={`/compound/${toId}`}
          className="text-sm font-medium text-zinc-200 hover:text-white"
        >
          {to?.name ?? toId}
        </Link>
      </div>

      <div className="mt-2 flex gap-4 text-xs text-zinc-500">
        <span>Yield: {formatYield(reaction.yield)}</span>
        <span>Cost: {reaction.cost_score.toFixed(2)}</span>
        {reaction.cofactors && reaction.cofactors.length > 0 && (
          <span>Cofactors: {reaction.cofactors.join(", ")}</span>
        )}
        {reaction.ec_number && (
          <span>EC: {reaction.ec_number}</span>
        )}
      </div>

      {/* Expandable engineering panel */}
      {hasCandidates && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="mt-2 flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300"
        >
          {expanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
          {reaction.enzyme_coverage === "cross_substrate"
            ? `${reaction.cross_substrate_candidates?.length ?? 0} engineering candidates`
            : "View engineering options"}
        </button>
      )}

      {reaction.enzyme_coverage === "direct" && reaction.ec_number && (
        <div className="mt-2 rounded-md border border-green-400/20 bg-green-400/5 p-2 text-xs text-green-400">
          Known enzyme: {reaction.ec_number}
          {reaction.enzyme_name && ` (${reaction.enzyme_name})`}
          {reaction.organism && reaction.organism.length > 0 && (
            <span className="text-green-400/60">
              {" "}from {reaction.organism.join(", ")}
            </span>
          )}
        </div>
      )}

      {expanded && <CandidatePanel reaction={reaction} />}
    </div>
  );
}

export function PathwayDetail({ pathway, reactionMap }: PathwayDetailProps) {
  const reactions = pathway.reactionIds
    .map((id) => reactionMap.get(id))
    .filter(Boolean) as Reaction[];
  const yields = reactions.map((r) => r.yield);
  const cumYield = cumulativeYield(yields);

  // Coverage summary
  const coverageCounts = { direct: 0, cross_substrate: 0, family_only: 0, none: 0 };
  for (const r of reactions) {
    const level = r.enzyme_coverage ?? "none";
    coverageCounts[level]++;
  }

  const avgEng =
    reactions.reduce((sum, r) => sum + (r.engineerability_score ?? 1), 0) /
    reactions.length;

  return (
    <div className="flex flex-col gap-4">
      <h3 className="text-sm font-medium text-zinc-300">
        Pathway Detail ({pathway.nodes.length - 1} steps)
      </h3>

      <div className="flex flex-col gap-3">
        {reactions.map((reaction, i) => (
          <StepCard
            key={reaction.id}
            reaction={reaction}
            fromId={pathway.nodes[i]}
            toId={pathway.nodes[i + 1]}
            stepNumber={i + 1}
          />
        ))}
      </div>

      {/* Summary */}
      <div className="rounded-lg border border-zinc-800 bg-zinc-800/40 p-3">
        <h4 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
          Summary
        </h4>
        <div className="mt-2 grid grid-cols-2 gap-4 text-sm sm:grid-cols-4">
          <div>
            <span className="text-zinc-500">Steps</span>
            <p className="font-medium text-zinc-200">
              {pathway.nodes.length - 1}
            </p>
          </div>
          <div>
            <span className="text-zinc-500">Est. Yield</span>
            <p className="font-medium text-zinc-200">{formatYield(cumYield)}</p>
          </div>
          <div>
            <span className="text-zinc-500">Total Cost</span>
            <p className="font-medium text-zinc-200">
              {pathway.totalCost.toFixed(2)}
            </p>
          </div>
          <div>
            <span className="text-zinc-500">Avg Engineerability</span>
            <p className="font-medium text-zinc-200">{avgEng.toFixed(2)}</p>
          </div>
        </div>

        {/* Coverage breakdown */}
        <div className="mt-3 flex items-center gap-3 text-xs">
          {coverageCounts.direct > 0 && (
            <span className="flex items-center gap-1 text-green-400">
              <span className="inline-block h-2 w-2 rounded-full bg-green-400" />
              {coverageCounts.direct} known
            </span>
          )}
          {coverageCounts.cross_substrate > 0 && (
            <span className="flex items-center gap-1 text-amber-400">
              <span className="inline-block h-2 w-2 rounded-full bg-amber-400" />
              {coverageCounts.cross_substrate} similar
            </span>
          )}
          {coverageCounts.none > 0 && (
            <span className="flex items-center gap-1 text-red-400">
              <span className="inline-block h-2 w-2 rounded-full bg-red-400" />
              {coverageCounts.none} gaps
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
