"""Streamlit web interface for Codex."""

import os
import sys
from datetime import datetime
from pathlib import Path

import streamlit as st
import streamlit_shadcn_ui as ui

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src.agent import ComplianceAgent
from src.memory import MemoryManager, MemoryType
from src.utils import logger
from src.utils.report_generator import generate_safety_report, get_weather_trend_analysis

# Setup logging
logger.info("Starting Codex Streamlit UI")


# Page configuration
st.set_page_config(
    page_title="Codex - AI Compliance Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom CSS
_css_path = Path(__file__).parent / "style.css"
if _css_path.exists():
    with open(_css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'docs_ingested' not in st.session_state:
    st.session_state.docs_ingested = False

if 'last_decision' not in st.session_state:
    st.session_state.last_decision = None

if 'last_site_location' not in st.session_state:
    st.session_state.last_site_location = None

if 'last_operation_type' not in st.session_state:
    st.session_state.last_operation_type = None


def init_agent():
    """Initialize the compliance agent and auto-ingest sample docs."""
    if not os.getenv('NVIDIA_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        return None
    try:
        agent = ComplianceAgent()

        # Auto-ingest sample docs if vector store is empty
        stats = agent.document_store.get_collection_stats()
        if stats.get("document_count", 0) == 0:
            sample_dir = Path(__file__).parent.parent.parent / "sample_docs"
            sample_files = list(sample_dir.glob("*.txt")) + list(sample_dir.glob("*.pdf"))
            if sample_files:
                agent.ingest_documents([str(f) for f in sample_files])
                st.session_state.docs_ingested = True

        return agent
    except Exception as e:
        raise e


def render_sidebar():
    """Render sidebar with controls."""
    with st.sidebar:
        ui.badges(badge_list=[("Codex", "default"), ("AI Agent", "secondary")], class_name="flex gap-2")
        st.markdown("### Operational Risk & Compliance")

        # API Key check
        if not os.getenv('NVIDIA_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            ui.alert(title="API Key Missing", description="NVIDIA_API_KEY required")
            api_key = st.text_input("Enter NVIDIA API Key:", type="password")
            if api_key:
                os.environ['NVIDIA_API_KEY'] = api_key
                st.rerun()
            return False

        # Initialize agent
        if st.session_state.agent is None:
            with st.spinner("Initializing AI Agent..."):
                try:
                    st.session_state.agent = init_agent()
                except Exception as e:
                    ui.alert(title="Initialization Failed", description=str(e))

        if st.session_state.agent:
            st.success("🟢 Agent Ready")

            # Show current doc count
            try:
                stats = st.session_state.agent.document_store.get_collection_stats()
                doc_count = stats.get("document_count", 0)
                st.caption(f"📚 {doc_count} chunks in knowledge base")
            except Exception:
                pass

            # Document upload
            st.markdown("#### 📄 Knowledge Base")

            # Tab: File Upload vs URL
            upload_tab, url_tab = st.tabs(["⬆️ Upload File", "🔗 From URL"])

            with upload_tab:
                uploaded_files = st.file_uploader(
                    "Upload safety manuals, protocols...",
                    accept_multiple_files=True,
                    type=['pdf', 'txt'],
                    label_visibility="collapsed",
                )
                if uploaded_files:
                    if ui.button("Ingest Documents", key="ingest_btn"):
                        with st.spinner("Processing..."):
                            file_paths = []
                            for uploaded_file in uploaded_files:
                                tmp_dir = Path("./tmp_uploads")
                                tmp_dir.mkdir(exist_ok=True)
                                temp_path = tmp_dir / uploaded_file.name
                                with open(temp_path, 'wb') as f:
                                    f.write(uploaded_file.getvalue())
                                file_paths.append(str(temp_path))

                            chunks = st.session_state.agent.ingest_documents(file_paths)
                            st.success(f"✅ {len(uploaded_files)} file(s) → {chunks} chunks")

            with url_tab:
                doc_url = st.text_input(
                    "Document URL",
                    placeholder="https://example.com/safety_manual.pdf",
                    label_visibility="collapsed",
                )
                if ui.button("Load from URL", key="url_ingest_btn"):
                    if not doc_url:
                        st.warning("Please enter a URL")
                    else:
                        with st.spinner(f"Downloading from URL..."):
                            try:
                                import requests as req
                                import urllib.parse
                                parsed = urllib.parse.urlparse(doc_url)
                                filename = Path(parsed.path).name or "document.txt"

                                tmp_dir = Path("./tmp_uploads")
                                tmp_dir.mkdir(exist_ok=True)
                                temp_path = tmp_dir / filename

                                response = req.get(doc_url, timeout=30)
                                response.raise_for_status()
                                with open(temp_path, 'wb') as f:
                                    f.write(response.content)

                                chunks = st.session_state.agent.ingest_documents([str(temp_path)])
                                st.success(f"✅ Loaded `{filename}` → {chunks} chunks")
                            except Exception as e:
                                st.error(f"Failed to load URL: {str(e)}")

            # Stats
            st.markdown("---")
            if ui.button("View System Stats", key="stats_btn"):
                stats = st.session_state.agent.get_stats()
                st.json(stats)

        st.markdown("---")
        st.caption("Powered by NVIDIA AI · LangChain · LlamaIndex")

        return st.session_state.agent is not None


def render_custom_badges(engine, latency):
    """Render badges using same style as LlamaIndex badge."""
    ui.badges(
        badge_list=[
            (f"⚡ {engine}", "secondary"),
            (f"⏱️ {latency}ms", "secondary"),
            ("🛡️ RAG", "secondary"),
        ],
        class_name="flex gap-2 mt-1",
    )


def render_safety_check_tab(agent):
    """Render the safety check tab."""
    st.header("🛡️ Site Safety Check")

    col1, col2 = st.columns(2)

    with col1:
        site_location = st.text_input(
            "Site Location",
            placeholder="e.g., Boston, MA or Site Alpha",
            help="Enter a location name or site identifier",
        )

    with col2:
        operation_type = st.selectbox(
            "Operation Type",
            ["outdoor work", "crane operation", "roof work", "excavation", "concrete pouring", "other"],
        )
        if operation_type == "other":
            operation_type = st.text_input("Specify operation:")

    if ui.button("🚀 Run Safety Check", key="run_check_btn"):
        if not site_location:
            ui.alert(title="Input Required", description="Please enter a site location")
            return

        with st.spinner("Analyzing safety compliance..."):
            decision = agent.check_site_safety(
                site_location=site_location,
                operation_type=operation_type,
            )
            
            # Store decision for report generation
            st.session_state.last_decision = decision
            st.session_state.last_site_location = site_location
            st.session_state.last_operation_type = operation_type

        st.markdown("---")

        # Decision banner
        if decision.can_proceed:
            st.success(f"✅ SAFE TO PROCEED — {operation_type.title()} at {site_location}")
        else:
            st.error(f"🚫 DO NOT PROCEED — {operation_type.title()} at {site_location}")

        # Results columns
        col1, col2 = st.columns(2)

        with col1:
            weather_status = (
                decision.weather_compliance.get('compliance_status', 'Unknown')
                if decision.weather_compliance else "N/A"
            )
            ui.metric_card(title="Weather Status", content=weather_status, description="Real-time check")

            if decision.weather_compliance:
                weather = decision.weather_compliance
                if weather['violations']:
                    st.error("Violations Detected:")
                    for v in weather['violations'][:2]:
                        st.markdown(f"**{v['date']}**: {', '.join(v['issues'])}")
                else:
                    st.success("No active weather violations")

                if decision.current_conditions:
                    current = decision.current_conditions.get('current', {})
                    if current:
                        st.caption("Current Conditions")
                        cols = st.columns(3)
                        with cols[0]:
                            st.metric("Temp", f"{current.get('temperature_2m', 'N/A')}°C")
                        with cols[1]:
                            st.metric("Wind", f"{current.get('wind_speed_10m', 'N/A')} km/h")
                        with cols[2]:
                            st.metric("Rain", f"{current.get('precipitation', 'N/A')} mm")
            else:
                st.info("Weather data not available for this location")

        with col2:
            st.subheader("🧠 Reasoning")
            st.write(decision.reasoning)

            if decision.recommendations:
                st.markdown("**💡 Recommendations:**")
                for rec in decision.recommendations:
                    st.markdown(f"- {rec}")

        # Citations
        if decision.citations:
            with st.expander("📜 View Supporting Documents"):
                for citation in decision.citations[:3]:
                    st.markdown(f"**[{citation['number']}] `{citation['filename']}`**")
                    st.caption(citation.get('text_preview', '')[:200])
                    st.markdown("---")

        # Memory updates
        if decision.new_memories:
            with st.expander("🧪 Memory Updates"):
                for mem in decision.new_memories:
                    st.info(f"{mem['type'].title()} Memory: {mem['content']}")
        
        # Download report button
        st.markdown("---")
        if ui.button("📄 Download Safety Report", key="download_report_btn"):
            try:
                pdf_bytes = generate_safety_report(
                    site_location=site_location,
                    operation_type=operation_type,
                    decision=decision
                )
                st.download_button(
                    label="⬇️ Download PDF",
                    data=pdf_bytes,
                    file_name=f"safety_report_{site_location.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf"
                )
            except Exception as e:
                st.error(f"Failed to generate report: {str(e)}")
        
        # Weather Trends Section
        st.markdown("---")
        st.subheader("📈 7-Day Weather Trends")
        
        with st.spinner("Analyzing weather trends..."):
            try:
                from src.weather import OpenMeteoClient
                weather_client = OpenMeteoClient()
                trend_data = get_weather_trend_analysis(
                    weather_client=weather_client,
                    site_location=site_location,
                    days=7
                )
                
                if trend_data:
                    # Display trend as a table
                    trend_df_data = []
                    for day in trend_data:
                        trend_df_data.append({
                            'Date': day['date'],
                            'Status': '✅ Safe' if day['is_safe'] else '🚫 Unsafe',
                            'Wind (km/h)': f"{day['wind_speed']:.1f}",
                            'Gusts (km/h)': f"{day['wind_gusts']:.1f}",
                            'Rain (mm)': f"{day['precipitation']:.1f}",
                            'Issues': ', '.join(day['issues']) if day['issues'] else 'None'
                        })
                    
                    import pandas as pd
                    trend_df = pd.DataFrame(trend_df_data)
                    st.dataframe(trend_df, use_container_width=True)
                    
                    # Summary
                    safe_days = sum(1 for d in trend_data if d['is_safe'])
                    st.info(f"📅 **{safe_days} out of 7 days** are safe for {operation_type}")
                    
                    # Best day recommendation
                    safe_days_list = [d for d in trend_data if d['is_safe']]
                    if safe_days_list:
                        best_day = min(safe_days_list, key=lambda x: x['wind_speed'] + x['precipitation'])
                        st.success(f"⭐ **Best day to work:** {best_day['date']} (lowest risk)")
                else:
                    st.warning("Could not retrieve weather trend data")
            except Exception as e:
                st.error(f"Failed to load weather trends: {str(e)}")


def render_chat_tab(agent):
    """Render the chat/Q&A tab."""
    st.header("💬 Ask Codex")
    st.caption("Powered by LlamaIndex · Conversational RAG over your compliance documents")

    # Chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Render metadata if present
            if message["role"] == "assistant":
                metadata = message.get("metadata", {})
                if metadata:
                    render_custom_badges(
                        engine=metadata.get("engine", "LlamaIndex"),
                        latency=metadata.get("latency_ms", 0)
                    )
                    
                    citations = metadata.get("citations", [])
                    if citations:
                        with st.expander(f"[SOURCES] {len(citations)} Source(s)"):
                            for citation in citations[:3]:
                                st.markdown(f"**[{citation['number']}]** `{citation['filename']}`")
                                if citation.get('text_preview'):
                                    st.caption(citation['text_preview'])

    # Input
    if prompt := st.chat_input("Ask about safety rules, compliance, or procedures..."):
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Querying knowledge base..."):
                result = agent.ask_question(prompt)
                response = result['answer']
                
                # Metadata to persist
                metadata = {
                    "engine": result.get("engine", "LlamaIndex"),
                    "latency_ms": result.get("latency_ms", 0),
                    "citations": result.get("citations", [])
                }

            st.markdown(response)

            # Custom high-visibility badges
            render_custom_badges(
                engine=metadata["engine"],
                latency=metadata["latency_ms"]
            )

            if metadata['citations']:
                with st.expander(f"[SOURCES] {len(metadata['citations'])} Source(s)"):
                    for citation in metadata['citations'][:3]:
                        st.markdown(f"**[{citation['number']}]** `{citation['filename']}`")
                        if citation.get('text_preview'):
                            st.caption(citation['text_preview'])

        # Store message with metadata in history
        st.session_state.chat_history.append({
            "role": "assistant", 
            "content": response,
            "metadata": metadata
        })


def render_memory_tab():
    """Render the memory view tab."""
    st.header("🧠 Memory Viewer")

    memory_manager = MemoryManager()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("User Memory")
        user_memories = memory_manager.read_memories(memory_type=MemoryType.USER)
        if user_memories:
            for mem in user_memories[-10:]:
                st.markdown(f"- {mem.to_markdown()}")
        else:
            st.info("No user memories yet")

    with col2:
        st.subheader("Company Memory")
        company_memories = memory_manager.read_memories(memory_type=MemoryType.COMPANY)
        if company_memories:
            for mem in company_memories[-10:]:
                st.markdown(f"- {mem.to_markdown()}")
        else:
            st.info("No company memories yet")


def main():
    """Main Streamlit app."""
    agent_ready = render_sidebar()

    if not agent_ready:
        st.warning("👈 Please configure the agent in the sidebar")
        return

    tab1, tab2, tab3 = st.tabs([
        "🛡️ Safety Check",
        "💬 Chat",
        "🧠 Memory",
    ])

    with tab1:
        render_safety_check_tab(st.session_state.agent)

    with tab2:
        render_chat_tab(st.session_state.agent)

    with tab3:
        render_memory_tab()


if __name__ == '__main__':
    main()
