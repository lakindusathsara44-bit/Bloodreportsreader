import os
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Blood Glucose Report Reader", page_icon="🩸", layout="wide")
st.title("🩸 AI Blood Glucose Analysis System")
st.caption("Educational health-information tool — not a medical diagnosis.")

st.warning("This app provides general educational information only. Glucose interpretation depends on test type, timing, symptoms, medicines, pregnancy status, and clinical history. Please consult a qualified healthcare professional.")

with st.sidebar:
    st.header("Patient details")
    patient = st.text_input("Patient name / ID (optional)")
    test_date = st.date_input("Report date", value=date.today())
    test_type = st.selectbox("Test type", ["Fasting blood glucose", "Random blood glucose", "2-hour after meal", "HbA1c"])
    unit = "mmol/L" if test_type != "HbA1c" else "%"
    if test_type == "HbA1c":
        value = st.number_input("HbA1c (%)", min_value=0.0, max_value=25.0, value=5.5, step=0.1)
    elif test_type == "Random blood glucose":
        value = st.number_input("Glucose (mmol/L)", min_value=0.0, max_value=60.0, value=5.5, step=0.1)
    else:
        value = st.number_input("Glucose (mmol/L)", min_value=0.0, max_value=60.0, value=5.0, step=0.1)

st.subheader("Result overview")
c1, c2, c3 = st.columns(3)
c1.metric("Entered result", f"{value:.1f} {unit}")
c2.metric("Test type", test_type)
c3.metric("Report date", str(test_date))

st.subheader("General interpretation")
if test_type == "Fasting blood glucose":
    if value < 3.9:
        interpretation = "Below the usual range; low blood glucose may require prompt attention, especially if symptoms are present."
    elif value < 5.6:
        interpretation = "Within the commonly used normal fasting range for many non-pregnant adults."
    elif value < 7.0:
        interpretation = "Higher than the usual normal fasting range. A clinician may recommend repeat testing or further assessment."
    else:
        interpretation = "In a range that can be associated with diabetes, but a single result cannot confirm a diagnosis."
elif test_type == "2-hour after meal":
    if value < 7.8:
        interpretation = "Often within the expected range for a 2-hour post-meal result, depending on the clinical context."
    elif value < 11.1:
        interpretation = "Higher than expected for many people. Discuss the result with a healthcare professional."
    else:
        interpretation = "A high 2-hour glucose result. Clinical assessment and confirmatory testing are important."
elif test_type == "HbA1c":
    if value < 5.7:
        interpretation = "Below the commonly used prediabetes threshold."
    elif value < 6.5:
        interpretation = "Within the commonly used prediabetes range."
    else:
        interpretation = "At or above the commonly used diabetes threshold; diagnosis requires clinical confirmation."
else:
    interpretation = "Random glucose values depend on meal timing and symptoms. A clinician should interpret this result in context."

st.info(interpretation)
st.caption("Thresholds shown are general adult reference points and may not apply to every person or laboratory. Follow the reference range on your own lab report.")

st.subheader("Track results over time")
st.write("Add previous measurements to view a trend. These values are stored only for this current session.")
if "records" not in st.session_state:
    st.session_state.records = []
if st.button("Add this result to trend"):
    st.session_state.records.append({"Date": str(test_date), "Test": test_type, "Value": float(value), "Unit": unit})
if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df, use_container_width=True)
    fig = px.line(df, x="Date", y="Value", color="Test", markers=True, title="Glucose / HbA1c trend (compare same test types)")
    st.plotly_chart(fig, use_container_width=True)
    st.download_button("Download results as CSV", df.to_csv(index=False).encode("utf-8"), "glucose_results.csv", "text/csv")
else:
    st.caption("No results added to the trend yet.")

st.subheader("AI-generated report (optional)")
st.write("Set OPENAI_API_KEY in your Streamlit Cloud Secrets or local environment to enable an AI-written educational summary.")
if st.button("Generate English report"):
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    try:
        if not api_key:
            api_key = str(st.secrets.get("OPENAI_API_KEY", "")).strip()
    except Exception:
        pass
    if not api_key:
        st.error("OPENAI_API_KEY is not configured. Add it under Streamlit Cloud → App settings → Secrets. Do not put API keys in public GitHub files.")
    else:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            prompt = f"""Write a concise English educational summary of this blood test entry. Test: {test_type}. Value: {value} {unit}. Date: {test_date}. General interpretation: {interpretation}. Include limitations, encourage clinician review, and do not diagnose or prescribe treatment. State clearly that AI output is not a medical diagnosis."""
            with st.spinner("Preparing report..."):
                response = client.responses.create(model=model, input=prompt)
            st.markdown(response.output_text)
            st.download_button("Download report as TXT", response.output_text, "blood_glucose_report.txt", "text/plain")
        except Exception as exc:
            st.error(f"Could not generate report: {exc}")

st.caption("For severe symptoms or suspected dangerously low/high blood glucose, seek urgent medical help. Do not delay care to use this app.")
