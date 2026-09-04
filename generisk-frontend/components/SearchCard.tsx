"use client";

import { SearchIcon } from "lucide-react";
import { ExampleChip } from "@/data/exampleChips";

interface SearchCardProps {
  query: string;
  onQueryChange: (value: string) => void;
  onAnalyze: () => void;
  examples: ExampleChip[];
  activeId: string | null;
  onSelectExample: (chip: ExampleChip) => void;
  error: string | null;
}

export function SearchCard({
  query,
  onQueryChange,
  onAnalyze,
  examples,
  activeId,
  onSelectExample,
  error,
}: SearchCardProps) {
  return (
    <section className="rounded-card border border-line bg-white p-6 sm:p-7">
      <form
        className="flex flex-col gap-3 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          onAnalyze();
        }}
      >
        <div className="relative flex-1">
          <SearchIcon
            className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-ink-soft"
            aria-hidden="true"
          />
          <label className="sr-only" htmlFor="variant-search">
            Search gene or variant coordinate
          </label>
          <input
            id="variant-search"
            type="text"
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            placeholder="Search gene (e.g. HBB) or paste chrom:position ref>alt"
            autoComplete="off"
            spellCheck={false}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? "variant-search-error" : undefined}
            className="h-12 w-full rounded-soft border border-line bg-paper pl-11 pr-4 font-mono text-sm text-ink placeholder:font-sans placeholder:text-ink-soft focus:border-teal focus:outline-none focus:ring-2 focus:ring-teal/25"
          />
        </div>
        <button
          type="submit"
          className="h-12 shrink-0 rounded-soft bg-teal px-7 text-sm font-semibold tracking-wide text-white transition-colors duration-150 ease-out hover:bg-[#095A54] focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white"
        >
          Analyze
        </button>
      </form>

      {error && (
        <p id="variant-search-error" role="status" className="mt-3 font-mono text-xs text-clay">
          {error}
        </p>
      )}

      <div className="mt-5 flex flex-wrap items-center gap-2">
        <span className="mr-1 font-mono text-[11px] uppercase tracking-[0.14em] text-ink-soft">
          Examples
        </span>
        {examples.map((chip) => {
          const isActive = chip.id === activeId;
          return (
            <button
              key={chip.id}
              type="button"
              aria-pressed={isActive}
              onClick={() => onSelectExample(chip)}
              className={`rounded-full border px-3.5 py-1.5 text-xs transition-colors duration-150 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 ${
                isActive
                  ? "border-teal bg-teal/10 text-teal"
                  : "border-line bg-paper text-ink-soft hover:border-teal-light hover:text-ink"
              }`}
            >
              <span className="font-mono">{chip.chipLabel}</span>
              <span className="ml-1.5">({chip.chipNote})</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}