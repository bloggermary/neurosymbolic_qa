from llm.client import client

# FEEDBACK: This does not actually result in the Python ask method being called through Janus.
# This results in the internal Prolog input mechanism being triggered.
# Please look closely at the template I provided you.
# You must instruct the LLM how it can trigger the Python function.
# Exampel prompt:
# -----------------
# Add and use the following Prolog predicate to ask a yes/no question to the user through the Janus integration.
# ask(Question) :-
#    py_call(main:ask(Question), yes).


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
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()
