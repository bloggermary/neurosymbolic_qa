from llm.client import client

def generate_query(question: str) -> str:
    prompt = f"""
    Convert the medical question into a valid Prolog query.

    RULES:
    - Output ONLY this format:
        diagnose(Result).
    - DO NOT output "diabetes"
    - DO NOT output "prediabetes"
    - DO NOT output plain words
    - ALWAYS use: diagnose(Result)

    Examples:
    Question: Is the patient diabetic?
    Answer: diagnose(Result).

    Question: What is the diagnosis?
    Answer: diagnose(Result).

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