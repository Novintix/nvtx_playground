from graph import app

sample_application = (
    "Candidate have 4 years experience in Python. "
    "Strong Python fundamentals, OOP, and data structures. "
    "Used Pandas and NumPy in coursework projects. "
    "Comfortable with Git and unit testing."
)

result = app.invoke({"application": sample_application})

print("Experience Level:", result.get("experience_level"))
print("Skill Match:", result.get("skill_match"))
print("Decision:", result.get("response"))
