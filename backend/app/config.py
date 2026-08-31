import os

from dotenv import load_dotenv


load_dotenv()

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000",
    ).split(",")
    if origin.strip()
]


# UCSC
UCSC_BASE_URL = "https://api.genome.ucsc.edu"

GENOME_ASSEMBLY = os.getenv(
    "GENOME_ASSEMBLY",
    "hg38",
)


# Evo2 / NVIDIA
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")

EVO2_BASE_URL = os.getenv(
    "EVO2_BASE_URL",
    "https://health.api.nvidia.com/v1/biology/arc",
)

EVO2_MODEL = os.getenv(
    "EVO2_MODEL",
    "evo2-7b",
)

# NCBI / ClinVar
NCBI_EUTILS_BASE_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
)

NCBI_TOOL = os.getenv(
    "NCBI_TOOL",
    "GeneRisk",
)

NCBI_EMAIL = os.getenv(
    "NCBI_EMAIL",
)

NCBI_API_KEY = os.getenv(
    "NCBI_API_KEY",
)

# Evo2 cache

EVO2_CACHE_MAXSIZE = int(
    os.getenv(
        "EVO2_CACHE_MAXSIZE",
        "512",
    )
)

EVO2_CACHE_TTL_SECONDS = int(
    os.getenv(
        "EVO2_CACHE_TTL_SECONDS",
        "86400",
    )
)