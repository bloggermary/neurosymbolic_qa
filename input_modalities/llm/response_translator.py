from llm.client import client

def translate_result(result):
    """
    Convert Prolog output into a clean medical answer.
    """

    prompt = f"""
You are a medical reasoning assistant.

Convert the following Prolog result into a short, clear medical explanation.

Rules:
- Be concise (1–3 sentences)
- Do NOT explain Prolog
- Do NOT mention "true/false"
- Use medical language only

Prolog result:
{result}

Output:
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()