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
    - Measurements, lab values, age, weight, or any other percentage
      or quantity expressed as one number.


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
    - Choose one option from predefined categories the text describes.

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
    - The user provides MULTIPLE inputs that have a specific structure or relationship between them.
    - Use this modality when multiple inputs are collected together AND their order, ranking, or grouping is important.
    - This modality has three possible modes:

        sequence:
        - Multiple inputs are collected in a predefined sequential order, where the order matters.
        - The system provides the sequence labels or time points in advance.
        - The user only provides the values associated with each predefined position or time point.
        - The user does NOT need to enter the sequence labels themselves, only the values for each label.
        - The sequence may represent chronological events, steps in a process, temporal progression or any other ordered list where the order is important.

        ranking:
        - Multiple items are ordered according to a ranking, priority, importance, severity, or preference.
        - Each item receives a relative position in the ordering.
        - The ranking position is provided automatically by the system, and the user only provides the values for each item.
        - The user does NOT need to enter the ranking positions themselves.
        - The system automatically displays the ranking position (e.g. 1., 2., 3., etc.).

        grouping:
        - Multiple items are assigned to predefined groups.
        - The groups are provided by the system in advance.
        - The user only provides the items that belong to each predefined group.
        - The user does NOT need to enter the group names themselves.
        - Multiple items may belong to the same group.
        - A group may contain zero, one, or multiple items.

        
    multi_attribute_entity:
    - Several different attributes of ONE single entity, collected
      together (name/dose/frequency of one medication, etc.), where
      each attribute must be entered SEPARATELY as its own field.
    - The system provides the attribute names or field labels in advance.
    - The user only provides the values for each attribute.
    - Each attribute describes a different property of the same entity.
    - A conventional combined reading that is normally given as one
      value (e.g. a blood pressure reading like "120/80", a date) is
      "numeric" or "string", NOT this - only use multi_attribute_entity
      when the question itself lists out multiple distinct, separately
      named fields to fill in.
    
      
    Important distinction:
    - If the user simply selects multiple options from ONE list, use multiple_category.
    - If the user orders, ranks, or groups multiple inputs, use multi_structured_input.
    - If the user enters several attributes belonging to ONE single entity, use multi_attribute_entity.

    
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