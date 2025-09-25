"""
Convert a Synthea patient JSON into our app's patient.json format.
Usage:
    python scripts/synthea_to_patient.py path/to/synthea_patient.json
"""

import json
import sys
import os
from pathlib import Path
from datetime import date

OUT_PATH = Path("data/patient.json")


def convert_synthea_to_patient(synthea_json: dict) -> dict:
    patient = synthea_json["entry"][0]["resource"]  # main Patient resource
    demographics = {
        "full_name": f"{patient['name'][0]['given'][0]} {patient['name'][0]['family']}",
        "dob": patient.get("birthDate", ""),
        "blood_type": patient.get("extension", [{}])[0].get("valueCode", ""),  # optional
        "medical_aid": {
            "provider": "SyntheticHealth",  # not in Synthea
            "plan": "DemoPlan",
            "member_no": patient.get("id", ""),
            "emergency_hotline": ""
        }
    }

    # Conditions
    conditions = []
    for e in synthea_json["entry"]:
        if e["resource"]["resourceType"] == "Condition":
            c = e["resource"]
            conditions.append({
                "name": c.get("code", {}).get("text", ""),
                "severity": c.get("severity", {}).get("text", ""),
                "notes": c.get("clinicalStatus", {}).get("text", "")
            })

    # Allergies
    allergies = []
    for e in synthea_json["entry"]:
        if e["resource"]["resourceType"] == "AllergyIntolerance":
            a = e["resource"]
            allergies.append({
                "substance": a.get("code", {}).get("text", ""),
                "reaction": ", ".join(
                    [r["description"] for r in a.get("reaction", []) if "description" in r]
                ),
                "severity": a.get("criticality", "")
            })

    # Medications
    medications = []
    for e in synthea_json["entry"]:
        if e["resource"]["resourceType"] == "MedicationRequest":
            m = e["resource"]
            med = {
                "name": m.get("medicationCodeableConcept", {}).get("text", ""),
                "device": {"type": "Medication", "model": ""},
                "dosage": "",
                "storage_location": "Unknown",
                "how_to_use_steps": [],
                "warnings": [],
                "leaflets": [],
                "last_updated": str(date.today())
            }
            if "dosageInstruction" in m:
                med["dosage"] = "; ".join(
                    [d.get("text", "") for d in m["dosageInstruction"] if "text" in d]
                )
            medications.append(med)

    profile = {
        "patient_id": patient.get("id", "synthea-demo"),
        "profile": demographics,
        "emergency_contacts": [],  # Synthea doesn’t include family contacts
        "conditions": conditions,
        "allergies": allergies,
        "medications": medications,
        "preferences": {"preferred_hospital": "", "gp": ""},
        "meta": {"last_reviewed": str(date.today())}
    }

    return profile


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/synthea_to_patient.py path/to/synthea_patient.json")
        sys.exit(1)

    in_path = Path(sys.argv[1])
    if not in_path.exists():
        print(f"File not found: {in_path}")
        sys.exit(1)

    with open(in_path, "r", encoding="utf-8") as f:
        synthea_data = json.load(f)

    profile = convert_synthea_to_patient(synthea_data)

    os.makedirs(OUT_PATH.parent, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"✅ Converted Synthea record saved to {OUT_PATH}")


if __name__ == "__main__":
    main()
