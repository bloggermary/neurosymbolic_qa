from openai import OpenAI

client = OpenAI()

def translate_result(result) -> str:

    prompt = f"""
Translate this Prolog result into a medical explanation.

Result:
{result}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content