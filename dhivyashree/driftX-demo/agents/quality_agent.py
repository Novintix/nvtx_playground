import os
import json
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from mcp_server.tools.analysis import run_radon, run_bandit

class QualityAgent:
    def __init__(self, model_name="gemini-pro"):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.0)
        
    def analyze(self, repo_path):
        """
        Performs both quantitative and qualitative analysis.
        """
        # 1. Quantitative Analysis (Tools)
        print(f"Running Radon on {repo_path}...")
        radon_metrics = run_radon(repo_path)
        print(f"Running Bandit on {repo_path}...")
        bandit_metrics = run_bandit(repo_path)
        
        # 2. Qualitative Analysis (LLM as Senior Dev)
        # We'll read a few key files to give the LLM context. 
        # For simplicity, we'll list files and read the top 2-3 Python files by size.
        code_context = self._get_code_context(repo_path)
        
        senior_dev_review = self._perform_senior_review(code_context, radon_metrics, bandit_metrics)
        
        return {
            "metrics": {
                "radon": radon_metrics,
                "bandit": bandit_metrics
            },
            "review": senior_dev_review
        }

    def _get_code_context(self, repo_path):
        """
         Reads content of key files for the LLM.
        """
        context = ""
        # Universal reader: Read all text-based files
        for root, dirs, files in os.walk(repo_path):
            if '.git' in root: continue
            
            # Filter out ignored directories
            if any(ignored in root for ignored in ['node_modules', 'venv', 'dist', 'build', '__pycache__']):
                continue

            for file in files:
                # Skip known binary/system files and irrelevant extensions
                if file.endswith(('.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc', '.git', '.lock', '.json')):
                     continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        # Limit context per file to avoid token limits
                        context += f"\n--- FILE: {file} ---\n{content[:2000]}\n"
                except Exception:
                    pass
        return context[:30000] # Cap total context

    def _perform_senior_review(self, code, radon, bandit):
        """
        Asks the LLM to review the code like a Senior Developer.
        """
        prompt = PromptTemplate(
            template="""
            You are a strict but helpful Senior Software Engineer reviewing a Junior Developer's code.
            
            Context:
            - Static Analysis (Radon): {radon}
            - Security Scan (Bandit): {bandit}
            
            Code Snippets:
            {code}
            
            Your Task:
            1. Assign a **Quality Score** (0-100) based on this Rubric:
               - 90-100: Excellent (Clean, Secure, Well-structured, DRY).
               - 80-89: Good (Minor issues, mostly readable).
               - 70-79: Fair (Some messiness, hard coded values, slight security risks).
               - 60-69: Poor (Spaghetti code, major security flaws, no error handling).
               - Below 60: Critical failure.
            2. Identify top 3-5 critical issues (Design patterns, Readability, Security, Standards).
            3. For EACH issue, you MUST provide:
               - **Reasoning**: Why is this bad? (e.g., "Hard to test", "Security vulnerability")
               - **Rectification**: Specific advice on how to fix it.
            
            Output JSON format ONLY:
            {{
                "score": 85,
                "summary": "Overall specific feedback...",
                "issues": [
                    {{
                        "title": "Issue Title",
                        "severity": "High/Medium/Low",
                        "description": "...",
                        "reasoning": "...",
                        "rectification": "..."
                    }}
                ]
            }}
            """,
            input_variables=["radon", "bandit", "code"]
        )
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "radon": json.dumps(radon)[:1000], # Truncate metrics for token safety
                "bandit": json.dumps(bandit)[:1000],
                "code": code
            })
            # Clean up response to ensure valid JSON
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {"error": str(e), "score": 0, "issues": []}

    def analyze_compliance(self, repo_path, dos_donts_text=""):
        """
        Performs code compliance analysis against Do's and Don'ts guidelines.
        """
        # 1. Get static analysis metrics
        radon_metrics = run_radon(repo_path)
        bandit_metrics = run_bandit(repo_path)
        
        # 2. Get code context
        code_context = self._get_code_context(repo_path)
        
        # 3. Perform compliance review
        compliance_review = self._perform_compliance_review(code_context, radon_metrics, bandit_metrics, dos_donts_text)
        
        return {
            "metrics": {
                "radon": radon_metrics,
                "bandit": bandit_metrics
            },
            "review": compliance_review
        }

    def _perform_compliance_review(self, code, radon, bandit, dos_donts):
        """
        Reviews code compliance against Do's and Don'ts guidelines.
        """
        prompt = PromptTemplate(
            template="""
            You are a Code Compliance Auditor reviewing code against established guidelines.
            
            Do's and Don'ts Guidelines:
            {dos_donts}
            
            Static Analysis (Radon):
            {radon}
            
            Security Scan (Bandit):
            {bandit}
            
            Code Snippets:
            {code}
            
            Your Task:
            1. Assign a **Compliance Score** (0-100) based on adherence to guidelines:
               - 90-100: Excellent compliance (Follows all Do's, avoids all Don'ts)
               - 80-89: Good compliance (Minor deviations)
               - 70-79: Fair compliance (Some guideline violations)
               - 60-69: Poor compliance (Multiple violations)
               - Below 60: Critical non-compliance
               
            2. Identify compliance issues by checking:
               - Are "Do" guidelines followed?
               - Are "Don't" guidelines violated?
               - Code quality, security, and best practices
               - Static analysis findings
               
            3. For EACH issue, provide:
               - **Reasoning**: Why this violates guidelines or best practices
               - **Rectification**: Specific code changes or actions needed
            
            Output JSON format ONLY:
            {{
                "score": 85,
                "summary": "Overall compliance assessment...",
                "issues": [
                    {{
                        "title": "Issue Title",
                        "severity": "High/Medium/Low",
                        "description": "What's wrong",
                        "reasoning": "Why it's a problem",
                        "rectification": "How to fix it"
                    }}
                ]
            }}
            """,
            input_variables=["dos_donts", "radon", "bandit", "code"]
        )
        
        chain = prompt | self.llm
        try:
            response = chain.invoke({
                "dos_donts": dos_donts[:5000] if dos_donts else "No specific guidelines provided. Use general best practices.",
                "radon": json.dumps(radon)[:1000],
                "bandit": json.dumps(bandit)[:1000],
                "code": code
            })
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except Exception as e:
            return {"error": str(e), "score": 0, "issues": []}


if __name__ == "__main__":
    # Test stub
    pass
