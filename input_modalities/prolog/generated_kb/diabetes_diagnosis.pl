:- dynamic known/2.

clear_answers :-
    retractall(known(_,_)).

% Ask for numeric HbA1c value
ask(hba1c(Value)) :-
    known(hba1c, Value), !.
ask(hba1c(Value)) :-
    write('Enter HbA1c (%) value (e.g. 6.5): '), flush_output,
    read(Input),
    (  number(Input)
    -> Value = Input,
       asserta(known(hba1c, Value))
    ;  write('Invalid input. Please enter a numeric value.'), nl,
       ask(hba1c(Value))
    ).

% Ask for numeric fasting glucose value
ask(fasting_glucose(Value)) :-
    known(fasting_glucose, Value), !.
ask(fasting_glucose(Value)) :-
    write('Enter fasting blood glucose (mg/dL) (e.g. 110): '), flush_output,
    read(Input),
    (  number(Input)
    -> Value = Input,
       asserta(known(fasting_glucose, Value))
    ;  write('Invalid input. Please enter a numeric value.'), nl,
       ask(fasting_glucose(Value))
    ).

% Ask about a named symptom; succeeds if user answers yes, fails if no.
ask(symptom(Name)) :-
    known(symptom(Name), Answer),
    Answer == yes, !.
ask(symptom(Name)) :-
    known(symptom(Name), Answer),
    Answer == no, !, fail.
ask(symptom(Name)) :-
    format('Does the patient have ~w? (yes/no): ', [Name]), flush_output,
    read(Response),
    (  Response == yes
    -> asserta(known(symptom(Name), yes))
    ;  Response == no
    -> asserta(known(symptom(Name), no)), fail
    ;  write('Please answer yes or no.'), nl,
       ask(symptom(Name))
    ).

% Diagnosis rules

% Patients with HbA1c above 6.5% may have diabetes.
diabetes :-
    ask(hba1c(V)),
    V > 6.5.

% Patients with diabetes often experience both excessive thirst and excessive urination.
diabetes :-
    ask(symptom(excessive_thirst)),
    ask(symptom(excessive_urination)).

% Prediabetes may occur when fasting blood glucose is between 100 and 125 mg/dL.
prediabetes :-
    ask(fasting_glucose(G)),
    G >= 100,
    G =< 125.

% Convenience wrapper to query diagnoses
diagnosis(diabetes) :- diabetes.
diagnosis(prediabetes) :- prediabetes.