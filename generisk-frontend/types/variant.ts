export type Verdict = 'pathogenic' | 'benign' | 'uncertain'

export type ClinVarClassification =
  | 'Pathogenic'
  | 'Likely pathogenic'
  | 'Uncertain significance'
  | 'Likely benign'
  | 'Benign'
  | 'Not reported'

export type SignalStrength =
  | 'strong_pathogenic'
  | 'pathogenic_like'
  | 'benign_like'
  | 'strong_benign'
  | null

export interface Variant {
  id: string
  chipLabel: string
  chipNote: string
  gene: string
  chrom: string
  transcript: string
  hgvs: string
  rsid: string | null
  position: string
  refBase: string
  altBase: string

  /** Full variant sequence string, straight from the API's sequence_context.variant_sequence */
  variantSequence: string
  referenceSequence: string
  diffIndex: number
  windowStart: number

  verdict: Verdict
  verdictLabel: string
  clinvar: ClinVarClassification
  explanation: string

  deltaScore: number | null
  threshold: number | null
  calibrated: boolean
  pathogenicityIndex: number | null
  signalStrength: SignalStrength
  confidence: number | null

  clinvarReviewStatus: string
  clinvarAccession: string
  clinvarTitle: string
  clinvarVariationId: string
}