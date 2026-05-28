from llm.client import client

def generate_query(question: str) -> str:
    prompt = f"""
    Convert the medical question into ONE of these Prolog goals ONLY:

    - diabetes
    - prediabetes
    - low_risk
    - diagnose

    IMPORTANT:
    - DO NOT use variables like Patient
    - DO NOT use predicates with arguments
    - Output ONLY a single word

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()