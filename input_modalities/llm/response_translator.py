from llm.client import client


def translate_result(user_question: str, query: str, result) -> str:
    """
    Convert Prolog output into a clean medical answer.
    """

    prompt = f"""
You are a medical reasoning assistant.

Your task is to convert Prolog reasoning output into a clear medical explanation.

Rules:
- Be concise (1–3 sentences)
- Do NOT explain Prolog
- Do NOT mention true/false
- Use medical reasoning language only

User question:
{user_question}

Prolog query:
{query}

Prolog result:
{result}

Final answer:
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()