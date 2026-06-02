ask(Question) :-
    py_call(main:ask(Question), yes).

% Diagnostic criteria identifiers
diag_criterion(random_glucose).
diag_criterion(fasting_glucose_diag).
diag_criterion(ogtt_2h).
diag_criterion(hba1c).

% Prediabetes specific criterion
prediabetes_criterion(fasting_glucose_prediabetes).

% Human-readable question texts for each criterion
criterion_text(random_glucose, 'Is random (casual) plasma glucose >= 200 mg/dL (11.1 mmol/L)?').
criterion_text(fasting_glucose_diag, 'Is fasting plasma glucose >= 126 mg/dL (7.0 mmol/L) after 8-12 hours of fasting?').
criterion_text(ogtt_2h, 'Is 2-hour plasma glucose in an oral glucose tolerance test >= 200 mg/dL (11.1 mmol/L)?').
criterion_text(hba1c, 'Is HbA1c >= 6.5% (48 mmol/mol)?').
criterion_text(fasting_glucose_prediabetes, 'Is fasting plasma glucose between 100 and 125 mg/dL (5.6-6.9 mmol/L)?').

% Symptoms mentioned in the text
symptom(diabetes, excessive_thirst).
symptom(diabetes, excessive_urination).
symptom(diabetes, fatigue).
symptom(diabetes, blurred_vision).

% Human-readable symptom questions
symptom_text(excessive_thirst, 'Does the patient have excessive thirst?').
symptom_text(excessive_urination, 'Does the patient have excessive urination?').
symptom_text(fatigue, 'Does the patient experience fatigue?').
symptom_text(blurred_vision, 'Does the patient have blurred vision?').

% Convenience collections
criteria(Disease, Criteria) :-
    findall(C, criterion(Disease, C), Criteria).

criterion(diabetes, random_glucose).
criterion(diabetes, fasting_glucose_diag).
criterion(diabetes, ogtt_2h).
criterion(diabetes, hba1c).
criterion(prediabetes, fasting_glucose_prediabetes).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease, S), Symptoms).

% Map any question id to its text (criterion or symptom)
question_text(Id, Text) :-
    criterion_text(Id, Text).
question_text(Id, Text) :-
    symptom_text(Id, Text).

% Ask a yes/no question and return yes/no
ask_yesno(Id, Answer) :-
    question_text(Id, Text),
    ( ask(Text) -> Answer = yes ; Answer = no ).

% Ask a list of question ids, collecting Id-Answer pairs (asks all before evaluating)
ask_all([], []).
ask_all([Id|Rest], [Id-Ans|Pairs]) :-
    ask_yesno(Id, Ans),
    ask_all(Rest, Pairs).

% Evaluate diabetes presence from collected answers:
has_diabetes(Pairs) :-
    member(random_glucose-yes, Pairs);
    member(fasting_glucose_diag-yes, Pairs);
    member(ogtt_2h-yes, Pairs);
    member(hba1c-yes, Pairs).

% Evaluate prediabetes from collected answers:
% Prediabetes: fasting glucose between 100-125 mg/dL and no diabetes criterion met
has_prediabetes(Pairs) :-
    member(fasting_glucose_prediabetes-yes, Pairs),
    \+ has_diabetes(Pairs).

% low_risk: no diabetes criteria and no prediabetes
has_low_risk(Pairs) :-
    \+ has_diabetes(Pairs),
    \+ has_prediabetes(Pairs).

% Main entry: diagnose/0
% Ask all available diagnostic criteria (diabetes criteria + prediabetes criterion),
% collect all answers first, then evaluate and report. Do not stop after first positive.
diagnose :-
    findall(Id, diag_criterion(Id), DiagIds),
    findall(Pid, prediabetes_criterion(Pid), PredIds),
    append(DiagIds, PredIds, AllIds),
    ask_all(AllIds, Pairs),
    % After collecting answers, evaluate
    ( has_diabetes(Pairs) ->
        write('Diagnosis: Diabetes mellitus is present according to at least one diagnostic criterion.'), nl
    ; has_prediabetes(Pairs) ->
        write('Diagnosis: Prediabetes (impaired fasting glucose) is present.'), nl
    ; write('Diagnosis: No diabetes or prediabetes criteria were met (low risk based on these criteria).'), nl
    ),
    % Also report which criteria were positive for transparency
    write('Collected criterion answers: '), write(Pairs), nl.

% Specific predicate for asking only diabetes diagnostic criteria
diabetes :-
    findall(Id, diag_criterion(Id), DiagIds),
    ask_all(DiagIds, Pairs),
    ( has_diabetes(Pairs) ->
        write('Diabetes: YES (one or more diagnostic criteria met).'), nl
    ; write('Diabetes: NO (no diabetes diagnostic criteria met).'), nl
    ),
    write('Collected diabetes criterion answers: '), write(Pairs), nl.

% Specific predicate for prediabetes
prediabetes :-
    findall(Id, prediabetes_criterion(Id), PredIds),
    ask_all(PredIds, Pairs),
    ( has_prediabetes(Pairs) ->
        write('Prediabetes: YES (fasting glucose in 100-125 mg/dL and no diabetes criteria present).'), nl
    ; write('Prediabetes: NO.'), nl
    ),
    write('Collected prediabetes criterion answers: '), write(Pairs), nl.

% Optional: low_risk predicate if user asks specifically about low risk
low_risk :-
    findall(Id, diag_criterion(Id), DiagIds),
    findall(Pid, prediabetes_criterion(Pid), PredIds),
    append(DiagIds, PredIds, AllIds),
    ask_all(AllIds, Pairs),
    ( has_low_risk(Pairs) ->
        write('Low risk: YES (no diabetes or prediabetes criteria met).'), nl
    ; write('Low risk: NO (some criterion suggests diabetes or prediabetes).'), nl
    ),
    write('Collected answers for risk assessment: '), write(Pairs), nl.