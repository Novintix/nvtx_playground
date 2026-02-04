# fishbone.py

SIX_M = [
    "Man",
    "Machine",
    "Method",
    "Material",
    "Measurement",
    "Environment"
]


def create_empty_fishbone():
    return {m: [] for m in SIX_M}
