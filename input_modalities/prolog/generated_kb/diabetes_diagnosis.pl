:- use_module(library(janus)).

ask(Question) :-
    py_call(main:ask(Question), yes).

/* Symptoms */
symptom(diabetes, excessive_thirst).
symptom(diabetes, excessive_urination).
symptom(diabetes, fatigue).
symptom(diabetes, blurred_vision).

symptoms(Disease, Symptoms) :-
    findall(S, symptom(Disease, S), Symptoms).

/* Diagnostic criteria */
criterion(diabetes, random_plasma_glucose).
criterion(diabetes, fasting_plasma_glucose).
criterion(diabetes, ogtt_2h).
criterion(diabetes, hba1c).

criterion(prediabetes, fasting_100_125).

criteria(Disease, Criteria) :-
    findall(C, criterion(Disease, C), Criteria).

/* Human-readable questions for each criterion and symptom */
question_text(random_plasma_glucose, 'Is the random (casual) plasma glucose >= 200 mg/dL (11.1 mmol/L)?').
question_text(fasting_plasma_glucose, 'Is the fasting plasma glucose >= 126 mg/dL (7.0 mmol/L) after 8-12 hours fasting?').
question_text(ogtt_2h, 'Is the 2-hour plasma glucose in the oral glucose tolerance test >= 200 mg/dL (11.1 mmol/L)?').
question_text(hba1c, 'Is the HbA1c >= 6.5% (48 mmol/mol)?').
question_text(fasting_100_125, 'Is the fasting plasma glucose between 100 and 125 mg/dL (prediabetes)?').

question_text(excessive_thirst, 'Does the patient have excessive thirst?').
question_text(excessive_urination, 'Does the patient have excessive urination?').
question_text(fatigue, 'Does the patient feel fatigued?').
question_text(blurred_vision, 'Does the patient have blurred vision?').

/* Gather answers for a list of items (criteria or symptoms).
   Each answer is returned as a pair (Item, yes) or (Item, no).
   This predicate asks every question, regardless of individual answers. */
gather_answers([], []).
gather_answers([Item|Rest], [(Item,Answer)|RestAnswers]) :-
    (   question_text(Item, Q)
    ->  ( ask(Q) -> Answer = yes ; Answer = no )
    ;   % If no question_text is available, default to no and continue
        Answer = no
    ),
    gather_answers(Rest, RestAnswers).

/* Helper: check if an item is marked yes in gathered answers */
positive(Item, Answers) :-
    member((Item, yes), Answers).

/* Evaluate diagnosis given gathered answers.
   - Diabetes is true if any diabetes criterion is positive.
   - Prediabetes is true if prediabetes criterion positive and diabetes is not true.
   - Low risk is true if no diagnostic criteria are positive and no diabetes symptoms present. */
evaluate_outcome(Answers, outcome{
    diabetes:DiabetesBool,
    prediabetes:PrediabetesBool,
    positive_criteria:PosCriteria,
    positive_symptoms:PosSymptoms,
    low_risk:LowRiskBool
}) :-
    % collect positive criteria
    findall(C, (criterion(_,C), positive(C, Answers)), PosCriteriaDup),
    list_to_set(PosCriteriaDup, PosCriteria),
    % collect positive symptoms
    findall(S, (symptom(_,S), positive(S, Answers)), PosSymptomsDup),
    list_to_set(PosSymptomsDup, PosSymptoms),
    % diabetes true if any diabetes-specific criterion positive
    findall(Dc, (criterion(diabetes, Dc), positive(Dc, Answers)), DiabetesPosList),
    ( DiabetesPosList \= [] -> DiabetesBool = true ; DiabetesBool = false ),
    % prediabetes true if its criterion positive and diabetes not true
    ( positive(fasting_100_125, Answers), DiabetesBool = false -> PrediabetesBool = true ; PrediabetesBool = false ),
    % low risk if no positive criteria and no symptoms
    ( PosCriteria = [], PosSymptoms = [] -> LowRiskBool = true ; LowRiskBool = false ).

/* Print a human-readable summary of the outcome */
print_outcome(outcome{
    diabetes:DiabetesBool,
    prediabetes:PrediabetesBool,
    positive_criteria:PosCriteria,
    positive_symptoms:PosSymptoms,
    low_risk:LowRiskBool
}) :-
    ( DiabetesBool = true ->
        format('Diagnosis: Diabetes mellitus.~n', [])
    ; PrediabetesBool = true ->
        format('Diagnosis: Prediabetes (impaired fasting glucose).~n', [])
    ; LowRiskBool = true ->
        format('Assessment: Low risk for diabetes based on available answers.~n', [])
    ; format('Assessment: No diagnostic criteria for diabetes met, but not classified as low risk.~n', [])
    ),
    ( PosCriteria = [] ->
        format('No diagnostic laboratory criteria were reported positive.~n', [])
    ; format('Positive diagnostic criteria: ~w~n', [PosCriteria])
    ),
    ( PosSymptoms = [] ->
        format('No typical symptoms were reported positive.~n', [])
    ; format('Reported symptoms: ~w~n', [PosSymptoms])
    ).

/* Main entrypoint: diagnose/0
   - Asks all available diagnostic criteria and symptom questions.
   - Does not stop after the first positive criterion; collects all answers first.
   - Then evaluates and prints the diagnosis/assessment. */
diagnose :-
    % collect all criteria items
    findall(C, criterion(_, C), AllCriteriaDup),
    % collect all symptom items
    findall(S, symptom(_, S), AllSymptomsDup),
    append(AllCriteriaDup, AllSymptomsDup, AllItemsDup),
    list_to_set(AllItemsDup, AllItems),
    % gather answers for every item
    gather_answers(AllItems, Answers),
    % evaluate
    evaluate_outcome(Answers, Outcome),
    print_outcome(Outcome).

/* Predicate to check specifically for diabetes.
   Asks all diabetes-specific diagnostic criteria, collects answers, then evaluates.
   Does not stop after first positive; collects all diabetes criteria answers before concluding. */
diabetes :-
    criteria(diabetes, DiabetesCriteria),
    gather_answers(DiabetesCriteria, Answers),
    % evaluate diabetes truth: any diabetes criterion positive
    ( findall(C, (member(C, DiabetesCriteria), positive(C, Answers)), Pos), Pos \= [] ->
        format('Result: Diabetes mellitus criteria met: ~w~n', [Pos])
    ; format('Result: No diabetes diagnostic criteria met based on answers to the diabetes-specific questions.~n', [])
    ).

/* Predicate to check specifically for prediabetes.
   Asks the prediabetes criterion(s) and also asks diabetes criteria to ensure distinction,
   collects all answers first, then evaluates. */
prediabetes :-
    criteria(prediabetes, PredCriteria),
    criteria(diabetes, DiabetesCriteria),
    append(PredCriteria, DiabetesCriteria, Combined),
    list_to_set(Combined, Items),
    gather_answers(Items, Answers),
    % check diabetes first
    ( findall(C, (member(C, DiabetesCriteria), positive(C, Answers)), DiabetesPos), DiabetesPos \= [] ->
        format('Result: Diabetes diagnostic criteria were met (so prediabetes is not applicable): ~w~n', [DiabetesPos])
    ; % otherwise check prediabetes
      ( findall(P, (member(P, PredCriteria), positive(P, Answers)), PredPos), PredPos \= [] ->
            format('Result: Prediabetes criteria met: ~w~n', [PredPos])
        ; format('Result: No prediabetes criteria met based on answers to the prediabetes-specific questions.~n', [])
      )
    ).

/* low_risk predicate: asks all diagnostic criteria and symptom questions,
   collects answers, and succeeds (with a printed message) if no criteria nor symptoms are positive. */
low_risk :-
    findall(C, criterion(_, C), AllCriteriaDup),
    findall(S, symptom(_, S), AllSymptomsDup),
    append(AllCriteriaDup, AllSymptomsDup, AllItemsDup),
    list_to_set(AllItemsDup, AllItems),
    gather_answers(AllItems, Answers),
    findall(C, (member(C, AllItems), positive(C, Answers), criterion(_, C)), PosCriteria),
    findall(S, (member(S, AllItems), positive(S, Answers), symptom(_, S)), PosSymptoms),
    ( PosCriteria = [], PosSymptoms = [] ->
        format('Assessment: Low risk for diabetes (no positive criteria or typical symptoms reported).~n', [])
    ; format('Assessment: Not low risk. Positive items: criteria ~w, symptoms ~w~n', [PosCriteria, PosSymptoms])
    ).