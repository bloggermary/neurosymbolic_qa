:- multifile ask/1.

% Common diabetes symptoms
common_symptom(excessive_thirst).
common_symptom(excessive_urination).
common_symptom(fatigue).
common_symptom(blurred_vision).

% Input wrappers (use ask/1 to obtain information from the user/system)
hba1c(Patient, Value) :-
    ask(hba1c(Patient, Value)).

fasting_glucose(Patient, Value) :-
    ask(fasting_glucose(Patient, Value)).

has_symptom(Patient, Symptom) :-
    ask(symptom(Patient, Symptom)).

% Diagnosis rules

% Patients with HbA1c above 6.5% may have diabetes
diagnosis(Patient, diabetes) :-
    hba1c(Patient, V),
    number(V),
    V > 6.5.

% Prediabetes when fasting blood glucose is between 100 and 125 mg/dL
diagnosis(Patient, prediabetes) :-
    fasting_glucose(Patient, V),
    number(V),
    V >= 100,
    V =< 125.

% Patients with diabetes often experience both excessive thirst and excessive urination.
diagnosis(Patient, diabetes) :-
    has_symptom(Patient, excessive_thirst),
    has_symptom(Patient, excessive_urination).

% Supportive rule: possible diabetes when at least two common symptoms are present
possible_diabetes(Patient) :-
    findall(S, (common_symptom(S), has_symptom(Patient, S)), Symptoms),
    sort(Symptoms, Unique),
    length(Unique, N),
    N >= 2.

    diagnose(Result) :-
        ( diagnosis(_, diabetes) ->
            Result = diabetes
        ; diagnosis(_, prediabetes) ->
            Result = prediabetes
        ; possible_diabetes(_) ->
            Result = possible_diabetes
        ;   Result = no_diabetes
        ).
    