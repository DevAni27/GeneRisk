import asyncio

from app.services.evo2 import (
    decode_logits,
    forward_sequence,
    score_sequence,
)


async def main():
    sequence = "ACGTACGTACGTACGT"

    print("Sending sequence to Evo2...")
    print("Sequence:", sequence)
    print("Length:", len(sequence))

    response = await forward_sequence(
        sequence,
    )

    print()
    print("Evo2 request successful!")

    logits = decode_logits(
        response,
    )

    print("Logits shape:", logits.shape)
    print("Logits dtype:", logits.dtype)

    score = await score_sequence(
        sequence,
    )

    print()
    print("Sequence log-likelihood:", score)


if __name__ == "__main__":
    asyncio.run(main())