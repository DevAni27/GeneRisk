import React from 'react'
import { ClinVarClassification } from '../types/variant'

const STYLES: Record<ClinVarClassification, string> = {
  Pathogenic: 'border-clay/30 bg-clay/10 text-clay',
  'Likely pathogenic': 'border-clay/30 bg-clay/10 text-clay',
  'Uncertain significance': 'border-amber/40 bg-amber/15 text-[#8A6416]',
  'Likely benign': 'border-moss/30 bg-moss/10 text-moss',
  Benign: 'border-moss/30 bg-moss/10 text-moss',
  'Not reported': 'border-line bg-paper text-ink-soft',
}

export function ClinVarBadge({ value }: { value: ClinVarClassification }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 font-mono text-[11px] ${STYLES[value]}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden="true" />
      {value}
    </span>
  )
}
