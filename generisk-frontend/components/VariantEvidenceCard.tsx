

import React from 'react'
import { Variant } from '../types/variant'
import { SequenceCompare } from './SequenceCompare'

export function VariantEvidenceCard({ variant }: { variant: Variant }) {
  return (
    <section className="rounded-card border border-line bg-white p-6 sm:p-7">
      <SequenceCompare variant={variant} />

      <div className="mt-7 rounded-soft border-l-2 border-teal bg-paper px-5 py-4">
        <h3 className="font-mono text-[11px] uppercase tracking-[0.14em] text-teal">
          What this means
        </h3>
        <p className="mt-2 text-sm leading-relaxed text-ink">{variant.explanation}</p>
      </div>

      <p className="mt-5 rounded-soft border border-dashed border-ink-soft/45 px-5 py-4 text-xs leading-relaxed text-ink-soft">
        Pre-counseling triage aid only — not a diagnosis. Review with a genetic
        counselor before any clinical decision.
      </p>
    </section>
  )
}
