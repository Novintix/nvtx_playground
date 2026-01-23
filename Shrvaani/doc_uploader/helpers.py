from pathlib import Path

# Where routed resumes will go
STORAGE_ROOT = Path("hrms_storage")
TECH_FOLDER = STORAGE_ROOT / "technical_resumes"
HR_FOLDER = STORAGE_ROOT / "hr_resumes"

# Registry file (dedupe database)
REGISTRY_PATH = Path("doc_uploader") / "registry.csv"

# Scan only inside folder names containing these keywords (case-insensitive)
ALLOWED_PARENT_FOLDERS = [
    "resume",
    "resumes",
    "cv",
    "candidate profile",
    "candidate_profiles",
]

# Resume structure signals
RESUME_SECTIONS = [
    "education",
    "experience",
    "work experience",
    "skills",
    "technical skills",
    "projects",
    "summary",
]

# Contact signals
CONTACT_SIGNALS = [
    "linkedin.com",
    "github.com",
    "@",
    "gmail.com",
]

# Strong non-resume file name patterns
NON_RESUME_FILENAME_HINTS = [
    "offer letter",
    "appointment letter",
    "experience letter",
    "relieving",
    "payslip",
    "pay slip",
    "invoice",
    "agreement",
    "certificate",
    "report",
    "brochure",
    "account statement",
    "form",
    "story",
    "book",
    "cover letter",
]

TECH_KEYWORDS = [
    "python", "django", "flask",
    "ai", "ml", "machine learning", "deep learning",
    "gen ai", "llm", "rag",
    "data science", "computer vision",
    "aws", "lambda", "s3",
    "pytorch", "tensorflow",
]

HR_KEYWORDS = [
    "hr", "human resources",
    "recruitment", "talent acquisition",
    "people & culture",
    "organization development", "od",
    "ocm", "employee engagement",
]
