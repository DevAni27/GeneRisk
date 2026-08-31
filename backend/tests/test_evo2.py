import numpy as np

from app.services.evo2 import compute_log_likelihood


def test_compute_log_likelihood_returns_float():
    sequence = "ACGT"

    # 4 sequence positions × 512 vocabulary tokens
    logits = np.zeros(
        (1, 4, 512),
        dtype=np.float32,
    )

    score = compute_log_likelihood(
        sequence=sequence,
        logits=logits,
    )

    assert isinstance(score, float)


def test_correct_next_base_increases_likelihood():
    sequence = "ACGT"

    baseline_logits = np.zeros(
        (1, 4, 512),
        dtype=np.float32,
    )

    improved_logits = baseline_logits.copy()

    # Position 0 predicts C
    improved_logits[0, 0, ord("C")] = 10.0

    # Position 1 predicts G
    improved_logits[0, 1, ord("G")] = 10.0

    # Position 2 predicts T
    improved_logits[0, 2, ord("T")] = 10.0

    baseline_score = compute_log_likelihood(
        sequence,
        baseline_logits,
    )

    improved_score = compute_log_likelihood(
        sequence,
        improved_logits,
    )

    assert improved_score > baseline_score
    
def test_uniform_logits_equal_log_vocab_probability():
    sequence = "ACGT"

    logits = np.zeros(
        (1, 4, 512),
        dtype=np.float64,
    )

    score = compute_log_likelihood(
        sequence,
        logits,
    )

    expected = -np.log(512)

    assert np.isclose(
        score,
        expected,
    )