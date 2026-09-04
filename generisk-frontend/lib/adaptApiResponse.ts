import { Variant, Verdict, ClinVarClassification } from "@/types/variant";
import { ScoreQueryResponse } from "@/lib/api";

const CLINVAR_MAP: Record<string, ClinVarClassification> = {
  Pathogenic: "Pathogenic",
  "Likely pathogenic": "Likely pathogenic",
  Benign: "Benign",
  "Likely benign": "Likely benign",
  "Uncertain significance": "Uncertain significance",
  VUS: "Uncertain significance",
  "Not found": "Not reported",
  "Not reported": "Not reported",
};

export function adaptApiResponse(api: ScoreQueryResponse): Variant {
  const verdict: Verdict =
    api.prediction === "likely_pathogenic"
      ? "pathogenic"
      : api.prediction === "likely_benign"
      ? "benign"
      : "uncertain";

  const clinvarClassificationRaw =
    api.clinvar?.classification ?? api.clinvar_label ?? "Not reported";

  const rv = api.resolved_variant;
  const sc = api.sequence_context;

  return {
    id: `${rv.chrom}-${rv.position}-${rv.ref}-${rv.alt}`,
    chipLabel: rv.normalized_hgvs || api.input_query,
    chipNote: "",
    gene: rv.gene,
    chrom: rv.chrom,
    transcript: "",
    hgvs: rv.normalized_hgvs || api.input_query,
    rsid: rv.rsid,
    position: `chr${rv.chrom}:${rv.position.toLocaleString()}`,
    refBase: rv.ref,
    altBase: rv.alt,

    variantSequence: sc.variant_sequence,
    referenceSequence: sc.reference_sequence,
    diffIndex: sc.variant_index,
    windowStart: sc.window_start,

    verdict,
    verdictLabel:
      verdict === "pathogenic"
        ? "Likely pathogenic"
        : verdict === "benign"
        ? "Likely benign"
        : "Uncertain significance",

    deltaScore: api.delta_score,
    threshold: api.threshold,
    calibrated: api.calibrated,
    pathogenicityIndex: api.pathogenicity_index,
    signalStrength: api.signal_strength,
    confidence: api.confidence,

    clinvar: CLINVAR_MAP[clinvarClassificationRaw] ?? "Not reported",
    clinvarReviewStatus: api.clinvar?.review_status ?? "",
    clinvarAccession:
      api.clinvar?.accession_version ?? api.clinvar?.accession ?? "",
    clinvarTitle: api.clinvar?.title ?? "",
    clinvarVariationId: api.clinvar?.variation_id ?? "",

    explanation: api.explanation,
  };
}