:- use_module(library(janus)).

ask(Question) :-
    py_call(main:ask(Question), yes).

% Symptoms associated with hypertension
symptom(hypertension, headache).
symptom(hypertension, dizziness).
symptom(hypertension, blurred_vision).
symptom(hypertension, chest_pain).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease, S), Symptoms).

% Diagnostic criteria identifiers
criterion(hypertension, elevated_systolic).
criterion(hypertension, elevated_diastolic).
criterion(hypertension, repeated_measurements).
criterion(hypertension, antihypertensive_medication).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease, C), Criteria).

% Individual criterion queries

elevated_systolic(Result) :-
    ( ask('Is systolic blood pressure greater than or equal to 140 mmHg?')
    -> Result = true
    ; Result = false ).

elevated_diastolic(Result) :-
    ( ask('Is diastolic blood pressure greater than or equal to 90 mmHg?')
    -> Result = true
    ; Result = false ).

repeated_measurements(Result) :-
    ( ask('Have elevated blood pressure readings been observed on at least two separate occasions?')
    -> Result = true
    ; Result = false ).

antihypertensive_medication(Result) :-
    ( ask('Is the patient currently taking antihypertensive medication for diagnosed hypertension?')
    -> Result = true
    ; Result = false ).

% Hypertension diagnosis

hypertension(Result) :-

    elevated_systolic(SYS),
    elevated_diastolic(DIA),
    repeated_measurements(REP),
    antihypertensive_medication(MED),

    (
        (
            (SYS == true ; DIA == true),
            REP == true
        )
        ;
        MED == true
    )
    -> Result = true
    ; Result = false.

diagnose(Diagnosis) :-

    elevated_systolic(SYS),
    elevated_diastolic(DIA),
    repeated_measurements(REP),
    antihypertensive_medication(MED),

    (
        (
            (SYS == true ; DIA == true),
            REP == true
        )
        ;
        MED == true
    )
    ->
        findall(Name,
            (
                member(Name-Value,
                [
                    elevated_systolic-SYS,
                    elevated_diastolic-DIA,
                    repeated_measurements-REP,
                    antihypertensive_medication-MED
                ]),
                Value == true
            ),
            Positives),

        Diagnosis = diagnosis(hypertension, Positives)

    ;
        Diagnosis = diagnosis(normal_blood_pressure)
    ).