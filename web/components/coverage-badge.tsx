import type { Reaction } from "@/lib/types";

type CoverageLevel = "direct" | "cross_substrate" | "family_only" | "none";

const COVERAGE_CONFIG: Record<
  CoverageLevel,
  { dot: string; label: string; border: string }
> = {
  direct: {
    dot: "bg-green-400",
    label: "Known enzyme",
    border: "border-green-400/20 bg-green-400/10 text-green-400",
  },
  cross_substrate: {
    dot: "bg-amber-400",
    label: "Similar enzyme",
    border: "border-amber-400/20 bg-amber-400/10 text-amber-400",
  },
  family_only: {
    dot: "bg-orange-400",
    label: "EC family only",
    border: "border-orange-400/20 bg-orange-400/10 text-orange-400",
  },
  none: {
    dot: "bg-red-400",
    label: "No enzyme",
    border: "border-red-400/20 bg-red-400/10 text-red-400",
  },
};

interface CoverageDotProps {
  coverage: CoverageLevel | undefined;
  size?: "sm" | "md";
}

export function CoverageDot({ coverage, size = "sm" }: CoverageDotProps) {
  const level = coverage ?? "none";
  const config = COVERAGE_CONFIG[level];
  const sizeClass = size === "sm" ? "h-2 w-2" : "h-2.5 w-2.5";

  return (
    <span
      className={`inline-block shrink-0 rounded-full ${config.dot} ${sizeClass}`}
      title={config.label}
    />
  );
}

interface CoverageBadgeProps {
  coverage: CoverageLevel | undefined;
  className?: string;
}

export function CoverageBadge({
  coverage,
  className = "",
}: CoverageBadgeProps) {
  const level = coverage ?? "none";
  const config = COVERAGE_CONFIG[level];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium ${config.border} ${className}`}
    >
      <span className={`inline-block h-1.5 w-1.5 rounded-full ${config.dot}`} />
      {config.label}
    </span>
  );
}

export function coverageSummary(reactions: Reaction[]) {
  const counts = { direct: 0, cross_substrate: 0, family_only: 0, none: 0 };
  for (const r of reactions) {
    const level = r.enzyme_coverage ?? "none";
    counts[level]++;
  }
  return counts;
}
