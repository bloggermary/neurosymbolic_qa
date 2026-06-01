% ask/1: ask a yes/no question, accept yes/y/true and no/n/false (case-insensitive)
ask(Question) :-
    format('~w (yes/no): ', [Question]),
    read_line_to_string(user_input, Raw),
    ( Raw = "" ->
        write('Please answer yes or no.'), nl,
        ask(Question)
    ;
        string_lower(Raw, Lower),
        normalize_space(string(Input), Lower),
        ( member(Input, ["yes","y","true"]) -> true
        ; member(Input, ["no","n","false"]) -> fail
        ; write('Please answer yes or no.'), nl,
          ask(Question)
        )
    ).

% Symptom predicates that query the user
symptom(excessive_thirst) :-
    ask('Do you have excessive thirst').

symptom(excessive_urination) :-
    ask('Do you have excessive urination').

symptom(fatigue) :-
    ask('Do you have fatigue').

symptom(blurred_vision) :-
    ask('Do you have blurred vision').

% Laboratory-based checks
hbA1c_above_65 :-
    ask('Is your HbA1c above 6.5%').

fasting_100_125 :-
    ask('Is your fasting blood glucose between 100 and 125 mg/dL').

% Diagnostic rules (logical)
diabetes_condition :-
    hbA1c_above_65.

diabetes_condition :-
    symptom(excessive_thirst),
    symptom(excessive_urination).

prediabetes_condition :-
    fasting_100_125.

% Public predicates required by the specification

% diabetes/0: run the diabetes check and report result (uses ask/1)
diabetes :-
    ( diabetes_condition ->
        write('Diagnosis: Diabetes suspected.'), nl
    ;
        write('Diagnosis: Diabetes not indicated.'), nl
    ).

% prediabetes/0: run the prediabetes check and report result (uses ask/1)
prediabetes :-
    ( prediabetes_condition ->
        write('Diagnosis: Prediabetes suspected.'), nl
    ;
        write('Diagnosis: Prediabetes not indicated.'), nl
    ).

% diagnose/0: perform a full interview for diabetes and prediabetes
diagnose :-
    write('Beginning diagnostic interview.'), nl,
    diabetes,
    prediabetes,
    write('Diagnostic interview complete.'), nl.