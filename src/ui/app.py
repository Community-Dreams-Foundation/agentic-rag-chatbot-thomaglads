"""Streamlit web interface for Codex."""

import os
import sys
from pathlib import Path

import streamlit as st

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.agent import ComplianceAgent
from src.memory import MemoryManager, MemoryType


# Page configuration
st.set_page_config(
    page_title="Codex - Compliance Agent",
    page_icon="🛡️",
    layout="wide",
)

# Initialize session state
if 'agent' not in st.session_state:
    st.session_state.agent = None

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


def init_agent():
    """Initialize the compliance agent."""
    if not os.getenv('OPENAI_API_KEY'):
        st.error("❌ OPENAI_API_KEY not found. Please set it in your environment.")
        return None
    
    try:
        return ComplianceAgent()
    except Exception as e:
        st.error(f"❌ Error initializing agent: {e}")
        return None


def render_sidebar():
    """Render sidebar with controls."""
    with st.sidebar:
        st.title("🛡️ Codex")
        st.markdown("*Operational Risk & Compliance Agent*")
        st.markdown("---")
        
        # API Key check
        if not os.getenv('OPENAI_API_KEY'):
            st.error("⚠️ OPENAI_API_KEY required")
            api_key = st.text_input("Enter OpenAI API Key:", type="password")
            if api_key:
                os.environ['OPENAI_API_KEY'] = api_key
                st.rerun()
            return False
        
        # Initialize agent
        if st.session_state.agent is None:
            with st.spinner("Initializing..."):
                st.session_state.agent = init_agent()
        
        if st.session_state.agent:
            st.success("✅ Agent Ready")
            
            # Document upload
            st.markdown("### 📄 Upload Documents")
            uploaded_files = st.file_uploader(
                "Upload safety manuals, protocols...",
                accept_multiple_files=True,
                type=['pdf', 'txt'],
            )
            
            if uploaded_files and st.button("Ingest Documents"):
                with st.spinner("Processing..."):
                    # Save uploaded files temporarily
                    file_paths = []
                    for uploaded_file in uploaded_files:
                        temp_path = f"/tmp/{uploaded_file.name}"
                        with open(temp_path, 'wb') as f:
                            f.write(uploaded_file.getvalue())
                        file_paths.append(temp_path)
                    
                    # Ingest
                    chunks = st.session_state.agent.ingest_documents(file_paths)
                    st.success(f"✅ Ingested {chunks} chunks")
            
            # Stats
            if st.button("📊 Show Stats"):
                stats = st.session_state.agent.get_stats()
                st.json(stats)
        
        st.markdown("---")
        st.markdown("**Built for Agentic RAG Hackathon**")
        
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
    
    if st.button("🚀 Run Safety Check", type="primary"):
        if not site_location:
            st.warning("Please enter a site location")
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
            st.success(f"✅ SAFE TO PROCEED - {operation_type.title()} at {site_location}")
        else:
            st.error(f"❌ DO NOT PROCEED - {operation_type.title()} at {site_location}")
        
        # Results columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🌤️ Weather Analysis")
            if decision.weather_compliance:
                weather = decision.weather_compliance
                
                status_color = "🟢" if weather['compliance_status'] == "COMPLIANT" else "🔴"
                st.write(f"Status: {status_color} {weather['compliance_status']}")
                
                if weather['violations']:
                    st.markdown("**Violations:**")
                    for v in weather['violations'][:2]:  # Show first 2
                        st.markdown(f"- **{v['date']}**")
                        for issue in v['issues']:
                            st.markdown(f"  - {issue}")
                else:
                    st.write("✅ No weather violations")
                
                # Current conditions
                if decision.current_conditions:
                    current = decision.current_conditions.get('current', {})
                    if current:
                        st.markdown("**Current Conditions:**")
                        if 'temperature_2m' in current:
                            st.write(f"🌡️ Temperature: {current['temperature_2m']}°C")
                        if 'wind_speed_10m' in current:
                            st.write(f"💨 Wind: {current['wind_speed_10m']} km/h")
                        if 'precipitation' in current:
                            st.write(f"🌧️ Precipitation: {current['precipitation']} mm")
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
            with st.expander("📚 View Sources"):
                for citation in decision.citations[:5]:
                    st.markdown(f"**[{citation['number']}] {citation['filename']}**")
                    st.markdown(f"Relevance: {citation['relevance_score']}")
                    st.markdown(f"> {citation['text_preview'][:150]}...")
                    st.markdown("---")
        
        # Memory updates
        if decision.new_memories:
            with st.expander("💾 Memory Updates"):
                for mem in decision.new_memories:
                    st.markdown(f"**{mem['type'].title()} Memory:** {mem['content']}")


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
