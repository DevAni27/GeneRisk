"use client";

import { useEffect, useState } from "react";
import { supabase } from "@/lib/supabase";

type LookupResult = "Pathogenic" | "Benign" | "Uncertain" | string;

interface LookupRow {
  id: string;
  worker_id: string;
  variant_label: string;
  gene: string | null;
  position: string | null;
  result: LookupResult | null;
  confidence: number | null;
  created_at: string;
  patient_name: string | null;
  patient_ref: string | null;
  area: string | null;
}

function resultStyle(result: string | null): string {
  const r = (result || "").toLowerCase();
  if (r.includes("pathogenic")) return "border-clay/30 bg-clay/10 text-clay";
  if (r.includes("benign")) return "border-moss/30 bg-moss/10 text-moss";
  return "border-amber/40 bg-amber/15 text-[#8A6416]";
}

function ResultPill({ value }: { value: string | null }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[11px] ${resultStyle(value)}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {value || "Unknown"}
    </span>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-US", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const COLUMNS = "md:grid md:grid-cols-[9rem_1fr_9rem_8rem_8.5rem] md:items-center md:gap-4";

function HistoryDetailModal({
  record,
  onClose,
}: {
  record: LookupRow;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-ink/40 px-4 py-10"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-card border border-line bg-white p-6 sm:p-7"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.14em] text-ink-soft">
              {formatDate(record.created_at)}
            </p>
            <h2 className="mt-1 font-mono text-lg font-semibold text-ink">
              {record.variant_label}
            </h2>
            <p className="mt-1 text-sm text-ink-soft">
              Worker: {record.worker_id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-soft border border-line px-3 py-1.5 text-sm text-ink-soft transition-colors hover:bg-paper hover:text-ink"
          >
            Close
          </button>
        </div>

        <div className="mt-6 space-y-3 rounded-soft border border-line bg-paper p-5">
          <div className="flex items-center justify-between">
            <span className="text-sm text-ink-soft">Result</span>
            <ResultPill value={record.result} />
          </div>
          <div className="flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-ink-soft">Patient</span>
            <span className="text-sm text-ink">{record.patient_name || "—"}</span>
          </div>
          <div className="flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-ink-soft">Reference code</span>
            <span className="font-mono text-sm text-ink">{record.patient_ref || "—"}</span>
          </div>
          <div className="flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-ink-soft">Area</span>
            <span className="text-sm text-ink">{record.area || "—"}</span>
          </div>
          <div className="flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-ink-soft">Gene</span>
            <span className="font-mono text-sm text-ink">{record.gene || "—"}</span>
          </div>
          <div className="flex items-center justify-between border-t border-line pt-3">
            <span className="text-sm text-ink-soft">Position</span>
            <span className="font-mono text-sm text-ink">{record.position || "—"}</span>
          </div>
        </div>

        <p className="mt-4 text-xs leading-relaxed text-ink-soft">
          Full sequence detail isn&apos;t stored in this log — only the
          summary result is saved. Re-run the search on the Search page for
          the complete sequence comparison.
        </p>
      </div>
    </div>
  );
}

export default function HistoryPage() {
  const [records, setRecords] = useState<LookupRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<LookupRow | null>(null);

  useEffect(() => {
    async function fetchHistory() {
      const { data, error } = await supabase
        .from("lookups")
        .select("*")
        .order("created_at", { ascending: false })
        .limit(50);

      if (error) {
        console.error("Failed to fetch history:", error);
      } else {
        setRecords(data || []);
      }
      setLoading(false);
    }

    fetchHistory();
  }, []);

  return (
    <main className="mx-auto max-w-6xl px-6 py-10">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-teal">
        Worker log
      </p>
      <h1 className="mt-3 text-3xl font-semibold tracking-tight text-ink sm:text-[34px]">
        Recent variant lookups
      </h1>
      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-ink-soft">
        Every search run from any device, most recent first. Click a row to
        see details.
      </p>

      {loading ? (
        <p className="mt-8 font-mono text-xs text-ink-soft">Loading history…</p>
      ) : records.length === 0 ? (
        <p className="mt-8 rounded-card border border-dashed border-line bg-white px-6 py-10 text-center text-sm text-ink-soft">
          No lookups yet. Run a search to see it appear here.
        </p>
      ) : (
        <>
          <section className="mt-8 rounded-card border border-line bg-white">
            <div
              className={`hidden border-b border-line px-6 py-3 ${COLUMNS}`}
              aria-hidden="true"
            >
              {["Date", "Variant", "Patient", "Area", "Result"].map((heading) => (
                <span
                  key={heading}
                  className="font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft"
                >
                  {heading}
                </span>
              ))}
            </div>

            <ul className="divide-y divide-line">
              {records.map((record) => (
                <li
                  key={record.id}
                  onClick={() => setSelected(record)}
                  className={`cursor-pointer px-6 py-4 transition-colors hover:bg-paper ${COLUMNS}`}
                >
                  <div className="flex items-center justify-between gap-4 md:block">
                    <span className="font-mono text-xs text-ink-soft">
                      {formatDate(record.created_at)}
                    </span>
                    <span className="md:hidden">
                      <ResultPill value={record.result} />
                    </span>
                  </div>

                  <p className="mt-2 font-mono text-sm text-ink md:mt-0">
                    {record.variant_label}
                  </p>

                  <p className="mt-1 text-sm text-ink-soft md:mt-0">
                    {record.patient_name || "—"}
                    {record.patient_ref && (
                      <span className="ml-1 font-mono text-xs text-ink-soft/70">
                        ({record.patient_ref})
                      </span>
                    )}
                  </p>

                  <p className="mt-1 text-sm text-ink-soft md:mt-0">
                    {record.area || "—"}
                  </p>

                  <div className="hidden md:block">
                    <ResultPill value={record.result} />
                  </div>
                </li>
              ))}
            </ul>
          </section>

          <p className="mt-4 font-mono text-[11px] text-ink-soft">
            {records.length} lookup{records.length === 1 ? "" : "s"} · showing most recent 50
          </p>
        </>
      )}

      {selected && (
        <HistoryDetailModal record={selected} onClose={() => setSelected(null)} />
      )}
    </main>
  );
}