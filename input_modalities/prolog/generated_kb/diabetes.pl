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

ask_multi_structured_input(Question, Mode, Structure, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Structure), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).

% Random plasma glucose criterion for diabetes
criterion_random_glucose(Evidence) :-
    ask_category('Which unit is the random plasma glucose reported in?', ['mmol_l','mg_dl'], Unit),
    ask_numeric('What is the random plasma glucose value (enter the number only)?', Value),
    (
        ( Unit = 'mmol_l', Value >= 11.1 )
        ;
        ( Unit = 'mg_dl', Value >= 200 )
    ),
    Evidence = _{test: random_plasma_glucose, unit: Unit, value: Value, criterion: '>=11.1 mmol/L or >=200 mg/dL'}.

% Fasting plasma glucose criterion for diabetes
criterion_fasting_glucose(Evidence) :-
    ask_duration('How many hours has the patient fasted?', Hours),
    Hours >= 8.0,
    Hours =< 12.0,
    ask_category('Which unit is the fasting plasma glucose reported in?', ['mmol_l','mg_dl'], Unit),
    ask_numeric('What is the fasting plasma glucose value (enter the number only)?', Value),
    (
        ( Unit = 'mmol_l', Value >= 7.0 )
        ;
        ( Unit = 'mg_dl', Value >= 126 )
    ),
    Evidence = _{test: fasting_plasma_glucose, unit: Unit, value: Value, hours_fasted: Hours, criterion: '>=7.0 mmol/L after 8-12 h or >=126 mg/dL after 8-12 h'}.

% 2-hour OGTT criterion for diabetes
criterion_ogtt(Evidence) :-
    ( ask_boolean('Was a 2-hour oral glucose tolerance test (OGTT) performed?')
      -> Performed = true
      ;  Performed = false
    ),
    Performed = true,
    ask_category('Which unit is the 2-hour plasma glucose reported in?', ['mmol_l','mg_dl'], Unit),
    ask_numeric('What is the 2-hour plasma glucose value (enter the number only)?', Value),
    (
        ( Unit = 'mmol_l', Value >= 11.1 )
        ;
        ( Unit = 'mg_dl', Value >= 200 )
    ),
    Evidence = _{test: ogtt_2_hour_glucose, unit: Unit, value: Value, criterion: '>=11.1 mmol/L or >=200 mg/dL'}.

% HbA1c criterion for diabetes
criterion_hba1c(Evidence) :-
    ask_category('Which unit is the HbA1c reported in?', ['percent','mmol_mol'], Unit),
    ask_numeric('What is the HbA1c value (enter the number only)?', Value),
    (
        ( Unit = 'percent', Value >= 6.5 )
        ;
        ( Unit = 'mmol_mol', Value >= 48 )
    ),
    Evidence = _{test: hba1c, unit: Unit, value: Value, criterion: '>=6.5% or >=48 mmol/mol'}.

% Prediabetes criterion based on fasting plasma glucose (100-125 mg/dL)
criterion_prediabetes_fpg(Evidence) :-
    ask_duration('How many hours has the patient fasted?', Hours),
    Hours >= 8.0,
    Hours =< 12.0,
    ask_category('Which unit is the fasting plasma glucose reported in?', ['mg_dl','mmol_l'], Unit),
    Unit = 'mg_dl',
    ask_numeric('What is the fasting plasma glucose value in mg/dL (enter the number only)?', Value),
    Value >= 100.0,
    Value =< 125.0,
    Evidence = _{test: fasting_plasma_glucose_prediabetes, unit: Unit, value: Value, hours_fasted: Hours, criterion: '100-125 mg/dL'}.

% Symptom checklist and support classification
symptoms_support(SupportEvidence) :-
    ask_multiple_category('Which of the following symptoms are currently present? Select all that apply:', ['excessive_thirst','excessive_urination','fatigue','blurred_vision'], Symptoms),
    (
        ( member(excessive_thirst, Symptoms), member(excessive_urination, Symptoms) )
        -> Support = strong
        ; ( member(excessive_thirst, Symptoms) ; member(excessive_urination, Symptoms) )
          -> Support = partial
          ; Support = none
    ),
    (
        member(fatigue, Symptoms)
        -> ask_range('On a scale of 1 to 10, what is the fatigue severity (whole number)?', 1.0, 10.0, FatigueScore)
        ;  FatigueScore = none
    ),
    (
        member(excessive_thirst, Symptoms)
        -> ask_category('How would you describe the thirst severity?', ['none','mild','moderate','severe'], ThirstSeverity)
        ;  ThirstSeverity = none
    ),
    ( Symptoms \= []
      -> ask_duration('For how many days have these symptoms been present?', Days),
         ( Days < 7.0 -> DurationCategory = recent ; Days =< 30.0 -> DurationCategory = persistent ; DurationCategory = long_term )
      ;  Days = none, DurationCategory = none
    ),
    SupportEvidence = _{symptoms: Symptoms, support_level: Support, fatigue_score: FatigueScore, thirst_severity: ThirstSeverity, duration_days: Days, duration_category: DurationCategory}.

% Diabetes medications structured entry (if any)
medication_entries(Meds) :-
    ( ask_boolean('Is the patient currently taking any diabetes medication?')
      -> Taking = true
      ;  Taking = false
    ),
    (
      Taking = true
      -> Fields = [
            [name, 'What is the medication name?', string],
            [dose_mg, 'What is the dose in mg?', float],
            [times_per_day, 'How many times per day is it taken?', float]
         ],
         ask_multi_attribute_entity('Please enter each diabetes medication as a structured entry. You will provide name, dose in mg, and times per day.', medication, Fields, Meds)
      ;  Meds = []
    ).

% Main diagnose workflow
diagnose(Result) :-
    % Check numeric diagnostic criteria in order; stop at first positive
    ( criterion_random_glucose(E1)
      -> Result = _{verdict: diabetes, evidence: [E1]}
      ; criterion_fasting_glucose(E2)
        -> Result = _{verdict: diabetes, evidence: [E2]}
        ; criterion_ogtt(E3)
          -> Result = _{verdict: diabetes, evidence: [E3]}
          ; criterion_hba1c(E4)
            -> Result = _{verdict: diabetes, evidence: [E4]}
            ; % No definitive diabetes numeric criterion met; check prediabetes
              ( criterion_prediabetes_fpg(P)
                -> Result = _{verdict: prediabetes, evidence: [P]}
                ; % No numeric criteria met; evaluate symptoms for support classification
                  symptoms_support(SupEvidence),
                  medication_entries(Meds),
                  (
                      SupEvidence.support_level = strong
                      -> Result = _{verdict: symptoms_strong_support, symptoms: SupEvidence, medications: Meds}
                      ; SupEvidence.support_level = partial
                        -> Result = _{verdict: symptoms_partial_support, symptoms: SupEvidence, medications: Meds}
                        ; Result = _{verdict: no_diagnostic_criteria_met, symptoms: SupEvidence, medications: Meds}
                  )
              )
    ).