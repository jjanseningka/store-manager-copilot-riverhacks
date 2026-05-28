from __future__ import annotations

import os
import sys

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from data.loader import DataStore
from llm.agent import RetailAgent
from llm.validators import validate_article_references, validate_numbers_reasonable

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Hej Assistant — IKEA Store Intelligence",
    page_icon="🏠",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Custom IKEA-inspired styling
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
    /* IKEA blue & yellow */
    .stApp { background-color: #fafafa; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #003399;
        color: white;
        border-radius: 4px 4px 0 0;
        padding: 8px 24px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFDA1A;
        color: #003399;
        font-weight: bold;
    }
    div[data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 12px;
    }
    .priority-critical { color: #d32f2f; font-weight: bold; }
    .priority-high { color: #f57c00; font-weight: bold; }
    .priority-medium { color: #1976d2; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Data loading (cached)
# ---------------------------------------------------------------------------
@st.cache_resource
def load_data() -> DataStore:
    return DataStore()


store = load_data()

# ---------------------------------------------------------------------------
# Sidebar — Store selector
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image(
        "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/200px-Ikea_logo.svg.png",
        width=120,
    )
    st.markdown("## 🏠 Hej Assistant")
    st.markdown("Your daily commercial intelligence co-worker.")
    st.markdown("---")

    stores = store.store_names()
    store_options = {s["bu_sk"]: f"{s['bu_short_name']} ({s['city']})" for s in stores}
    selected_bu = st.selectbox(
        "Select your store",
        options=list(store_options.keys()),
        format_func=lambda x: store_options[x],
    )

    st.markdown(f"**Data as of:** {store.today.strftime('%A, %d %B %Y')}")
    st.markdown("---")

    # Quick stats
    store_sales = store.sales[store.sales["bu_sk"] == selected_bu]
    total_transactions = store_sales["unique_transaction_identifier"].nunique()
    total_revenue = store_sales["created_sales_net_amount_euro"].sum()
    st.metric("Total Transactions (all data)", f"{total_transactions:,}")
    st.metric("Total Revenue (all data)", f"€{total_revenue:,.0f}")

# ---------------------------------------------------------------------------
# Initialize agent in session state
# ---------------------------------------------------------------------------
if "agent" not in st.session_state or st.session_state.get("current_bu") != selected_bu:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        st.session_state.agent = RetailAgent(store, selected_bu)
        st.session_state.current_bu = selected_bu
        st.session_state.chat_messages = []
        st.session_state.report = None
    else:
        st.session_state.agent = None

# ---------------------------------------------------------------------------
# Main content — Tabs
# ---------------------------------------------------------------------------
st.markdown("# 🏠 Hej Assistant")
st.markdown("*Your AI-powered commercial intelligence co-worker*")

tab_report, tab_chat, tab_data = st.tabs(["📋 Daily Briefing", "💬 Ask Me Anything", "📊 Raw Data"])

# ---------------------------------------------------------------------------
# Tab 1: Daily Briefing
# ---------------------------------------------------------------------------
with tab_report:
    if st.session_state.get("agent") is None:
        st.warning(
            "⚠️ Set your `ANTHROPIC_API_KEY` environment variable to enable AI features. "
            "Add it to a `.env` file in the project root."
        )
        st.stop()

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Daily Commercial Briefing")
        st.markdown(f"*Store: {store_options[selected_bu]}*")
    with col2:
        generate_btn = st.button("🔄 Generate Report", type="primary", use_container_width=True)

    if generate_btn:
        with st.spinner("Analysing your store data... This may take a moment."):
            try:
                report = st.session_state.agent.generate_report()
                st.session_state.report = report

                # Run validators
                warnings = validate_article_references(report, store)
                warnings += validate_numbers_reasonable(report)
                st.session_state.report_warnings = warnings
            except Exception as e:
                st.error(f"Error generating report: {e}")

    if st.session_state.get("report"):
        # Show warnings if any
        if st.session_state.get("report_warnings"):
            with st.expander("⚠️ Validation Warnings", expanded=False):
                for w in st.session_state.report_warnings:
                    st.warning(w)

        st.markdown(st.session_state.report)

        # PDF export
        st.markdown("---")
        if st.button("📄 Export as PDF"):
            try:
                from fpdf import FPDF

                pdf = FPDF()
                pdf.add_page()
                pdf.set_auto_page_break(auto=True, margin=15)
                pdf.set_font("Helvetica", size=10)

                # Simple text export
                for line in st.session_state.report.split("\n"):
                    # Strip markdown formatting for PDF
                    clean = line.replace("#", "").replace("**", "").replace("*", "")
                    clean = clean.replace("🔴", "[!]").replace("🟡", "[~]").replace("🟢", "[OK]")
                    clean = clean.replace("📊", "").replace("📦", "").replace("💰", "")
                    clean = clean.replace("⚡", "").replace("→", "->")
                    if clean.strip():
                        pdf.multi_cell(0, 6, clean.encode("latin-1", "replace").decode("latin-1"))

                pdf_bytes = pdf.output()
                st.download_button(
                    "⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"daily_briefing_{store.today.strftime('%Y-%m-%d')}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF export error: {e}")
    else:
        st.info("👆 Click **Generate Report** to create your daily commercial briefing.")

        # Show quick data preview while waiting
        st.markdown("---")
        st.markdown("### Quick Snapshot")
        from tools.sales import get_sales_vs_forecast
        from tools.stock import get_stock_alerts

        c1, c2, c3, c4 = st.columns(4)
        try:
            s7 = get_sales_vs_forecast(store, selected_bu, "7d")
            alerts = get_stock_alerts(store, selected_bu)

            with c1:
                st.metric("7-Day Sales (units)", f"{s7['actual_sales_units']:,}")
            with c2:
                st.metric(
                    "vs Forecast",
                    f"{s7['gap_percent']:+.1f}%",
                    delta=f"{s7['gap_units']:+.0f} units",
                )
            with c3:
                st.metric("🔴 Out of Stock", alerts["out_of_stock_count"])
            with c4:
                st.metric("🟡 Low Stock", alerts["low_stock_count"])
        except Exception:
            st.info("Loading quick stats...")

# ---------------------------------------------------------------------------
# Tab 2: Chat
# ---------------------------------------------------------------------------
with tab_chat:
    if st.session_state.get("agent") is None:
        st.warning("⚠️ Set your `ANTHROPIC_API_KEY` to enable the chat feature.")
        st.stop()

    st.markdown("### Ask your store data anything")
    st.markdown("*I'll analyse the data and give you actionable insights.*")

    # Suggested questions
    with st.expander("💡 Suggested questions", expanded=False):
        suggestions = [
            "What are my top 10 selling articles last 7 days?",
            "Which HFB is driving the highest sales growth?",
            "Which high-selling articles are currently out of stock?",
            "What is my store's gross margin this week?",
            "What are the top 5 actions I should take today?",
            "Which articles have declining sales momentum?",
            "What should I brief my team on in today's huddle?",
            "Which HFBs have strong sales but low margin?",
            "Are any articles overstocked relative to forecast?",
            "What should I focus on in the first 2 hours?",
        ]
        for s in suggestions:
            if st.button(s, key=f"sug_{s[:20]}"):
                st.session_state.pending_question = s

    # Display chat history
    for msg in st.session_state.get("chat_messages", []):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat input
    prompt = st.chat_input("Ask me anything about your store...")

    # Handle suggested question clicks
    if st.session_state.get("pending_question"):
        prompt = st.session_state.pending_question
        st.session_state.pending_question = None

    if prompt:
        # Add user message
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Analysing..."):
                try:
                    response = st.session_state.agent.chat(prompt)

                    # Validate
                    warnings = validate_article_references(response, store)
                    if warnings:
                        for w in warnings:
                            st.caption(w)

                    st.markdown(response)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": response}
                    )
                except Exception as e:
                    error_msg = f"Sorry, I encountered an error: {e}"
                    st.error(error_msg)
                    st.session_state.chat_messages.append(
                        {"role": "assistant", "content": error_msg}
                    )

    # Clear chat button
    if st.session_state.get("chat_messages"):
        if st.button("🗑️ Clear chat history"):
            st.session_state.chat_messages = []
            if st.session_state.get("agent"):
                st.session_state.agent.reset_history()
            st.rerun()

# ---------------------------------------------------------------------------
# Tab 3: Raw Data Explorer
# ---------------------------------------------------------------------------
with tab_data:
    st.markdown("### Data Explorer")
    st.markdown(f"*Filtered for: {store_options[selected_bu]}*")

    data_view = st.selectbox(
        "Select dataset",
        ["Sales", "Stock (Latest)", "Forecast", "Products", "Business Units"],
    )

    if data_view == "Sales":
        df = store.sales_with_products(selected_bu)
        st.dataframe(
            df.sort_values("transaction_date", ascending=False).head(500),
            use_container_width=True,
        )
        st.caption(f"Showing latest 500 of {len(df):,} rows")

    elif data_view == "Stock (Latest)":
        df = store.latest_stock(selected_bu)
        st.dataframe(df, use_container_width=True)
        st.caption(f"{len(df)} items")

    elif data_view == "Forecast":
        df = store.forecast_with_products(selected_bu)
        st.dataframe(
            df.sort_values("local_forecast_date", ascending=False).head(500),
            use_container_width=True,
        )
        st.caption(f"Showing latest 500 of {len(df):,} rows")

    elif data_view == "Products":
        st.dataframe(store.products, use_container_width=True)

    elif data_view == "Business Units":
        st.dataframe(store.business_units, use_container_width=True)
