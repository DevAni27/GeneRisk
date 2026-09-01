from app.services.report_parser import (
    parse_hbb_report,
)


def test_extract_single_hbs_variant():
    text = """
    Beta Globin (HBB) Sequencing

    PATHOGENIC VARIANT

    Gene: HBB (NM_000518.5)
    Nucleic Acid Change: c.20A>T; Homozygous
    Amino Acid Alteration: p.Glu7Val
    Commonly Known As: Hb S
    """

    result = parse_hbb_report(
        text,
        "hbs-report.pdf",
    )

    assert (
        result.report_type
        == "molecular_genetic"
    )

    assert result.variants_found == 1
    assert result.scorable_variants == 1

    variant = result.variants[0]

    assert variant.gene == "HBB"
    assert variant.hgvs_c == "c.20A>T"
    assert variant.hgvs_p == "p.Glu7Val"

    assert (
        variant.transcript
        == "NM_000518.5"
    )

    assert (
        variant.zygosity
        == "homozygous"
    )

    assert (
        variant.reported_classification
        == "Pathogenic"
    )

    assert (
        variant.common_name
        == "Hb S"
    )

    assert (
        variant.query
        == "HBB c.20A>T"
    )

    assert variant.can_score is True


def test_extract_multiple_hbb_variants():
    text = """
    Beta Globin (HBB) Sequencing

    PATHOGENIC VARIANT
    Gene: HBB (NM_000518.5)
    Nucleic Acid Change: c.20A>T; Heterozygous
    Amino Acid Alteration: p.Glu7Val
    Commonly Known As: Hb S

    PATHOGENIC VARIANT
    Gene: HBB (NM_000518.5)
    Nucleic Acid Change: c.19G>A; Heterozygous
    Amino Acid Alteration: p.Glu7Lys
    Commonly Known As: Hb C
    """

    result = parse_hbb_report(
        text,
        "hbs-hbc.pdf",
    )

    assert result.variants_found == 2
    assert result.scorable_variants == 2

    first = result.variants[0]
    second = result.variants[1]

    assert (
        first.hgvs_c
        == "c.20A>T"
    )

    assert (
        first.hgvs_p
        == "p.Glu7Val"
    )

    assert (
        first.common_name
        == "Hb S"
    )

    assert (
        second.hgvs_c
        == "c.19G>A"
    )

    assert (
        second.hgvs_p
        == "p.Glu7Lys"
    )

    assert (
        second.common_name
        == "Hb C"
    )


def test_fractionation_report_is_not_scored():
    text = """
    Hgb Fractionation Cascade

    Hgb Fractionation by CE:

    Hgb F    0.0 %
    Hgb A   98.0 %
    Hgb A2   2.0 %
    Hgb S    0.0 %

    Interpretation:
    Normal hemoglobin present;
    no hemoglobin variant or
    thalassemia observed.
    """

    result = parse_hbb_report(
        text,
        "fractionation.pdf",
    )

    assert (
        result.report_type
        == "hemoglobin_fractionation"
    )

    assert result.variants_found == 0
    assert result.scorable_variants == 0
    assert result.variants == []


def test_unsupported_indel_is_detected():
    text = """
    Beta Globin (HBB) Sequencing

    PATHOGENIC VARIANT
    Gene: HBB (NM_000518.5)
    Nucleic Acid Change:
    c.27_28insG; Heterozygous
    """

    result = parse_hbb_report(
        text,
        "indel.pdf",
    )

    assert result.variants_found == 1

    variant = result.variants[0]

    assert (
        variant.hgvs_c
        == "c.27_28insG"
    )

    assert variant.can_score is False

    assert (
        variant.reason_not_scorable
        is not None
    )