import streamlit as st

from src.data_loader import load_data
from src.query_engine import run_query
from src.anomaly_detector import detect_anomalies

st.set_page_config(
    page_title="AI Support Ticket Assistant",
    layout="wide"
)

@st.cache_data
def get_data():
    return load_data()


st.title("AI Support Ticket Assistant")

try:
    df = get_data()
except Exception as exc:
    st.error(f"Unable to load support ticket data: {exc}")
    st.stop()

metric_columns = st.columns(4)
metric_columns[0].metric("Tickets", f"{len(df):,}")
metric_columns[1].metric("Open", f"{(df['status'].str.casefold() == 'open').sum():,}")
metric_columns[2].metric("Critical", f"{(df['priority'].str.casefold() == 'critical').sum():,}")
metric_columns[3].metric("Avg Rating", f"{df['customer_rating'].mean():.2f}")

tab1, tab2, tab3 = st.tabs(["Dataset", "Ask Questions", "Anomalies"])

with tab1:
    st.subheader("Dataset Preview")
    st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    question = st.text_input(
        "Ask a question",
        placeholder="Example: How many tickets are currently open?"
    )
    if st.button("Submit", type="primary"):
        result = run_query(
            question,
            df
        )

        if result.get("error"):
            st.error(result["error"])
        else:
            st.caption(f"Generated query: `{result['query']}`")
            output = result["result"]
            if hasattr(output, "to_frame") or hasattr(output, "columns"):
                st.dataframe(output, use_container_width=True)
            else:
                st.write(output)

with tab3:
    anomalies = detect_anomalies(df)

    st.subheader(
        "Critical Unresolved Tickets"
    )
    st.dataframe(
        anomalies["critical_unresolved"],
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Long Resolution Times"
    )
    st.dataframe(
        anomalies["long_resolution"],
        use_container_width=True,
        hide_index=True
    )

    st.subheader(
        "Low Customer Ratings"
    )
    st.dataframe(
        anomalies["low_ratings"],
        use_container_width=True,
        hide_index=True
    )
