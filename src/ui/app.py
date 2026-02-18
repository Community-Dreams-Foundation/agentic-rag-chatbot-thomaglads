"""Streamlit web interface for Codex."""

import os
import sys
from pathlib import Path

import streamlit as st

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agent import ComplianceAgent
from src.memory import MemoryManager, MemoryType


import streamlit_shadcn_ui as ui

# Page configuration
st.set_page_config(
    page_title="Codex - AI Compliance Agent",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def init_agent():
    """Initialize the compliance agent."""
    if not os.getenv('NVIDIA_API_KEY') and not os.getenv('OPENAI_API_KEY'):
        # Fallback to OPENAI if user insists, but prefer NVIDIA
        return None
    
    try:
        return ComplianceAgent()
    except Exception as e:
        # Re-raise to be caught in render_sidebar
        raise e


def render_sidebar():
    """Render sidebar with controls."""
    with st.sidebar:
        ui.badges(badge_list=[("Codex", "default"), ("AI Agent", "secondary")], class_name="flex gap-2")
        st.markdown("### Operational Risk & Compliance")
        
        # API Key check
        if not os.getenv('NVIDIA_API_KEY') and not os.getenv('OPENAI_API_KEY'):
            ui.alert(title="API Key Missing", description="NVIDIA_API_KEY or OPENAI_API_KEY required", variant="destructive")
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
                    ui.alert(title="Initialization Failed", description=str(e), variant="destructive")
        
        if st.session_state.agent:
            ui.alert(title="System Ready", description="Agent is online", variant="default")
            
            # Document upload
            st.markdown("#### 📄 Knowledge Base")
            uploaded_files = st.file_uploader(
                "Upload safety manuals, protocols...",
                accept_multiple_files=True,
                type=['pdf', 'txt'],
            )
            
            if uploaded_files:
                if ui.button("Ingest Documents", key="ingest_btn"):
                    with st.spinner("Processing..."):
                        # Save uploaded files temporarily
                        file_paths = []
                        for uploaded_file in uploaded_files:
                            temp_path = f"/tmp/{uploaded_file.name}"
                            # Ensure tmp directory exists
                            os.makedirs("/tmp", exist_ok=True)
                            with open(temp_path, 'wb') as f:
                                f.write(uploaded_file.getvalue())
                            file_paths.append(temp_path)
                        
                        # Ingest
                        chunks = st.session_state.agent.ingest_documents(file_paths)
                        ui.metric_card(title="Documents Processed", content=f"{len(uploaded_files)} Files", description=f"{chunks} chunks created")
            
            # Stats
            st.markdown("---")
            if ui.button("View System Stats", variant="outline", key="stats_btn"):
                stats = st.session_state.agent.get_stats()
                st.json(stats)
        
        st.markdown("---")
        st.caption("Powered by NVIDIA AI & LangChain")
        
        return st.session_state.agent is not None


def render_safety_check_tab(agent):
    """Render the safety check tab."""
    st.header("🔍 Site Safety Check")
    
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
            ui.alert(title="Input Required", description="Please enter a site location", variant="destructive")
            return
        
        with st.spinner("Analyzing safety compliance..."):
            decision = agent.check_site_safety(
                site_location=site_location,
                operation_type=operation_type,
            )
        
        # Display results in cards
        st.markdown("---")
        
        # Decision card
        if decision.can_proceed:
            ui.alert(title="SAFE TO PROCEED", description=f"{operation_type.title()} at {site_location}", variant="default")
        else:
            ui.alert(title="DO NOT PROCEED", description=f"{operation_type.title()} at {site_location}", variant="destructive")
        
        # Results columns
        col1, col2 = st.columns(2)
        
        with col1:
            ui.metric_card(title="Weather Status", content=decision.weather_compliance.get('compliance_status', 'Unknown') if decision.weather_compliance else "N/A", description="Real-time check")
            
            if decision.weather_compliance:
                weather = decision.weather_compliance
                if weather['violations']:
                    st.error("Violations Detected:")
                    for v in weather['violations'][:2]:  # Show first 2
                        st.markdown(f"**{v['date']}**: {', '.join(v['issues'])}")
                else:
                    st.success("No active weather violations")
                
                # Current conditions
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
                    ui.alert(title="Recommendation", description=rec, variant="secondary")
        
        # Citations
        if decision.citations:
            with st.expander("📚 View Supporting Documents"):
                for citation in decision.citations[:3]:
                    ui.card(title=f"[{citation['number']}] {citation['filename']}", content=citation['text_preview'][:200] + "...", description=f"Rel: {citation['relevance_score']}")
        
        # Memory updates
        if decision.new_memories:
            with st.expander("💾 Memory Updates"):
                for mem in decision.new_memories:
                    st.info(f"{mem['type'].title()} Memory: {mem['content']}")


def render_chat_tab(agent):
    """Render the chat/Q&A tab."""
    st.header("💬 Ask Codex")
    
    # Chat interface
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # Input
    if prompt := st.chat_input("Ask about safety rules, compliance, or procedures..."):
        # Add user message
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                result = agent.ask_question(prompt)
                response = result['answer']
            
            st.markdown(response)
            
            # Show citations
            if result['citations']:
                with st.expander("📚 Sources"):
                    for citation in result['citations'][:3]:
                        st.markdown(f"[{citation['number']}] {citation['filename']}")
        
        # Add assistant message
        st.session_state.chat_history.append({"role": "assistant", "content": response})


def render_memory_tab():
    """Render the memory view tab."""
    st.header("🧠 Memory Viewer")
    
    memory_manager = MemoryManager()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("User Memory")
        user_memories = memory_manager.read_memories(memory_type=MemoryType.USER)
        if user_memories:
            for mem in user_memories[-10:]:  # Show last 10
                st.markdown(f"- {mem.to_markdown()}")
        else:
            st.info("No user memories yet")
    
    with col2:
        st.subheader("Company Memory")
        company_memories = memory_manager.read_memories(memory_type=MemoryType.COMPANY)
        if company_memories:
            for mem in company_memories[-10:]:  # Show last 10
                st.markdown(f"- {mem.to_markdown()}")
        else:
            st.info("No company memories yet")


def main():
    """Main Streamlit app."""
    # Sidebar
    agent_ready = render_sidebar()
    
    if not agent_ready:
        st.warning("👈 Please configure the agent in the sidebar")
        return
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "🔍 Safety Check",
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
