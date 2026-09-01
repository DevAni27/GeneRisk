from io import BytesIO
import re

from pypdf import PdfReader

from app.models.report import (
    ReportExtractionResponse,
    ReportVariantCandidate,
)


MAX_PDF_PAGES = 25


class ReportParsingError(Exception):
    pass


# ---------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------

# Matches examples such as:
#
# c.20A>T
# c.92+5G>A
# c.19G>A
# c.27_28insG
# c.51delC
#
# We detect some unsupported variant types too so that
# we can tell the user why they cannot currently be scored.
HGVS_C_RE = re.compile(
    r"\bc\.\s*\d+(?:[+-]\d+)?"
    r"(?:_\d+(?:[+-]\d+)?)?\s*"
    r"(?:"
    r"[ACGT]\s*>\s*[ACGT]"
    r"|delins\s*[ACGT]+"
    r"|del\s*[ACGT]*"
    r"|dup\s*[ACGT]*"
    r"|ins\s*[ACGT]+"
    r")\b",
    re.IGNORECASE,
)


# Current GeneRisk resolver/scoring pipeline:
# substitution SNVs only.
SUPPORTED_SNV_RE = re.compile(
    r"^c\.\d+(?:[+-]\d+)?[ACGT]>[ACGT]$",
    re.IGNORECASE,
)


HBB_TRANSCRIPT_RE = re.compile(
    r"\bNM_000518(?:\.\d+)?\b",
    re.IGNORECASE,
)


PROTEIN_RE = re.compile(
    r"\bp\.\(?"
    r"[A-Za-z]{1,3}"
    r"\d+"
    r"(?:[A-Za-z]{1,3}|Ter|\*|=)"
    r"\)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------
# PDF text extraction
# ---------------------------------------------------------

def extract_pdf_text(
    pdf_bytes: bytes,
) -> str:
    """
    Extract machine-readable text from a PDF.

    The PDF is processed in memory only.
    It is not written to disk.
    """

    try:
        reader = PdfReader(
            BytesIO(pdf_bytes)
        )
    except Exception as exc:
        raise ReportParsingError(
            "The uploaded file could not be read as a PDF."
        ) from exc

    if reader.is_encrypted:
        raise ReportParsingError(
            "Encrypted or password-protected PDFs "
            "are not currently supported."
        )

    if len(reader.pages) > MAX_PDF_PAGES:
        raise ReportParsingError(
            f"PDFs may contain at most "
            f"{MAX_PDF_PAGES} pages."
        )

    page_text = []

    for page in reader.pages:
        try:
            text = (
                page.extract_text()
                or ""
            )
        except Exception:
            text = ""

        page_text.append(text)

    full_text = "\n".join(
        page_text
    )

    # Check whether useful text exists.
    non_whitespace = re.sub(
        r"\s+",
        "",
        full_text,
    )

    if len(non_whitespace) < 20:
        raise ReportParsingError(
            "No machine-readable text was found in this PDF. "
            "It may be a scanned/image-only report. "
            "OCR is not currently supported."
        )

    return full_text


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _clean_text(
    text: str,
) -> str:
    return (
        text
        .replace("→", ">")
        .replace("−", "-")
        .replace("–", "-")
    )


def _normalize_hgvs_c(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        "",
        value,
    )


def _extract_classification(
    context: str,
) -> str | None:

    classifications = (
        (
            "Likely Pathogenic",
            r"\blikely\s+pathogenic\b",
        ),
        (
            "Likely Benign",
            r"\blikely\s+benign\b",
        ),
        (
            "Pathogenic",
            r"\bpathogenic\b",
        ),
        (
            "Benign",
            r"\bbenign\b",
        ),
        (
            "VUS",
            (
                r"\b(?:"
                r"variant\s+of\s+uncertain\s+significance"
                r"|uncertain\s+significance"
                r"|VUS"
                r")\b"
            ),
        ),
    )

    for label, pattern in classifications:
        if re.search(
            pattern,
            context,
            re.IGNORECASE,
        ):
            return label

    return None


def _extract_zygosity(
    context: str,
) -> str | None:

    for value in (
        "homozygous",
        "heterozygous",
        "hemizygous",
    ):
        if re.search(
            rf"\b{value}\b",
            context,
            re.IGNORECASE,
        ):
            return value

    return None


def _extract_protein_change(
    context: str,
) -> str | None:

    match = PROTEIN_RE.search(
        context
    )

    if not match:
        return None

    return match.group(0)


def _extract_common_name(
    context: str,
) -> str | None:
    """
    Prefer structured lines like:

    Commonly Known As: Hb S
    """

    match = re.search(
        (
            r"Commonly\s+Known\s+As"
            r"\s*:\s*"
            r"(Hb\s+[A-Za-z0-9-]+)"
        ),
        context,
        re.IGNORECASE,
    )

    if not match:
        return None

    return " ".join(
        match
        .group(1)
        .split()
    )


def _detect_report_type(
    text: str,
    has_variants: bool,
) -> str:

    hbb_present = bool(
        re.search(
            r"\bHBB\b|NM_000518",
            text,
            re.IGNORECASE,
        )
    )

    molecular_keywords = bool(
        re.search(
            (
                r"\b(?:"
                r"sequencing"
                r"|molecular genetic"
                r"|nucleic acid change"
                r"|massively parallel sequencing"
                r")\b"
            ),
            text,
            re.IGNORECASE,
        )
    )

    fractionation_keywords = bool(
        re.search(
            (
                r"\b(?:"
                r"hgb fractionation"
                r"|hemoglobin fractionation"
                r"|electrophoresis"
                r"|HPLC"
                r"|Hb A2"
                r"|Hb F"
                r")\b"
            ),
            text,
            re.IGNORECASE,
        )
    )

    if (
        has_variants
        or (
            hbb_present
            and molecular_keywords
        )
    ):
        return "molecular_genetic"

    if fractionation_keywords:
        return "hemoglobin_fractionation"

    return "unknown"


# ---------------------------------------------------------
# Main report parser
# ---------------------------------------------------------

def parse_hbb_report(
    text: str,
    filename: str,
) -> ReportExtractionResponse:

    text = _clean_text(
        text
    )

    matches = list(
        HGVS_C_RE.finditer(
            text
        )
    )

    global_transcripts = list(
        dict.fromkeys(
            match.group(0).upper()
            for match
            in HBB_TRANSCRIPT_RE.finditer(
                text
            )
        )
    )

    variants: list[
        ReportVariantCandidate
    ] = []

    seen_variants: set[str] = set()

    for index, match in enumerate(
        matches
    ):

        hgvs_c = _normalize_hgvs_c(
            match.group(0)
        )

        dedupe_key = (
            hgvs_c.upper()
        )

        if dedupe_key in seen_variants:
            continue

        # Look immediately before the variant for:
        # Gene, transcript, classification etc.
        before = text[
            max(
                0,
                match.start() - 400,
            ):
            match.start()
        ]

        # Stop at the next HGVS variant so information
        # from another variant does not leak into this one.
        if index + 1 < len(matches):
            next_start = (
                matches[
                    index + 1
                ].start()
            )
        else:
            next_start = min(
                len(text),
                match.end() + 700,
            )

        after = text[
            match.end():
            next_start
        ]

        gene_context = (
            before[-350:]
            + match.group(0)
            + after[:200]
        )

        # Do not interpret random c. notation from another
        # gene in a large genetic panel as HBB.
        if not re.search(
            r"\bHBB\b|NM_000518",
            gene_context,
            re.IGNORECASE,
        ):
            continue

        seen_variants.add(
            dedupe_key
        )

        # Prefer transcript close to the variant.
        transcript_matches = list(
            HBB_TRANSCRIPT_RE.finditer(
                before[-350:]
            )
        )

        transcript = None

        if transcript_matches:
            transcript = (
                transcript_matches[-1]
                .group(0)
                .upper()
            )

        elif len(global_transcripts) == 1:
            transcript = (
                global_transcripts[0]
            )

        # Information occurring after the HGVS entry
        # normally belongs to this variant.
        variant_after_context = (
            after[:500]
        )

        hgvs_p = (
            _extract_protein_change(
                variant_after_context
            )
        )

        zygosity = (
            _extract_zygosity(
                after[:180]
            )
        )

        common_name = (
            _extract_common_name(
                variant_after_context
            )
        )

        # Classification normally appears just before
        # "Gene: HBB" / "Nucleic Acid Change".
        classification = (
            _extract_classification(
                before[-250:]
            )
        )

        can_score = bool(
            SUPPORTED_SNV_RE.fullmatch(
                hgvs_c
            )
        )

        if can_score:
            reason_not_scorable = None
        else:
            reason_not_scorable = (
                "GeneRisk currently scores "
                "single-nucleotide HBB variants only."
            )

        variants.append(
            ReportVariantCandidate(
                gene="HBB",

                # Deliberately use the same human-readable
                # input accepted by your existing resolver.
                query=f"HBB {hgvs_c}",

                transcript=transcript,
                hgvs_c=hgvs_c,
                hgvs_p=hgvs_p,
                zygosity=zygosity,
                reported_classification=classification,
                common_name=common_name,
                can_score=can_score,
                reason_not_scorable=reason_not_scorable,
            )
        )

    scorable_count = sum(
        1
        for variant in variants
        if variant.can_score
    )

    report_type = (
        _detect_report_type(
            text=text,
            has_variants=bool(
                variants
            ),
        )
    )

    if scorable_count > 0:

        message = (
            f"Found {len(variants)} explicit "
            f"HBB variant(s); "
            f"{scorable_count} can currently "
            "be analyzed by GeneRisk. "
            "Confirm a variant before scoring."
        )

    elif variants:

        message = (
            "Explicit HBB variant(s) were found, "
            "but none are supported by the current "
            "SNV-only GeneRisk scoring pipeline."
        )

    elif (
        report_type
        == "hemoglobin_fractionation"
    ):

        message = (
            "This appears to be a hemoglobin "
            "fractionation/electrophoresis report. "
            "No explicit HBB DNA variant was found, "
            "so Evo2 scoring cannot be run from "
            "this report."
        )

    elif (
        report_type
        == "molecular_genetic"
    ):

        message = (
            "This appears to be an HBB molecular "
            "genetic report, but no explicit HBB "
            "DNA variant was found."
        )

    else:

        message = (
            "No explicit HBB DNA variant was "
            "found in this PDF."
        )

    return ReportExtractionResponse(
        filename=filename,
        report_type=report_type,
        variants_found=len(
            variants
        ),
        scorable_variants=(
            scorable_count
        ),
        requires_confirmation=True,
        variants=variants,
        message=message,
    )