"use client";

import { useState } from "react";
import { exampleChips, ExampleChip } from "@/data/exampleChips";
import { Variant } from "@/types/variant";
import { SearchCard } from "@/components/SearchCard";
import { VariantEvidenceCard } from "@/components/VariantEvidenceCard";
import { VariantSummaryCard } from "@/components/VariantSummaryCard";
import { ReportUpload } from "@/components/ReportUpload";
import { scoreQuery } from "@/lib/api";
import { adaptApiResponse } from "@/lib/adaptApiResponse";
import { supabase } from "@/lib/supabase";
import { useAuth } from "@/lib/auth-context";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [activeChipId, setActiveChipId] = useState<string | null>(null);
  const [selected, setSelected] = useState<Variant | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const { workerId } = useAuth();

  const [patientName, setPatientName] = useState("");
  const [patientRef, setPatientRef] = useState("");
  const [area, setArea] = useState("");

  const saveLookup = async (variant: Variant) => {
    try {
      const { error: insertError } = await supabase.from("lookups").insert({
        worker_id: workerId || "unknown",
        variant_label: variant.hgvs,
        gene: variant.gene,
        position: variant.position,
        result: variant.verdictLabel,
        confidence: variant.confidence,
        patient_name: patientName || null,
        patient_ref: patientRef || null,
        area: area || null,
      });
      if (insertError) console.error("Failed to save lookup:", insertError);
    } catch (err) {
      console.error("Failed to save lookup:", err);
    }
  };

  const runQuery = async (rawQuery: string) => {
    if (!rawQuery.trim()) {
      setError("Enter a gene, HGVS change, chrom:position ref>alt, or rsID.");
      return;
    }

    setError(null);
    setLoading(true);

    try {
      const apiResult = await scoreQuery(rawQuery.trim());
      const variant = adaptApiResponse(apiResult);
      setSelected(variant);
      await saveLookup(variant);
    } catch (err) {
      console.error("scoreQuery failed:", err);
      setSelected(null);
      setError(
        err instanceof Error ? err.message : "Unable to analyze this variant."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = () => {
    runQuery(query);
  };

  const handleSelectExample = (chip: ExampleChip) => {
    setQuery(chip.query);
    setActiveChipId(chip.id);
    setSelected(null);
    setError(null);
  };

  const handleAnalyzeFromReport = (reportQuery: string) => {
    setQuery(reportQuery);
    setActiveChipId(null);
    runQuery(reportQuery);
  };

  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <h1 className="text-2xl font-semibold tracking-tight text-ink sm:text-[28px]">
        Triage a genomic variant
      </h1>
      <p className="mt-1.5 max-w-2xl text-sm leading-relaxed text-ink-soft">
        Look up a single-base change and get a plain-language read on what it
        affects, how confident the evidence is, and what to bring into a
        counseling conversation.
      </p>

      <div className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-3 no-print">
        <div>
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
            Patient name
          </label>
          <input
            type="text"
            value={patientName}
            onChange={(e) => setPatientName(e.target.value)}
            placeholder="e.g. Priya Sharma"
            className="h-11 w-full rounded-soft border border-line bg-white px-3.5 text-sm text-ink placeholder:text-ink-soft/70 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25"
          />
        </div>
        <div>
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
            Patient reference code
          </label>
          <input
            type="text"
            value={patientRef}
            onChange={(e) => setPatientRef(e.target.value)}
            placeholder="e.g. SCR-2026-04821"
            className="h-11 w-full rounded-soft border border-line bg-white px-3.5 text-sm text-ink placeholder:text-ink-soft/70 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25"
          />
        </div>
        <div>
          <label className="mb-1.5 block font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
            Area / village
          </label>
          <input
            type="text"
            value={area}
            onChange={(e) => setArea(e.target.value)}
            placeholder="e.g. Betul Block 3"
            className="h-11 w-full rounded-soft border border-line bg-white px-3.5 text-sm text-ink placeholder:text-ink-soft/70 focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25"
          />
        </div>
      </div>

      <div className="mt-4 no-print">
        <SearchCard
          query={query}
          onQueryChange={(v) => {
            setQuery(v);
            setActiveChipId(null);
          }}
          onAnalyze={handleAnalyze}
          examples={exampleChips}
          activeId={activeChipId}
          onSelectExample={handleSelectExample}
          error={error}
        />
      </div>

      <div className="mt-4 no-print">
        <ReportUpload onAnalyzeVariant={handleAnalyzeFromReport} />
      </div>

      {loading && (
        <p className="mt-6 text-center font-mono text-xs text-teal">
          Scoring variant…
        </p>
      )}

      {!loading && selected ? (
        <>
          <div className="mt-6 flex justify-end no-print">
            <button
              onClick={() => window.print()}
              className="rounded-soft border border-line bg-white px-4 py-2 text-sm font-medium text-ink-soft transition-colors hover:bg-paper hover:text-ink"
            >
              Print result
            </button>
          </div>
          <div className="mt-3 grid grid-cols-1 items-start gap-6 lg:grid-cols-5 print-area">
            <div className="lg:col-span-3">
              <VariantEvidenceCard variant={selected} />
            </div>
            <div className="lg:col-span-2">
              <VariantSummaryCard variant={selected} />
            </div>
          </div>
        </>
      ) : !loading && !selected ? (
        <p className="mt-6 rounded-card border border-dashed border-line bg-white px-6 py-10 text-center text-sm text-ink-soft">
          Search a variant, pick an example, or upload a report to see results.
        </p>
      ) : null}
    </main>
  );
}