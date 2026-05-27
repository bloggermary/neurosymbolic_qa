:- use_module(library(janus)).

ask(Question) :-
    py_call(diabetes_diagnosis:ask(Question), yes).

% Diagnosekriterien als Ja/Nein-Fragen
random_plasma_glucose :-
    ask('Gelegenheits-Plasmaglukose >= 11.1 mmol/l (200 mg/dl)?').

fasting_plasma_glucose :-
    ask('Nüchtern-Plasmaglukose >= 7.0 mmol/l (126 mg/dl) nach 8-12 Stunden Fasten?').

ogtt_2h :-
    ask('Oraler Glukosetoleranztest: Plasmaglukose nach 2 Stunden >= 11.1 mmol/l (200 mg/dl)?').

hba1c :-
    ask('HbA1c >= 48 mmol/mol (6.5%)?').

% diagnose/1 liefert diabetes, wenn eines der Kriterien erfüllt ist,
% andernfalls no_diabetes.
diagnose(diabetes) :-
    ( random_plasma_glucose
    ; fasting_plasma_glucose
    ; ogtt_2h
    ; hba1c
    ), !.

diagnose(no_diabetes) :-
    \+ ( random_plasma_glucose
       ; fasting_plasma_glucose
       ; ogtt_2h
       ; hba1c
       ).