from app.services.clinvar import (
    build_canonical_spdi,
    find_exact_spdi_record,
    normalize_chromosome_for_clinvar,
)


def test_normalize_chromosome():
    assert normalize_chromosome_for_clinvar("11") == "11"
    assert normalize_chromosome_for_clinvar("chr11") == "11"
    assert normalize_chromosome_for_clinvar("CHR11") == "11"


def test_build_hbs_canonical_spdi():
    spdi = build_canonical_spdi(
        chrom="11",
        position=5227002,
        ref="T",
        alt="A",
    )

    assert (
        spdi
        == "NC_000011.10:5227001:T:A"
    )


def test_exact_spdi_record_is_selected_over_haplotype():
    target_spdi = (
        "NC_000011.10:5227001:T:A"
    )

    records = {
        # Wrong: haplotype containing multiple variants
        "446748": {
            "variation_set": [
                {
                    "canonical_spdi":
                        "NC_000011.10:5227001:T:A"
                },
                {
                    "canonical_spdi":
                        "NC_000011.10:5226900:G:A"
                },
            ],
            "title":
                "HBB haplotype",
        },

        # Correct: exact simple allele
        "15333": {
            "variation_set": [
                {
                    "canonical_spdi":
                        "NC_000011.10:5227001:T:A"
                }
            ],
            "title":
                "NM_000518.5(HBB):c.20A>T (p.Glu7Val)",
        },
    }

    match = find_exact_spdi_record(
        records=records,
        target_spdi=target_spdi,
    )

    assert match is not None

    variation_id, record = match

    assert variation_id == "15333"
    assert (
        record["title"]
        == "NM_000518.5(HBB):c.20A>T (p.Glu7Val)"
    )


def test_no_exact_spdi_returns_none():
    records = {
        "12345": {
            "variation_set": [
                {
                    "canonical_spdi":
                        "NC_000011.10:123:T:C"
                }
            ]
        }
    }

    result = find_exact_spdi_record(
        records=records,
        target_spdi=(
            "NC_000011.10:5227001:T:A"
        ),
    )

    assert result is None