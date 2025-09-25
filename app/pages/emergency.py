import os
import streamlit as st
from app.data_store import load_profile
from app.utils.tts_utils import speak_steps_button

EMERGENCY_PIN_HASH = os.environ.get("EMERGENCY_PIN_HASH", "")  # optional

st.set_page_config(page_title="Emergency Mode", page_icon="🚑", layout="wide")

st.title("🚑 Emergency Mode")

# Minimal read-only until PIN entered
pin_ok = False
if EMERGENCY_PIN_HASH:
    with st.expander("Unlock additional details (PIN)"):
        pin = st.text_input("Enter 6-digit PIN", type="password")
        if pin:
            import hashlib
            if hashlib.sha256(pin.encode()).hexdigest() == EMERGENCY_PIN_HASH:
                st.success("Unlocked emergency details.")
                pin_ok = True
            else:
                st.error("Incorrect PIN")
else:
    pin_ok = True  # no PIN set

prof = load_profile()

# Top strip: name + key flags
col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.subheader(prof["profile"].get("full_name", ""))
    st.caption(f"DOB: {prof['profile'].get('dob', '')} · Blood: {prof['profile'].get('blood_type', '')}")
with col2:
    st.markdown("**Allergies**")
    for a in prof.get("allergies", [])[:3]:
        st.write(f"• {a.get('substance')} — {a.get('severity','')}")
with col3:
    st.markdown("**Conditions**")
    for c in prof.get("conditions", [])[:3]:
        st.write(f"• {c.get('name')} ({c.get('severity','')})")

st.divider()

# Current meds: show first as primary tile
meds = prof.get("medications", [])
if meds:
    med = meds[0]
    left, right = st.columns([2, 1])
    with left:
        st.markdown(f"### Current Med: **{med.get('name','')}**")
        device = med.get("device", {})
        if device:
            st.write(f"**Device**: {device.get('model','')} · {device.get('type','')}")
        st.write(f"**Dosage**: {med.get('dosage','')}")
        st.write(f"**Where kept**: **{med.get('storage_location','')}**")
        st.markdown("#### How to use")
        steps = med.get("how_to_use_steps", [])
        for i, s in enumerate(steps, 1):
            st.write(f"{i}. {s}")
        speak_steps_button(steps)
        if med.get("warnings"):
            st.warning("\n".join(f"⚠️ {w}" for w in med["warnings"]))
        if pin_ok and med.get("leaflets"):
            with st.expander("Leaflets / Guides"):
                for lf in med["leaflets"]:
                    st.write(lf)
    with right:
        st.markdown("#### Device photos")
        device = med.get("device", {})
        for img in device.get("photos", [])[:3]:
            try:
                st.image(img, use_column_width=True)
            except Exception:
                st.caption(img)

st.divider()

# Contacts & medical aid
cols = st.columns(2)
with cols[0]:
    st.markdown("### ICE Contacts")
    for c in prof.get("emergency_contacts", []):
        st.write(f"**{c.get('name')}** — {c.get('relation')} — {c.get('phone')}")
with cols[1]:
    st.markdown("### Medical Aid")
    aid = prof["profile"].get("medical_aid", {})
    st.write(f"**Provider**: {aid.get('provider','')}")
    st.write(f"**Plan**: {aid.get('plan','')}")
    st.write(f"**Member #**: {aid.get('member_no','')}")
    st.write(f"**Emergency hotline**: {aid.get('emergency_hotline','')}")

st.caption("This view shows only what’s essential during emergencies.")
