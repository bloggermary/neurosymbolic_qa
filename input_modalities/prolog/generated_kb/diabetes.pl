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

/* Standalone numeric/lab criterion predicates (each asks its own questions) */

/* Random plasma glucose ≥ 11.1 mmol/L (200 mg/dL) */
random_glucose_criterion :-
    ask_numeric('What is the random plasma glucose in mmol/L?', Value),
    Value >= 11.1.

/* Fasting plasma glucose ≥ 7.0 mmol/L (126 mg/dL) after 8–12 hours of fasting */
fasting_glucose_criterion :-
    ask_numeric('What is the fasting plasma glucose in mmol/L?', Value),
    ask_range('How many hours did you fast before this blood sample?', 0.0, 72.0, Hours),
    Hours >= 8.0,
    Hours =< 12.0,
    Value >= 7.0.

/* 2-hour plasma glucose during OGTT ≥ 11.1 mmol/L (200 mg/dL) */
ogtt_2h_criterion :-
    ask_numeric('What is the 2-hour plasma glucose during an oral glucose tolerance test in mmol/L?', Value),
    Value >= 11.1.

/* HbA1c ≥ 6.5% (48 mmol/mol) */
hba1c_criterion :-
    ask_numeric('What is the HbA1c percentage?', Value),
    Value >= 6.5.

/* Prediabetes fasting criterion: fasting plasma glucose between 100 and 125 mg/dL */
prediabetes_fasting_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0,
    Value =< 125.0.

/* Symptom collection and interpretation (used as supportive evidence) */
collect_symptoms(SymptomList) :-
    ask_multiple_category('Which of the following symptoms currently apply to you? Please select all that apply: excessive thirst, excessive urination, fatigue, blurred vision.', [excessive_thirst, excessive_urination, fatigue, blurred_vision], SymptomList).

symptom_support_level(SupportLevel) :-
    collect_symptoms(List),
    (   member(excessive_thirst, List),
        member(excessive_urination, List)
    ->  SupportLevel = strong
    ;   (   member(excessive_thirst, List)
        ;   member(excessive_urination, List)
        )
    ->  SupportLevel = partial
    ;   SupportLevel = none
    ).

/* If multiple symptoms present, optionally ask for their order */
symptom_order_if_needed(Order) :-
    collect_symptoms(List),
    length(List, N),
    (   N > 1
    ->  ask_string('You reported more than one symptom. Please list the symptoms in the order they first appeared, from earliest to most recent (use the symptom names)', Order)
    ;   Order = []
    ).

/* If fatigue present, optionally ask severity and classify */
fatigue_severity_class(Class) :-
    collect_symptoms(List),
    (   member(fatigue, List)
    ->  ask_range('On a scale from 1 to 10, how severe is your fatigue (1 = mild, 10 = severe)?', 1.0, 10.0, Score),
        (   Score >= 1.0, Score =< 3.0 -> Class = mild
        ;   Score >= 4.0, Score =< 6.0 -> Class = moderate
        ;   Score >= 7.0, Score =< 10.0 -> Class = severe
        )
    ;   Class = none
    ).

/* Thirst severity when thirst is reported */
thirst_severity_if_needed(Severity) :-
    collect_symptoms(List),
    (   member(excessive_thirst, List)
    ->  ask_category('How would you describe your thirst severity?', [none, mild, moderate, severe], Severity)
    ;   Severity = none
    ).

/* Medication recording: if patient is taking diabetes medications, collect structured entries */
collect_medications(MedPairs) :-
    (   ask_boolean('Are you currently taking any diabetes medication?')
    ->  (   ask_numeric('How many diabetes medications do you take?', CountF),
            CountF >= 1.0
        ->  CountInt is integer(CountF),
            collect_medications_n(CountInt, [], RevPairs),
            reverse(RevPairs, MedPairs)
        ;   MedPairs = []
        )
    ;   MedPairs = []
    ).

collect_medications_n(0, Acc, Acc) :- !.
collect_medications_n(N, Acc, MedPairs) :-
    N > 0,
    number_string(N, NStr),
    atomic_list_concat(['med_', NStr], EntityName),
    Fields = [
        ['name', 'Medication name', string],
        ['dose_mg', 'Dose in milligrams', float],
        ['times_per_day', 'How many times per day is it taken?', float]
    ],
    ask_multi_attribute_entity('Please provide the medication details', EntityName, Fields, Answer),
    get_dict(data, Answer, DataDict),
    dict_pairs(DataDict, _, Pairs),
    N1 is N - 1,
    collect_medications_n(N1, [Pairs|Acc], MedPairs).

/* High-level predicates required */

/* diabetes/0 succeeds if any diagnostic diabetes criterion is met */
diabetes :-
    (   random_glucose_criterion
    ;   fasting_glucose_criterion
    ;   ogtt_2h_criterion
    ;   hba1c_criterion
    ).

/* prediabetes/0 succeeds if prediabetes fasting criterion is met */
prediabetes :-
    prediabetes_fasting_criterion.

/* low_risk/0 succeeds when neither diabetes nor prediabetes criteria are met */
low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* Main adaptive diagnosis workflow.
   Returns a janus-safe dict describing the verdict and minimal supporting evidence. */
diagnose(Result) :-
    % First, check for diabetes criteria, stopping at first positive criterion.
    (   (   random_glucose_criterion
        ->  Evidence = [random_glucose],
            SymptomSupport = none,
            Result = _{verdict: diabetes, evidence: Evidence, symptom_support: SymptomSupport}
        ;   fasting_glucose_criterion
        ->  Evidence = [fasting_glucose],
            SymptomSupport = none,
            Result = _{verdict: diabetes, evidence: Evidence, symptom_support: SymptomSupport}
        ;   ogtt_2h_criterion
        ->  Evidence = [ogtt_2h],
            SymptomSupport = none,
            Result = _{verdict: diabetes, evidence: Evidence, symptom_support: SymptomSupport}
        ;   hba1c_criterion
        ->  Evidence = [hba1c],
            SymptomSupport = none,
            Result = _{verdict: diabetes, evidence: Evidence, symptom_support: SymptomSupport}
        )
    ->  true
    ;   % No diabetes by numeric criteria. Check for prediabetes.
        (   prediabetes_fasting_criterion
        ->  % For prediabetes, collect basic symptom support (one combined question) to contextualize the finding.
            collect_symptoms(SList),
            (   SList = [] -> SymSupport = none ; (member(excessive_thirst, SList), member(excessive_urination, SList) -> SymSupport = strong ; SymSupport = partial) ),
            Result = _{verdict: prediabetes, evidence: [prediabetes_fasting], symptom_support: SymSupport}
        ;   % Neither diabetes nor prediabetes: low risk. Offer optional short risk and symptom recording.
            (   ask_boolean('Would you like to record current symptoms and risk factors to help future follow-up?')
            ->  collect_symptoms(SList2),
                (   SList2 = [] -> SymSupport2 = none ; (member(excessive_thirst, SList2), member(excessive_urination, SList2) -> SymSupport2 = strong ; SymSupport2 = partial) ),
                % Do not include medication details in the top-level result to keep the returned structure simple.
                Result = _{verdict: low_risk, evidence: [], symptom_support: SymSupport2}
            ;   Result = _{verdict: low_risk, evidence: [], symptom_support: none}
            )
        )
    ).