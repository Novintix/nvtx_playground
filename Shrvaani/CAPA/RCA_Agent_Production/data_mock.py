# data_mock.py
# In a real production system, these would be fetched via MCP from PDFs or Databases.

TOTAL_CAPA_CASES = 100

HISTORICAL_DATA = {
    "Supplier material defect in barrel plastic": {"freq": 25, "evidence": ["batch: B-90210", "barrel crack"]},
    "Excessive plunger force from filling machine": {"freq": 15, "evidence": ["Pressure sensor spike", "Force limit exceeded"]},
    "Improper aseptic handling by nurse": {"freq": 12, "evidence": ["Staff ID", "Aseptic violation"]},
    "Thermal stress during sterilization": {"freq": 10, "evidence": ["Temperature excursion", "Autoclave spike"]}
}

DEVICE_LOGS = [
    "SYRINGE_CRACK detected at hub",
    "Pressure sensor spike: 45psi",
    "Material batch: B-90210",
    "Staff ID: Nurse_A"
]

# Scattered Fragments - Simulations of different data silos
SCATTERED_FRAGMENTS = {
    "COMPLAINTS": [
        "Record #C-882: Syringe hub fractured during use at surgical center. Patient injury avoided.",
        "Record #C-885: Reports of brittle barrel plastics in Batch B-90210."
    ],
    "LAB_REPORTS": [
        "Lab ID #L-404 (Batch B-90210): Thermal analysis confirms brittle transition. Polymer chain degradation observed.",
        "Lab ID #L-405: Moisture content in resin pellets recorded at 0.12%, significantly exceeding 0.02% limit."
    ],
    "MFG_LOGS": [
        "Log #M-101: Dryer unit DH-04 under-temperature alarm triggered during Batch B-90210 production run.",
        "Log #M-102: Operator manual bypass recorded for heat alarm on DH-04 to maintain throughput."
    ],
    "MAINTENANCE": [
        "Equipment DH-04: Heating element resistance high (450 ohms). Expected: 50 ohms.",
        "PM Schedule for DH-04: Status OVERDUE. Last maintenance performed 6 months ago (90-day cycle)."
    ]
}
