from llm.client import client
from config import MODEL_NAME


ALLOWED_MODALITIES = {
    "boolean",
    "numeric",
    "string",
    "category",
    "range",
    "duration",
    "multiple_category",
    "multi_structured_input",
    "multi_attribute_entity",
}


def detect_modality(question: str) -> str:
    prompt = f"""
    Classify the expected user input type.

    Return ONLY ONE label:

    boolean
    numeric
    string
    category
    range
    duration
    multiple_category
    multi_structured_input
    multi_attribute_entity

    Rules:

    boolean:
    - Yes/no answers.
    - True/false questions.

    numeric:
    - A single number value.
    - Measurements, lab values, age, weight, glucose, percentage.


    duration:
    - Time length with a unit, asked as an open-ended amount (not
      bounded by two endpoints).
    - Years, months, weeks, days, hours.
    - "When did X begin/start/first appear?" also counts as duration,
      not string - the natural answer is elapsed time ("3 weeks ago"),
      not a free-text description or calendar date.
   

    range:
    - A lower and upper numeric boundary is given, and the user picks
      or reports a value inside that boundary.
    - Includes rating/severity scores (e.g. 1-10, mild-to-severe),
      since those are also bounded-interval answers.
 

    category:
    - Choose one option from predefined categories.
    Examples:
    "Low/medium/high"
    "Male/female"
    "Type 1/type 2"

    string:
    - Free text explanation.
    

    multiple_category:
    - Selecting SEVERAL applicable options at once from a fixed list,
      not just one. Requires explicit plural/multi-select language
      ("select all that apply", "which of the following apply",
      "choose several/all"). A plain "select"/"choose" with no such
      language, picking ONE option, is "category", not this - do not
      guess multi-select just because several options exist.
   
    

    multi_structured_input:
    - Ordering, ranking, or grouping several items together.
   

    multi_attribute_entity:
    - Several different attributes of ONE single thing, collected
      together (name/dose/frequency of one medication, etc.), where
      each attribute must be entered SEPARATELY as its own field.
      A conventional combined reading that is normally given as one
      value (e.g. a blood pressure reading like "120/80", a date) is
      "numeric" or "string", NOT this - only use multi_attribute_entity
      when the question itself lists out multiple distinct, separately
      named fields to fill in.
    

    Important:
    - Ignore medical meaning.
    - Only classify the answer format.
    - Return only the label.

    Question:
    {question}
    """

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
    )

    modality = response.choices[0].message.content.strip().lower()

    if modality not in ALLOWED_MODALITIES:
        return "string"

    return modality