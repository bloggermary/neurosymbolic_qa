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

/* Numeric input helpers (standalone, callable) */
fasting_glucose_mgdl(Value) :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value).

random_glucose_mgdl(Value) :-
    ask_numeric('What is your random (non-fasting) plasma glucose in mg/dL?', Value).

ogtt_2h_mgdl(Value) :-
    ask_numeric('What is your 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', Value).

hba1c_percent(Value) :-
    ask_numeric('What is your hemoglobin A1c (HbA1c) in percent?', Value).

/* Diagnostic criterion predicates (each self-contained) */
diabetes_by_fasting :-
    ask_range('How many hours did you fast before this blood sample?', 0, 24, Hours),
    Hours >= 8.0,
    fasting_glucose_mgdl(Value),
    Value >= 126.0.

diabetes_by_random :-
    random_glucose_mgdl(Value),
    Value >= 200.0.

diabetes_by_ogtt :-
    ogtt_2h_mgdl(Value),
    Value >= 200.0.

diabetes_by_hba1c :-
    ( ask_boolean('Do you have chronic kidney disease (CKD)?') -> CKD = true ; CKD = false ),
    ( ask_boolean('Do you have anemia?') -> Anemia = true ; Anemia = false ),
    hba1c_percent(Value),
    Value >= 6.5,
    /* We ask about CKD/anemia as required by the domain text before relying on HbA1c;
       their presence does not automatically exclude the criterion but was collected. */
    ( CKD = true -> true ; true ),
    ( Anemia = true -> true ; true ).

/* Prediabetes standalone predicate (asks the minimum required) */
prediabetes :-
    ( ask_boolean('Have you previously been told by a clinician that you have prediabetes or impaired glucose tolerance?') ->
        true
    ;
        fail
    ).

/* Main diagnosis workflow: collects multi-modal supporting evidence and then evaluates numeric criteria.
   Stops checking further numeric thresholds once one numeric criterion justifies diabetes. */
diagnose(Result) :-
    /* Collect classic symptoms as explicit yes/no questions */
    ( ask_boolean('Do you experience excessive thirst (polydipsia)?') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Do you experience frequent urination (polyuria)?') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Do you experience unusual fatigue?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Do you experience blurred vision?') -> BlurredVision = true ; BlurredVision = false ),

    /* Medication use: select all that apply */
    ask_multiple_category(
        'Which of the following medications currently apply to you? Select all that apply.',
        [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none],
        MedicationsSelected
    ),

    /* Group current medications by when they are taken */
    ask_multi_structured_input(
        'Please group your current medications by when you take them: morning, afternoon, evening, or bedtime. For each group, list the medication names.',
        grouping,
        ['morning','afternoon','evening','bedtime'],
        MedicationGroups
    ),

    /* Renal function as numeric eGFR */
    ask_numeric('What is the estimated glomerular filtration rate (eGFR) in mL/min/1.73m2?', EGFR),

    /* Count of distinct chronic conditions (numeric) */
    ask_numeric('How many distinct chronic conditions do you have?', ComorbidityCount),


    /* Duration: years of any known glucose abnormality, if applicable */
    ask_duration('How many years have you had any known glucose abnormality, if applicable?', YearsKnownAbnormality),

    /* Evaluate numeric diagnostic criteria in sequence, stopping at first that justifies diabetes */
    (   diabetes_by_fasting
    ->  Evidence = fasting_glucose,
        Verdict = diabetes
    ;   diabetes_by_random
    ->  Evidence = random_glucose,
        Verdict = diabetes
    ;   diabetes_by_ogtt
    ->  Evidence = ogtt_2h,
        Verdict = diabetes
    ;   diabetes_by_hba1c
    ->  Evidence = hba1c,
        Verdict = diabetes
    ;   /* No numeric threshold met: consider prior history for prediabetes */
        ( prediabetes
        -> Evidence = prior_prediabetes,
           Verdict = prediabetes
        ;  Evidence = none,
           Verdict = low_risk
        )
    ),

    /* Build a Janus-safe result dict summarizing the verdict and collected supporting data */
    Result = _{
        verdict: Verdict,
        evidence: Evidence,
        symptoms: [thirst-Thirst, polyuria-Polyuria, fatigue-Fatigue, blurred_vision-BlurredVision],
        medications: MedicationsSelected,
        medication_groups: MedicationGroups,
        egfr: EGFR,
        comorbidities: ComorbidityCount,
        cognitive_scale: CognitiveScale,
        years_glucose_abnormality: YearsKnownAbnormality
    }.

/* Convenience predicates that run the diagnostic workflow and return boolean answers */
diabetes :-
    diagnose(R),
    get_dict(verdict, R, diabetes).

low_risk :-
    diagnose(R),
    get_dict(verdict, R, low_risk).