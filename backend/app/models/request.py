from pydantic import BaseModel, Field


class ScoreVariantRequest(BaseModel):
    gene: str = Field(..., examples=["HBB"])
    chrom: str = Field(..., examples=["11"])
    position: int = Field(..., gt=0, examples=[5227002])
    ref: str = Field(..., min_length=1, examples=["A"])
    alt: str = Field(..., min_length=1, examples=["T"])