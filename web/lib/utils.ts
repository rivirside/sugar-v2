import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import type { EvidenceTier, CompoundType } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const EVIDENCE_COLORS: Record<EvidenceTier, string> = {
  validated: "text-green-400 bg-green-400/10 border-green-400/20",
  predicted: "text-blue-400 bg-blue-400/10 border-blue-400/20",
  inferred: "text-amber-400 bg-amber-400/10 border-amber-400/20",
  hypothetical: "text-zinc-500 bg-zinc-500/10 border-zinc-500/20",
};

export const EVIDENCE_DOT_COLORS: Record<EvidenceTier, string> = {
  validated: "bg-green-400",
  predicted: "bg-blue-400",
  inferred: "bg-amber-400",
  hypothetical: "bg-zinc-600",
};

export const COMPOUND_TYPE_COLORS: Record<CompoundType, string> = {
  aldose: "text-purple-400",
  ketose: "text-orange-400",
  polyol: "text-indigo-400",
  phosphate: "text-yellow-400",
  acid: "text-red-400",
  lactone: "text-pink-400",
  amino_sugar: "text-teal-400",
  nucleotide_sugar: "text-cyan-400",
  deoxy_sugar: "text-lime-400",
  disaccharide: "text-rose-400",
};

export function formatYield(y: number | null): string {
  return y === null ? "unknown" : `${Math.round(y * 100)}%`;
}

export function cumulativeYield(yields: (number | null)[]): number {
  return yields.reduce<number>((acc, y) => acc * (y ?? 0.5), 1);
}
