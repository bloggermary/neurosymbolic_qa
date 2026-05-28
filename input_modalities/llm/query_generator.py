from openai import OpenAI

client = OpenAI()

def generate_query(question: str) -> str:

    prompt = f"""
Convert the medical question into a Prolog query.

Question:
{question}

Output ONLY the query.
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()