import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
import json
from datetime import datetime
from mcp_server.tools.commit_analyzer import CommitAnalyzer

class ComplianceAgent:
    def __init__(self, model_name="gemini-pro"):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)

    def analyze(self, repo_path, requirements_text, dos_donts_text=""):
        """
        Checks for Requirement Drift with Do's and Don'ts compliance.
        """
        code_context = self._get_code_summary(repo_path)
        
        prompt = PromptTemplate(
            template="""
            You are a Compliance Officer checking for "Requirement Drift".
            
            Requirements Document:
            {requirements}
            
            Do's and Don'ts Guidelines:
            {dos_donts}
            
            Implemented Code Context:
            {code_context}
            
            Your Task:
            1. Compare the Requirements vs. Actual Code.
            2. Check compliance with Do's and Don'ts guidelines.
            3. Detect **MISSING** features (in requirements but not in code).
            4. Detect **EXTRA** features (in code but not in requirements - "Gold Plating").
            5. Detect **MODIFIED** features (implemented differently than required).
            6. Detect violations of Do's and Don'ts guidelines.
            
            Scoring Rubric (Start at 100):
            - -20 points: Major feature MISSING.
            - -15 points: Violation of critical "Don't" guideline.
            - -10 points: Feature MODIFIED significantly without justification.
            - -10 points: Missing critical "Do" guideline.
            - -5 points: Minor EXTRA feature (gold plating).
            - -5 points: Missing minor edge case or validation.
            
            For EACH drift item, provide:
            - **Evidence**: Quote the specific file and code snippet that proves your point.
            - **Reasoning**: Why you think it's drift or non-compliant.
            - **Rectification**: How to align code with requirements and guidelines.
            
            Output JSON format ONLY:
            {{
                "drift_score": 90, 
                "drift_detected": true/false,
                "issues": [
                    {{
                        "type": "Missing/Extra/Modified/Guideline Violation",
                        "description": "...",
                        "evidence": "File: ... Code: ...",
                        "reasoning": "...",
                        "rectification": "..."
                    }}
                ]
            }}
            """,
            input_variables=["requirements", "dos_donts", "code_context"]
        )
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "requirements": requirements_text[:10000],
                "dos_donts": dos_donts_text[:5000] if dos_donts_text else "No specific guidelines provided.",
                "code_context": code_context
            })
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {"error": str(e), "drift_score": 0, "issues": []}

    def _get_code_summary(self, repo_path):
        # Universal file reader
        summary = ""
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root: continue
            
            summary += f"\nDirectory: {root}\nFiles: {', '.join(files)}\n"
            for file in files:
                 # Skip known binary/system files
                 if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.git', '.exe', '.dll', '.so', '.dylib')):
                     continue
                     
                 # Try to read every file as text with multiple encodings
                 file_path = os.path.join(root, file)
                 try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Limit to first 2000 chars per file to check features
                        summary += f"--- {file} ---\n{content[:2000]}\n"
                 except: 
                     # Skip non-text files
                     pass
        return summary[:30000]

    def evaluate_analysis(self, repo_path, requirements_text, dos_donts_text=""):
        """
        Performs Evaluation Analysis: Feature Loss and Coverage Gap.
        """
        code_context = self._get_code_summary(repo_path)
        
        prompt = PromptTemplate(
            template="""
            You are a Technical Evaluator performing comprehensive analysis.
            
            Requirements Document:
            {requirements}
            
            Do's and Don'ts Guidelines:
            {dos_donts}
            
            Implemented Code Context:
            {code_context}
            
            Your Task:
            Perform TWO types of analysis:
            
            1. **FEATURE LOSS ANALYSIS**:
               - Identify features specified in requirements that are missing or incomplete in code
               - Assess the impact of each missing feature
               - Score based on completeness (100 = all features present)
               
            2. **COVERAGE GAP ANALYSIS**:
               - Compare code against Do's and Don'ts guidelines
               - Identify areas where guidelines are not followed
               - Check for missing best practices, security measures, error handling
               - Score based on guideline coverage (100 = full compliance)
            
            Scoring Rubric:
            Feature Loss Score (Start at 100):
            - -25 points: Critical feature completely missing
            - -15 points: Major feature partially implemented
            - -10 points: Minor feature missing
            - -5 points: Feature implemented but incomplete
            
            Coverage Score (Start at 100):
            - -20 points: Critical "Don't" guideline violated
            - -15 points: Critical "Do" guideline missing
            - -10 points: Important best practice not followed
            - -5 points: Minor guideline deviation
            
            For EACH issue, provide:
            - **Reasoning**: Why this is a problem
            - **Remediation**: Specific steps to fix it
            
            Output JSON format ONLY:
            {{
                "feature_loss_score": 85,
                "coverage_score": 90,
                "feature_loss_issues": [
                    {{
                        "feature": "Feature name",
                        "description": "What's missing",
                        "impact": "High/Medium/Low",
                        "reasoning": "Why this matters",
                        "remediation": "How to implement it"
                    }}
                ],
                "coverage_gaps": [
                    {{
                        "area": "Area name",
                        "description": "What's not covered",
                        "gap_type": "Security/Best Practice/Guideline/Error Handling",
                        "reasoning": "Why this is a gap",
                        "remediation": "How to address it"
                    }}
                ],
                "summary": "Overall evaluation summary"
            }}
            """,
            input_variables=["requirements", "dos_donts", "code_context"]
        )
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "requirements": requirements_text[:10000],
                "dos_donts": dos_donts_text[:5000] if dos_donts_text else "No specific guidelines provided.",
                "code_context": code_context
            })
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {
                "error": str(e), 
                "feature_loss_score": 0, 
                "coverage_score": 0,
                "feature_loss_issues": [],
                "coverage_gaps": [],
                "summary": f"Analysis failed: {str(e)}"
            }

    def analyze_feature_loss_with_history(self, repo_path, requirements_text, dos_donts_text=""):
        """
        Analyzes feature loss by comparing commit history with requirements.
        Detects features that existed in earlier commits but were removed.
        Provides scoring for each repository to track mistakes over time.
        """
        # Get commit analysis
        commit_analyzer = CommitAnalyzer(repo_path)
        commit_history = commit_analyzer.get_commit_history(max_commits=50)
        
        if len(commit_history) < 2:
            return {
                "error": "Not enough commit history to analyze feature loss",
                "score": 0
            }
        
        # Get feature loss context
        feature_loss_context = commit_analyzer.get_feature_loss_context(max_commits=20)
        
        # Get detailed deletions between first and last commit
        initial_vs_recent = commit_analyzer.analyze_feature_loss(
            initial_commit_index=-1,  # Oldest commit
            recent_commit_index=0      # Most recent commit
        )
        
        # Get current code context
        code_context = self._get_code_summary(repo_path)
        
        prompt = PromptTemplate(
            template="""
            You are a Feature Loss Detective analyzing commit history to identify removed features.
            
            Requirements Document:
            {requirements}
            
            Do's and Don'ts Guidelines:
            {dos_donts}
            
            Current Code Context:
            {code_context}
            
            Commit History Analysis:
            {commit_analysis}
            
            Deleted Code Between Initial and Recent Commits:
            {deletions}
            
            Your Task:
            1. **Identify Feature Loss**: Find features that existed in earlier commits but are now removed
            2. **Cross-reference Requirements**: Check if removed features are still in requirements
            3. **Assess Impact**: Determine if removal was intentional or accidental
            4. **Track Patterns**: Identify if developer is "vibe coding" (removing features without checking requirements)
            5. **Prevent Cloud Deployment Issues**: Flag critical removals that would break production
            
            Analysis Focus:
            - Code that was deleted but NOT replaced with equivalent functionality
            - Features mentioned in requirements but missing in current code
            - Functions/classes/modules that existed before but are gone now
            - Critical functionality removed in recent commits
            
            Scoring Rubric (Start at 100):
            - -30 points: Critical feature from requirements deleted and not replaced
            - -25 points: Major functionality removed without documentation
            - -20 points: Security/validation code deleted
            - -15 points: Important feature partially removed
            - -10 points: Minor feature removed but still in requirements
            - -5 points: Code refactored but functionality preserved
            
            For EACH feature loss issue, provide:
            - **Feature Name**: What was removed
            - **Evidence**: Specific files and code that were deleted
            - **Requirement Reference**: Quote from requirements showing it's still needed
            - **Impact**: How this affects production deployment
            - **Commit Info**: When it was removed (commit hash/message)
            - **Reasoning**: Why this is problematic
            - **Remediation**: How to restore or replace the feature
            
            Output JSON format ONLY:
            {{
                "feature_loss_score": 85,
                "total_commits_analyzed": 20,
                "commits_with_deletions": 5,
                "critical_issues_found": 2,
                "feature_loss_issues": [
                    {{
                        "feature_name": "User Authentication",
                        "severity": "Critical/High/Medium/Low",
                        "evidence": "File: auth.py, Lines deleted: 150, Functions removed: login(), validate_token()",
                        "requirement_reference": "Quote from requirements doc",
                        "impact": "Production deployment will fail - users cannot login",
                        "commit_info": "Removed in commit abc123: 'Refactoring auth module'",
                        "reasoning": "Feature still required but code deleted without replacement",
                        "remediation": "Restore authentication functions or implement alternative"
                    }}
                ],
                "deployment_risk": "High/Medium/Low",
                "recommendation": "Block/Warn/Approve deployment",
                "summary": "Overall assessment of feature loss and deployment readiness",
                "repo_score_card": {{
                    "feature_completeness": 85,
                    "code_stability": 90,
                    "requirement_alignment": 75,
                    "overall_score": 83,
                    "grade": "B"
                }}
            }}
            """,
            input_variables=["requirements", "dos_donts", "code_context", "commit_analysis", "deletions"]
        )
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "requirements": requirements_text[:10000],
                "dos_donts": dos_donts_text[:5000] if dos_donts_text else "No specific guidelines provided.",
                "code_context": code_context[:15000],
                "commit_analysis": json.dumps(feature_loss_context, indent=2)[:5000],
                "deletions": json.dumps(initial_vs_recent, indent=2)[:5000]
            })
            content = response.content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            
            # Add metadata
            result["analysis_metadata"] = {
                "repo_path": repo_path,
                "total_commits_in_history": len(commit_history),
                "oldest_commit": commit_history[-1]["hash"][:8] if commit_history else "N/A",
                "newest_commit": commit_history[0]["hash"][:8] if commit_history else "N/A",
                "analysis_date": str(datetime.now())
            }
            
            return result
        except Exception as e:
            return {
                "error": str(e),
                "feature_loss_score": 0,
                "feature_loss_issues": [],
                "summary": f"Analysis failed: {str(e)}"
            }
