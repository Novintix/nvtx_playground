from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq


generation_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant tasked with writing excellent twitter posts."
            "The user will provide a tweet title or topic."
            "Generate the best twitter post possible based on the user's request."
            "Generate ONLY the tweet text"
            "Do not add explanations, prefaces or commentary"
            "Keep it under 280 characters."
            "If the user provides critique, respond with a revised version of your previous attempts.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

reflector_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a viral twitter influencer garding a tweet. Generate critique and recommendation for the user's tweet."
            "Always provide detailed recommendations focusing on clarity, engagement, virality, hashtags, tone and length.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

llm = ChatGroq(model="llama-3.1-8b-instant")

generation_chain = generation_prompt | llm
reflection_chain = reflector_prompt | llm
