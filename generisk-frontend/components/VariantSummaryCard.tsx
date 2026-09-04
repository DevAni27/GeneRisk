"use client";

import { Variant } from "@/types/variant";
import { RiskGauge } from "./RiskGauge";
import { ClinVarBadge } from "./ClinVarBadge";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-line py-3 last:border-b-0">
      <dt className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
        {label}
      </dt>
      <dd className="text-right font-mono text-sm text-ink">{children}</dd>
    </div>
  );
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-teal">
      {children}
    </p>
  );
}

export function VariantSummaryCard({ variant }: { variant: Variant }) {
  return (
    <section className="rounded-card border border-line bg-white p-6 sm:p-7">
      <SectionLabel>AI Triage Result</SectionLabel>

      <div className="mt-4">
        <RiskGauge
          verdict={variant.verdict}
          verdictLabel={variant.verdictLabel.toUpperCase()}
          deltaScore={variant.deltaScore}
          threshold={variant.threshold}
          pathogenicityIndex={variant.pathogenicityIndex}
        />
      </div>

      <dl className="mt-6">
        <Row label="Gene">
          <span className="font-semibold">{variant.gene}</span>
        </Row>
        <Row label="Position">{variant.position}</Row>
        <Row label="Change">{variant.hgvs}</Row>
        <Row label="dbSNP">{variant.rsid ?? "—"}</Row>
      </dl>

      <div className="my-6 border-t border-line" />

      <SectionLabel>External Clinical Evidence</SectionLabel>
      <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">
        Independent of the Evo2 AI prediction above — sourced from ClinVar,
        NCBI&apos;s public clinical variant database.
      </p>

      <dl className="mt-4">
        <Row label="Classification">
          <ClinVarBadge value={variant.clinvar} />
        </Row>
        <Row label="Review status">{variant.clinvarReviewStatus || "—"}</Row>
        <Row label="Accession">{variant.clinvarAccession || "—"}</Row>
      </dl>
    </section>
  );
}