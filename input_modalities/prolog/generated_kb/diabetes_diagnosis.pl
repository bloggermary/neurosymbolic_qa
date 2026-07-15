:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value).

ask_category(Question, Categories, Answer) :-
    py_call(main:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(main:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(main:ask_duration(Question), Value).  

ask_category_multiple(Question, Categories, Answers) :-
    py_call(main:ask_category_multiple(Question, Categories), Answers).

ask_multi_attribute_entity(Question, Entity, Fields, Result) :-
    py_call(main:ask_multi_attribute_entity(Question, Entity), Fields, Result).

ask_multi_structured_input(Question, Mode, Groups, Result) :-
    py_call(main:ask_multi_structured_input(Question, Mode, Groups), Result).

% simple wrapper for boolean questions if needed by workflows
ask(Question) :-
    ask_boolean(Question).

% Specific checks for diagnostic criteria
random_plasma_glucose_mgdl(Value) :-
    ask_numeric('Random (casual) plasma glucose (mg/dL)?', Value).

fasting_plasma_glucose_mgdl(Value) :-
    ask_numeric('Fasting plasma glucose after 8-12 hours fast (mg/dL)?', Value).

ogtt_2h_plasma_mmol_l(Value) :-
    ask_numeric('2-hour plasma glucose during oral glucose tolerance test (mmol/L)?', Value).

hba1c_percent(Value) :-
    ask_numeric('HbA1c (%)?', Value).

% Predicate that establishes diabetes by any single diagnostic criterion.
% This predicate asks only the minimum necessary questions and stops as soon as
% one diagnostic criterion for diabetes is met.
diabetes :-
    random_plasma_glucose_mgdl(RG),
    ( RG >= 200 ->
        true
    ; fasting_plasma_glucose_mgdl(FG),
      ( FG >= 126 ->
          true
      ; ogtt_2h_plasma_mmol_l(OGTT),
        ( OGTT >= 11.1 ->
            true
        ; hba1c_percent(H),
          H >= 6.5
        )
      )
    ).

% Predicate for prediabetes based on fasting plasma glucose (mg/dL).
% As per source, prediabetes may occur when fasting blood glucose is between 100 and 125 mg/dL.
prediabetes :-
    fasting_plasma_glucose_mgdl(FG),
    FG >= 100,
    FG =< 125.

% low_risk is true if neither diabetes nor prediabetes can be established.
% This will call diabetes and prediabetes; those predicates will ask the
% minimal necessary information to reach a conclusion.
low_risk :-
    \+ diabetes,
    \+ prediabetes.

% Main entry predicate for overall diagnosis.
% According to requirements, diagnose/1 will query all available diagnostic criteria
% (random glucose, fasting glucose, OGTT 2h, HbA1c) before producing a result.
% It then classifies as diabetes if any criterion meets thresholds, otherwise
% as prediabetes if fasting glucose in 100-125 mg/dL, otherwise no_diabetes.
diagnose(diabetes) :-
    random_plasma_glucose_mgdl(RG),
    fasting_plasma_glucose_mgdl(FG),
    ogtt_2h_plasma_mmol_l(OGTT),
    hba1c_percent(H),
    ( RG >= 200
    ; FG >= 126
    ; OGTT >= 11.1
    ; H >= 6.5
    ), !.

diagnose(prediabetes) :-
    % ask same set of measurements to ensure full evaluation was performed
    random_plasma_glucose_mgdl(_RG),
    fasting_plasma_glucose_mgdl(FG),
    ogtt_2h_plasma_mmol_l(_OGTT),
    hba1c_percent(_H),
    FG >= 100,
    FG =< 125, !.

diagnose(no_diabetes) :-
    % full set of measurements asked and none meet criteria for diabetes or prediabetes
    random_plasma_glucose_mgdl(RG),
    fasting_plasma_glucose_mgdl(FG),
    ogtt_2h_plasma_mmol_l(OGTT),
    hba1c_percent(H),
    RG < 200,
    FG < 100,
    OGTT < 11.1,
    H < 6.5.