import sys
import os
import argparse
from dotenv import load_dotenv
from mcp_server.tools.git_reader import clone_repo, cleanup_repo
from agents.compliance_agent import ComplianceAgent
from agents.quality_agent import QualityAgent

# Load env immediately
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="DriftX 2.0 CI/CD Gate")
    parser.add_argument("--repo", required=True, help="Git Repository URL")
    parser.add_argument("--requirements", required=True, help="Path to requirements document (txt/md)")
    parser.add_argument("--dos-donts", help="Path to do's and don'ts document (txt/md)")
    parser.add_argument("--mode", choices=["standard", "evaluation"], default="standard", 
                        help="Analysis mode: standard (compliance) or evaluation (feature/coverage with history)")
    parser.add_argument("--threshold", type=int, default=90, help="Minimum score to pass (default: 90)")
    args = parser.parse_args()

    repo_url = args.repo
    requirements_path = args.requirements
    dos_donts_path = args.dos_donts
    
    print(f"🚀 Starting DriftX 2.0 Gate Analysis for {repo_url}")
    print(f"📋 Mode: {args.mode.upper()}")
    
    # Read requirements
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            requirements_text = f.read()
    except Exception as e:
        print(f"❌ Error reading requirements file: {e}")
        sys.exit(1)
    
    # Read do's and don'ts if provided
    dos_donts_text = ""
    if dos_donts_path:
        try:
            with open(dos_donts_path, 'r', encoding='utf-8') as f:
                dos_donts_text = f.read()
            print(f"✅ Loaded Do's and Don'ts guidelines")
        except Exception as e:
            print(f"⚠️ Warning: Could not read do's and don'ts file: {e}")

    repo_path = None
    try:
        print("🔄 Cloning repository...")
        repo_path = clone_repo(repo_url)
        
        if args.mode == "standard":
            # Standard Compliance Mode
            print("🤖 Running Compliance Agent (Drift Analysis)...")
            comp_agent = ComplianceAgent()
            comp_results = comp_agent.analyze(repo_path, requirements_text, dos_donts_text)
            drift_score = comp_results.get("drift_score", 0)
            print(f"   -> Drift Compliance Score: {drift_score}/100")
            if comp_results.get("drift_detected"):
                print("   -> ⚠️ Drift Detected")
            
            print("🕵️ Running Quality Agent (Code Compliance)...")
            qual_agent = QualityAgent()
            qual_results = qual_agent.analyze_compliance(repo_path, dos_donts_text)
            review = qual_results.get("review", {})
            compliance_score = review.get("score", 0)
            print(f"   -> Code Compliance Score: {compliance_score}/100")
            
            final_score = (drift_score + compliance_score) / 2
            print(f"\n🏁 Final Score: {final_score:.1f}/100 (Threshold: {args.threshold})")
            
            if final_score >= args.threshold:
                print("✅ Quality Gate Passed! Proceeding to deployment.")
                sys.exit(0)
            else:
                print("⛔ Quality Gate Failed. Deployment blocked.")
                print("\n--- Failure Details ---")
                for issue in comp_results.get("issues", []):
                    print(f"[Drift] {issue.get('type')}: {issue.get('description')}")
                for issue in review.get("issues", []):
                    print(f"[Compliance] {issue.get('title')}: {issue.get('description')}")
                sys.exit(1)
        
        else:
            # Evaluation Analysis Mode (includes history review)
            print("🔍 Running Evaluation Analysis (Feature Loss + Coverage Gap + History Review)...")
            comp_agent = ComplianceAgent()
            eval_results = comp_agent.evaluate_analysis(repo_path, requirements_text, dos_donts_text)
            
            feature_score = eval_results.get("feature_loss_score", 0)
            coverage_score = eval_results.get("coverage_score", 0)
            print(f"   -> Feature Completeness Score: {feature_score}/100")
            print(f"   -> Coverage Score: {coverage_score}/100")
            
            final_score = (feature_score + coverage_score) / 2
            print(f"\n🏁 Final Score: {final_score:.1f}/100 (Threshold: {args.threshold})")
            
            if final_score >= args.threshold:
                print("✅ Evaluation Passed!")
                sys.exit(0)
            else:
                print("⛔ Evaluation Failed.")
                print("\n--- Failure Details ---")
                for issue in eval_results.get("feature_loss_issues", []):
                    print(f"[Feature Loss] {issue.get('feature')}: {issue.get('description')}")
                for issue in eval_results.get("coverage_gaps", []):
                    print(f"[Coverage Gap] {issue.get('area')}: {issue.get('description')}")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Fatal Error: {e}")
        sys.exit(1)
    finally:
        if repo_path:
            cleanup_repo(repo_path)

if __name__ == "__main__":
    main()
