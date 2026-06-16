:- use_module(library(janus)).

ask(Question) :-
    py_call(main:ask(Question), yes).

% Symptom facts for diseases
symptom(diabetes, excessive_thirst).
symptom(diabetes, excessive_urination).
symptom(diabetes, fatigue).
symptom(diabetes, blurred_vision).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease,S), Symptoms).

% Criterion facts mapping diseases to criterion keys
criterion(diabetes, random_glucose).
criterion(diabetes, fasting_glucose).
criterion(diabetes, ogtt_2h).
criterion(diabetes, hba1c).

criterion(prediabetes, fasting_prediabetes).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease,C), Criteria).

% Human-readable question text for each criterion key
criterion_question(random_glucose, 'Is random (non-fasting) plasma glucose >= 200 mg/dL (11.1 mmol/L)?').
criterion_question(fasting_glucose, 'Is fasting plasma glucose >= 126 mg/dL (7.0 mmol/L) after 8-12 hours fasting?').
criterion_question(ogtt_2h, 'Is the 2-hour plasma glucose in an oral glucose tolerance test >= 200 mg/dL (11.1 mmol/L)?').
criterion_question(hba1c, 'Is HbA1c >= 6.5% (48 mmol/mol)?').
criterion_question(fasting_prediabetes, 'Is fasting plasma glucose between 100 and 125 mg/dL (5.6-6.9 mmol/L)?').

% Helper: ask a single question key and return yes/no
ask_key(Key, Answer) :-
    criterion_question(Key, Q),
    ( ask(Q) -> Answer = yes ; Answer = no ).

% Helper: ask a list of keys, collect Key-Answer pairs
ask_all_keys([], []).
ask_all_keys([K|Ks], [K-A|Rest]) :-
    ask_key(K, A),
    ask_all_keys(Ks, Rest).

% Helper: collect keys answered yes from pairs
positive_keys(Pairs, Positives) :-
    findall(K, member(K-yes, Pairs), Positives).

% Lists of criterion keys per diagnostic group
diabetes_criteria([random_glucose, fasting_glucose, ogtt_2h, hba1c]).
prediabetes_criteria([fasting_prediabetes]).

% diabetes/1 asks all diabetes-specific diagnostic criteria and returns result
% Result = positive(ListOfPositiveCriteria) or negative
diabetes(Result) :-
    diabetes_criteria(Keys),
    ask_all_keys(Keys, Answers),
    positive_keys(Answers, Pos),
    ( Pos \= [] -> Result = positive(Pos) ; Result = negative ).

% prediabetes/1 asks prediabetes-specific criteria and returns result
% Result = positive(ListOfPositiveCriteria) or negative
prediabetes(Result) :-
    prediabetes_criteria(Keys),
    ask_all_keys(Keys, Answers),
    positive_keys(Answers, Pos),
    ( Pos \= [] -> Result = positive(Pos) ; Result = negative ).

% diagnose/1 asks all available diagnostic criteria (both diabetes and prediabetes)
% Collects all answers first, then evaluates the diagnosis.
% Result = diabetes(ListOfPositiveDiabetesCriteria)
%        ; prediabetes(ListOfPositivePrediabetesCriteria)
%        ; low_risk(AllAnswersPairs)
diagnose(Result) :-
    % gather all criteria keys known
    findall(K, criterion_question(K,_), AllKeys),
    % ask every available diagnostic question
    ask_all_keys(AllKeys, AllAnswers),
    % determine positives for diabetes and prediabetes
    diabetes_criteria(DKeys),
    prediabetes_criteria(PKeys),
    findall(K, (member(K-yes, AllAnswers), member(K, DKeys)), DPos),
    findall(K, (member(K-yes, AllAnswers), member(K, PKeys)), PPos),
    ( DPos \= [] -> Result = diabetes(DPos)
    ; PPos \= [] -> Result = prediabetes(PPos)
    ; Result = low_risk(AllAnswers)
    ).