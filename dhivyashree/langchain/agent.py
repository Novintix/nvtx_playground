import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

class TaskAgent:
    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7
        )
        
        # Planner Chain
        self.planner_prompt = PromptTemplate(
            template="""
            You are a helpful assistant.
            Target: {objective}
            
            Please break down the target into a numbered list of execution steps.
            Return ONLY the numbered list.
            """,
            input_variables=["objective"]
        )
        self.planner_chain = self.planner_prompt | self.llm | StrOutputParser()
        
        # Executor Chain
        self.executor_prompt = PromptTemplate(
            template="""
            You are a helpful worker agent.
            Task: {step}
            Context: {context}
            
            Execute the task and provide the result.
            """,
            input_variables=["step", "context"]
        )
        self.executor_chain = self.executor_prompt | self.llm | StrOutputParser()

    def plan(self, objective):
        print(f"Planning task: {objective}")
        plan_text = self.planner_chain.invoke({"objective": objective})
        steps = [line.strip() for line in plan_text.split('\n') if line.strip() and (line[0].isdigit() or line.startswith('-'))]
        return steps

    def execute(self, steps):
        context = ""
        results = []
        for step in steps:
            print(f"Executing step: {step}")
            result = self.executor_chain.invoke({"step": step, "context": context})
            print(f"Result: {result}\n")
            results.append({"step": step, "result": result})
            context += f"Step: {step}\nResult: {result}\n\n"
        return results

    def run(self, objective):
        steps = self.plan(objective)
        print(f"Generated Plan: {steps}\n")
        return self.execute(steps)
