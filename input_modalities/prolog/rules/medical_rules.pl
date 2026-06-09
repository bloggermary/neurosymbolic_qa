%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Medical Reasoning Knowledge Base Rules
% University-level symbolic reasoning layer
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Core Ontology Constraints
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A disease is valid if it is declared explicitly
valid_disease(D) :-
    disease(D).

% A symptom is valid if linked to a known disease
valid_symptom(D, S) :-
    symptom(D, S),
    disease(D).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Diagnostic Reasoning (Forward Inference)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A disease is suspected if ALL required symptoms are present
% (strong diagnostic rule)
possible_diagnosis(PatientSymptoms, Disease) :-
    disease(Disease),
    findall(S, symptom(Disease, S), RequiredSymptoms),
    subset(RequiredSymptoms, PatientSymptoms).


% A weak diagnosis if at least one symptom matches
weak_diagnosis(PatientSymptoms, Disease) :-
    disease(Disease),
    symptom(Disease, S),
    member(S, PatientSymptoms).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Risk Factor Reasoning
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A disease risk is elevated if risk factor is present
high_risk(Disease, Factors) :-
    disease(Disease),
    findall(F, risk_factor(Disease, F), Factors),
    Factors \= [].


% Check if a specific risk factor applies
has_risk_factor(Disease, Factor) :-
    risk_factor(Disease, Factor).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Treatment Reasoning
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% A disease is treatable if at least one treatment exists
treatable(Disease) :-
    disease(Disease),
    treatment(Disease, _).


% Retrieve all treatments
all_treatments(Disease, Treatments) :-
    findall(T, treatment(Disease, T), Treatments).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Symptom Aggregation Logic
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Count matching symptoms between patient and disease
symptom_overlap(PatientSymptoms, Disease, Count) :-
    findall(S,
        (symptom(Disease, S), member(S, PatientSymptoms)),
        Matches
    ),
    length(Matches, Count).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Ranking / Best Match Diagnosis
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

best_match(PatientSymptoms, BestDisease) :-
    findall(Count-Disease,
        symptom_overlap(PatientSymptoms, Disease, Count),
        Pairs
    ),
    sort(Pairs, Sorted),
    reverse(Sorted, [_-BestDisease | _]).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Utility Predicates
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

subset([], _).
subset([H|T], List) :-
    member(H, List),
    subset(T, List).


member(X, [X|_]).
member(X, [_|T]) :-
    member(X, T).