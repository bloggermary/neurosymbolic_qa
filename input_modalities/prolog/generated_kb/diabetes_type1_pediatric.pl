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

ask_multiple_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_multiple_category(Question, Categories), Answer).

ask_multi_structured_input(Question, Mode, Groups, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Groups), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).

/* Diagnostic criteria predicates (standalone) */

/* Random plasma glucose criterion: ≥ 200 mg/dL */
random_glucose_criterion :-
    ask_numeric('What is the random plasma glucose in mg/dL?', Value),
    ( Value >= 200.0 ).

/* Fasting plasma glucose criterion: ≥ 126 mg/dL */
fasting_glucose_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    ( Value >= 126.0 ).

/* HbA1c criterion: ≥ 6.5% */
hba1c_criterion :-
    ask_numeric('What is the HbA1c percentage?', Value),
    ( Value >= 6.5 ).

/* Prediabetes fasting criterion: 100–125 mg/dL (asks minimal required) */
fasting_prediabetes_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    ( Value >= 100.0, Value < 126.0 ).

/* Prediabetes HbA1c criterion: 5.7–6.4% */
hba1c_prediabetes_criterion :-
    ask_numeric('What is the HbA1c percentage?', Value),
    ( Value >= 5.7, Value < 6.5 ).

/* Emergency symptoms that mandate immediate referral (any one is sufficient) */
emergency_symptoms :-
    ask_multiple_category('Has the child experienced any of the following emergency symptoms (select all that apply)?', [nausea, vomiting, abdominal_pain, rapid_breathing], Answers),
    ( Answers = [] -> fail ; true ).

/* When emergency symptoms present, optionally collect key DKA labs (asked only then) */
dka_lab_values :-
    emergency_symptoms,
    ask_numeric('What is the venous blood pH?', PH),
    ask_numeric('What is the serum bicarbonate in mEq/L?', Bicarbonate),
    % succeed regardless of values; values are collected for clinician use
    ( number(PH), number(Bicarbonate) ).

/* Classic symptom triad: polyuria, polydipsia, unexplained weight loss (all three) */
triad_symptoms :-
    ask_multiple_category('Which of these classic symptoms does the child have? (select all that apply)', [polyuria, polydipsia, unexplained_weight_loss], Answers),
    member(polyuria, Answers),
    member(polydipsia, Answers),
    member(unexplained_weight_loss, Answers).

/* Rapid onset in days: characteristic if less than 14 days */
symptom_duration_short :-
    ask_duration('How many days have the symptoms been present?', Days),
    ( Days < 14.0 ).

/* Dehydration severity rating 1–10 (optional supplementary detail) */
dehydration_severity :-
    ask_range('On a scale of 1 (mild) to 10 (severe shock), how severe is the dehydration?', 1, 10, _Severity).

/* Autoantibody results collection (GAD65, IA-2, ZnT8) */
autoantibody_results :-
    Fields = [
      ['gad65', 'GAD65 antibody result (positive / negative / not_tested)', category],
      ['ia2', 'IA-2 antibody result (positive / negative / not_tested)', category],
      ['znt8', 'ZnT8 antibody result (positive / negative / not_tested)', category]
    ],
    ask_multi_attribute_entity('Please provide autoantibody test results for GAD65, IA-2, and ZnT8.', autoantibodies, Fields, _Answer).

/* Medication status (none / insulin / unknown) */
medication_status(Status) :-
    ask_category('What is the child''s current diabetes medication status?', [none, insulin, unknown], Status).

/* Public diagnostic predicates */

/* Diabetes is true if any core glycemic threshold is met */
diabetes :-
    random_glucose_criterion
    ;
    fasting_glucose_criterion
    ;
    hba1c_criterion.

/* Prediabetes based on commonly used ranges (asks minimal required data) */
prediabetes :-
    fasting_prediabetes_criterion
    ;
    hba1c_prediabetes_criterion.

/* Low risk when neither diabetes nor prediabetes nor emergency features are present */
low_risk :-
    \+ diabetes,
    \+ prediabetes,
    ask_multiple_category('Has the child experienced any of the following emergency symptoms (select all that apply)?', [nausea, vomiting, abdominal_pain, rapid_breathing], Answers),
    Answers = [].

/* Main workflow: adaptive questioning and conclusions.
   Returns a janus-safe top-level dict describing the result. */
diagnose(Result) :-
    (  emergency_symptoms ->
          % Immediate referral required; collect labs for grading if available
          dka_lab_values,
          Result = _{verdict: dka_emergency, action: 'Immediate referral required'}
    ;  random_glucose_criterion ->
          Result = _{verdict: diabetes, evidence: random_plasma_glucose}
    ;  fasting_glucose_criterion ->
          Result = _{verdict: diabetes, evidence: fasting_plasma_glucose}
    ;  hba1c_criterion ->
          Result = _{verdict: diabetes, evidence: hba1c}
    ;  triad_symptoms, symptom_duration_short ->
          Result = _{verdict: suspected_type1, evidence: symptoms, rapid_onset: true, recommended: 'Obtain confirmatory glycemic testing (fasting/random glucose or HbA1c) and consider autoantibody testing'}
    ;  triad_symptoms ->
          Result = _{verdict: suspected_type1, evidence: symptoms, rapid_onset: false, recommended: 'Obtain confirmatory glycemic testing'}
    ;  prediabetes ->
          Result = _{verdict: prediabetes}
    ;  low_risk ->
          Result = _{verdict: low_risk}
    ).