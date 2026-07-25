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

/* Standalone numeric/lab criteria predicates */

/* Fasting plasma glucose diagnostic criterion: >= 126 mg/dL */
fasting_diabetes_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    ( Value >= 126.0 -> true ; fail ).

/* Random (non-fasting) plasma glucose diagnostic criterion: >= 200 mg/dL */
random_diabetes_criterion :-
    ask_numeric('What is the random (non-fasting) plasma glucose in mg/dL?', Value),
    ( Value >= 200.0 -> true ; fail ).

/* 2-hour OGTT diagnostic criterion: >= 200 mg/dL */
ogtt_diabetes_criterion :-
    ask_numeric('What is the 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', Value),
    ( Value >= 200.0 -> true ; fail ).

/* HbA1c unreliability check: chronic kidney disease or anemia */
hba1c_unreliable :-
    ( ask_boolean('Do you have chronic kidney disease?') -> CKD = true ; CKD = false ),
    ( ask_boolean('Do you have anemia?') -> Anemia = true ; Anemia = false ),
    ( CKD = true ; Anemia = true ).

/* HbA1c diagnostic criterion: >= 6.5% when reliable; if unreliable, require confirmatory glucose test */
hba1c_diabetes_criterion :-
    ask_numeric('What is the glycated hemoglobin (HbA1c) percentage?', Value),
    ( Value >= 6.5 ->
        ( hba1c_unreliable ->
            /* If HbA1c is potentially unreliable, require a confirmatory glucose test */
            ( fasting_diabetes_criterion ; random_diabetes_criterion ; ogtt_diabetes_criterion )
        ;
            true
        )
    ; fail ).

/* Prediabetes criterion (checks minimal necessary tests in sequence, stops when one applies)
   - fasting 100-125 mg/dL
   - OR 2-hour OGTT 140-199 mg/dL
   - OR HbA1c 5.7-6.4% when HbA1c is considered reliable */
prediabetes_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 100.0, Fasting < 126.0 -> true
    ;
      /* If fasting not in prediabetes range, check OGTT next */
      ask_numeric('What is the 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', Ogtt),
      ( Ogtt >= 140.0, Ogtt < 200.0 -> true
      ;
        /* If OGTT not in range, check HbA1c last (only if reliable) */
        ask_numeric('What is the glycated hemoglobin (HbA1c) percentage?', Hba1c),
        Hba1c >= 5.7, Hba1c < 6.5,
        \+ hba1c_unreliable
      )
    ).

/* Classic symptoms: succeed if any classic symptom is present (asks in a single question) */
classic_symptoms :-
    ask_multiple_category('Which of the following classic symptoms do you experience? Select all that apply.', ['excessive_thirst','frequent_urination','fatigue','blurred_vision'], List),
    member(_, List).

/* Medication confounders: succeed if any of the listed glucose-raising medication classes are selected */
meds_confounders :-
    ask_multiple_category('Which of the following medications do you currently take? Select all that apply.', ['corticosteroids','thiazide_diuretics','atypical_antipsychotics','none'], List),
    /* succeed only if user selected at least one real medication (not just "none") */
    member(Choice, List),
    Choice \= none,
    !.

/* Group current medications by time of day: collect grouped input (always succeeds after asking) */
med_grouping :-
    ask_multi_structured_input('Please list your current medications grouped by when you take them: morning, afternoon, evening, or bedtime. For each group, enter medication names separated by commas.', grouping, ['morning','afternoon','evening','bedtime'], _Answer),
    true.

/* Capture eGFR as a numeric value (standalone predicate asks and succeeds) */
egfr_value :-
    ask_numeric('What is the estimated glomerular filtration rate (eGFR) in mL/min/1.73m2?', _Value),
    true.

/* Number of distinct chronic conditions (count) */
comorbidity_count :-
    ask_numeric('How many distinct chronic conditions do you have?', _Count),
    true.

/* Cognitive and functional status rating 1-10 */
cognitive_rating :-
    ask_range('On a scale from 1 (fully independent) to 10 (fully dependent), how would you rate your cognitive and functional status?', 1, 10, _Rating),
    true.

/* Years of known glucose abnormality (duration in years) */
years_glucose_history :-
    ask_duration('How many years have you had any known glucose abnormality?', _Years),
    true.

/* Systolic blood pressure and unintentional weight loss (used only when glucose evidence is inconclusive) */
systolic_bp_and_weight_loss :-
    ask_numeric('What is the systolic blood pressure (mmHg)?', _Systolic),
    ask_numeric('How many kilograms of unintentional weight loss have you had over the past 6 months?', _Kg),
    true.

/* Public helper predicates for direct queries (standalone, no args) */

diabetes :-
    ( fasting_diabetes_criterion
    ; random_diabetes_criterion
    ; ogtt_diabetes_criterion
    ; hba1c_diabetes_criterion ).

prediabetes :-
    \+ diabetes,
    prediabetes_criterion.

low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* Main diagnostic workflow: adaptive questioning, stops when a confident conclusion is reached.
   Returns a janus-safe top-level dict with verdict and minimal supporting evidence. */
diagnose(Result) :-
    ( fasting_diabetes_criterion ->
        Result = _{verdict: diabetes, evidence: fasting_glucose}
    ; random_diabetes_criterion ->
        Result = _{verdict: diabetes, evidence: random_glucose}
    ; ogtt_diabetes_criterion ->
        Result = _{verdict: diabetes, evidence: ogtt}
    ; hba1c_diabetes_criterion ->
        ( hba1c_unreliable ->
            /* HbA1c required confirmatory glucose test to satisfy diabetes() above, so label accordingly */
            Result = _{verdict: diabetes, evidence: hba1c_confirmed_by_glucose}
        ;
            Result = _{verdict: diabetes, evidence: hba1c}
        )
    ; prediabetes_criterion ->
        /* Gather a limited set of supporting contextual data that meaningfully affects interpretation */
        ask_multiple_category('Which of the following medications do you currently take? Select all that apply.', ['corticosteroids','thiazide_diuretics','atypical_antipsychotics','none'], MedList),
        ask_multi_structured_input('Please list your current medications grouped by when you take them: morning, afternoon, evening, or bedtime. For each group, enter medication names separated by commas.', grouping, ['morning','afternoon','evening','bedtime'], GroupingDict),
        ask_numeric('What is the estimated glomerular filtration rate (eGFR) in mL/min/1.73m2?', Egfr),
        ask_numeric('How many distinct chronic conditions do you have?', ComorbCount),
        ask_range('On a scale from 1 (fully independent) to 10 (fully dependent), how would you rate your cognitive and functional status?', 1, 10, CogRating),
        ask_duration('How many years have you had any known glucose abnormality?', YearsGlucose),
        /* Convert grouping dict to pairs to keep the top-level Result janus-safe (no nested dicts) */
        dict_pairs(GroupingDict, _, GroupPairs),
        Result = _{verdict: prediabetes,
                   evidence: prediabetes_test,
                   medications: MedList,
                   medication_groups: GroupPairs,
                   egfr: Egfr,
                   comorbidity_count: ComorbCount,
                   cognitive_rating: CogRating,
                   years_glucose_history: YearsGlucose}
    ;
        /* No diagnostic thresholds met and not prediabetes */
        Result = _{verdict: low_risk}
    ).