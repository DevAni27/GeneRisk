

import React from 'react'

interface ToggleRowProps {
  id: string
  label: string
  description: string
  checked: boolean
  onChange: (next: boolean) => void
}

export function ToggleRow({
  id,
  label,
  description,
  checked,
  onChange,
}: ToggleRowProps) {
  return (
    <div className="flex items-start justify-between gap-6 border-b border-line py-4 last:border-b-0">
      <div className="min-w-0">
        <label
          htmlFor={id}
          className="block text-sm font-medium text-ink"
        >
          {label}
        </label>
        <p className="mt-1 text-xs leading-relaxed text-ink-soft">{description}</p>
      </div>

      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        onClick={() => onChange(!checked)}
        className={`relative mt-0.5 h-6 w-11 shrink-0 rounded-full border transition-colors duration-150 ease-out focus:outline-none focus-visible:ring-2 focus-visible:ring-teal/40 focus-visible:ring-offset-2 focus-visible:ring-offset-white ${
          checked ? 'border-teal bg-teal' : 'border-line bg-paper'
        }`}
      >
        <span
          className={`absolute top-1/2 h-4 w-4 -translate-y-1/2 rounded-full transition-[left,background-color] duration-150 ease-out ${
            checked ? 'left-[1.5rem] bg-white' : 'left-[0.2rem] bg-ink-soft/50'
          }`}
        />
      </button>
    </div>
  )
}
