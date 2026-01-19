from langchain_core.prompts import ChatPromptTemplate
from state import State
from llm import llm


def categorize_experience(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        """
        You are an HR assistant.

        Categorize the candidate strictly as:
        Entry-level, Mid-level, or Senior-level.

        Application:
        {application}

        Return only the category.
        """
    )

    result = (prompt | llm).invoke(
        {"application": state["application"]}
    ).content.strip()

    return {"experience_level": result}


def assess_skill_match(state: State) -> State:
    prompt = ChatPromptTemplate.from_template(
        """
        You are an HR assistant evaluating a candidate's skills for a Python Developer position.
        
        Assess whether the candidate has relevant Python skills based on the application.
        Look for:
        - Python programming experience
        - Python frameworks (Django, Flask, FastAPI, etc.)
        - Python libraries (NumPy, Pandas, Scikit-learn, TensorFlow, etc.)
        - Backend development experience with Python
        - Any other relevant Python-related skills
        
        Job Description: Python Developer position requiring Python programming skills.
        
        Application:
        {application}
        
        Respond with ONLY one of these two options:
        - "Match" if the candidate has relevant Python skills
        - "No Match" if the candidate lacks relevant Python skills
        
        Your response:
        """
    )

    result = (prompt | llm).invoke(
        {"application": state["application"]}
    ).content.strip()

    # Normalize the response to ensure it's either "Match" or "No Match"
    normalized_result = result
    if "match" in result.lower() and "no" not in result.lower()[:10]:
        normalized_result = "Match"
    elif "no match" in result.lower() or ("no" in result.lower()[:10] and "match" in result.lower()):
        normalized_result = "No Match"
    else:
        # Default to No Match if unclear
        normalized_result = "No Match"

    return {"skill_match": normalized_result}


def schedule_interview(state: State) -> State:
    return {"response": "Candidate shortlisted for HR interview"}


def escalate_to_manager(state: State) -> State:
    return {"response": "Application escalated to recruiter for review"}


def reject_application(state: State) -> State:
    return {"response": "Candidate rejected"}
