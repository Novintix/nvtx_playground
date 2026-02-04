# scientific_kb.py

# Simulating the LLM's "latent engineering knowledge"
MATERIAL_SCIENCE_LAWS = {
    "Polypropylene": {
        "properties": "Semi-crystalline, chemical resistant.",
        "failure_modes": {
            "Gamma_Discoloration": "Reacts with Antioxidant B above 25kGy dose to produce a purple/yellow hue.",
            "Thermal_Stress": "Glass transition at 150C. Below this, crystalline structure remains stable."
        }
    },
    "Polycarbonate": {
        "properties": "High impact, moisture sensitive.",
        "failure_modes": {
            "Brittle_Fracture": "Occurs when moisture content >0.02% during molding (Embrittlement).",
            "Cold_Chain_Fail": "Brittle-to-ductile transition at -15C. Sudden fracture likely under load at low temps."
        }
    }
}

# Simulating Batch-Specific Reality (What MCP would pull)
BATCH_REALITY = {
    "B-90210": {
        "gamma_dose": "45kGy", # Over the 25kGy threshold
        "antioxidant": "Type B",
        "molding_temp": "280C"
    },
    "B-111": {
        "moisture": "0.15%",
        "storage_temp": "22C"
    }
}
