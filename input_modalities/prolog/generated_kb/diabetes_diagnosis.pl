:- module(diabetes_kb, [diagnose/0, diabetes/0, prediabetes/0, low_risk/0]).

% Use Janus/py_call for user interaction as required
ask(Question) :-
    py_call(main:ask(Question), yes).

% Generic yes/no query wrapper that always asks and returns yes/no atom
query_yesno(Question, yes) :-
    ask(Question), !.
query_yesno(_Question, no).

% Helper to lookup answers in a list of pairs Key-Value
lookup(Key, [Key-Value|_], Value) :- !.
lookup(Key, [_|T], Value) :-
    lookup(Key, T, Value).

% Collect all diagnostic criteria and symptom questions first, before any evaluation.
collect_all_answers(Answers) :-
    query_yesno("Is the random (casual) plasma glucose >= 200 mg/dL (11.1 mmol/L)?", RandomPlasmaHigh),
    query_yesno("Is the fasting plasma glucose >= 126 mg/dL (7.0 mmol/L) after 8-12 hours fasting?", FastingDiabetes),
    query_yesno("Is the 2-hour plasma glucose in the oral glucose tolerance test >= 200 mg/dL (11.1 mmol/L)?", OGTT2hHigh),
    query_yesno("Is the HbA1c >= 6.5% (48 mmol/mol)?", HbA1cHigh),
    query_yesno("Is the fasting plasma glucose between 100 and 125 mg/dL (5.6-6.9 mmol/L)?", FastingPrediabetes),
    query_yesno("Does the patient have excessive thirst?", ExcessiveThirst),
    query_yesno("Does the patient have excessive urination?", ExcessiveUrination),
    query_yesno("Does the patient have fatigue?", Fatigue),
    query_yesno("Does the patient have blurred vision?", BlurredVision),
    Answers = [
        random_plasma_glucose-RandomPlasmaHigh,
        fasting_plasma_glucose_diabetes-FastingDiabetes,
        ogtt_2h-OGTT2hHigh,
        hba1c-HbA1cHigh,
        fasting_plasma_glucose_prediabetes-FastingPrediabetes,
        symptom_thirst-ExcessiveThirst,
        symptom_urination-ExcessiveUrination,
        symptom_fatigue-Fatigue,
        symptom_blurred_vision-BlurredVision
    ].

% Evaluate whether laboratory criteria meet diabetes (any one criterion suffices)
diabetes_laboratory(Answers) :-
    lookup(random_plasma_glucose, Answers, yes), !.
diabetes_laboratory(Answers) :-
    lookup(fasting_plasma_glucose_diabetes, Answers, yes), !.
diabetes_laboratory(Answers) :-
    lookup(ogtt_2h, Answers, yes), !.
diabetes_laboratory(Answers) :-
    lookup(hba1c, Answers, yes), !.

% Evaluate whether criteria meet prediabetes (fasting between 100 and 125 mg/dL)
prediabetes_fastening(Answers) :-
    lookup(fasting_plasma_glucose_prediabetes, Answers, yes).

% Symptoms support: both excessive thirst and excessive urination often seen in diabetes
symptoms_support_diabetes(Answers) :-
    lookup(symptom_thirst, Answers, yes),
    lookup(symptom_urination, Answers, yes).

% High-level predicate: diagnose/0
% Must ask all available diagnostic criteria before producing a result.
% Collects all answers first, then evaluates and reports.
diagnose :-
    collect_all_answers(Answers),
    (   diabetes_laboratory(Answers)
    ->  format("Diagnosis: Diabetes mellitus criteria met by laboratory values.~n", [])
    ;   ( prediabetes_fastening(Answers)
        -> format("Result: Prediabetes (impaired fasting glucose) likely based on fasting glucose range.~n", [])
        ;  ( symptoms_support_diabetes(Answers)
           -> format("Result: Symptoms (thirst + urination) suggest diabetes, but no laboratory diagnostic criteria were reported as met.~n", [])
           ;  format("Result: No laboratory criteria for diabetes or prediabetes were reported; patient appears low risk based on available answers.~n", [])
           )
        )
    ),
    % Also print a summary of collected answers for transparency
    format("Summary of answers:~n", []),
    print_answers(Answers).

% Helper to print collected answers
print_answers([]).
print_answers([Key-Value|T]) :-
    format(" - ~w: ~w~n", [Key, Value]),
    print_answers(T).

% Predicate diabetes/0: specific check for diabetes logical truth
% Ask only the diagnostic criteria relevant to diabetes and then evaluate.
diabetes :-
    query_yesno("Is the random (casual) plasma glucose >= 200 mg/dL (11.1 mmol/L)?", RandomPlasmaHigh),
    query_yesno("Is the fasting plasma glucose >= 126 mg/dL (7.0 mmol/L) after 8-12 hours fasting?", FastingDiabetes),
    query_yesno("Is the 2-hour plasma glucose in the oral glucose tolerance test >= 200 mg/dL (11.1 mmol/L)?", OGTT2hHigh),
    query_yesno("Is the HbA1c >= 6.5% (48 mmol/mol)?", HbA1cHigh),
    Answers = [
        random_plasma_glucose-RandomPlasmaHigh,
        fasting_plasma_glucose_diabetes-FastingDiabetes,
        ogtt_2h-OGTT2hHigh,
        hba1c-HbA1cHigh
    ],
    (   diabetes_laboratory(Answers)
    ->  format("Diabetes: TRUE (one or more diagnostic laboratory criteria met).~n", [])
    ;   format("Diabetes: FALSE (no diagnostic laboratory criteria met).~n", []), fail
    ).

% Predicate prediabetes/0: specific check for prediabetes (fasting 100-125 mg/dL)
prediabetes :-
    query_yesno("Is the fasting plasma glucose between 100 and 125 mg/dL (5.6-6.9 mmol/L)?", FastingPrediabetes),
    (   FastingPrediabetes == yes
    ->  format("Prediabetes: TRUE (impaired fasting glucose range reported).~n", [])
    ;   format("Prediabetes: FALSE (fasting glucose not reported in the 100-125 mg/dL range).~n", []), fail
    ).

% Predicate low_risk/0: true if none of the diabetes or prediabetes criteria and no cardinal symptoms
low_risk :-
    collect_all_answers(Answers),
    \+ diabetes_laboratory(Answers),
    \+ prediabetes_fastening(Answers),
    lookup(symptom_thirst, Answers, no),
    lookup(symptom_urination, Answers, no),
    lookup(symptom_fatigue, Answers, no),
    lookup(symptom_blurred_vision, Answers, no),
    format("Low risk: No laboratory criteria for diabetes/prediabetes and no key symptoms reported.~n", []).