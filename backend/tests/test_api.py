from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200

    assert response.json() == {
        "status": "healthy",
        "service": "GeneRisk API",
        "version": "0.1.0",
        "genome_build": "hg38",
    }


def test_score_variant_endpoint(monkeypatch):

    async def fake_get_centered_variant_context(
        chrom,
        position,
        ref,
        window_size,
    ):
        return SimpleNamespace(
            genome="hg38",
            chrom="chr11",
            position=5227002,
            ref="T",
        )

    async def fake_score_variant_with_evo2(
        context,
        alt,
    ):
        return SimpleNamespace(
            delta_score=-0.001635491940367606,
        )

    async def fake_lookup_clinvar(
        chrom,
        position,
        ref,
        alt,
    ):
        return SimpleNamespace(
            status="found",
            classification="Pathogenic",
            variation_id="15333",
            accession="VCV000015333",
            accession_version="VCV000015333.180",
            review_status=(
                "criteria provided, multiple submitters, no conflicts"
            ),
            title="NM_000518.5(HBB):c.20A>T (p.Glu7Val)",
        )

    def fake_build_display_sequence_context(
        context,
        alt,
        flank_size,
    ):
        return SimpleNamespace(
            window_start=5226991,
            window_end=5227012,
            reference_sequence="AGACTTCTCCTCAGGAGTCAG",
            variant_sequence="AGACTTCTCCACAGGAGTCAG",
            variant_index=10,
            ref="T",
            alt="A",
        )

    monkeypatch.setattr(
        "app.api.routes.get_centered_variant_context",
        fake_get_centered_variant_context,
    )

    monkeypatch.setattr(
        "app.api.routes.score_variant_with_evo2",
        fake_score_variant_with_evo2,
    )

    monkeypatch.setattr(
        "app.api.routes.lookup_clinvar",
        fake_lookup_clinvar,
    )

    monkeypatch.setattr(
        "app.api.routes.build_display_sequence_context",
        fake_build_display_sequence_context,
    )

    payload = {
        "gene": "HBB",
        "chrom": "11",
        "position": 5227002,
        "ref": "T",
        "alt": "A",
    }

    response = client.post(
        "/score-variant",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["delta_score"] == -0.001635491940367606
    assert data["clinvar_label"] == "Pathogenic"
    assert data["clinvar"]["variation_id"] == "15333"
    assert data["sequence_context"]["ref"] == "T"
    assert data["sequence_context"]["alt"] == "A"
    
def test_score_variant_survives_clinvar_failure(
    monkeypatch,
):
    async def fake_context(
        chrom,
        position,
        ref,
        window_size,
    ):
        return SimpleNamespace(
            genome="hg38",
            chrom="chr11",
            position=5227002,
            ref="T",
        )

    async def fake_evo(
        context,
        alt,
    ):
        return SimpleNamespace(
            delta_score=-0.001,
        )

    async def broken_clinvar(
        chrom,
        position,
        ref,
        alt,
    ):
        from app.services.clinvar import (
            ClinVarServiceError,
        )

        raise ClinVarServiceError(
            "NCBI unavailable"
        )

    def fake_display(
        context,
        alt,
        flank_size,
    ):
        return SimpleNamespace(
            window_start=5226991,
            window_end=5227012,
            reference_sequence="AGACTTCTCCTCAGGAGTCAG",
            variant_sequence="AGACTTCTCCACAGGAGTCAG",
            variant_index=10,
            ref="T",
            alt="A",
        )

    monkeypatch.setattr(
        "app.api.routes.get_centered_variant_context",
        fake_context,
    )

    monkeypatch.setattr(
        "app.api.routes.score_variant_with_evo2",
        fake_evo,
    )

    monkeypatch.setattr(
        "app.api.routes.lookup_clinvar",
        broken_clinvar,
    )

    monkeypatch.setattr(
        "app.api.routes.build_display_sequence_context",
        fake_display,
    )

    response = client.post(
        "/score-variant",
        json={
            "gene": "HBB",
            "chrom": "11",
            "position": 5227002,
            "ref": "T",
            "alt": "A",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["clinvar_label"] == "Unavailable"
    assert data["clinvar"]["status"] == "unavailable"