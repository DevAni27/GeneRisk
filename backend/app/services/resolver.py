import re
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


# =========================================================
# External services
# =========================================================

NCBI_VARIATION_BASE_URL = (
    "https://api.ncbi.nlm.nih.gov/variation/v0"
)

ENSEMBL_VARIANT_RECODER_URL = (
    "https://rest.ensembl.org/"
    "variant_recoder/human"
)


# =========================================================
# HBB configuration
# =========================================================

HBB_GENE = "HBB"

# RefSeq MANE Select transcript
HBB_TRANSCRIPT = "NM_000518.5"

# Corresponding Ensembl MANE Select transcript
HBB_ENSEMBL_TRANSCRIPT = (
    "ENST00000335295.4"
)

# GRCh38 chromosome 11 RefSeq accession
HBB_GRCH38_REFSEQ = "NC_000011.10"

HBB_CHROM = "11"

GENOME_BUILD = "GRCh38"

# ---------------------------------------------------------
# Verified local HGVS -> GRCh38 fallback mappings
#
# These are NOT model predictions and NOT fake results.
# They are fixed nomenclature mappings for known HBB SNVs.
#
# They are used only when the external HGVS resolver
# cannot provide a result.
# ---------------------------------------------------------

LOCAL_HBB_HGVS_FALLBACKS = {
    "NM_000518.5:C.20A>T": {
        "position": 5227002,
        "ref": "T",
        "alt": "A",
        "rsid": "rs334",
    },

    "NM_000518.5:C.19G>A": {
        "position": 5227003,
        "ref": "C",
        "alt": "T",
        "rsid": "rs33930165",
    },

    # IVS-I-5 variants.
    # HBB is on the reverse strand, therefore the
    # transcript substitutions appear complemented
    # in GRCh38 genomic coordinates.
    "NM_000518.5:C.92+5G>A": {
        "position": 5226925,
        "ref": "C",
        "alt": "T",
        "rsid": None,
    },

    "NM_000518.5:C.92+5G>C": {
        "position": 5226925,
        "ref": "C",
        "alt": "G",
        "rsid": None,
    },

    "NM_000518.5:C.92+5G>T": {
        "position": 5226925,
        "ref": "C",
        "alt": "A",
        "rsid": None,
    },

    # Useful for the ARUP PDF demo.
    "NM_000518.5:C.92+6T>C": {
        "position": 5226924,
        "ref": "A",
        "alt": "G",
        "rsid": "rs35724775",
    },

    "NM_000518.5:C.52A>T": {
        "position": 5226970,
        "ref": "T",
        "alt": "A",
        "rsid": "rs33986703",
    },
}


# =========================================================
# Exceptions
# =========================================================

class VariantResolutionError(ValueError):
    """
    The user input could not be safely resolved.
    """


class VariantResolutionServiceError(
    RuntimeError
):
    """
    An external variant resolution service failed.
    """


# =========================================================
# Result model
# =========================================================

@dataclass(frozen=True)
class ResolvedVariant:
    gene: str
    genome_build: str
    chrom: str
    position: int
    ref: str
    alt: str
    input_format: str

    normalized_hgvs: str | None = None

    rsid: str | None = None


# =========================================================
# Known HBB aliases
# =========================================================

HBB_ALIASES = {

    "hbs": ResolvedVariant(
        gene="HBB",
        genome_build="GRCh38",
        chrom="11",
        position=5227002,
        ref="T",
        alt="A",
        input_format="alias",
        normalized_hgvs=(
            "NM_000518.5:c.20A>T"
        ),
        rsid="rs334",
    ),

    "sickle cell": ResolvedVariant(
        gene="HBB",
        genome_build="GRCh38",
        chrom="11",
        position=5227002,
        ref="T",
        alt="A",
        input_format="alias",
        normalized_hgvs=(
            "NM_000518.5:c.20A>T"
        ),
        rsid="rs334",
    ),
}


# =========================================================
# Legacy HBB notation
# =========================================================

LEGACY_HBB_HGVS = {

    "ivs1-5g>a":
        "NM_000518.5:c.92+5G>A",

    "ivs1-5g>c":
        "NM_000518.5:c.92+5G>C",

    "ivs1-5g>t":
        "NM_000518.5:c.92+5G>T",
}


# =========================================================
# General helpers
# =========================================================

def _resolve_hgvs_locally(
    hgvs: str | None,
    *,
    input_format: str = "hgvs",
) -> ResolvedVariant | None:
    """
    Resolve a small set of verified HBB HGVS variants
    without contacting an external service.

    Used as a reliability fallback only.
    """

    if not hgvs:
        return None

    key = (
        hgvs
        .replace(" ", "")
        .upper()
    )

    mapping = (
        LOCAL_HBB_HGVS_FALLBACKS
        .get(key)
    )

    if mapping is None:
        return None

    return ResolvedVariant(
        gene=HBB_GENE,
        genome_build=GENOME_BUILD,
        chrom=HBB_CHROM,
        position=mapping["position"],
        ref=mapping["ref"],
        alt=mapping["alt"],

        # Keep this as "hgvs" so the frontend does not
        # need to know whether Ensembl or the local
        # fallback resolved it.
        input_format=input_format,

        normalized_hgvs=hgvs,
        rsid=mapping.get("rsid"),
    )

def _normalize_query(
    query: str,
) -> str:

    query = query.strip()

    query = query.replace(
        "→",
        ">",
    )

    query = query.replace(
        "−",
        "-",
    )

    query = query.replace(
        "–",
        "-",
    )

    return query


def _collect_values(
    obj,
    target_key: str,
) -> list[str]:
    """
    Recursively collect values belonging to target_key
    from an arbitrary JSON structure.
    """

    values: list[str] = []

    if isinstance(
        obj,
        dict,
    ):

        for key, value in obj.items():

            if key == target_key:

                if isinstance(
                    value,
                    list,
                ):

                    values.extend(
                        str(item)
                        for item in value
                    )

                elif isinstance(
                    value,
                    str,
                ):

                    values.append(
                        value
                    )

            values.extend(
                _collect_values(
                    value,
                    target_key,
                )
            )

    elif isinstance(
        obj,
        list,
    ):

        for item in obj:

            values.extend(
                _collect_values(
                    item,
                    target_key,
                )
            )

    return values


def _resolved_from_genomic_spdi(
    spdi: dict,
    *,
    input_format: str,
    normalized_hgvs: str | None = None,
    rsid: str | None = None,
) -> ResolvedVariant:
    """
    Convert an NCBI/Ensembl genomic SPDI object into
    the representation used by GeneRisk.

    SPDI positions are 0-based.
    GeneRisk API positions are 1-based.
    """

    seq_id = spdi.get(
        "seq_id"
    )

    if seq_id != HBB_GRCH38_REFSEQ:

        raise VariantResolutionError(
            "The resolved variant does not "
            "map to HBB on GRCh38 "
            "chromosome 11."
        )

    ref = str(
        spdi.get(
            "deleted_sequence",
            "",
        )
    ).upper()

    alt = str(
        spdi.get(
            "inserted_sequence",
            "",
        )
    ).upper()

    # Current GeneRisk model pipeline:
    # SNVs only.
    if (
        len(ref) != 1
        or len(alt) != 1
        or ref not in "ACGT"
        or alt not in "ACGT"
    ):

        raise VariantResolutionError(
            "GeneRisk currently supports "
            "single-nucleotide HBB "
            "variants only."
        )

    if ref == alt:

        raise VariantResolutionError(
            "Reference and alternate "
            "alleles cannot be identical."
        )

    position_0_based = (
        spdi.get(
            "position"
        )
    )

    if not isinstance(
        position_0_based,
        int,
    ):

        raise (
            VariantResolutionServiceError(
                "Variant resolver returned "
                "an invalid genomic position."
            )
        )

    return ResolvedVariant(
        gene=HBB_GENE,
        genome_build=GENOME_BUILD,
        chrom=HBB_CHROM,

        # SPDI = 0-based
        # GeneRisk = 1-based
        position=(
            position_0_based + 1
        ),

        ref=ref,
        alt=alt,

        input_format=input_format,

        normalized_hgvs=(
            normalized_hgvs
        ),

        rsid=rsid,
    )


# =========================================================
# Ensembl Variant Recoder
# =========================================================

async def _resolve_with_ensembl(
    identifier: str,
    *,
    input_format: str,
    normalized_hgvs: str | None = None,
    rsid: str | None = None,
) -> ResolvedVariant:
    """
    Resolve HGVS / variant notation using Ensembl Variant Recoder.

    Reliability behavior:
    - Ensembl remains the primary resolver.
    - If Ensembl cannot be reached, is rate-limited, returns a
      server error, returns invalid JSON, or cannot return a usable
      GRCh38 HBB SNV, GeneRisk silently falls back to a verified
      local HGVS -> GRCh38 mapping when one exists.
    - Unknown variants are NEVER guessed. If the variant is not
      present in the verified local fallback table, the original
      resolver error is raised.
    """

    def try_local_fallback(
        reason: str,
    ) -> ResolvedVariant | None:
        """
        Try the verified local mapping without exposing the
        fallback to the frontend response.

        We log the reason server-side so Render logs still show
        when/why the fallback was used.
        """

        fallback = _resolve_hgvs_locally(
            normalized_hgvs,
            input_format=input_format,
        )

        if fallback is not None:
            logger.warning(
                "Ensembl fallback used for %s "
                "(identifier=%s, reason=%s).",
                normalized_hgvs,
                identifier,
                reason,
            )

        return fallback

    try:
        # Keep this shorter than the general backend timeout so a
        # temporary Ensembl outage does not freeze the live demo
        # before the verified local fallback is attempted.
        timeout = httpx.Timeout(
            8.0,
            connect=4.0,
        )

        async with httpx.AsyncClient(
            timeout=timeout
        ) as client:

            response = await client.post(
                ENSEMBL_VARIANT_RECODER_URL,
                headers={
                    "Content-Type":
                        "application/json",
                    "Accept":
                        "application/json",
                },
                json={
                    "ids": [
                        identifier
                    ]
                },
            )

    except httpx.RequestError as exc:

        fallback = try_local_fallback(
            reason=type(exc).__name__,
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionServiceError(
            "Ensembl variant resolution "
            "service could not be reached."
        ) from exc

    # 429 = rate limited.
    # 5xx = Ensembl / gateway temporarily unavailable.
    if (
        response.status_code == 429
        or response.status_code >= 500
    ):

        fallback = try_local_fallback(
            reason=(
                f"http_{response.status_code}"
            ),
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionServiceError(
            "Ensembl variant resolution "
            "service is temporarily unavailable."
        )

    # For a verified local HGVS mapping, a temporary or unexpected
    # Ensembl 400/404 should not break a known demo/clinical variant.
    if response.status_code in {
        400,
        404,
    }:

        fallback = try_local_fallback(
            reason=(
                f"http_{response.status_code}"
            ),
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionError(
            "Could not resolve variant "
            f"description: {identifier}"
        )

    if response.status_code != 200:

        fallback = try_local_fallback(
            reason=(
                f"http_{response.status_code}"
            ),
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionError(
            "Variant resolution failed for "
            f"{identifier}."
        )

    try:
        payload = response.json()

    except ValueError as exc:

        fallback = try_local_fallback(
            reason="invalid_json",
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionServiceError(
            "Ensembl returned an invalid response."
        ) from exc

    # Ensembl Variant Recoder can return multiple representations.
    # We only keep simple SNV SPDIs on the HBB GRCh38 chromosome.
    spdi_values = _collect_values(
        payload,
        "spdi",
    )

    candidates: list[dict] = []

    for spdi_string in spdi_values:

        parts = spdi_string.split(
            ":",
            3,
        )

        if len(parts) != 4:
            continue

        seq_id = parts[0]

        # Keep only GRCh38 chromosome 11.
        if seq_id != HBB_GRCH38_REFSEQ:
            continue

        try:
            position = int(
                parts[1]
            )

        except ValueError:
            continue

        ref = parts[2].upper()
        alt = parts[3].upper()

        # Current GeneRisk scoring supports SNVs only.
        if (
            len(ref) != 1
            or len(alt) != 1
            or ref not in "ACGT"
            or alt not in "ACGT"
        ):
            continue

        if ref == alt:
            continue

        candidates.append(
            {
                "seq_id":
                    seq_id,
                "position":
                    position,
                "deleted_sequence":
                    ref,
                "inserted_sequence":
                    alt,
            }
        )

    # Remove duplicate representations.
    unique = {}

    for spdi in candidates:

        key = (
            spdi["seq_id"],
            spdi["position"],
            spdi["deleted_sequence"],
            spdi["inserted_sequence"],
        )

        unique[key] = spdi

    candidates = list(
        unique.values()
    )

    if not candidates:

        fallback = try_local_fallback(
            reason="no_supported_grch38_hbb_snv",
        )

        if fallback is not None:
            return fallback

        raise VariantResolutionError(
            "The variant could not be mapped "
            "to a supported HBB GRCh38 SNV."
        )

    if len(candidates) > 1:

        # An exact verified HGVS fallback is safer than guessing
        # among multiple external representations.
        fallback = try_local_fallback(
            reason="multiple_candidates",
        )

        if fallback is not None:
            return fallback

        options = ", ".join(
            (
                f"chr11:"
                f"{candidate['position'] + 1} "
                f"{candidate['deleted_sequence']}>"
                f"{candidate['inserted_sequence']}"
            )
            for candidate in candidates
        )

        raise VariantResolutionError(
            "The input resolves to multiple "
            "possible HBB alleles. "
            "Please specify one allele. "
            f"Possible variants: {options}"
        )

    return _resolved_from_genomic_spdi(
        candidates[0],
        input_format=input_format,
        normalized_hgvs=normalized_hgvs,
        rsid=rsid,
    )


# =========================================================
# HGVS resolver
# =========================================================

async def _resolve_hgvs_via_ensembl(
    hgvs: str,
) -> ResolvedVariant:
    """
    Resolve HBB RefSeq HGVS through the matching
    MANE Select Ensembl transcript.

    Example:

        NM_000518.5:c.92+5G>A

    becomes:

        ENST00000335295.4:c.92+5G>A
    """

    if ":" not in hgvs:

        raise VariantResolutionError(
            "Invalid HBB HGVS description."
        )


    transcript, coding_part = (
        hgvs.split(
            ":",
            1,
        )
    )


    transcript = (
        transcript.upper()
    )


    if transcript != HBB_TRANSCRIPT:

        raise VariantResolutionError(
            "GeneRisk currently supports "
            f"HBB transcript "
            f"{HBB_TRANSCRIPT} only."
        )


    ensembl_hgvs = (
        f"{HBB_ENSEMBL_TRANSCRIPT}:"
        f"{coding_part}"
    )


    return await (
        _resolve_with_ensembl(
            ensembl_hgvs,

            input_format="hgvs",

            # Keep the RefSeq HGVS for the
            # API/frontend display.
            normalized_hgvs=hgvs,
        )
    )


# =========================================================
# dbSNP resolver
# =========================================================

async def _resolve_rsid_via_ncbi(
    rsid: str,
) -> ResolvedVariant:
    """
    Resolve an rsID through NCBI dbSNP.

    We keep NCBI for rsIDs because its RefSNP
    endpoint provides explicit GRCh38 placements.
    """

    rsid = (
        rsid.lower()
    )

    rs_number = (
        rsid.removeprefix(
            "rs"
        )
    )


    if not rs_number.isdigit():

        raise VariantResolutionError(
            f"Invalid dbSNP ID: {rsid}"
        )


    url = (
        f"{NCBI_VARIATION_BASE_URL}"
        f"/refsnp/{rs_number}"
    )


    try:

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:

            response = (
                await client.get(
                    url
                )
            )

    except httpx.RequestError as exc:

        raise (
            VariantResolutionServiceError(
                "dbSNP resolution service "
                "could not be reached."
            )
        ) from exc


    if response.status_code == 404:

        raise VariantResolutionError(
            f"dbSNP variant {rsid} "
            "was not found."
        )


    if response.status_code >= 500:

        raise (
            VariantResolutionServiceError(
                "dbSNP resolution service "
                "is temporarily unavailable."
            )
        )


    if response.status_code != 200:

        raise VariantResolutionError(
            f"Could not resolve {rsid}."
        )


    try:
        payload = response.json()

    except ValueError as exc:

        raise (
            VariantResolutionServiceError(
                "dbSNP returned an invalid "
                "response."
            )
        ) from exc


    primary = payload.get(
        "primary_snapshot_data",
        {},
    )


    placements = primary.get(
        "placements_with_allele",
        [],
    )


    candidate_variants = []


    for placement in placements:

        annotation = (
            placement.get(
                "placement_annot",
                {},
            )
        )


        traits = (
            annotation.get(
                "seq_id_traits_by_assembly",
                [],
            )
        )


        assembly_names = {
            trait.get(
                "assembly_name",
                ""
            )
            for trait in traits
        }


        # Only use GRCh38 placements.
        if not any(
            name.startswith(
                "GRCh38"
            )
            for name in assembly_names
        ):
            continue


        for allele in placement.get(
            "alleles",
            []
        ):

            spdi = (
                allele
                .get(
                    "allele",
                    {}
                )
                .get(
                    "spdi",
                    {}
                )
            )


            if (
                spdi.get(
                    "seq_id"
                )
                != HBB_GRCH38_REFSEQ
            ):
                continue


            ref = str(
                spdi.get(
                    "deleted_sequence",
                    "",
                )
            ).upper()


            alt = str(
                spdi.get(
                    "inserted_sequence",
                    "",
                )
            ).upper()


            # Skip the reference allele.
            if ref == alt:
                continue


            if (
                len(ref) == 1
                and len(alt) == 1
                and ref in "ACGT"
                and alt in "ACGT"
            ):

                candidate_variants.append(
                    spdi
                )


    # Remove duplicates.
    unique = {}


    for spdi in candidate_variants:

        key = (
            spdi[
                "seq_id"
            ],

            spdi[
                "position"
            ],

            spdi[
                "deleted_sequence"
            ],

            spdi[
                "inserted_sequence"
            ],
        )

        unique[key] = spdi


    variants = list(
        unique.values()
    )


    if not variants:

        raise VariantResolutionError(
            f"{rsid} does not resolve "
            "to a supported HBB "
            "GRCh38 SNV."
        )


    # Important:
    # Never guess the ALT allele of a
    # multi-allelic rsID.
    if len(variants) > 1:

        options = ", ".join(
            (
                f"chr11:"
                f"{variant['position'] + 1} "
                f"{variant['deleted_sequence']}>"
                f"{variant['inserted_sequence']}"
            )
            for variant in variants
        )

        raise VariantResolutionError(
            f"{rsid} is multi-allelic. "
            "Please specify one allele. "
            f"Possible variants: {options}"
        )


    return _resolved_from_genomic_spdi(
        variants[0],

        input_format="rsid",

        rsid=rsid,
    )


# =========================================================
# Main flexible query resolver
# =========================================================

async def resolve_variant_query(
    query: str,
) -> ResolvedVariant:
    """
    Accept several human-friendly HBB variant formats
    and normalize them into the canonical representation
    required by the GeneRisk scoring pipeline.

    Supported examples:

        HbS

        rs334

        c.20A>T

        HBB c.20A>T

        NM_000518.5:c.20A>T

        ENST00000335295.4:c.20A>T

        HBB c.92+5G>A (IVS1-5G>A)

        IVS1-5G>A

        chr11:5227002 T>A

        11:5227002:T:A

        5227002 T>A
    """

    query = _normalize_query(
        query
    )


    if not query:

        raise VariantResolutionError(
            "Variant query cannot be empty."
        )


    lowered = (
        query.lower()
    )


    # =====================================================
    # 1. Known aliases
    # =====================================================

    if re.search(
        r"\bhbs\b",
        lowered,
    ):

        return HBB_ALIASES[
            "hbs"
        ]


    if (
        "classic sickle"
        in lowered
    ):

        return HBB_ALIASES[
            "hbs"
        ]


    if (
        lowered.strip()
        == "sickle cell"
    ):

        return HBB_ALIASES[
            "sickle cell"
        ]


    # =====================================================
    # 2. Full RefSeq HGVS
    #
    # NM_000518.5:c.92+5G>A
    # =====================================================

    refseq_hgvs_match = (
        re.search(
            (
                r"(NM_\d+\.\d+)"
                r"\s*:\s*"
                r"(c\.\d+"
                r"(?:[+-]\d+)?"
                r"[ACGT]>"
                r"[ACGT])"
            ),
            query,
            re.IGNORECASE,
        )
    )


    if refseq_hgvs_match:

        transcript = (
            refseq_hgvs_match
            .group(1)
            .upper()
        )


        if transcript != HBB_TRANSCRIPT:

            raise VariantResolutionError(
                "GeneRisk currently supports "
                f"HBB transcript "
                f"{HBB_TRANSCRIPT} only."
            )


        coding_hgvs = (
            refseq_hgvs_match
            .group(2)
        )


        normalized_hgvs = (
            f"{HBB_TRANSCRIPT}:"
            f"{coding_hgvs}"
        )


        return await (
            _resolve_hgvs_via_ensembl(
                normalized_hgvs
            )
        )


    # =====================================================
    # 3. Full Ensembl transcript HGVS
    #
    # ENST00000335295.4:c.92+5G>A
    # =====================================================

    ensembl_hgvs_match = (
        re.search(
            (
                r"(ENST\d+\.\d+)"
                r"\s*:\s*"
                r"(c\.\d+"
                r"(?:[+-]\d+)?"
                r"[ACGT]>"
                r"[ACGT])"
            ),
            query,
            re.IGNORECASE,
        )
    )


    if ensembl_hgvs_match:

        transcript = (
            ensembl_hgvs_match
            .group(1)
            .upper()
        )


        if (
            transcript
            != HBB_ENSEMBL_TRANSCRIPT
        ):

            raise VariantResolutionError(
                "GeneRisk currently supports "
                "the HBB MANE Select "
                f"transcript "
                f"{HBB_ENSEMBL_TRANSCRIPT} "
                "only."
            )


        coding_hgvs = (
            ensembl_hgvs_match
            .group(2)
        )


        normalized_refseq = (
            f"{HBB_TRANSCRIPT}:"
            f"{coding_hgvs}"
        )


        return await (
            _resolve_with_ensembl(
                (
                    f"{HBB_ENSEMBL_TRANSCRIPT}:"
                    f"{coding_hgvs}"
                ),

                input_format="hgvs",

                normalized_hgvs=(
                    normalized_refseq
                ),
            )
        )


    # =====================================================
    # 4. HBB / bare c. notation
    #
    # HBB c.92+5G>A (IVS1-5G>A)
    #
    # c.92+5G>A
    # =====================================================

    coding_match = re.search(
        (
            r"(c\.\d+"
            r"(?:[+-]\d+)?"
            r"[ACGT]>"
            r"[ACGT])"
        ),
        query,
        re.IGNORECASE,
    )


    if coding_match:

        # If somebody explicitly typed another gene,
        # do not silently treat it as HBB.
        gene_match = re.search(
            (
                r"\b([A-Za-z0-9-]+)"
                r"\s+"
                r"c\."
            ),
            query,
            re.IGNORECASE,
        )


        if gene_match:

            gene = (
                gene_match
                .group(1)
                .upper()
            )


            if gene != HBB_GENE:

                raise VariantResolutionError(
                    "GeneRisk currently "
                    "supports HBB only."
                )


        coding_hgvs = (
            coding_match
            .group(1)
        )


        normalized_hgvs = (
            f"{HBB_TRANSCRIPT}:"
            f"{coding_hgvs}"
        )


        return await (
            _resolve_hgvs_via_ensembl(
                normalized_hgvs
            )
        )


    # =====================================================
    # 5. Legacy HBB IVS notation
    #
    # IVS1-5G>A
    # =====================================================

    compact = re.sub(
        r"\s+",
        "",
        lowered,
    )


    for alias, hgvs in (
        LEGACY_HBB_HGVS.items()
    ):

        if alias in compact:

            return await (
                _resolve_hgvs_via_ensembl(
                    hgvs
                )
            )


    # =====================================================
    # 6. rsID
    #
    # rs334
    # =====================================================

    rs_match = re.search(
        r"\brs\d+\b",
        lowered,
    )


    if rs_match:

        return await (
            _resolve_rsid_via_ncbi(
                rs_match.group(0)
            )
        )


    # =====================================================
    # 7. Explicit genomic notation
    #
    # chr11:5226925 C>T
    #
    # 11:5226925:C:T
    #
    # chr11-5226925-C-T
    # =====================================================

    genomic_match = re.search(
        (
            r"(?:chr)?11"
            r"\s*[:\-\s]\s*"
            r"([\d,]+)"
            r"\s*[:\-\s]\s*"
            r"([ACGT])"
            r"\s*(?:>|:|-|/)\s*"
            r"([ACGT])"
        ),
        query,
        re.IGNORECASE,
    )


    if genomic_match:

        position = int(
            genomic_match
            .group(1)
            .replace(
                ",",
                "",
            )
        )


        ref = (
            genomic_match
            .group(2)
            .upper()
        )


        alt = (
            genomic_match
            .group(3)
            .upper()
        )


        if ref == alt:

            raise VariantResolutionError(
                "Reference and alternate "
                "alleles cannot be identical."
            )


        return ResolvedVariant(
            gene="HBB",
            genome_build="GRCh38",
            chrom="11",
            position=position,
            ref=ref,
            alt=alt,
            input_format="genomic",
        )


    # =====================================================
    # 8. Genomic HBB position without chromosome
    #
    # 5226925 C>T
    # =====================================================

    position_only_match = re.search(
        (
            r"\b([\d,]{7,})"
            r"\s+"
            r"([ACGT])"
            r"\s*>\s*"
            r"([ACGT])"
            r"\b"
        ),
        query,
        re.IGNORECASE,
    )


    if position_only_match:

        position = int(
            position_only_match
            .group(1)
            .replace(
                ",",
                "",
            )
        )


        ref = (
            position_only_match
            .group(2)
            .upper()
        )


        alt = (
            position_only_match
            .group(3)
            .upper()
        )


        if ref == alt:

            raise VariantResolutionError(
                "Reference and alternate "
                "alleles cannot be identical."
            )


        return ResolvedVariant(
            gene="HBB",
            genome_build="GRCh38",
            chrom="11",

            position=position,

            ref=ref,

            alt=alt,

            input_format=(
                "genomic_inferred_hbb"
            ),
        )


    # =====================================================
    # 9. Unsupported / ambiguous input
    # =====================================================

    if "c." in lowered:

        raise VariantResolutionError(
            "The query looks like HGVS "
            "notation, but GeneRisk could "
            "not safely parse it. "
            "Try formats such as "
            "'c.20A>T' or "
            "'c.92+5G>A'."
        )


    if "ivs" in lowered:

        raise VariantResolutionError(
            "GeneRisk recognized legacy IVS "
            "notation but could not safely "
            "resolve this variant. "
            "Try the equivalent HBB c. "
            "notation if available."
        )


    raise VariantResolutionError(
        "GeneRisk could not safely understand "
        "this variant. Try an HBB HGVS "
        "variant, genomic coordinate, rsID, "
        "or known HBB alias."
    )