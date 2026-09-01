import asyncio

from fastapi import APIRouter, HTTPException


from app.models.request import (
    ScoreQueryRequest,
    ScoreVariantRequest,
)

from app.models.response import (
    ClinVarInfoResponse,
    ResolvedVariantResponse,
    ScoreQueryResponse,
    ScoreVariantResponse,
    SequenceContextResponse,
)

from app.services.resolver import (
    VariantResolutionError,
    VariantResolutionServiceError,
    resolve_variant_query,
)

from app.services.prediction import (
    PredictionServiceError,
    predict_from_delta,
)

from app.services.clinvar import (
    ClinVarResult,
    ClinVarServiceError,
    lookup_clinvar,
)

from app.services.evo2 import (
    Evo2ServiceError,
    get_evo2_cache_stats,
)

from app.services.scoring import (
    build_display_sequence_context,
    score_variant_with_evo2,
)

from app.services.ucsc import (
    ReferenceAlleleMismatchError,
    UCSCServiceError,
    get_centered_variant_context,
)

from fastapi import (
    File,
    HTTPException,
    UploadFile,
)

from app.models.report import (
    ReportExtractionResponse,
)

from app.services.report_parser import (
    ReportParsingError,
    extract_pdf_text,
    parse_hbb_report,
)


async def safe_lookup_clinvar(
    chrom: str,
    position: int,
    ref: str,
    alt: str,
):
    try:
        return await lookup_clinvar(
            chrom=chrom,
            position=position,
            ref=ref,
            alt=alt,
        )

    except ClinVarServiceError:
        return ClinVarResult(
            status="unavailable",
        )


router = APIRouter()

MAX_REPORT_BYTES = (
    5 * 1024 * 1024
)


@router.post(
    "/extract-report",
    response_model=ReportExtractionResponse,
)
async def extract_report(
    file: UploadFile = File(...),
):
    filename = (
        file.filename
        or "report.pdf"
    )

    is_pdf_name = (
        filename
        .lower()
        .endswith(".pdf")
    )

    is_pdf_content_type = (
        file.content_type
        in {
            "application/pdf",
            "application/x-pdf",
        }
    )

    if not (
        is_pdf_name
        or is_pdf_content_type
    ):
        raise HTTPException(
            status_code=415,
            detail=(
                "Only PDF reports "
                "are currently supported."
            ),
        )

    pdf_bytes = await file.read(
        MAX_REPORT_BYTES + 1
    )

    await file.close()

    if len(pdf_bytes) == 0:
        raise HTTPException(
            status_code=422,
            detail="The uploaded PDF is empty.",
        )

    if (
        len(pdf_bytes)
        > MAX_REPORT_BYTES
    ):
        raise HTTPException(
            status_code=413,
            detail=(
                "PDF is too large. "
                "Maximum file size is 5 MB."
            ),
        )

    # Basic PDF signature validation.
    if (
        b"%PDF-"
        not in pdf_bytes[:1024]
    ):
        raise HTTPException(
            status_code=422,
            detail=(
                "The uploaded file does not "
                "appear to be a valid PDF."
            ),
        )

    try:
        text = extract_pdf_text(
            pdf_bytes
        )

        result = parse_hbb_report(
            text=text,
            filename=filename,
        )

    except ReportParsingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return result

@router.get(
    "/cache-stats",
)
async def cache_stats():
    return get_evo2_cache_stats()


@router.post(
    "/score-variant",
    response_model=ScoreVariantResponse,
)
async def score_variant(
    variant: ScoreVariantRequest,
) -> ScoreVariantResponse:

    try:
        # -------------------------------------------------
        # 1. Get reference sequence from UCSC
        # -------------------------------------------------
        context = await get_centered_variant_context(
            chrom=variant.chrom,
            position=variant.position,
            ref=variant.ref,
            window_size=8192,
        )

        # -------------------------------------------------
        # 2. Run Evo2 and ClinVar simultaneously
        # -------------------------------------------------
        evo_result, clinvar_result = await asyncio.gather(

            score_variant_with_evo2(
                context=context,
                alt=variant.alt,
            ),

            safe_lookup_clinvar(
                chrom=variant.chrom,
                position=variant.position,
                ref=variant.ref,
                alt=variant.alt,
            ),
        )

        # -------------------------------------------------
        # 3. Build small sequence window for frontend
        # -------------------------------------------------
        display_context = build_display_sequence_context(
            context=context,
            alt=variant.alt,
            flank_size=10,
        )

        # -------------------------------------------------
        # 4. Convert Evo2 delta into prediction
        # -------------------------------------------------
        prediction_result = predict_from_delta(
            evo_result.delta_score
        )

    except ReferenceAlleleMismatchError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except UCSCServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Reference genome service error: {exc}"
            ),
        ) from exc

    except Evo2ServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Evo2 service error: {exc}",
        ) from exc

    except PredictionServiceError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Prediction configuration error: {exc}"
            ),
        ) from exc

    # -----------------------------------------------------
    # 5. Convert ClinVar result into display label
    # -----------------------------------------------------

    if (
        clinvar_result.status == "found"
        and clinvar_result.classification
    ):
        clinvar_label = (
            clinvar_result.classification
        )

    elif clinvar_result.status == "unavailable":
        clinvar_label = "Unavailable"

    else:
        clinvar_label = "Not found"

    # -----------------------------------------------------
    # 6. Build final API response
    # -----------------------------------------------------

    return ScoreVariantResponse(

        # REAL Evo2 score
        delta_score=evo_result.delta_score,

        # Calibration-dependent prediction
        prediction=prediction_result.prediction,

        confidence=prediction_result.confidence,

        calibrated=prediction_result.calibrated,
        
        pathogenicity_index=(
            prediction_result.pathogenicity_index
        ),

        signal_strength=(
            prediction_result.signal_strength
        ),

        threshold=(
            prediction_result.threshold
        ),

        # REAL ClinVar data
        clinvar_label=clinvar_label,

        clinvar=ClinVarInfoResponse(
            status=clinvar_result.status,

            variation_id=(
                clinvar_result.variation_id
            ),

            accession=(
                clinvar_result.accession
            ),

            accession_version=(
                clinvar_result.accession_version
            ),

            classification=(
                clinvar_result.classification
            ),

            review_status=(
                clinvar_result.review_status
            ),

            title=(
                clinvar_result.title
            ),
        ),

        explanation=(
            "Evo2 compared the reference and alternate genomic "
            "sequences and the resulting delta score was evaluated "
            "using an HBB-specific calibration threshold. "
            "ClinVar classification is retrieved independently "
            "from NCBI. This result is intended for variant triage "
            "and is not a clinical diagnosis."
        ),

        # REAL sequence data
        sequence_context=SequenceContextResponse(

            genome=context.genome,

            chrom=context.chrom,

            position=context.position,

            window_start=(
                display_context.window_start
            ),

            window_end=(
                display_context.window_end
            ),

            reference_sequence=(
                display_context.reference_sequence
            ),

            variant_sequence=(
                display_context.variant_sequence
            ),

            variant_index=(
                display_context.variant_index
            ),

            ref=display_context.ref,

            alt=display_context.alt,
        ),
    )
    
@router.post(
    "/score-query",
    response_model=ScoreQueryResponse,
)
async def score_query(
    request: ScoreQueryRequest,
) -> ScoreQueryResponse:

    # -------------------------------------------------
    # 1. Understand / normalize user input
    # -------------------------------------------------

    try:
        resolved = await resolve_variant_query(
            request.query
        )

    except VariantResolutionError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except VariantResolutionServiceError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc


    # -------------------------------------------------
    # 2. Feed normalized variant into EXISTING pipeline
    # -------------------------------------------------

    variant_request = ScoreVariantRequest(
        gene=resolved.gene,
        chrom=resolved.chrom,
        position=resolved.position,
        ref=resolved.ref,
        alt=resolved.alt,
    )

    scored = await score_variant(
        variant_request
    )


    # -------------------------------------------------
    # 3. Return normal score + resolution information
    # -------------------------------------------------

    return ScoreQueryResponse(
        **scored.model_dump(),

        input_query=request.query,

        resolved_variant=(
            ResolvedVariantResponse(
                gene=resolved.gene,
                genome_build=(
                    resolved.genome_build
                ),
                chrom=resolved.chrom,
                position=resolved.position,
                ref=resolved.ref,
                alt=resolved.alt,
                input_format=(
                    resolved.input_format
                ),
                normalized_hgvs=(
                    resolved.normalized_hgvs
                ),
                rsid=resolved.rsid,
            )
        ),
    )