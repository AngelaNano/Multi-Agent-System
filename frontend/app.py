import streamlit as st
import requests
import time
import json
from datetime import datetime

# ── PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Multi-Agent Research System",
    page_icon="🤖",
    layout="wide"
)

API_URL = "http://localhost:8000"

# ── HEADER ────────────────────────────────────────────────────────
st.title("🤖 Multi-Agent Research System")
st.markdown("*Powered by AWS Bedrock Agents + Step Functions + DynamoDB*")
st.divider()
st.info("🌐 Live Demo Mode — Backend runs locally. Clone the repo and run FastAPI to enable full functionality.")

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.header("System Info")
    st.markdown("**AWS Services:**")
    st.markdown("- 🧠 Bedrock Agents")
    st.markdown("- ⚡ Step Functions")
    st.markdown("- 🗄️ DynamoDB")
    st.markdown("- 📦 S3")
    st.markdown("- λ Lambda")
    st.divider()
    st.markdown("**Pipeline:**")
    st.markdown("1. Research Agent")
    st.markdown("2. Analysis Agent")
    st.markdown("3. Writer Agent")
    st.markdown("4. HITL Approval")
    st.divider()

    # Check API health
    try:
        health = requests.get(f"{API_URL}/", timeout=3)
        if health.status_code == 200:
            st.success("✅ API Online")
        else:
            st.error("❌ API Offline")
    except:
        st.error("❌ API Offline")

# ── MAIN TABS ─────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🔬 Research", "📊 Reports", "🔍 Sessions"])

# ── TAB 1: RESEARCH ───────────────────────────────────────────────
with tab1:
    st.header("Start New Research")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        topic = st.text_input(
            "Research Topic",
            placeholder="e.g., AWS Bedrock, multi-agent systems, machine learning...",
            help="Enter any topic to research"
        )
    with col2:
        session_id = st.text_input(
            "Session ID (optional)",
            placeholder="auto-generated"
        )
    
    if st.button("🚀 Start Research Pipeline", type="primary", disabled=not topic):
        with st.spinner("Starting pipeline..."):
            try:
                response = requests.post(
                    f"{API_URL}/research",
                    json={
                        "topic": topic,
                        "session_id": session_id or ""
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    st.session_state['execution_arn'] = data['execution_arn']
                    st.session_state['session_id'] = data['session_id']
                    st.session_state['topic'] = topic
                    st.success(f"✅ Pipeline started! Session: {data['session_id']}")
                else:
                    st.error(f"Error: {response.text}")
            except Exception as e:
                st.error(f"Could not connect to API: {e}")
    
    # Show pipeline progress if running
    if 'execution_arn' in st.session_state:
        st.divider()
        st.subheader(f"Pipeline Status: {st.session_state.get('topic', '')}")
        
        
        status_placeholder = st.empty()
        progress_placeholder = st.empty()
        result_placeholder = st.empty()
        
        # Poll for status
        if st.button("🔄 Check Status"):
            try:
                status_response = requests.get(
                    f"{API_URL}/status/{st.session_state['execution_arn']}"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data['status']
                    
                    if status == "RUNNING":
                        status_placeholder.info("⏳ Pipeline running...")
                        
                        # Show checkpoints from DynamoDB
                        session_response = requests.get(
                            f"{API_URL}/session/{st.session_state['session_id']}"
                        )
                        if session_response.status_code == 200:
                            checkpoints = session_response.json().get('checkpoints', [])
                            if checkpoints:
                                progress_placeholder.markdown("**Completed steps:**")
                                for cp in checkpoints:
                                    step = cp.get('step', cp.get('status', 'unknown'))
                                    progress_placeholder.markdown(f"✅ {step}")
                    
                    elif status == "SUCCEEDED":
                        status_placeholder.success("✅ Pipeline completed successfully!")
                        output = status_data.get('output', {})
                        
                        if output:
                            report_location = output.get('report_location', '')
                            if report_location:
                                result_placeholder.success(f"📄 Report saved: {report_location}")
                                
                                # Show approval status
                                approval = output.get('approval_status', 'unknown')
                                result_placeholder.info(f"🔍 HITL Status: {approval.upper()}")
                    
                    elif status == "FAILED":
                        status_placeholder.error("❌ Pipeline failed")
                        
            except Exception as e:
                st.error(f"Error checking status: {e}")

# ── TAB 2: REPORTS ────────────────────────────────────────────────
with tab2:
    st.header("Generated Reports")
    
    if st.button("🔄 Refresh Reports"):
        try:
            response = requests.get(f"{API_URL}/reports")
            if response.status_code == 200:
                data = response.json()
                reports = data.get('reports', [])
                
                if reports:
                    st.success(f"Found {data['total']} reports")
                    
                    for report in reports:
                        with st.expander(f"📄 {report['key']}"):
                            st.markdown(f"**Size:** {report['size']} bytes")
                            st.markdown(f"**Created:** {report['last_modified']}")
                            
                            if st.button(f"📖 View Report", key=report['key']):
                                report_response = requests.get(
                                    f"{API_URL}/report/{report['key']}"
                                )
                                if report_response.status_code == 200:
                                    content = report_response.json()['content']
                                    st.text_area("Report Content", content, height=400)
                else:
                    st.info("No reports yet. Run a research pipeline first.")
        except Exception as e:
            st.error(f"Could not load reports: {e}")

# ── TAB 3: SESSIONS ───────────────────────────────────────────────
with tab3:
    st.header("Session Checkpoints")
    st.markdown("View DynamoDB checkpoints for any session")
    
    lookup_session = st.text_input(
        "Session ID",
        value=st.session_state.get('session_id', ''),
        placeholder="e.g., session-20260510-123456"
    )
    
    if st.button("🔍 Look Up Session") and lookup_session:
        try:
            response = requests.get(f"{API_URL}/session/{lookup_session}")
            if response.status_code == 200:
                data = response.json()
                checkpoints = data.get('checkpoints', [])
                
                if checkpoints:
                    st.success(f"Found {len(checkpoints)} checkpoints")
                    
                    for cp in checkpoints:
                        step = cp.get('step', cp.get('status', 'checkpoint'))
                        status = cp.get('status', 'unknown')
                        timestamp = cp.get('timestamp', '')
                        
                        col1, col2, col3 = st.columns([2, 2, 3])
                        with col1:
                            st.markdown(f"**{step}**")
                        with col2:
                            if status == 'APPROVED':
                                st.success(status)
                            elif status == 'IN_PROGRESS':
                                st.info(status)
                            else:
                                st.warning(status)
                        with col3:
                            st.markdown(timestamp)
                else:
                    st.info("No checkpoints found for this session.")
        except Exception as e:
            st.error(f"Could not load session: {e}")