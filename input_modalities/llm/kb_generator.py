from openai import OpenAI

client = OpenAI()

def generate_prolog_kb(text: str) -> str:

    prompt = f"""
Convert this medical guideline into valid SWI-Prolog.

Requirements:
- Use predicates
- Use ask(...) for user information
- Generate diagnosis rules
- Generate only Prolog code

Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content