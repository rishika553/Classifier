import pandas as pd
import streamlit as st
from classifier import classify

st.set_page_config(page_title="Spelling Attempt Classifier", page_icon="✏️")
st.title("Spelling Attempt Classifier")
st.write("Checks whether an incorrect answer looks like a genuine spelling attempt, random input, or an uncertain case.")

st.subheader("1. Try a word")
actual = st.text_input("Actual word", placeholder="beautiful")
attempt = st.text_input("Child's attempt", placeholder="beutiful")

if st.button("Check"):
    if not actual or not attempt:
        st.warning("Enter both words.")
    else:
        result = classify(actual, attempt)
        label = result["label"].replace("_", " ").title()
        st.metric("Result", label)
        st.metric("Confidence", f"{result['confidence'] * 100:.0f}%")
        st.info(result["reason"])

st.divider()
st.subheader("2. Classify the CSV")
file = st.file_uploader("Upload CSV", type=["csv"])

if file:
    df = pd.read_csv(file)
    required = {"actual_word", "typed_word"}
    if not required.issubset(df.columns):
        st.error("CSV must contain actual_word and typed_word columns.")
    else:
        results = df.apply(lambda row: classify(row["actual_word"], row["typed_word"]), axis=1)
        df["prediction"] = [r["label"] for r in results]
        df["confidence"] = [r["confidence"] for r in results]
        df["reason"] = [r["reason"] for r in results]
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download classified CSV", csv, "classified_results.csv", "text/csv")
