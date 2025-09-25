import json
import os
from typing import Any, Dict

DATA_PATH = os.environ.get("PATIENT_JSON_PATH", os.path.join("data", "patient.json"))

DEFAULT_PROFILE: Dict[str, Any] = {
    "patient_id": "demo-patient-uuid",
    "profile": {
        "full_name": "Jane Doe",
        "dob": "1970-06-12",
        "blood_type": "O+",
        "medical_aid": {
            "provider": "",
            "plan": "",
            "member_no": "",
            "emergency_hotline": ""
        }
    },
    "emergency_contacts": [
        {"name": "John Doe", "relation": "Son", "phone": "+27 000 0000"}
    ],
    "conditions": [
        {"name": "Asthma", "severity": "moderate", "notes": "Exercise-induced"}
    ],
    "allergies": [
        {"substance": "Penicillin", "reaction": "Rash", "severity": "high"}
    ],
    "medications": [
        {
            "name": "Tiotropium capsules",
            "device": {
                "type": "Dry powder inhaler",
                "model": "HandiHaler",
                "photos": ["/media/handihaler_front.jpg", "/media/capsule.jpg"]
            },
            "dosage": "18 µg once daily",
            "storage_location": "Handbag, front pouch",
            "how_to_use_steps": [
                "Open dust cap and mouthpiece.",
                "Place one capsule in the chamber.",
                "Close mouthpiece until it clicks; press button once to pierce capsule.",
                "Exhale away, seal lips around mouthpiece; inhale deeply; hold breath; repeat."
            ],
            "warnings": ["Do not swallow capsules."],
            "leaflets": ["/docs/handihaler_pil.pdf"],
            "last_updated": "2025-09-01"
        }
    ],
    "preferences": {"preferred_hospital": "", "gp": ""},
    "meta": {"last_reviewed": "2025-09-10"}
}


def ensure_file_exists(path: str = DATA_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_PROFILE, f, indent=2, ensure_ascii=False)


def load_profile(path: str = DATA_PATH) -> Dict[str, Any]:
    ensure_file_exists(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(profile: Dict[str, Any], path: str = DATA_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)
