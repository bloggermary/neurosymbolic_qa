% diabetes_diagnosis.pl
% Requires SWI-Prolog with Janus (built-in from version 9.1+)

:- use_module(library(janus)).

% Ask a yes/no question via the Python function defined in diabetes_diagnosis.py
% Documentation: https://www.swi-prolog.org/pldoc/doc_for?object=janus%3Apy_call/1
ask(Question) :-
%   py_call(file_name:function_name(argument_value), return_value)
    py_call(diabetes_diagnosis:ask(Question), yes).

% Ask a categorical question via the Python function defined in diabetes_diagnosis.py
ask_category(Question, Categories, Answer) :-
    py_call(diabetes_diagnosis:ask_category(Question, Categories), Answer).

% Example categorical check
thirst_severity(Severity) :-
    ask_category("How severe is the patient's thirst?", [none, mild, moderate, severe], Severity).

% Symptom checks
has_polyuria       :- ask("Does the patient have polyuria (excessive urination)? (yes/no): ").
has_polydipsia     :- ask("Does the patient have polydipsia (excessive thirst)? (yes/no): ").
has_polyphagia     :- ask("Does the patient have polyphagia (excessive hunger)? (yes/no): ").
has_fatigue        :- ask("Does the patient have fatigue? (yes/no): ").
has_blurred_vision :- ask("Does the patient have blurred vision? (yes/no): ").
has_slow_healing   :- ask("Does the patient have slow-healing wounds? (yes/no): ").

% Lab value checks
high_fasting_glucose :- ask("Is fasting blood glucose >= 126 mg/dL? (yes/no): ").
high_hba1c           :- ask("Is HbA1c >= 6.5%? (yes/no): ").
impaired_glucose     :- ask("Is fasting blood glucose between 100-125 mg/dL? (yes/no): ").

% --- Diagnosis Rules ---

% Diabetes: lab confirmation + at least two classic symptoms
diabetes :-
    (high_fasting_glucose ; high_hba1c),
    has_polyuria,
    has_polydipsia,
    !.

diabetes :-
    (high_fasting_glucose ; high_hba1c),
    has_fatigue,
    has_blurred_vision,
    !.

% Prediabetes: borderline labs, some symptoms
prediabetes :-
    impaired_glucose,
    (has_fatigue ; has_polydipsia),
    !.

% Low risk: no lab flags
low_risk :-
    \+ high_fasting_glucose,
    \+ high_hba1c,
    \+ impaired_glucose.

% --- Entry point ---
diagnose :-
    write("=== Diabetes Screening ==="), nl,
    (   diabetes       -> write("Result: DIABETES likely. Please refer for full clinical evaluation.")
    ;   prediabetes    -> write("Result: PREDIABETES suspected. Lifestyle intervention recommended.")
    ;   low_risk       -> write("Result: LOW RISK. No immediate concern based on provided values.")
    ;                     write("Result: INCONCLUSIVE. Consider further testing.")
    ),
    nl.