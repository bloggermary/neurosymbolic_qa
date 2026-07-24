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

ask_multiple_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_multiple_category(Question, Categories), Answer).

ask_multi_structured_input(Question, Mode, Groups, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Groups), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).

/* Standalone diagnostic criterion predicates.
   Each asks its own required questions and succeeds if that single
   measurement criterion for diabetes is met. */

fasting_glucose_criteria :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 126.0 ).

random_glucose_criteria :-
    ask_numeric('What is the random (non-fasting) plasma glucose in mg/dL?', Random),
    ( Random >= 200.0 ).

ogtt_2hr_criteria :-
    ask_numeric('What is the 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', OGTT2),
    ( OGTT2 >= 200.0 ).

hba1c_criteria :-
    ask_numeric('What is the hemoglobin A1c (%)?', HbA1c),
    ( ask_boolean('Do you have chronic kidney disease?') -> CKD = true ; CKD = false ),
    ( ask_boolean('Do you have anemia?') -> Anemia = true ; Anemia = false ),
    ( HbA1c >= 6.5 ->
        ( (CKD = false, Anemia = false) -> true
        ; /* HbA1c is high but unreliable because of CKD or anemia.
             In that case we require either no major confounding meds and at least one classic symptom. */
          ask_multiple_category('Which of the following medications currently apply? Select all that apply.', [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none], Meds),
          ( member(none, Meds) -> NoMedConfound = true ; NoMedConfound = false ),
          NoMedConfound = true,
          ask_multiple_category('Do you have any of these classic symptoms? Select all that apply.', [excessive_thirst, frequent_urination, fatigue, blurred_vision], Symptoms),
          Symptoms \= []
        )
    ; fail ).

/* Prediabetes predicate using standard ADA ranges (used only if diabetes criteria not met).
   Each numeric check is done in sequence and stops when one threshold is met. */

prediabetes :-
    /* fasting 100-125 mg/dL */
    ask_numeric('What is the fasting plasma glucose in mg/dL?', FastingP),
    ( FastingP >= 100.0, FastingP =< 125.0 ) -> true ;
    /* HbA1c 5.7-6.4% */
    ask_numeric('What is the hemoglobin A1c (%)?', HbA1cP),
    ( HbA1cP >= 5.7, HbA1cP =< 6.4 ) -> true ;
    /* 2-hour OGTT 140-199 mg/dL */
    ask_numeric('What is the 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', OGTT2P),
    ( OGTT2P >= 140.0, OGTT2P =< 199.0 ).

/* diabetes/0 succeeds if any diagnostic criterion for diabetes is met.
   It is callable independently and will perform the same measurements. */

diabetes :-
    ( fasting_glucose_criteria -> true
    ; random_glucose_criteria -> true
    ; ogtt_2hr_criteria -> true
    ; hba1c_criteria -> true ).

/* Helper to convert a dict of grouped medications into a list of Group-List pairs.
   This avoids returning nested dicts in the top-level result. */

med_groups_pairs_from_dict(Dict, Pairs) :-
    findall(Group-List, get_dict(Group, Dict, List), Pairs).

/* Main workflow: diagnose/1 performs an adaptive question sequence and returns
   a janus-safe top-level dict describing the verdict and minimal supporting data.
   It asks only the information necessary to reach a confident conclusion and
   asks additional contextual questions (medication confounders, grouping, comorbidity,
   renal function, cognitive/functional status, history) when they affect interpretation. */

diagnose(Result) :-
    /* First, check clear diabetes diagnostic criteria in order. Stop as soon as one is met. */
    ( ask_numeric('What is the fasting plasma glucose in mg/dL?', F1), (F1 >= 126.0) ->
        Evidence = fasting_glucose,
        Verdict = diabetes,
        EvidenceValue = F1,
        CriterionMet = true
    ; ask_numeric('What is the random (non-fasting) plasma glucose in mg/dL?', R1), (R1 >= 200.0) ->
        Evidence = random_glucose,
        Verdict = diabetes,
        EvidenceValue = R1,
        CriterionMet = true
    ; ask_numeric('What is the 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL?', O1), (O1 >= 200.0) ->
        Evidence = ogtt_2hr,
        Verdict = diabetes,
        EvidenceValue = O1,
        CriterionMet = true
    ; /* HbA1c handled with caution for CKD/anemia */
      ask_numeric('What is the hemoglobin A1c (%)?', H1),
      ( (H1 >= 6.5) ->
          ( ( ask_boolean('Do you have chronic kidney disease?') -> CKD2 = true ; CKD2 = false ),
            ( ask_boolean('Do you have anemia?') -> Anemia2 = true ; Anemia2 = false )
          ),
          ( (CKD2 = false, Anemia2 = false) ->
                Evidence = hba1c,
                Verdict = diabetes,
                EvidenceValue = H1,
                CriterionMet = true
          ; /* HbA1c high but potentially unreliable: seek medication confounders and symptoms before concluding */
            ask_multiple_category('Which of the following medications currently apply? Select all that apply.', [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none], MedsConf),
            ( member(none, MedsConf) ->
                ask_multiple_category('Do you have any of these classic symptoms? Select all that apply.', [excessive_thirst, frequent_urination, fatigue, blurred_vision], Symptoms2),
                ( Symptoms2 \= [] ->
                    Evidence = hba1c_with_symptoms,
                    Verdict = diabetes,
                    EvidenceValue = H1,
                    CriterionMet = true
                ; CriterionMet = false
                )
            ; CriterionMet = false
            )
          )
      ; CriterionMet = false,
        Evidence = none,
        Verdict = unknown,
        EvidenceValue = 0.0
      )
    ),
    /* If any diabetes criterion met, collect contextual modifiers that matter for elderly/polypharmacy patients. */
    ( CriterionMet = true ->
        ( ask_multiple_category('Which of the following medications currently apply? Select all that apply.', [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none], MedsList) -> true ; MedsList = [] ),
        ask_multi_structured_input('Please group your current medications by when they are taken (provide medication names or leave groups empty).', grouping, [morning, afternoon, evening, bedtime], MedGroupsDict),
        med_groups_pairs_from_dict(MedGroupsDict, MedGroupsPairs),
        ask_numeric('What is the estimated glomerular filtration rate (eGFR) in mL/min/1.73m2?', EGFR),
        ask_numeric('How many distinct chronic conditions do you have?', ComorbidityCount),
        ask_range('Please rate cognitive/functional status on a scale from 1 (fully independent) to 10 (fully dependent).', 1, 10, CognitiveFunctional),
        ( ask_boolean('Have you previously been told you have any glucose abnormality (pre-diabetes or diabetes)?') ->
            ( ask_numeric('If yes, how many years have you had a known glucose abnormality?', YearsKnown) -> Years = YearsKnown ; Years = 0.0 )
        ; Years = 0.0 ),
        Result = _{verdict: Verdict, evidence: Evidence, evidence_value: EvidenceValue, medications: MedsList, medication_groups: MedGroupsPairs, egfr: EGFR, comorbidity_count: ComorbidityCount, cognitive_functional_rating: CognitiveFunctional, years_known_glucose_abnormality: Years}
    ; /* No clear diabetes criterion met: check for prediabetes using minimal questions, then collect limited additional data if still inconclusive. */
      ( prediabetes ->
            Result = _{verdict: prediabetes, evidence: prediabetes, evidence_value: none}
      ; /* Neither diabetes nor prediabetes — gather systolic BP and unintentional weight loss only because glucose evidence is inconclusive. */
        ask_numeric('What is the systolic blood pressure in mmHg?', SystolicBP),
        ask_numeric('How much unintentional weight loss have you had over the past 6 months in kg?', WeightLoss6mo),
        Result = _{verdict: low_risk, evidence: none, systolic_bp: SystolicBP, weight_loss_6mo_kg: WeightLoss6mo}
      )
    ).