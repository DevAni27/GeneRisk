"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { validationMetrics } from "@/data/validation";

const BAR_COLOR = "#0B6E67";
const COMPOSITION_COLORS = ["#B8462F", "#4C7A4F"];

export default function AccuracyPage() {
  const m = validationMetrics;

  const metricData = [
    { name: "AUROC", value: m.auroc },
    { name: "Precision", value: m.precision },
    { name: "Recall", value: m.recall },
    { name: "Specificity", value: m.specificity },
    { name: "F1", value: m.f1 },
    { name: "Bal. Acc.", value: m.balancedAccuracy },
  ];

  const compositionData = [
    { name: "Pathogenic", count: m.pathogenicVariants },
    { name: "Benign", count: m.benignVariants },
  ];

  const scoredRate = ((m.successfullyScored / m.totalVariants) * 100).toFixed(0);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-teal">
        Data &amp; validation
      </p>
      <h1 className="mt-3 max-w-3xl text-3xl font-semibold tracking-tight text-ink sm:text-[34px]">
        How accurate is the HBB prediction?
      </h1>
      <p className="mt-3 max-w-3xl text-sm leading-relaxed text-ink-soft">
        Evo2&apos;s published benchmarks are for BRCA1. These numbers are our own
        recalibration against known HBB variants — this is what we&apos;re claiming,
        not the model&apos;s original paper.
      </p>

      <section aria-label="Key metrics" className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { value: `${(m.auroc * 100).toFixed(1)}%`, label: "AUROC" },
          { value: `${(m.precision * 100).toFixed(1)}%`, label: "Precision" },
          { value: `${(m.recall * 100).toFixed(1)}%`, label: "Recall" },
          { value: `${m.totalVariants}`, label: "Labeled variants" },
        ].map((stat) => (
          <div key={stat.label} className="rounded-card border border-line bg-white px-5 py-6">
            <p className="font-mono text-[38px] font-semibold leading-none tracking-tight text-ink">
              {stat.value}
            </p>
            <p className="mt-3 text-xs leading-relaxed text-ink-soft">
              {stat.label}
            </p>
          </div>
        ))}
      </section>

      <section className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-card border border-line bg-white p-6 sm:p-7">
          <h2 className="text-base font-semibold text-ink">Model performance</h2>
          <p className="mt-1 text-xs text-ink-soft">
            All six metrics from the recalibrated HBB validation run
          </p>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={metricData} margin={{ top: 10, right: 10, left: -10, bottom: 24 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#D5DDD8" vertical={false} />
                <XAxis
                  dataKey="name"
                  interval={0}
                  angle={-35}
                  textAnchor="end"
                  height={50}
                  tick={{ fontSize: 10, fill: "#4A5A5F", fontFamily: "IBM Plex Mono" }}
                  axisLine={{ stroke: "#D5DDD8" }}
                  tickLine={false}
                />
                <YAxis
                  domain={[0, 1]}
                  tick={{ fontSize: 12, fill: "#4A5A5F", fontFamily: "IBM Plex Mono" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  formatter={(value) => `${(Number(value) * 100).toFixed(1)}%`}
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #D5DDD8",
                    fontFamily: "IBM Plex Sans",
                    fontSize: 13,
                  }}
                />
                <Bar dataKey="value" fill={BAR_COLOR} radius={[6, 6, 0, 0]} maxBarSize={40} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-card border border-line bg-white p-6 sm:p-7">
          <h2 className="text-base font-semibold text-ink">Validation set composition</h2>
          <p className="mt-1 text-xs text-ink-soft">
            {m.totalVariants} labeled HBB variants · {scoredRate}% successfully scored
          </p>
          <div className="mt-5 h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={compositionData}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#D5DDD8" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: "#4A5A5F", fontFamily: "IBM Plex Mono" }}
                  axisLine={{ stroke: "#D5DDD8" }}
                  tickLine={false}
                />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={90}
                  tick={{ fontSize: 12, fill: "#17242B", fontFamily: "IBM Plex Sans" }}
                  axisLine={false}
                  tickLine={false}
                />
                <Tooltip
                  contentStyle={{
                    borderRadius: 8,
                    border: "1px solid #D5DDD8",
                    fontFamily: "IBM Plex Sans",
                    fontSize: 13,
                  }}
                />
                <Bar dataKey="count" radius={[0, 6, 6, 0]} maxBarSize={36}>
                  {compositionData.map((_, index) => (
                    <Cell key={index} fill={COMPOSITION_COLORS[index]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </section>

      <section className="mt-6 rounded-card border border-line bg-white p-6 sm:p-7">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-base font-semibold text-ink">Threshold recalibrated for HBB, not inherited from BRCA1</h2>
          <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
            Δ cutoff {m.threshold.toFixed(6)}
          </p>
        </div>
        <p className="mt-2 max-w-3xl text-sm leading-relaxed text-ink-soft">
          Evo2&apos;s published accuracy is reported on BRCA1 saturation-mutagenesis
          data. We reran zero-shot scoring on this HBB-specific validation set
          and picked a new delta-score cutoff that maximizes accuracy on this
          gene, achieving an F1 score of {(m.f1 * 100).toFixed(1)}% and balanced
          accuracy of {(m.balancedAccuracy * 100).toFixed(1)}%.
        </p>
      </section>
    </main>
  );
}