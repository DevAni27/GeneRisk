

import React from 'react'
import { Variant } from '../types/variant'

interface SequenceCompareProps {
  variant: Variant
}

function Track({
  label,
  sequence,
  diffIndex,
  emphasise,
}: {
  label: string
  sequence: string
  diffIndex: number
  emphasise: boolean
}) {
  return (
    <div className="flex items-center gap-4">
      <span className="w-20 shrink-0 font-mono text-[11px] uppercase tracking-[0.12em] text-ink-soft">
        {label}
      </span>
      <div className="flex gap-[3px] overflow-x-auto font-mono text-sm">
        {sequence.split('').map((base, index) => {
          const isDiff = index === diffIndex
          return (
            <span
              key={`${label}-${index}`}
              className={`flex h-8 w-6 shrink-0 items-center justify-center rounded-[4px] ${
                isDiff
                  ? emphasise
                    ? 'bg-amber font-semibold text-ink'
                    : 'bg-amber/25 font-semibold text-ink'
                  : 'bg-paper text-ink-soft'
              }`}
            >
              {base}
            </span>
          )
        })}
      </div>
    </div>
  )
}

export function SequenceCompare({ variant }: SequenceCompareProps) {
  const variantSequence =
    variant.referenceSequence.slice(0, variant.diffIndex) +
    variant.altBase +
    variant.referenceSequence.slice(variant.diffIndex + 1)

  return (
    <div>
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h3 className="text-sm font-semibold text-ink">Sequence comparison</h3>
        <p className="font-mono text-xs text-ink-soft">
          {variant.position} · {variant.refBase}&gt;{variant.altBase}
        </p>
      </div>

      <div className="mt-4 space-y-2">
        <Track
          label="Reference"
          sequence={variant.referenceSequence}
          diffIndex={variant.diffIndex}
          emphasise={false}
        />
        <Track
          label="Variant"
          sequence={variantSequence}
          diffIndex={variant.diffIndex}
          emphasise
        />
      </div>

      <p className="mt-3 pl-24 font-mono text-[11px] text-ink-soft">
        Window {variant.windowStart.toLocaleString('en-US')}–
        {(variant.windowStart + variant.referenceSequence.length - 1).toLocaleString('en-US')}
        {' · '}
        single-base substitution at offset {variant.diffIndex + 1}
      </p>
    </div>
  )
}
