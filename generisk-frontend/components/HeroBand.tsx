import Link from "next/link";

const stats = [
  { label: "people screened nationwide", value: "6 Cr" },
  { label: "carriers identified", value: "16.7L" },
  { label: "trained genetic counselors, all of Asia", value: "~350" },
];

function AmbientSequence() {
  const rows = Array.from({ length: 14 }, () =>
    Array.from(
      { length: 60 },
      () => "ACGT"[Math.floor(Math.random() * 4)],
    ).join(" "),
  );
  return (
    <div
      aria-hidden="true"
      className="pointer-events-none absolute inset-0 select-none overflow-hidden font-mono text-[13px] leading-[1.9] tracking-[0.3em] text-paper/[0.04]"
    >
      {rows.map((row, i) => (
        <p key={i}>{row}</p>
      ))}
    </div>
  );
}

export function HeroBand() {
  return (
    <section className="relative w-full overflow-hidden bg-ink text-paper">
      <AmbientSequence />

      <div
        aria-hidden="true"
        className="pointer-events-none absolute -top-32 left-1/4 h-[420px] w-[420px] rounded-full bg-teal/20 blur-[120px]"
      />
      <div
        aria-hidden="true"
        className="pointer-events-none absolute -bottom-24 right-10 h-[300px] w-[300px] rounded-full bg-amber/10 blur-[100px]"
      />

      <div className="relative mx-auto w-full max-w-6xl px-6 py-20 sm:px-10 lg:py-28">
        <div className="max-w-[640px]">
          <p className="font-mono text-[11px] font-medium uppercase tracking-[0.16em] text-amber">
            National Sickle Cell Anaemia Elimination Mission
          </p>
          <div aria-hidden="true" className="mt-3 h-px w-16 bg-amber" />

          <h1 className="mt-8 text-3xl font-semibold leading-[1.18] tracking-[-0.01em] sm:text-[38px]">
            Millions are screened.{" "}
            <span className="text-teal-light">Almost no one</span> is left to
            explain what the result means.
          </h1>

          <Link
            href="/search"
            className="mt-8 inline-flex items-center gap-2 rounded-soft bg-teal px-5 py-2.5 text-sm font-semibold text-white transition-colors duration-150 hover:bg-[#095A54]"
          >
            Start a triage
            <span aria-hidden="true">→</span>
          </Link>
        </div>

        <dl className="mt-14 grid grid-cols-1 overflow-hidden rounded-card border border-paper/10 sm:grid-cols-3">
          {stats.map((stat, i) => (
            <div
              key={stat.label}
              className={`group relative flex flex-col gap-2 px-6 py-7 transition-colors duration-150 hover:bg-paper/[0.03] sm:px-7 ${
                i > 0
                  ? "border-t border-paper/10 sm:border-t-0 sm:border-l"
                  : ""
              }`}
            >
              <span
                aria-hidden="true"
                className="absolute left-0 top-0 h-[2px] w-0 bg-amber transition-all duration-300 group-hover:w-full"
              />
              <dt className="order-2 text-xs tabular-nums text-paper/60">
                {stat.label}
              </dt>
              <dd className="order-1 font-mono text-3xl font-bold tabular-nums tracking-tight text-paper">
                {stat.value}
              </dd>
            </div>
          ))}
        </dl>
      </div>
    </section>
  );
}
