:- use_module(library(janus)).

ask(Question) :-
    py_call(main:ask(Question), yes).

% Symptoms for diabetes
symptom(diabetes, excessive_thirst).
symptom(diabetes, excessive_urination).
symptom(diabetes, fatigue).
symptom(diabetes, blurred_vision).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease, S), Symptoms).

% Diagnostic criteria identifiers
criterion(diabetes, random_glucose).
criterion(diabetes, fasting_glucose).
criterion(diabetes, ogtt_2h).
criterion(diabetes, hba1c).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease, C), Criteria).

% Individual criterion queries (return true/false without double-prompting)
random_glucose(Result) :-
    ( ask('Random plasma glucose >= 11.1 mmol/l (200 mg/dl)?') -> Result = true ; Result = false ).

fasting_glucose(Result) :-
    ( ask('Fasting plasma glucose >= 7.0 mmol/l (126 mg/dl) after 8-12 hours fasting?') -> Result = true ; Result = false ).

ogtt_2h(Result) :-
    ( ask('2-hour plasma glucose in oral glucose tolerance test >= 11.1 mmol/l?') -> Result = true ; Result = false ).

hba1c(Result) :-
    ( ask('HbA1c >= 48 mmol/mol (6.5%)?') -> Result = true ; Result = false ).

% Prediabetes fasting-range criterion
fasting_pred(Result) :-
    ( ask('Fasting plasma glucose between 100 and 125 mg/dL (5.6-6.9 mmol/l)?') -> Result = true ; Result = false ).

% diabetes/1: asks all diabetes diagnostic criteria once, then returns true/false
diabetes(Result) :-
    random_glucose(RG),
    fasting_glucose(FG),
    ogtt_2h(OG),
    hba1c(HB),
    ( (RG == true ; FG == true ; OG == true ; HB == true) -> Result = true ; Result = false ).

% prediabetes/1: asks fasting prediabetes criterion and ensures no diabetes criterion is positive.
prediabetes(Result) :-
    % Ask all diabetes criteria and prediabetes fasting range (collect answers first)
    random_glucose(RG),
    fasting_glucose(FG),
    ogtt_2h(OG),
    hba1c(HB),
    fasting_pred(PRED),
    ( PRED == true,
      RG \== true, FG \== true, OG \== true, HB \== true
    -> Result = true
    ; Result = false ).

% diagnose/1: ask all available diagnostic criteria, collect answers, then evaluate
% The result is a structured term:
%   diagnosis(diabetes, [ListOfPositiveCriteria])
%   diagnosis(prediabetes)
%   diagnosis(low_risk)
diagnose(Diagnosis) :-
    % Ask all criteria first (each predicate prompts once)
    random_glucose(RG),
    fasting_glucose(FG),
    ogtt_2h(OG),
    hba1c(HB),
    fasting_pred(PRED),
    % Evaluate after collection
    ( (RG == true ; FG == true ; OG == true ; HB == true) ->
        findall(Name,
                ( member(Name-Value, [random_glucose-RG, fasting_glucose-FG, ogtt_2h-OG, hba1c-HB]),
                  Value == true ),
                Positives),
        Diagnosis = diagnosis(diabetes, Positives)
    ; PRED == true ->
        Diagnosis = diagnosis(prediabetes)
    ;
        Diagnosis = diagnosis(low_risk)
    ).