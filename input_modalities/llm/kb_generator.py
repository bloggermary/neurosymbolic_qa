from openai import OpenAI

client = OpenAI()


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

STRICT REQUIREMENTS:
- Output ONLY Prolog code (no explanations)
- NO markdown (no ``` blocks)
- Must include ask(Question) usage for user interaction
- Must define:
    - diagnose/0
    - diabetes/0
    - prediabetes/0
- Use logical predicates only
- Ensure rules are consistent and executable in SWI-Prolog
- Must be compatible with SWI-Prolog + Janus

Medical Text:
{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()