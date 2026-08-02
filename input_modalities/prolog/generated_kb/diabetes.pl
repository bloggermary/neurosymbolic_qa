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

ask_multi_structured_input(Question, Mode, Structure, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Structure), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).

/* Main entry point: returns a dictionary with verdict and evidence */
diagnose(Result) :-
    ( taking_diabetes_medications(Meds)
      -> Result = _{verdict: diabetes, evidence: [_{basis: medications, medications: Meds}]}
    ;  check_fasting(FastingOutcome)
      -> fasting_outcome_result(FastingOutcome, Result)
    ;  check_random_glucose(RandomV)
      -> Result = _{verdict: diabetes, evidence: [_{basis: random_plasma_glucose_mgdl, value: RandomV}]}
    ;  check_ogtt_2h(OGTTV)
      -> Result = _{verdict: diabetes, evidence: [_{basis: ogtt_2h_plasma_glucose_mgdl, value: OGTTV}]}
    ;  check_hba1c(HbA1cV)
      -> Result = _{verdict: diabetes, evidence: [_{basis: hba1c_percent, value: HbA1cV}]}
    ;  assess_symptoms(SymVerdict)
      -> symptom_outcome_result(SymVerdict, Result)
    ;  Result = _{verdict: insufficient_data, evidence: []}
    ).

/* Medication check: if patient is taking any diabetes medication, collect structured entries */
taking_diabetes_medications(Medications) :-
    ( ask_boolean('Are you currently taking any diabetes medication?')
      -> ask_multi_attribute_entity('Please enter each diabetes medication as a separate entry (name, dose in mg, times per day).', medication,
            [
                [name, 'What is the medication name?', string],
                [dose_mg, 'What is the dose in mg?', float],
                [times_per_day, 'How many times per day is it taken?', float]
            ],
            Medications)
      ;  fail
    ).

/* Fasting glucose check: asks fasting glucose and classifies outcome */
check_fasting(outcome(diabetes, Value)) :-
    ask_numeric('What is the fasting plasma glucose in mg/dL (after 8-12 hours of fasting)?', Value),
    Value >= 126.0.
check_fasting(outcome(prediabetes, Value)) :-
    ask_numeric('What is the fasting plasma glucose in mg/dL (after 8-12 hours of fasting)?', Value),
    Value >= 100.0,
    Value =< 125.0.
check_fasting(outcome(normal, Value)) :-
    ask_numeric('What is the fasting plasma glucose in mg/dL (after 8-12 hours of fasting)?', Value),
    Value < 100.0.

/* Helper to convert fasting outcome into the overall result or allow further checks */
fasting_outcome_result(outcome(diabetes, Value), _{verdict: diabetes, evidence: [_{basis: fasting_plasma_glucose_mgdl, value: Value}]}) :- !.
fasting_outcome_result(outcome(prediabetes, Value), _{verdict: prediabetes, evidence: [_{basis: fasting_plasma_glucose_mgdl, value: Value}]}) :- !.
fasting_outcome_result(outcome(normal, _Value), _) :- fail.

/* Random plasma glucose check */
check_random_glucose(Value) :-
    ask_numeric('What is the random (any time) plasma glucose in mg/dL?', Value),
    Value >= 200.0.

/* 2-hour OGTT check */
check_ogtt_2h(Value) :-
    ask_numeric('What is the 2-hour plasma glucose during an oral glucose tolerance test (OGTT) in mg/dL?', Value),
    Value >= 200.0.

/* HbA1c check */
check_hba1c(Value) :-
    ask_numeric('What is the HbA1c percentage (e.g. 6.5)?', Value),
    Value >= 6.5.

/* Symptom assessment: only ask when numeric and medication checks did not establish a diagnosis */
assess_symptoms(strong_support(Symptoms)) :-
    ask_multiple_category('Select all symptoms that currently apply (choose all that apply): excessive thirst, excessive urination, fatigue, blurred vision.', 
                          ['excessive_thirst','excessive_urination','fatigue','blurred_vision'],
                          Symptoms),
    member('excessive_thirst', Symptoms),
    member('excessive_urination', Symptoms), !.
assess_symptoms(partial_support(Symptoms)) :-
    ask_multiple_category('Select all symptoms that currently apply (choose all that apply): excessive thirst, excessive urination, fatigue, blurred vision.', 
                          ['excessive_thirst','excessive_urination','fatigue','blurred_vision'],
                          Symptoms),
    ( member('excessive_thirst', Symptoms)
    ; member('excessive_urination', Symptoms)
    ; member('fatigue', Symptoms)
    ; member('blurred_vision', Symptoms)
    ),
    \+ ( member('excessive_thirst', Symptoms), member('excessive_urination', Symptoms) ).

/* Convert symptom assessment into an overall result */
symptom_outcome_result(strong_support(Symptoms), _{verdict: possible_diabetes, evidence: [_{basis: symptom_pattern_strong, symptoms: Symptoms}]}) :- !.
symptom_outcome_result(partial_support(Symptoms), _{verdict: insufficient_data, evidence: [_{basis: symptom_pattern_partial, symptoms: Symptoms}]}) :- !.