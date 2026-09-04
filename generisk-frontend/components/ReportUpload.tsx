"use client";

import { useState, useRef } from "react";
import { extractReport, ExtractedVariant, ExtractReportResponse } from "@/lib/api";

interface ReportUploadProps {
  onAnalyzeVariant: (query: string) => void;
}

export function ReportUpload({ onAnalyzeVariant }: ReportUploadProps) {
  const [status, setStatus] = useState<"idle" | "parsing" | "done" | "error">("idle");
  const [result, setResult] = useState<ExtractReportResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [fileName, setFileName] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (file.type !== "application/pdf") {
      setStatus("error");
      setErrorMessage("Please upload a PDF file.");
      return;
    }

    setFileName(file.name);
    setStatus("parsing");
    setErrorMessage(null);
    setResult(null);

    try {
      const data = await extractReport(file);
      setResult(data);
      setStatus("done");
    } catch (err) {
      console.error("Failed to extract report:", err);
      setErrorMessage(
        err instanceof Error ? err.message : "Unable to analyze this report."
      );
      setStatus("error");
    }
  };

  return (
    <div className="rounded-card border border-dashed border-line bg-white p-6">
      <p className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
        Upload a lab report
      </p>
      <p className="mt-1 text-xs text-ink-soft">
        PDF only. GeneRisk can extract HBB variants from compatible molecular
        genetic test reports.
      </p>

      <div
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          const file = e.dataTransfer.files[0];
          if (file) handleFile(file);
        }}
        onClick={() => inputRef.current?.click()}
        className="mt-4 flex cursor-pointer flex-col items-center justify-center rounded-soft border border-line bg-paper px-6 py-8 text-center transition-colors hover:border-teal"
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />
        <p className="text-sm text-ink-soft">
          {fileName || "Drop a PDF here, or click to browse"}
        </p>
      </div>

      {status === "parsing" && (
        <p className="mt-3 font-mono text-xs text-teal">Reading report…</p>
      )}

      {status === "error" && errorMessage && (
        <div className="mt-3 rounded-soft border border-clay/30 bg-clay/5 px-4 py-3">
          <p className="text-sm font-medium text-clay">
            {errorMessage.toLowerCase().includes("scan") ||
            errorMessage.toLowerCase().includes("text")
              ? "Scanned report detected"
              : "Couldn't process this report"}
          </p>
          <p className="mt-1 text-xs leading-relaxed text-ink-soft">
            {errorMessage}
          </p>
        </div>
      )}

      {status === "done" && result && result.variants_found === 0 && (
        <p className="mt-3 text-sm text-clay">
          {result.message || "No variants found in this report."}
        </p>
      )}

      {status === "done" && result && result.variants_found > 0 && (
        <div className="mt-4 space-y-3">
          <p className="text-sm font-medium text-ink">
            {result.variants_found} HBB variant{result.variants_found > 1 ? "s" : ""} found
          </p>
          {result.variants.map((variant: ExtractedVariant, i: number) => (
            <div
              key={i}
              className="rounded-soft border border-line bg-paper px-4 py-3.5"
            >
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm font-semibold text-ink">
                  {variant.common_name || variant.hgvs_c}
                </p>
                {variant.reported_classification && (
                  <span className="font-mono text-[11px] text-ink-soft">
                    Lab classification: {variant.reported_classification}
                  </span>
                )}
              </div>
              <p className="mt-1 font-mono text-xs text-ink-soft">
                {variant.gene} · {variant.transcript}:{variant.hgvs_c}
                {variant.hgvs_p ? ` (${variant.hgvs_p})` : ""}
              </p>
              {variant.zygosity && (
                <p className="mt-0.5 text-xs capitalize text-ink-soft">
                  {variant.zygosity}
                </p>
              )}

              {variant.can_score ? (
                <button
                  onClick={() => onAnalyzeVariant(variant.query)}
                  className="mt-3 h-9 rounded-soft bg-teal px-4 text-xs font-semibold text-white transition-colors hover:bg-[#095A54]"
                >
                  Analyze with GeneRisk
                </button>
              ) : (
                <p className="mt-3 text-xs text-ink-soft">
                  This variant can&apos;t be scored automatically.
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}