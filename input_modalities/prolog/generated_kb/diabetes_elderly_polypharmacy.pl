:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(prolog_bridge:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(prolog_bridge:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(prolog_bridge:ask_string(Question), Value).

ask_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(prolog_bridge:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(prolog_bridge:ask_duration(Question), Value).

ask_scale(Question, Value) :-
    py_call(prolog_bridge:ask_scale(Question), Value).

% Main diagnostic workflow: single clause performs full multimodal collection.
diagnose(diagnosis_summary(Verdict, SymptomsPresent, MedicationPrimary, EGFR, ComorbidityCount, CognitiveScore, FastingHours, YearsKnown, NumericEvidence, HbA1cUnreliable)) :-
    % Ask classic symptoms (always asked; negative answers are down-weighted but collected)
    ( ask_boolean('Excessive thirst?') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Frequent urination (polyuria)?') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Fatigue?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Blurred vision?') -> BlurredVision = true ; BlurredVision = false ),
    SymptomsMap = [thirst-Thirst, polyuria-Polyuria, fatigue-Fatigue, blurred_vision-BlurredVision],
    findall(Name, (member(Name-true, SymptomsMap)), SymptomsPresent),

    % Medication category (primary contributor)
    MedCategories = [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none],
    ask_category('Which medication most likely affects glucose (choose primary)?', MedCategories, MedicationPrimary),

    % Fasting hours before sample (range question)
    ask_range('How many hours fasting before the fasting plasma glucose sample?', 0, 72, FastingHours),

    % Renal function numeric
    ask_numeric('Estimated glomerular filtration rate (eGFR) in mL/min/1.73m2?', EGFR),

    % Comorbidity count
    ask_numeric('How many distinct chronic conditions does the patient have (count)?', ComorbidityCount),

    % Cognitive/functional status scale 1-10
    ask_scale('Cognitive/functional status rated 1 (fully independent) to 10 (fully dependent)?', CognitiveScore),

    % Years with known glucose abnormality (duration; 0 if none)
    ask_duration('How many years has the patient had any known glucose abnormality (0 if none)?', YearsKnown),

    % Conditions affecting HbA1c reliability
    ( ask_boolean('Chronic kidney disease present?') -> CKD = true ; CKD = false ),
    ( ask_boolean('Anemia present?') -> Anemia = true ; Anemia = false ),
    ( (CKD = true ; Anemia = true) -> HbA1cUnreliable = true ; HbA1cUnreliable = false ),

    % Numeric diagnostic thresholds: stop after first numeric threshold that alone justifies diabetes
    % Order: fasting glucose, random glucose, 2-hour OGTT, HbA1c (but HbA1c only if not flagged unreliable for sole diagnosis)
    (
        % Check fasting plasma glucose first
        ask_numeric('Fasting plasma glucose (mg/dL)?', FastingValue),
        ( number(FastingValue), FastingValue >= 126 ->
            NumericEvidence = [fasting(FastingValue)],
            Verdict = diabetes
        ;
            % Not diagnostic by fasting -> check random
            ask_numeric('Random plasma glucose (mg/dL)?', RandomValue),
            ( number(RandomValue), RandomValue >= 200 ->
                NumericEvidence = [random(RandomValue)],
                Verdict = diabetes
            ;
                % Not diagnostic by random -> check 2-hour OGTT
                ask_numeric('2-hour oral glucose tolerance test (OGTT) plasma glucose (mg/dL)?', OgttValue),
                ( number(OgttValue), OgttValue >= 200 ->
                    NumericEvidence = [ogtt2h(OgttValue)],
                    Verdict = diabetes
                ;
                    % Not diagnostic by OGTT -> check HbA1c but heed unreliability
                    ask_numeric('Hemoglobin A1c (%)?', Hba1cValue),
                    ( number(Hba1cValue), Hba1cValue >= 6.5, HbA1cUnreliable = false ->
                        NumericEvidence = [hba1c(Hba1cValue,reliable)],
                        Verdict = diabetes
                    ;
                        ( number(Hba1cValue), Hba1cValue >= 6.5, HbA1cUnreliable = true ->
                            NumericEvidence = [hba1c(Hba1cValue,unreliable)],
                            Verdict = possible_diabetes_unconfirmed
                        ;
                            % No single numeric diabetes threshold met; check prediabetes ranges
                            determine_prediabetes(FastingValue, RandomValue, OgttValue, Hba1cValue, PredFlag, PredEvidence),
                            ( PredFlag = true ->
                                NumericEvidence = PredEvidence,
                                Verdict = prediabetes
                            ;
                                NumericEvidence = [],
                                Verdict = low_risk
                            )
                        )
                    )
                )
            )
        )
    ).

% Determine prediabetes using common thresholds (uses already-asked numeric values if available)
determine_prediabetes(FastingValue, _RandomValue, OgttValue, Hba1cValue, true, Evidence) :-
    ( number(FastingValue), FastingValue >= 100, FastingValue =< 125 ->
        Evidence = [prediabetes_fasting(FastingValue)]
    ;
      number(OgttValue), OgttValue >= 140, OgttValue =< 199 ->
        Evidence = [prediabetes_ogtt2h(OgttValue)]
    ;
      number(Hba1cValue), Hba1cValue >= 5.7, Hba1cValue =< 6.4 ->
        Evidence = [prediabetes_hba1c(Hba1cValue)]
    ).

determine_prediabetes(_, _, _, _, false, []).

% Public predicates that trigger the interactive workflow and succeed according to the result
diabetes :-
    diagnose(diagnosis_summary(Verdict, _, _, _, _, _, _, _, _, _)),
    Verdict = diabetes.

prediabetes :-
    diagnose(diagnosis_summary(Verdict, _, _, _, _, _, _, _, _, _)),
    Verdict = prediabetes.

low_risk :-
    diagnose(diagnosis_summary(Verdict, _, _, _, _, _, _, _, _, _)),
    Verdict = low_risk.