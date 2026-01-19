from typing_extensions import TypedDict

class State(TypedDict, total=False):
    application: str
    experience_level: str
    skill_match: str
    response: str
