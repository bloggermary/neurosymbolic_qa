:- use_module(library(janus)).

ask(Question) :-
    py_call(main:ask(Question), yes).

% Symptoms for asthma
symptom(asthma, wheezing).
symptom(asthma, shortness_of_breath).
symptom(asthma, chest_tightness).
symptom(asthma, coughing).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease, S), Symptoms).

% Diagnostic criteria identifiers
criterion(asthma, recurrent_symptoms).
criterion(asthma, bronchodilator_response).
criterion(asthma, variable_airflow_limitation).
criterion(asthma, nighttime_symptoms).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease, C), Criteria).

% Individual criterion queries

recurrent_symptoms(Result) :-
    ( ask('Does the patient experience recurrent episodes of wheezing, coughing, chest tightness, or shortness of breath?')
    -> Result = true
    ; Result = false ).

bronchodilator_response(Result) :-
    ( ask('Do symptoms improve after using a bronchodilator inhaler?')
    -> Result = true
    ; Result = false ).

variable_airflow_limitation(Result) :-
    ( ask('Has spirometry shown variable airflow limitation consistent with asthma?')
    -> Result = true
    ; Result = false ).

nighttime_symptoms(Result) :-
    ( ask('Does the patient experience symptoms that worsen at night or early morning?')
    -> Result = true
    ; Result = false ).

% Asthma diagnosis

asthma(Result) :-
    recurrent_symptoms(RS),
    bronchodilator_response(BR),
    variable_airflow_limitation(VA),
    nighttime_symptoms(NS),

    PositiveCount is
        (RS == true -> 1 ; 0) +
        (BR == true -> 1 ; 0) +
        (VA == true -> 1 ; 0) +
        (NS == true -> 1 ; 0),

    ( PositiveCount >= 2
    -> Result = true
    ; Result = false ).

diagnose(Diagnosis) :-

    recurrent_symptoms(RS),
    bronchodilator_response(BR),
    variable_airflow_limitation(VA),
    nighttime_symptoms(NS),

    findall(Name,
        (
            member(Name-Value,
            [
                recurrent_symptoms-RS,
                bronchodilator_response-BR,
                variable_airflow_limitation-VA,
                nighttime_symptoms-NS
            ]),
            Value == true
        ),
        Positives
    ),

    length(Positives, Count),

    ( Count >= 2 ->
        Diagnosis = diagnosis(asthma, Positives)
    ;
        Diagnosis = diagnosis(low_probability_asthma)
    ).