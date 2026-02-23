# DriftX 2.0 - Compliance Gateway Agent

AI-powered quality gate system for software deployment with comprehensive compliance and evaluation analysis.

## 🚀 Quick Start

### 1. Setup (One-time)
```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key in .env file
GOOGLE_API_KEY=your_gemini_api_key_here
```

Get your API key from: https://makersuite.google.com/app/apikey

### 2. Start the Application
```bash
# Windows
start.bat

# Linux/Mac
./start.sh

# Or manually
streamlit run app.py
```

### 3. Run Your First Analysis
1. Select analysis mode (Standard Compliance or Evaluation Analysis)
2. Enter Git repository URL (e.g., `https://github.com/user/repo`)
3. Upload requirement documents (PDF, TXT, or MD)
4. Upload Do's and Don'ts documents (optional but recommended)
5. Click "Start Analysis"
6. Review results with AI-generated remediation

## 📊 Two Analysis Modes

### Standard Compliance Mode
**Purpose:** Check if code matches requirements and follows guidelines

**Outputs:**
- **Drift Analysis**: Detects missing, extra, or modified features
- **Code Compliance**: Validates Do's and Don'ts adherence
- **AI Remediation**: Specific fix recommendations for all issues
- **Final Score**: Pass/Fail deployment decision

**Use for:** Deployment gates, code reviews, compliance audits

### Evaluation Analysis Mode
**Purpose:** Assess feature completeness and coverage with historical review

**Outputs:**
- **Feature Loss Analysis**: Identifies missing or incomplete features
- **Coverage Gap Analysis**: Finds guideline coverage gaps
- **Review History Tab**: Commit history analysis showing code deletions and feature loss over time
- **AI Remediation**: Implementation guidance
- **Final Score**: Overall assessment

**Use for:** Project assessment, feature tracking, coverage analysis, historical code review

**Review History includes:**
- Commit-by-commit tracking of code deletions
- Cross-reference with requirements to identify missing features
- Repository score card (feature completeness, stability, alignment)
- Deployment risk assessment
- Historical feature loss detection

## 📈 Scoring System

| Score | Status | Action |
|-------|--------|--------|
| 90-100 | 🟢 Excellent | Deploy with confidence |
| 75-89 | 🟡 Good | Minor improvements needed |
| 60-74 | 🟠 Fair | Improvements required |
| 0-59 | 🔴 Poor | Major fixes needed |

**Threshold:** Score must be > 90 for deployment approval

## 💻 Command Line Usage

### Standard Compliance Analysis
```bash
python ci_gate.py \
  --repo https://github.com/user/repo \
  --requirements requirements.md \
  --dos-donts guidelines.md \
  --mode standard \
  --threshold 90
```

### Evaluation Analysis
```bash
python ci_gate.py \
  --repo https://github.com/user/repo \
  --requirements requirements.md \
  --dos-donts guidelines.md \
  --mode evaluation \
  --threshold 85
```

### CLI Options
- `--repo`: Git repository URL (required)
- `--requirements`: Path to requirements document (required)
- `--dos-donts`: Path to Do's and Don'ts document (optional)
- `--mode`: Analysis mode - `standard` or `evaluation` (default: standard)
  - `evaluation` mode includes Review History analysis automatically
- `--threshold`: Minimum score to pass (default: 90)

## 🔧 CI/CD Integration

### GitHub Actions Example
```yaml
name: DriftX Quality Gate

on: [pull_request]

jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - run: pip install -r requirements.txt
    - run: |
        python ci_gate.py \
          --repo ${{ github.repository }} \
          --requirements docs/requirements.md \
          --dos-donts docs/guidelines.md \
          --mode standard
      env:
        GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
```

### GitLab CI Example
```yaml
driftx-gate:
  stage: quality-gate
  image: python:3.9
  before_script:
    - pip install -r requirements.txt
  script:
    - python ci_gate.py --repo $CI_REPOSITORY_URL --requirements docs/requirements.md --mode standard
  only:
    - merge_requests
```

## 📁 Project Structure

```
driftx-2.0/
├── app.py                      # Web interface (main app)
├── ci_gate.py                  # CLI tool for CI/CD
├── config.py                   # Configuration management
├── utils.py                    # Helper functions
├── .env                        # Your API key
├── requirements.txt            # Dependencies
├── agents/
│   ├── compliance_agent.py     # Drift & Evaluation analysis
│   └── quality_agent.py        # Code quality & compliance
├── mcp_server/tools/
│   ├── analysis.py             # Static analysis (Radon, Bandit)
│   └── git_reader.py           # Git operations
├── start.bat                   # Windows quick start
├── start.sh                    # Linux/Mac quick start
├── test_setup.py               # Setup validator
├── README.md                   # This file
├── QUICKSTART.md               # 5-minute tutorial
├── USAGE_EXAMPLES.md           # Detailed examples
└── sample_dos_donts.md         # Guidelines template
```

## 📋 Requirements

```
streamlit
PyPDF2
langchain-google-genai
langchain
langchain-core
radon
bandit
python-dotenv
```

## 🎓 Creating Do's and Don'ts Guidelines

Use `sample_dos_donts.md` as a template. Include:

**Do's:**
- Best practices to follow
- Security measures
- Code quality standards
- Architecture guidelines

**Don'ts:**
- Anti-patterns to avoid
- Security vulnerabilities
- Code smells
- Bad practices

Example:
```markdown
## DO's
- Validate all user inputs
- Use environment variables for secrets
- Write unit tests for critical functions

## DON'Ts
- Never hardcode credentials
- Avoid functions longer than 50 lines
- Don't skip input validation
```

## 🔍 How It Works

1. **Repository Analysis**: Clones and analyzes your Git repository
2. **Static Analysis**: Runs Radon (complexity) and Bandit (security)
3. **AI Analysis**: Uses Google Gemini to compare code vs requirements
4. **Guideline Validation**: Checks compliance with Do's and Don'ts
5. **Remediation**: Generates AI-powered fix recommendations
6. **Scoring**: Calculates final score based on rubrics
7. **Decision**: Approves or blocks deployment based on threshold

## 🛡️ Security

- API keys stored in `.env` (not in code)
- `.env` is in `.gitignore` (won't be committed)
- Input validation on all user inputs
- Secure temporary directory handling
- No credential storage

## 🧪 Testing Your Setup

```bash
python test_setup.py
```

This validates:
- All dependencies installed
- API key configured
- Git available
- Static analysis tools ready
- Project structure correct

## 🆘 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API key not found" error
Check `.env` file contains:
```
GOOGLE_API_KEY=your_actual_key_here
```

### Analysis fails
1. Check internet connection
2. Verify repository URL is correct and accessible
3. Ensure API key is valid
4. Review error messages in console

### Git not found
Install Git from: https://git-scm.com/

## 💡 Best Practices

1. **Start Small**: Test with a small repository first
2. **Use Guidelines**: Upload Do's and Don'ts for better results
3. **Iterate**: Use remediation suggestions to improve code
4. **Automate**: Integrate into CI/CD for continuous quality
5. **Customize**: Create team-specific guidelines
6. **Track Progress**: Save reports to monitor improvements

## 📚 Additional Documentation

- **QUICKSTART.md** - 5-minute tutorial with examples
- **USAGE_EXAMPLES.md** - Detailed usage examples and CI/CD integration
- **sample_dos_donts.md** - Template for creating guidelines

## 🤝 Contributing

This is a quality gate tool for your projects. Customize it to fit your team's needs:
- Modify scoring rubrics in agent files
- Add new static analysis tools
- Create custom guidelines
- Extend with additional features

## 📄 License

Use this tool to improve your code quality and deployment processes.

## 🎯 Example Workflow

### Web Interface
1. Start: `streamlit run app.py`
2. Select: Standard Compliance mode
3. Enter: Repository URL
4. Upload: Requirements + Do's and Don'ts
5. Analyze: Click "Start Analysis"
6. Review: Check drift and compliance results
7. Fix: Apply AI remediation suggestions
8. Deploy: If score > 90

### CI/CD Pipeline
1. Add `ci_gate.py` to your pipeline
2. Configure with your requirements and guidelines
3. Set threshold (default: 90)
4. Pipeline fails if score < threshold
5. Review console output for issues
6. Fix issues and re-run

## 🚀 Getting Started Checklist

- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Set API key in `.env` file
- [ ] Test setup: `python test_setup.py`
- [ ] Start app: `streamlit run app.py`
- [ ] Try sample analysis
- [ ] Create custom Do's and Don'ts
- [ ] Integrate into CI/CD

---

**Ready to start?** Run `streamlit run app.py` or `start.bat`

**Need help?** Check `QUICKSTART.md` for a step-by-step tutorial
