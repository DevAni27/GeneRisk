"use client";

import { Verdict } from "@/types/variant";

interface RiskGaugeProps {
  verdict: Verdict;
  verdictLabel: string;
  deltaScore: number | null;
  threshold: number | null;
  pathogenicityIndex: number | null;
}

const VERDICT_COLOR: Record<Verdict, string> = {
  pathogenic: "var(--color-clay)",
  benign: "var(--color-moss)",
  uncertain: "var(--color-amber)",
};

const RADIUS = 82;
const CENTER_X = 110;
const CENTER_Y = 100;
const ARC_LENGTH = Math.PI * RADIUS;
const ARC_PATH = `M ${CENTER_X - RADIUS} ${CENTER_Y} A ${RADIUS} ${RADIUS} 0 0 1 ${CENTER_X + RADIUS} ${CENTER_Y}`;

export function RiskGauge({
  verdict,
  verdictLabel,
  deltaScore,
  threshold,
  pathogenicityIndex,
}: RiskGaugeProps) {
  const color = VERDICT_COLOR[verdict];
  const hasIndex = pathogenicityIndex != null;
  const fillFraction = hasIndex
    ? Math.max(0, Math.min(100, pathogenicityIndex as number)) / 100
    : 1;

  return (
    <div className="flex flex-col items-center">
      <svg
        viewBox="0 0 220 150"
        className="w-full max-w-[240px]"
        role="img"
        aria-label={`${verdictLabel}, pathogenicity score ${pathogenicityIndex ?? "unavailable"}`}
      >
        <path d={ARC_PATH} fill="none" stroke="var(--color-line)" strokeWidth={14} strokeLinecap="round" />
        <path
          d={ARC_PATH}
          fill="none"
          stroke={color}
          strokeWidth={14}
          strokeLinecap="round"
          strokeDasharray={ARC_LENGTH}
          strokeDashoffset={ARC_LENGTH * (1 - fillFraction)}
        />

        <text x={CENTER_X} y={CENTER_Y + 14} textAnchor="middle" className="font-mono" fontSize="30" fontWeight={600} fill="var(--color-ink)">
          {hasIndex ? `${(pathogenicityIndex as number).toFixed(0)}/100` : "—"}
        </text>
        <text x={CENTER_X} y={CENTER_Y + 34} textAnchor="middle" className="font-mono" fontSize="10" letterSpacing="1.2" fill="var(--color-ink-soft)">
          PATHOGENICITY SCORE
        </text>
      </svg>

      <p className="mt-1 text-center text-lg font-semibold uppercase tracking-[0.08em]" style={{ color }}>
        {verdictLabel}
      </p>

      <div className="mt-2 flex items-center gap-2 font-mono text-[11px] text-ink-soft">
        <span>Δ score {typeof deltaScore === "number" ? deltaScore.toFixed(5) : "—"}</span>
        <span className="text-ink-soft/40">·</span>
        <span>cutoff {typeof threshold === "number" ? threshold.toFixed(5) : "n/a"}</span>
      </div>

      <p className="mt-1 font-mono text-[11px] text-ink-soft">
        Evo2 zero-shot genomic score · HBB-specific calibration
      </p>
    </div>
  );
}