import streamlit as st

try:
    import pyttsx3  # offline TTS
    _HAS_TTS = True
except Exception:
    _HAS_TTS = False


def speak_steps_button(steps):
    if not steps:
        return
    if _HAS_TTS:
        if st.button("🔊 Read steps aloud"):
            try:
                engine = pyttsx3.init()
                for i, s in enumerate(steps, 1):
                    engine.say(f"Step {i}: {s}")
                engine.runAndWait()
                st.info("Playing via system TTS (pyttsx3).")
            except Exception as e:
                st.warning(f"TTS unavailable: {e}")
    else:
        st.caption("TTS not available in this environment. Displaying steps above.")
