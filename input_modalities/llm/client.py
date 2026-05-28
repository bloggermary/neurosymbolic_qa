from openai import OpenAI
from config import OPENAI_API_KEY

# single shared client for the whole project
client = OpenAI(api_key=OPENAI_API_KEY)