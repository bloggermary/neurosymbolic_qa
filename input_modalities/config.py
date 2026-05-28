import os
from dotenv import load_dotenv

load_dotenv()

# API key for LLM
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# model used everywhere
MODEL_NAME = "gpt-5-mini"