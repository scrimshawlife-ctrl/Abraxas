import json


def test_schema_files_load():
    paths = [
        "tools/aatf/aatf/schemas/aalmanac.v0.json",
        "tools/aatf/aatf/schemas/memetic_weather.v0.json",
        "tools/aatf/aatf/schemas/neon_genie.v0.json",
        "tools/aatf/aatf/schemas/rune_proposal.v0.json",
    ]
    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            json.load(f)
