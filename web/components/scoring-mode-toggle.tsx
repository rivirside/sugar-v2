"use client";

import type { ScoringMode } from "@/lib/types";

const MODES: { value: ScoringMode; label: string; description: string }[] = [
  {
    value: "cost",
    label: "Cost",
    description: "Rank by biochemical cost (yield, cofactors)",
  },
  {
    value: "engineerability",
    label: "Engineerability",
    description: "Rank by enzyme engineering feasibility",
  },
  {
    value: "combined",
    label: "Combined",
    description: "Balanced ranking (cost + engineerability)",
  },
];

interface ScoringModeToggleProps {
  value: ScoringMode;
  onChange: (mode: ScoringMode) => void;
}

export function ScoringModeToggle({ value, onChange }: ScoringModeToggleProps) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-zinc-500">Rank by:</span>
      <div className="flex rounded-lg border border-zinc-800 p-0.5">
        {MODES.map((mode) => (
          <button
            key={mode.value}
            onClick={() => onChange(mode.value)}
            title={mode.description}
            className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
              value === mode.value
                ? "bg-zinc-700 text-zinc-200"
                : "text-zinc-500 hover:text-zinc-300"
            }`}
          >
            {mode.label}
          </button>
        ))}
      </div>
    </div>
  );
}
