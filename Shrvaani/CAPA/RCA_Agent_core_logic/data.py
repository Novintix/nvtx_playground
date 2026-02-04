# data.py

TOTAL_CAPA_CASES = 100

# Historical frequency for Syringe issues
HISTORICAL_CAUSE_FREQUENCY = {
    "Supplier material defect in barrel plastic": 25,
    "Excessive plunger force from filling machine": 15,
    "Thermal stress during sterilization": 10,
    "Dropped during hospital transport": 8,
    "Improper aseptic handling by nurse": 12,
    "Incorrect test method for brittle strength": 5
}

# Simulated logs/data for current event
DEVICE_LOGS = [
    "SYRINGE_CRACK detected at hub",
    "Pressure sensor spike: 45psi",
    "Material batch: B-90210",
    "Staff ID: Nurse_A"
]

# Log evidence mapping
LOG_EVIDENCE_MAP = {
    "Supplier material defect in barrel plastic": ["batch: B-90210", "barrel crack"],
    "Excessive plunger force from filling machine": ["Pressure sensor spike", "Force limit exceeded"],
    "Improper aseptic handling by nurse": ["Staff ID", "Aseptic violation"],
    "Thermal stress during sterilization": ["Temperature excursion", "Autoclave spike"]
}

# 5-Why Analysis Mapping (Simulating LLM depth)
FIVE_WHY_CHAINS = {
    "Supplier material defect in barrel plastic": [
        "Why 1: Syringe barrel cracked?",
        "Why 2: Because the plastic was brittle.",
        "Why 3: Because the raw material batch had high moisture content.",
        "Why 4: Because the supplier's dryer failed.",
        "Why 5: Because the dryer's preventive maintenance was skipped."
    ],
    "Excessive plunger force from filling machine": [
        "Why 1: Plunger jammed or broke?",
        "Why 2: Because the motor applied excessive torque.",
        "Why 3: Because the torque sensor was out of calibration.",
        "Why 4: Because the calibration schedule was not updated for the new model.",
        "Why 5: Because the change control process missed the calibration update."
    ],
    "Improper aseptic handling by nurse": [
        "Why 1: Syringe contaminated or damaged during prep?",
        "Why 2: Because incorrect aseptic technique was used.",
        "Why 3: Because the nurse was rushing due to high patient load.",
        "Why 4: Because the ward was understaffed for the night shift.",
        "Why 5: Because the resource allocation algorithm failed to predict the surge."
    ],
    "Thermal stress during sterilization": [
        "Why 1: Syringe material structure compromised?",
        "Why 2: Because the sterilization temperature exceeded the upper limit.",
        "Why 3: Because the autoclave's PID controller overshot.",
        "Why 4: Because the steam valve was sticking and responded slowly.",
        "Why 5: Because the valve seal was degraded from hard water buildup."
    ],
    "Incorrect test method for brittle strength": [
        "Why 1: Brittle barrels passed inspection?",
        "Why 2: Because the test method used lower-than-actual force.",
        "Why 3: Because the SOP was based on an outdated ISO standard.",
        "Why 4: Because the QA team missed the 2024 regulatory update.",
        "Why 5: Because the regulatory intelligence tool was not configured for regional updates."
    ],
    "Dropped during hospital transport": [
        "Why 1: Syringe fractured upon impact?",
        "Why 2: Because it fell from a height of 1 meter.",
        "Why 3: Because the transport box lid was not secured.",
        "Why 4: Because the locking latch was worn out.",
        "Why 5: Because the hospital equipment replacement budget was deferred."
    ]
}
