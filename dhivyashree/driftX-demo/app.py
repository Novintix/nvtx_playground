import streamlit as st
import os
from dotenv import load_dotenv
load_dotenv()
import time
import PyPDF2
from mcp_server.tools.git_reader import clone_repo, cleanup_repo
from agents.compliance_agent import ComplianceAgent
from agents.quality_agent import QualityAgent

st.set_page_config(
    page_title="DriftX 2.0 - Compliance Gateway", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Validate API key
if not os.getenv('GOOGLE_API_KEY'):
    st.error("⚠️ Configuration Error: GOOGLE_API_KEY not found in environment variables.")
    st.info("Please check your .env file and ensure GOOGLE_API_KEY is set.")
    st.stop()

def extract_text_from_file(uploaded_file):
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(uploaded_file)
            for page in reader.pages:
                text += page.extract_text() or ""
        else:
            # Assume text/md
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {e}")
    return text

def display_standard_compliance(compliance_results, quality_results):
    """Display Standard Compliance Analysis Results"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔍 Drift Analysis with AI Remediation")
        drift_score = compliance_results.get("drift_score", 0)
        st.metric("Drift Compliance Score", f"{drift_score}/100")
        
        if compliance_results.get("drift_detected"):
            st.error("Drift Detected!")
        elif "error" in compliance_results:
            st.error(f"Analysis Failed: {compliance_results['error']}")
        else:
            st.success("Requirements Aligned")
            
        with st.expander("View Drift Details & Remediation"):
            for issue in compliance_results.get("issues", []):
                st.write(f"**{issue.get('type')}**: {issue.get('description')}")
                st.caption(f"Evidence: {issue.get('evidence', 'N/A')}")
                st.caption(f"Reasoning: {issue.get('reasoning')}")
                st.info(f"🤖 AI Remediation: {issue.get('rectification')}")
                st.divider()

    with col2:
        st.subheader("✅ Code Compliance with AI Remediation")
        review = quality_results.get("review", {})
        if "error" in quality_results:
            st.error(f"Quality Analysis Failed: {quality_results['error']}")
        elif "error" in review:
            st.error(f"LLM Review Failed: {review['error']}")

        compliance_score = review.get("score", 0)
        st.metric("Code Compliance Score", f"{compliance_score}/100")
        
        st.write(f"**Summary**: {review.get('summary')}")
        
        with st.expander("View Compliance Issues & Remediation"):
            for issue in review.get("issues", []):
                st.write(f"**{issue.get('title')}** ({issue.get('severity')})")
                st.write(issue.get('description'))
                st.caption(f"Reasoning: {issue.get('reasoning')}")
                st.warning(f"🤖 AI Remediation: {issue.get('rectification')}")
                st.divider()

    # Final Score
    final_score = (drift_score + compliance_score) / 2
    st.divider()
    st.header("🏁 Standard Compliance Gate")
    st.write(f"**Final Score**: {final_score:.1f}/100")
    
    if final_score > 90:
        st.balloons()
        st.success("✅ Quality Gate Passed! Code is ready for deployment.")
        deploy_col, _ = st.columns([1, 4])
        with deploy_col:
            if st.button("🚀 Deploy to Production"):
                st.toast("Initiating Deployment Pipeline...", icon="🚀")
                time.sleep(2)
                st.success("Deployment Triggered Successfully!")
    else:
        st.error("⛔ Quality Gate Failed. Score must be > 90.")
        st.markdown("Please address the issues listed above and retry.")

def display_evaluation_analysis(evaluation_results, history_results=None):
    """Display Evaluation Analysis Results with Review History Tab"""
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📉 Feature Loss", "🎯 Coverage Gap", "📜 Review History"])
    
    with tab1:
        st.subheader("Feature Loss Analysis")
        feature_loss_score = evaluation_results.get("feature_loss_score", 0)
        st.metric("Feature Completeness", f"{feature_loss_score}/100")
        
        with st.expander("View Feature Loss Details & Remediation", expanded=True):
            for issue in evaluation_results.get("feature_loss_issues", []):
                st.write(f"**{issue.get('feature')}**")
                st.write(issue.get('description'))
                st.caption(f"Impact: {issue.get('impact')}")
                st.caption(f"Reasoning: {issue.get('reasoning')}")
                st.info(f"🤖 AI Remediation: {issue.get('remediation')}")
                st.divider()

    with tab2:
        st.subheader("Coverage Gap Analysis")
        coverage_score = evaluation_results.get("coverage_score", 0)
        st.metric("Coverage Score", f"{coverage_score}/100")
        
        with st.expander("View Coverage Gaps & Remediation", expanded=True):
            for issue in evaluation_results.get("coverage_gaps", []):
                st.write(f"**{issue.get('area')}**")
                st.write(issue.get('description'))
                st.caption(f"Gap Type: {issue.get('gap_type')}")
                st.caption(f"Reasoning: {issue.get('reasoning')}")
                st.warning(f"🤖 AI Remediation: {issue.get('remediation')}")
                st.divider()
    
    with tab3:
        st.subheader("Review History - Commit Analysis")
        
        if history_results and "error" not in history_results:
            # Metadata
            metadata = history_results.get("analysis_metadata", {})
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Commits Analyzed", history_results.get("total_commits_analyzed", 0))
            with col2:
                st.metric("Commits with Deletions", history_results.get("commits_with_deletions", 0))
            with col3:
                st.metric("Critical Issues", history_results.get("critical_issues_found", 0))
            with col4:
                deployment_risk = history_results.get("deployment_risk", "Unknown")
                risk_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(deployment_risk, "⚪")
                st.metric("Deployment Risk", f"{risk_color} {deployment_risk}")
            
            # Repository Score Card
            st.divider()
            st.subheader("📊 Repository Score Card")
            scorecard = history_results.get("repo_score_card", {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Feature Completeness", f"{scorecard.get('feature_completeness', 0)}/100")
                st.metric("Code Stability", f"{scorecard.get('code_stability', 0)}/100")
            with col2:
                st.metric("Requirement Alignment", f"{scorecard.get('requirement_alignment', 0)}/100")
                overall = scorecard.get('overall_score', 0)
                grade = scorecard.get('grade', 'N/A')
                st.metric("Overall Score", f"{overall}/100 (Grade: {grade})")
            
            # Feature Loss Issues from History
            st.divider()
            st.subheader("🚨 Historical Feature Loss Issues")
            
            issues = history_results.get("feature_loss_issues", [])
            if not issues:
                st.success("✅ No feature loss detected in commit history!")
            else:
                for idx, issue in enumerate(issues, 1):
                    severity = issue.get('severity', 'Unknown')
                    severity_icon = {
                        "Critical": "🔴",
                        "High": "🟠", 
                        "Medium": "🟡",
                        "Low": "🟢"
                    }.get(severity, "⚪")
                    
                    with st.expander(f"{severity_icon} Issue #{idx}: {issue.get('feature_name')} ({severity})"):
                        st.write(f"**Evidence**: {issue.get('evidence')}")
                        st.write(f"**Requirement Reference**: {issue.get('requirement_reference')}")
                        st.write(f"**Impact**: {issue.get('impact')}")
                        st.write(f"**Commit Info**: {issue.get('commit_info')}")
                        st.caption(f"**Reasoning**: {issue.get('reasoning')}")
                        st.info(f"🤖 **Remediation**: {issue.get('remediation')}")
            
            # Commit History Context
            if metadata:
                with st.expander("📋 Commit History Context"):
                    st.write(f"**Oldest Commit**: {metadata.get('oldest_commit', 'N/A')}")
                    st.write(f"**Newest Commit**: {metadata.get('newest_commit', 'N/A')}")
                    st.write(f"**Total Commits**: {metadata.get('total_commits_in_history', 0)}")
                    st.write(f"**Analysis Date**: {metadata.get('analysis_date', 'N/A')}")
        else:
            st.info("📜 Commit history analysis provides insights into code changes over time.")
            st.write("This tab shows:")
            st.write("- Features that were removed in previous commits")
            st.write("- Code deletions that may impact requirements")
            st.write("- Repository quality score card")
            st.write("- Deployment risk assessment")
            
            if history_results and "error" in history_results:
                st.warning(f"⚠️ History analysis unavailable: {history_results['error']}")

    # Final Score (below tabs)
    final_score = (evaluation_results.get("feature_loss_score", 0) + evaluation_results.get("coverage_score", 0)) / 2
    st.divider()
    st.header("🏁 Evaluation Analysis Score")
    st.write(f"**Final Score**: {final_score:.1f}/100")
    
    # Summary
    st.subheader("📊 Analysis Summary")
    st.write(evaluation_results.get("summary", "Analysis completed."))
    
    if final_score > 90:
        st.balloons()
        st.success("✅ Evaluation Passed! Implementation meets requirements.")
    elif final_score > 75:
        st.warning("⚠️ Evaluation shows gaps. Review remediation suggestions.")
    else:
        st.error("⛔ Significant gaps detected. Major improvements needed.")




def main():
    st.title("🛡️ DriftX 2.0: Compliance Gateway Agent")
    st.markdown("""
    Welcome to DriftX 2.0. This agent acts as a quality gate for your software deployment.
    Choose your analysis mode and upload your documents to get started.
    """)
    
    # Add info box
    with st.expander("ℹ️ How to use DriftX 2.0"):
        st.markdown("""
        **Standard Compliance Mode:**
        - Analyzes requirement drift (missing/extra/modified features)
        - Checks code compliance against Do's and Don'ts guidelines
        - Provides AI-generated remediation for all issues
        
        **Evaluation Analysis Mode:**
        - Identifies feature loss (missing or incomplete features)
        - Analyzes coverage gaps (security, best practices, error handling)
        - Provides detailed implementation guidance
        - **Review History Tab**: View commit history analysis showing code deletions and feature loss over time
        
        **Required Inputs:**
        - Git repository URL (GitHub, GitLab, Bitbucket)
        - Requirement documents (PDF, TXT, or MD)
        - Do's and Don'ts guidelines (optional but recommended)
        
        **Scoring:**
        - 90-100: Ready for deployment ✅
        - 75-89: Minor improvements needed ⚠️
        - Below 75: Major issues to address ⛔
        """)

    # Sidebar for Inputs
    with st.sidebar:
        st.header("🚀 Configuration")
        
        # Analysis Mode Selection
        analysis_mode = st.radio(
            "Analysis Mode",
            ["Standard Compliance", "Evaluation Analysis"],
            help="Standard: Drift + Code Compliance | Evaluation: Feature Loss + Coverage Gap + Review History"
        )
        
        repo_url = st.text_input("Git Repository URL", placeholder="https://github.com/user/repo")
        uploaded_files = st.file_uploader("Upload Requirement Docs", accept_multiple_files=True, type=['pdf', 'txt', 'md'])
        dos_donts_files = st.file_uploader("Upload Do's and Don'ts Docs", accept_multiple_files=True, type=['pdf', 'txt', 'md'])
        
        process_btn = st.button("Start Analysis")

    if process_btn:
        if not repo_url or not uploaded_files:
            st.error("Please provide both a Git URL and Requirement Documents.")
        else:
            st.info("🔄 Initializing Agents... Please wait.")
            
            # 1. Extract Requirements
            requirements_text = ""
            for uploaded_file in uploaded_files:
                requirements_text += f"\n\n--- {uploaded_file.name} ---\n"
                requirements_text += extract_text_from_file(uploaded_file)
            
            # 2. Extract Do's and Don'ts
            dos_donts_text = ""
            if dos_donts_files:
                for uploaded_file in dos_donts_files:
                    dos_donts_text += f"\n\n--- {uploaded_file.name} ---\n"
                    dos_donts_text += extract_text_from_file(uploaded_file)
            
            repo_path = None
            try:
                # 3. Clone Repository
                with st.spinner("Cloning Repository..."):
                    repo_path = clone_repo(repo_url)
                
                if analysis_mode == "Standard Compliance":
                    # Standard Compliance Mode
                    # 4a. Drift Analysis
                    compliance_agent = ComplianceAgent()
                    with st.spinner("🤖 Compliance Agent is analyzing Drift..."):
                        compliance_results = compliance_agent.analyze(repo_path, requirements_text, dos_donts_text)
                    
                    # 4b. Code Compliance Analysis
                    quality_agent = QualityAgent()
                    with st.spinner("🕵️ Quality Agent is checking Code Compliance..."):
                        quality_results = quality_agent.analyze_compliance(repo_path, dos_donts_text)
                    
                    # Display Standard Compliance Results
                    display_standard_compliance(compliance_results, quality_results)
                    
                else:
                    # Evaluation Analysis Mode with Review History
                    compliance_agent = ComplianceAgent()
                    
                    with st.spinner("🔍 Analyzing Feature Loss and Coverage Gap..."):
                        evaluation_results = compliance_agent.evaluate_analysis(repo_path, requirements_text, dos_donts_text)
                    
                    with st.spinner("📜 Analyzing commit history for review..."):
                        history_results = compliance_agent.analyze_feature_loss_with_history(repo_path, requirements_text, dos_donts_text)
                    
                    # Display Evaluation Results with History
                    display_evaluation_analysis(evaluation_results, history_results)
                    


            except Exception as e:
                st.error(f"An error occurred: {e}")
            finally:
                if repo_path:
                    cleanup_repo(repo_path)

if __name__ == "__main__":
    main()
