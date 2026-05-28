:- dynamic known/2.

% Ask for numeric HbA1c value (percent)
ask(hba1c(Value)) :-
    (   known(hba1c, V)
    ->  Value = V
    ;   format('Enter HbA1c (%) as a number (e.g. 7.2). End with a period: '),
        read(R),
        (   number(R)
        ->  assertz(known(hba1c, R)),
            Value = R
        ;   write('Invalid input, please enter a number (e.g. 6.8).'), nl,
            ask(hba1c(Value))
        )
    ).

% Ask for numeric fasting glucose value (mg/dL)
ask(fasting_glucose(Value)) :-
    (   known(fasting_glucose, V)
    ->  Value = V
    ;   format('Enter fasting blood glucose (mg/dL) as a number (e.g. 110). End with a period: '),
        read(R),
        (   number(R)
        ->  assertz(known(fasting_glucose, R)),
            Value = R
        ;   write('Invalid input, please enter a number (e.g. 105).'), nl,
            ask(fasting_glucose(Value))
        )
    ).

% Ask about symptoms; succeeds if the user answers 'yes.'
ask(has_symptom(Symptom)) :-
    (   known(has_symptom(Symptom), Ans)
    ->  Ans == yes
    ;   format('Does the patient have ~w? (yes/no). End with a period: ', [Symptom]),
        read(Raw),
        (   Raw == yes
        ->  assertz(known(has_symptom(Symptom), yes))
        ;   Raw == no
        ->  assertz(known(has_symptom(Symptom), no)), fail
        ;   write('Please answer yes. or no.'), nl,
            ask(has_symptom(Symptom))
        )
    ).

% Common diabetes symptoms
possible_symptom(excessive_thirst).
possible_symptom(excessive_urination).
possible_symptom(fatigue).
possible_symptom(blurred_vision).

% Diagnosis rules

% Patients with HbA1c above 6.5% may have diabetes.
diabetes :-
    ask(hba1c(H)),
    number(H),
    H > 6.5.

% Patients with diabetes often experience both excessive thirst and excessive urination.
diabetes :-
    ask(has_symptom(excessive_thirst)),
    ask(has_symptom(excessive_urination)).

% Prediabetes: fasting blood glucose between 100 and 125 mg/dL.
prediabetes :-
    ask(fasting_glucose(G)),
    number(G),
    G >= 100,
    G =< 125.

% Utility: clear stored answers
clear_answers :-
    retractall(known(_, _)).

% A simple interactive diagnosis that queries and reports
diagnose :-
    clear_answers,
    (   diabetes
    ->  write('Result: Patient may have diabetes.'), nl
    ;   prediabetes
    ->  write('Result: Patient may have prediabetes.'), nl
    ;   write('Result: No diabetes or prediabetes identified from provided information.'), nl
    ).