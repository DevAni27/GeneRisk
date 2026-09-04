interface ClinVarInfo {
  status: string;
  variation_id: string | null;
  accession: string | null;
  accession_version: string | null;
  classification: string | null;
  review_status: string | null;
  title: string | null;
}

interface SequenceContext {
  genome: string;
  chrom: string;
  position: number;
  window_start: number;
  window_end: number;
  reference_sequence: string;
  variant_sequence: string;
  variant_index: number;
  ref: string;
  alt: string;
}

interface ResolvedVariant {
  gene: string;
  genome_build: string;
  chrom: string;
  position: number;
  ref: string;
  alt: string;
  input_format: string;
  normalized_hgvs: string | null;
  rsid: string | null;
}

export interface ScoreQueryResponse {
  delta_score: number;
  prediction: "likely_pathogenic" | "likely_benign" | null;
  confidence: number | null;
  calibrated: boolean;
  pathogenicity_index: number | null;
  signal_strength:
    | "strong_pathogenic"
    | "pathogenic_like"
    | "benign_like"
    | "strong_benign"
    | null;
  threshold: number | null;
  clinvar_label: string;
  clinvar: ClinVarInfo;
  explanation: string;
  sequence_context: SequenceContext;
  input_query: string;
  resolved_variant: ResolvedVariant;
}

export async function scoreQuery(query: string): Promise<ScoreQueryResponse> {
  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/score-query`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      typeof error.detail === "string"
        ? error.detail
        : "Unable to analyze this variant."
    );
  }

  return response.json();
}

export interface ExtractedVariant {
  gene: string;
  query: string;
  transcript: string;
  hgvs_c: string;
  hgvs_p: string | null;
  zygosity: string | null;
  reported_classification: string | null;
  common_name: string | null;
  can_score: boolean;
}

export interface ExtractReportResponse {
  report_type: string;
  variants_found: number;
  scorable_variants: number;
  requires_confirmation: boolean;
  variants: ExtractedVariant[];
  message?: string;
}

export async function extractReport(file: File): Promise<ExtractReportResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${process.env.NEXT_PUBLIC_API_URL}/extract-report`,
    {
      method: "POST",
      body: formData,
      // Deliberately no Content-Type header — the browser sets the
      // multipart boundary automatically.
    }
  );

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Unable to read this report."
    );
  }

  return data;
}