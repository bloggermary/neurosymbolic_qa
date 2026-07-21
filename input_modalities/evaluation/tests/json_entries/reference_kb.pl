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

/* Numeric measurement predicates */
random_glucose_mgdl(Value) :-
    ask_numeric('Random plasma glucose (mg/dL)?', Value).

fasting_glucose_mgdl(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value).

fasting_plasma_glucose_mgdl(Value) :-
    fasting_glucose_mgdl(Value).

fasting_duration_hours(Hours) :-
    ask_duration('Hours fasting before sample?', Hours).

ogtt_2hr_mgdl(Value) :-
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)?', Value).

hba1c_percent(Value) :-
    ask_numeric('HbA1c (%)?', Value).

/* Symptom predicates */
excessive_thirst :-
    ask_boolean('Excessive thirst?').

excessive_urination :-
    ask_boolean('Excessive urination (polyuria)?').

fatigue :-
    ask_boolean('Fatigue?').

blurred_vision :-
    ask_boolean('Blurred vision?').

/* Diagnostic criterion predicates */
diabetes_positive_by_random_glucose :-
    random_glucose_mgdl(Value),
    Value >= 200.

diabetes_positive_by_fasting_glucose :-
    fasting_duration_hours(Hours),
    Hours >= 8,
    Hours =< 12,
    fasting_glucose_mgdl(Value),
    Value >= 126.

diabetes_positive_by_ogtt :-
    ogtt_2hr_mgdl(Value),
    Value >= 200.

diabetes_positive_by_hba1c :-
    hba1c_percent(Value),
    Value >= 6.5.

/* Public diagnosis predicates */
diabetes_positive :-
    diabetes_positive_by_random_glucose
    ;
    diabetes_positive_by_fasting_glucose
    ;
    diabetes_positive_by_ogtt
    ;
    diabetes_positive_by_hba1c.

diabetes :-
    diabetes_positive.

prediabetes_positive :-
    \+ diabetes_positive,
    fasting_duration_hours(Hours),
    Hours >= 8,
    Hours =< 12,
    fasting_glucose_mgdl(Value),
    Value >= 100,
    Value =< 125.

prediabetes :-
    prediabetes_positive.

low_risk :-
    \+ diabetes_positive,
    \+ prediabetes_positive.

diagnose(diabetes) :-
    diabetes_positive, !.

diagnose(prediabetes) :-
    \+ diabetes_positive,
    prediabetes_positive, !.

diagnose(low_risk) :-
    \+ diabetes_positive,
    \+ prediabetes_positive.
