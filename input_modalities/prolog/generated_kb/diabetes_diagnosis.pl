:- use_module(library(janus)).

ask_boolean(Key, Question) :-
    py_call(main:ask_boolean(Key, Question), true).

ask_numeric(Key, Question, Value) :-
    py_call(main:ask_numeric(Key, Question), Value).

ask_string(Key, Question, Value) :-
    py_call(main:ask_string(Key, Question), Value).

ask_category(Key, Question, Categories, Answer) :-
    py_call(main:ask_category(Key, Question, Categories), Answer).

ask_range(Key, Question, Start, Stop, Value) :-
    py_call(main:ask_range(Key, Question, Start, Stop), Value).

ask_duration(Key, Question, Value) :-
    py_call(main:ask_duration(Key, Question), Value).

% Simple ask/1 wrapper that uses predefined question texts for boolean items.
question_text(excessive_thirst, "Does the patient have excessive thirst?").
question_text(excessive_urination, "Does the patient have excessive urination?").
question_text(fatigue, "Does the patient have fatigue?").
question_text(blurred_vision, "Does the patient have blurred vision?").

ask(Key) :-
    question_text(Key, Q),
    ask_boolean(Key, Q).

% Diagnostic criteria for diabetes mellitus.
% Any one criterion is sufficient.

% Random plasma glucose criterion (mg/dL). Threshold >= 200 mg/dL.
random_plasma_glucose_diabetes :-
    ask_numeric(random_plasma_glucose_mg_dl, "Enter random plasma glucose (mg/dL):", Value),
    Value >= 200.

% Fasting plasma glucose criterion (mg/dL) after 8-12 h fast. Threshold >= 126 mg/dL.
fasting_plasma_glucose_diabetes :-
    ask_numeric(fasting_plasma_glucose_mg_dl, "Enter fasting plasma glucose after 8-12 h fast (mg/dL):", Value),
    Value >= 126.

% 2-hour OGTT plasma glucose criterion (mg/dL). Threshold >= 200 mg/dL.
ogtt_2h_plasma_glucose_diabetes :-
    ask_numeric(ogtt_2h_plasma_glucose_mg_dl, "Enter 2-hour OGTT plasma glucose (mg/dL):", Value),
    Value >= 200.

% HbA1c criterion (%). Threshold >= 6.5%.
hba1c_diabetes :-
    ask_numeric(hba1c_percent, "Enter HbA1c (%) : (e.g. 6.5)", Value),
    Value >= 6.5.

% Top-level diagnosis predicate for diabetes mellitus.
% Succeeds if any one of the diagnostic criteria is met.
diagnose(diabetes) :-
    random_plasma_glucose_diabetes.
diagnose(diabetes) :-
    fasting_plasma_glucose_diabetes.
diagnose(diabetes) :-
    ogtt_2h_plasma_glucose_diabetes.
diagnose(diabetes) :-
    hba1c_diabetes.

% Prediabetes: fasting plasma glucose 100-125 mg/dL.
% This classification can be concluded from the fasting value alone.
prediabetes :-
    ask_numeric(fasting_plasma_glucose_mg_dl, "Enter fasting plasma glucose after 8-12 h fast (mg/dL):", Value),
    Value >= 100,
    Value =< 125.

% Symptom-based suggestion (not diagnostic): both excessive thirst and urination often occur.
symptoms_suggest_diabetes :-
    ask(excessive_thirst),
    ask(excessive_urination).

% Additional symptom queries available individually.
has_fatigue :-
    ask(fatigue).

has_blurred_vision :-
    ask(blurred_vision).