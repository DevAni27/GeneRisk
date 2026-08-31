import argparse
import asyncio
import csv
from pathlib import Path

from app.services.evo2 import Evo2ServiceError
from app.services.scoring import score_variant_with_evo2
from app.services.ucsc import (
    ReferenceAlleleMismatchError,
    UCSCServiceError,
    get_centered_variant_context,
)


REQUIRED_COLUMNS = {
    "chrom",
    "position",
    "ref",
    "alt",
    "clinical_label",
    "source",
}


OUTPUT_COLUMNS = [
    "reference_score",
    "variant_score",
    "delta_score",
    "window_size",
    "score_status",
    "score_error",
]


def normalize_chromosome(chrom: str) -> str:
    chrom = chrom.strip()

    if chrom.lower().startswith("chr"):
        chrom = chrom[3:]

    return chrom


def variant_key(row: dict[str, str]) -> str:
    return (
        f"{normalize_chromosome(row['chrom'])}:"
        f"{row['position'].strip()}:"
        f"{row['ref'].strip().upper()}:"
        f"{row['alt'].strip().upper()}"
    )


def validate_columns(
    fieldnames: list[str] | None,
) -> None:

    if not fieldnames:
        raise ValueError(
            "Input CSV has no header."
        )

    missing = (
        REQUIRED_COLUMNS
        - set(fieldnames)
    )

    if missing:
        raise ValueError(
            "Input CSV is missing required columns: "
            + ", ".join(sorted(missing))
        )


def validate_duplicates(
    rows: list[dict[str, str]],
) -> None:

    seen: set[str] = set()
    duplicates: set[str] = set()

    for row in rows:
        key = variant_key(row)

        if key in seen:
            duplicates.add(key)

        seen.add(key)

    if duplicates:
        raise ValueError(
            (
                "Duplicate genomic variants found. "
                "Please deduplicate the validation dataset first: "
                + ", ".join(sorted(duplicates))
            )
        )


async def score_row(
    row: dict[str, str],
) -> dict[str, str]:

    output = dict(row)

    try:
        gene = (
            row.get("gene", "HBB")
            .strip()
            .upper()
        )

        genome_build = (
            row.get(
                "genome_build",
                "GRCh38",
            )
            .strip()
        )

        chrom = normalize_chromosome(
            row["chrom"]
        )

        position = int(
            row["position"]
        )

        ref = (
            row["ref"]
            .strip()
            .upper()
        )

        alt = (
            row["alt"]
            .strip()
            .upper()
        )

        # -----------------------------------------
        # Safety checks
        # -----------------------------------------

        if gene != "HBB":
            raise ValueError(
                (
                    "Current GeneRisk validation "
                    f"supports HBB only, got {gene}."
                )
            )

        if genome_build not in {
            "GRCh38",
            "hg38",
        }:
            raise ValueError(
                (
                    "Current backend expects GRCh38/hg38, "
                    f"got {genome_build}."
                )
            )

        if len(ref) != 1 or len(alt) != 1:
            output.update(
                {
                    "reference_score": "",
                    "variant_score": "",
                    "delta_score": "",
                    "window_size": "",
                    "score_status":
                        "skipped_non_snv",
                    "score_error":
                        (
                            "Current batch pipeline "
                            "is restricted to SNVs."
                        ),
                }
            )

            return output

        if ref == alt:
            raise ValueError(
                "REF and ALT cannot be identical."
            )

        # -----------------------------------------
        # Fetch hg38 reference window
        # -----------------------------------------

        context = (
            await get_centered_variant_context(
                chrom=chrom,
                position=position,
                ref=ref,
                window_size=8192,
            )
        )

        # -----------------------------------------
        # Score reference + alternate with Evo2
        # -----------------------------------------

        result = await score_variant_with_evo2(
            context=context,
            alt=alt,
        )

        output.update(
            {
                "reference_score":
                    str(result.reference_score),

                "variant_score":
                    str(result.variant_score),

                "delta_score":
                    str(result.delta_score),

                "window_size":
                    str(result.window_size),

                "score_status":
                    "success",

                "score_error":
                    "",
            }
        )

    except (
        ValueError,
        ReferenceAlleleMismatchError,
        UCSCServiceError,
        Evo2ServiceError,
    ) as exc:

        output.update(
            {
                "reference_score": "",
                "variant_score": "",
                "delta_score": "",
                "window_size": "",
                "score_status": "error",
                "score_error": str(exc),
            }
        )

    return output


async def run_batch(
    input_path: Path,
    output_path: Path,
    delay_seconds: float,
    limit: int | None,
) -> None:

    # ---------------------------------------------
    # Read input
    # ---------------------------------------------

    with input_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:

        reader = csv.DictReader(file)

        validate_columns(
            reader.fieldnames
        )

        rows = list(reader)

        input_columns = (
            reader.fieldnames or []
        )

    if not rows:
        raise ValueError(
            "Input CSV contains no variants."
        )

    validate_duplicates(rows)

    if limit is not None:
        rows = rows[:limit]

    output_columns = (
        input_columns
        + [
            column
            for column in OUTPUT_COLUMNS
            if column not in input_columns
        ]
    )

    print()
    print(
        f"Input variants: {len(rows)}"
    )

    print(
        f"Output: {output_path}"
    )

    print()

    # ---------------------------------------------
    # Score sequentially
    # ---------------------------------------------

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=output_columns,
        )

        writer.writeheader()

        total = len(rows)

        for index, row in enumerate(
            rows,
            start=1,
        ):

            key = variant_key(row)

            print(
                f"[{index}/{total}] "
                f"Scoring {key}..."
            )

            result = await score_row(
                row
            )

            writer.writerow(
                result
            )

            # Flush every row so progress is not
            # lost if the process stops midway.
            file.flush()

            status = result.get(
                "score_status"
            )

            if status == "success":
                print(
                    "    delta_score =",
                    result["delta_score"],
                )

            else:
                print(
                    "    status =",
                    status,
                )

                print(
                    "    reason =",
                    result.get(
                        "score_error",
                        "",
                    ),
                )

            # Each SNV requires two Evo2 calls.
            # Be conservative with the hosted API.
            if (
                index < total
                and delay_seconds > 0
            ):
                await asyncio.sleep(
                    delay_seconds
                )

    print()
    print("Batch scoring complete.")
    print(
        f"Saved to: {output_path}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Batch-score HBB variants with Evo2."
        )
    )

    parser.add_argument(
        "input_csv",
        type=Path,
        help="Input validation CSV.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output scored CSV.",
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=3.5,
        help=(
            "Delay in seconds between variants. "
            "Default: 3.5"
        ),
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help=(
            "Score only the first N rows. "
            "Useful for smoke testing."
        ),
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    input_path: Path = args.input_csv

    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}"
        )

    output_path = args.output

    if output_path is None:
        output_path = input_path.with_name(
            (
                input_path.stem
                + "_scored.csv"
            )
        )

    await run_batch(
        input_path=input_path,
        output_path=output_path,
        delay_seconds=args.delay,
        limit=args.limit,
    )


if __name__ == "__main__":
    asyncio.run(main())