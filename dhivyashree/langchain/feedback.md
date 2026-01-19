19/01/2026
Feedback on the agent
1. Separating the planner and the executer is good
2. Using monolithic prompts is also good. 
3. Prompt could be better. 
4. Handling steps something like this not recommended.
        steps = [line.strip() for line in plan_text.split('\n') if line.strip() and (line[0].isdigit() or line.startswith('-'))]

Overall good start. 