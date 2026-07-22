from llm.client import client


def generate_prolog_kb(text: str) -> str:

    prompt = f"""
You are an expert SWI-Prolog knowledge engineer.

Convert the following medical text into a VALID SWI-Prolog knowledge base.

GENERAL REQUIREMENTS:
- Output ONLY Prolog code.
- Do not use markdown.
- Do not add explanations.
- The code must run in SWI-Prolog.
- The code must be compatible with SWI-Prolog + Janus.
- Use logical predicates and rules only.
- Avoid singleton variables.
- Do not create unnecessary predicates.
- Ask only the minimum information necessary to reach a conclusion.

REASONING REQUIREMENTS:
- The knowledge base should support diagnosis, classification, and follow-up questioning.
- For the *numeric diagnostic threshold* (which single measurement proves diabetes),
  stop asking further numeric criteria as soon as one threshold is met - do not force
  every numeric criterion to be checked once a conclusion is already justified.
- Use the simplest valid reasoning path for the numeric threshold check itself.
- HOWEVER: the source text describes this domain as explicitly multi-modal (numeric,
  boolean, range, categorical, and temporal/duration data all appear in it). The main
  diagnose/1 workflow MUST also collect the supporting clinical picture described in
  the text - not just the numeric threshold - because that supporting evidence is part
  of what a real clinical dialogue would gather, and because this system is built to
  demonstrate multi-modal reasoning, not numeric-only reasoning. Concretely, diagnose/1
  (and diabetes/0 when used as the general entry point) should, in addition to the
  numeric threshold check:
    - ask_boolean for each symptom explicitly mentioned in the text (e.g. excessive
      thirst, excessive urination, fatigue, blurred vision)
    - ask_category for medication status and any categorical history mentioned in the
      text (e.g. insulin / oral antidiabetics / corticosteroids / none)
    - ask_range or ask_duration for any threshold/temporal detail mentioned in the text
      (e.g. hours of fasting before a glucose sample)
  This supporting evidence should be gathered as part of the interactive dialogue
  (that's what actually demonstrates multi-modal reasoning to the user - the
  QUESTIONS asked, not the shape of the return value). diagnose/1's own RETURN
  VALUE must still follow the janus-safe result rule below - see JANUS RESULT
  SAFETY. Do not invent clinical questions that aren't grounded in the provided
  text.

JANUS USER INTERACTION:

The generated knowledge base MUST start with:

:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(prolog_bridge:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(prolog_bridge:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(prolog_bridge:ask_string(Question), Value).

ask_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(prolog_bridge:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(prolog_bridge:ask_duration(Question), Value).

ask_scale(Question, Value) :-
    py_call(prolog_bridge:ask_scale(Question), Value).

ask_multiple_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_multiple_category(Question, Categories), Answer).

ask_multi_structured_input(Question, Mode, Groups, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Groups), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).


MODALITY RULES:

Use:
- ask_boolean for yes/no questions
- ask_numeric for measurements and numbers
- ask_duration for time durations
- ask_range for bounded numeric intervals
- ask_scale for ratings from 1-10
- ask_category for fixed choices
- ask_string for free text

CRITICAL - ask_numeric/ask_duration/ask_range/ask_scale ALWAYS RETURN A FLOAT:
even a count or "how many" answer comes back as e.g. 1.0, never the integer 1.
NEVER gate logic on integer(Value) for anything sourced from these - it will
silently and always fail, even for a perfectly valid answer. Use a numeric
comparison instead:
    GOOD: ( Count >= 1 -> ... )
    BAD:  ( integer(Count), Count >= 1 -> ... )   -- integer(1.0) is false, this branch never runs
If you need a whole-number count for something like "how many entries to
collect", compare with >= /=< or convert explicitly with round/1 or
truncate/1 - do not test the term's type.
- ask_multiple_category for selecting SEVERAL applicable options in one
  question, instead of asking one boolean per option - use this for
  "which of the following apply?" style questions (e.g. multiple
  symptoms at once). Answer is bound to a Prolog list of the selected
  atoms/strings (an empty list if none apply). Categories is a plain
  list, e.g. ['thirst', 'polyuria', 'fatigue', 'blurred_vision'] - you
  do not need to add 'none' yourself, the UI adds it automatically.
- ask_multi_structured_input for collecting several related items at
  once: Mode is one of sequence (ordered list), ranking (list of
  rank-value pairs), or grouping (Groups is a list of group-name
  atoms/strings; Answer is a top-level dict keyed by group name). Only
  use this when the source text genuinely describes ordering, ranking,
  or grouped multi-item data - do not force it into this domain if
  nothing in the text calls for it.
- ask_multi_attribute_entity for collecting ONE structured record with
  several typed fields in a single question, instead of several
  separate questions (e.g. a single medication's name, dose, and
  frequency together). Fields is a list of [Key, Prompt, Type] lists
  (Type is one of string, int, float, bool, category - each is a plain
  3-element list, NOT a compound term, per JANUS RESULT SAFETY below).
  Answer is a top-level dict: _{{entity: Entity, data: _{{...}}}}.
  Only use this when the text describes multiple attributes of the
  SAME thing that naturally belong together (e.g. one medication's
  dose AND frequency) - do not force unrelated facts into one entity.

These three are OPTIONAL, more expressive alternatives to the basic
modalities above - use them only where they are a clearly better fit
than several separate ask_boolean/ask_category calls, grounded in what
the source text actually describes. Do not use them just to
demonstrate that they exist.

QUESTION WORDING - every ask_* question string is shown DIRECTLY to a
patient in a chat interface, so each one MUST be a complete, natural
question, never a bare label, noun phrase, or field name:
    GOOD: ask_boolean('Do you experience excessive thirst?')
    BAD:  ask_boolean('Thirst?')
    BAD:  ask_boolean('Excessive thirst')
    GOOD: ask_numeric('What is your fasting plasma glucose in mg/dL?', Value)
    BAD:  ask_numeric('Fasting glucose', Value)
    GOOD: ask_category('What is your current medication status?', [insulin, oral_antidiabetics, none], Answer)
    BAD:  ask_category('Medication status?', [insulin, oral_antidiabetics, none], Answer)
    GOOD: ask_range('How many hours did you fast before this blood sample?', 0, 24, Value)
    BAD:  ask_range('Fasting duration', 0, 24, Value)
This applies to every single ask_* call in the file, including ones
for symptoms, history, and lab values - none of them should read like
a form field label. Phrase each one the way a clinician would actually
ask the patient.

CRITICAL - ask_boolean/1 HAS NO OUTPUT ARGUMENT:
ask_boolean(Question) only succeeds (on "yes") or fails (on "no") - it does NOT bind
a value anywhere. To actually capture the yes/no answer into a variable, you MUST use
this exact if-then-else idiom:
    ( ask_boolean('Some question?') -> Flag = true ; Flag = false )
Writing `ask_boolean(Question), X = SomeVar` does NOT capture the answer - X/SomeVar
stay unbound, and the whole clause simply fails whenever the user answers "no" (with
no fallback), which breaks the entire diagnosis. Never write ask_boolean this way.

NEVER add placeholder, dummy, or "ensure predicate is referenced" clauses that exist
only to make ask_boolean/ask_numeric/etc appear used in the source. Every clause you
write must be part of real, reachable diagnostic logic. Do not write multiple
near-duplicate diagnose/1 clauses - write exactly ONE diagnose/1 clause that performs
the complete workflow.

JANUS RESULT SAFETY - THIS IS A HARD REQUIREMENT, NOT A STYLE PREFERENCE:
janus can only automatically convert certain Prolog term shapes back to Python
when they are bound to a query's free variable and returned as a result. It
handles: atoms, numbers, strings, lists (recursively), Key-Value pairs written
as Key-Value, and SWI-Prolog dicts (Tag{{...}} or _{{...}}) written at the TOP
LEVEL of the returned value. It CANNOT convert a custom-named compound term
(any Name(Arg1, Arg2, ...) you invent, e.g. diagnosis_summary(...), point(1,2),
fatigue_severity(3,mild)) - if ANY custom compound term appears ANYWHERE in the
value bound to a query's result variable, even nested inside a list or dict,
the whole query crashes with "Domain error: py_term expected". This happens
AFTER the user has already answered every question, which is the worst
possible place for a crash, so this must never happen.
Concretely, diagnose/1's argument (and the argument of any other predicate a
query might bind a free variable to) must be built ONLY from: atoms, numbers,
strings, lists, Key-Value pairs, and top-level dicts whose values are
themselves only atoms/numbers/strings/lists/pairs - never a custom compound.
    GOOD: diagnose(diabetes)   -- just the bare verdict atom
    GOOD: diagnose(_{{verdict: diabetes, evidence: random_glucose, symptoms: [thirst-true, fatigue-false]}})
    BAD:  diagnose(diagnosis_summary(diabetes, symptoms(true,false), ...))  -- custom compound, WILL crash
    BAD:  X = fatigue_severity(6, moderate), ... , Result = summary(V, X, ...)  -- nested custom compound, WILL crash
If you want to report a classified/severity value (e.g. "moderate" fatigue),
just use the plain atom (moderate) or a pair (fatigue-moderate) directly -
never wrap it in its own named compound like fatigue_severity(6, moderate).
This same rule applies to ask_multi_attribute_entity's Fields argument:
each field must be a plain list [Key, Prompt, Type], never a compound term
like field(Key, Prompt, Type) - a list of lists is janus-safe, a list of
custom compounds is not.

PREDICATE DESIGN:

Create clear public predicates.

For diagnosis:
- diagnose/1 should be the main workflow predicate.
- diabetes/0 should answer whether diabetes is logically true.
- prediabetes/0 should answer whether prediabetes is true.
- low_risk/0 should answer whether criteria are not met.

For specific criteria:
Create ONE standalone, independently-callable predicate PER criterion - each
takes NO external parameters (it asks for whatever it needs internally via
ask_numeric/ask_range/etc, it does not require the caller to already have a
value like FastingHours ready to pass in). This matters because a user's
natural-language question may be translated into a query that calls one of
these criterion predicates directly, in isolation, without going through
diagnose/1 first - if a criterion predicate needs an external input argument
to work correctly, calling it alone will crash with an uninstantiated-argument
error. Each criterion predicate must gather everything it needs itself:

Example (GOOD - each one is fully self-contained):

fasting_glucose_mgdl(Value) :- ask_numeric('What is your fasting plasma glucose in mg/dL?', Value).

diabetes_positive_by_fasting_glucose :-
    ask_duration('How many hours did you fast before this blood sample?', Hours),
    Hours >= 8, Hours =< 12,
    fasting_glucose_mgdl(Value),
    Value >= 126.

diabetes_positive_by_hba1c :-
    hba1c_percent(Value),
    Value >= 6.5.

BAD - do NOT write a single combined helper that bundles several criteria
together and requires the caller to already supply values like FastingHours
as an argument (e.g. numeric_diabetes_evidence(FastingHours, RandomValue, ...)):
this cannot be safely called except from inside diagnose/1's own exact
sequence, so any other query that tries to use it directly will break.
diagnose/1 may of course call each standalone criterion predicate in
sequence itself (stopping early once one succeeds) - the requirement is
just that each criterion ALSO works when called completely on its own.


IMPORTANT:
- diagnose/1 should stop asking further NUMERIC threshold criteria once one of them
  alone already justifies the verdict (do not check every numeric criterion).
- diagnose/1 must still ALSO collect the supporting boolean symptoms, categorical
  medication/history, and any duration/range detail described in the text, every time -
  these are not part of the "stop early" rule, they are the multi-modal clinical
  picture this system is designed to demonstrate.

OUTPUT:
Return only executable Prolog code.

Medical Text:

{text}
"""

    response = client.chat.completions.create(
        model="gpt-5-mini", messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()