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

criterion_random_glucose(Evidence) :-
    ask_numeric('What is the random plasma glucose in mg/dL?', Value),
    Value >= 200.0,
    Evidence = _{test: random_plasma_glucose, units: 'mg/dL', value: Value}.

criterion_fasting_glucose(Evidence) :-
    ( ask_boolean('Was the plasma drawn after 8 to 12 hours of fasting?')
      -> FastingProper = true
      ;  FastingProper = false
    ),
    FastingProper = true,
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    Value >= 126.0,
    Evidence = _{test: fasting_plasma_glucose, units: 'mg/dL', value: Value, fasting_hours_confirmed: true}.

criterion_ogtt_2h(Evidence) :-
    ask_numeric('What is the 2-hour plasma glucose during an oral glucose tolerance test (OGTT) in mg/dL?', Value),
    Value >= 200.0,
    Evidence = _{test: ogtt_2h_plasma_glucose, units: 'mg/dL', value: Value}.

criterion_hba1c(Evidence) :-
    ask_numeric('What is the HbA1c percentage (for example enter 6.5 for 6.5%)?', Value),
    Value >= 6.5,
    Evidence = _{test: hba1c, units: '%', value: Value}.

prediabetes_criterion(Evidence) :-
    ( ask_boolean('Was the plasma drawn after 8 to 12 hours of fasting?')
      -> FastingProper = true
      ;  FastingProper = false
    ),
    FastingProper = true,
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0,
    Value =< 125.0,
    Evidence = _{test: fasting_glucose_prediabetes_range, units: 'mg/dL', value: Value}.

symptom_support(Support) :-
    ask_multiple_category('Please select any of the following symptoms that currently apply: excessive thirst, excessive urination, fatigue, blurred vision.', [excessive_thirst, excessive_urination, fatigue, blurred_vision], Symptoms),
    ( member(excessive_thirst, Symptoms), member(excessive_urination, Symptoms)
      -> SupportLevel = strong
      ; ( member(excessive_thirst, Symptoms) ; member(excessive_urination, Symptoms) )
        -> SupportLevel = partial
        ; SupportLevel = none
    ),
    ( member(fatigue, Symptoms)
      -> ask_range('On a scale from 1 to 10, how severe is the fatigue?', 1, 10, FatigueScore),
         ( FatigueScore >= 1.0, FatigueScore =< 3.0 -> FatigueSeverity = mild
         ; FatigueScore >= 4.0, FatigueScore =< 6.0 -> FatigueSeverity = moderate
         ; FatigueScore >= 7.0, FatigueScore =< 10.0 -> FatigueSeverity = severe
         ; FatigueSeverity = unknown
         )
      ; FatigueSeverity = not_present
    ),
    ( member(excessive_thirst, Symptoms)
      -> ask_category('How would you describe the thirst severity?', [none, mild, moderate, severe], ThirstSeverity)
      ; ThirstSeverity = not_present
    ),
    ask_duration('For how many days have these symptoms been present?', DurationDays),
    ( Symptoms = [_,_|_]
      -> ask_multi_structured_input('Please list the symptoms in the order they first appeared, from earliest to most recent.', sequence, Symptoms, OrderedSymptoms)
      ;  OrderedSymptoms = Symptoms
    ),
    ask_string('Is there anything else about your symptoms you would like to add?', AdditionalNotes),
    Support = _{support: SupportLevel, symptoms: Symptoms, fatigue_severity: FatigueSeverity, thirst_severity: ThirstSeverity, duration_days: DurationDays, symptom_order: OrderedSymptoms, additional_notes: AdditionalNotes}.

record_medications(Medications) :-
    ( ask_boolean('Are you currently taking any diabetes medication?')
      -> ask_multi_attribute_entity('For each diabetes medication, enter name, dose in mg, and times per day.', medication, [[name,'Medication name',string],[dose_mg,'Dose in mg',float],[times_per_day,'Times per day',float]], Medications)
      ;  Medications = []
    ).

diagnose(Result) :-
    ( criterion_random_glucose(E) ->
        Result = _{verdict: diabetes, evidence: E}
    ; criterion_fasting_glucose(E2) ->
        Result = _{verdict: diabetes, evidence: E2}
    ; criterion_ogtt_2h(E3) ->
        Result = _{verdict: diabetes, evidence: E3}
    ; criterion_hba1c(E4) ->
        Result = _{verdict: diabetes, evidence: E4}
    ; prediabetes_criterion(P) ->
        Result = _{verdict: prediabetes, evidence: P}
    ; symptom_support(Support),
      record_medications(Meds),
      ( Support.support = strong ->
          Result = _{verdict: no_definitive_diabetes, support: strong, details: Support, medications: Meds}
      ; Support.support = partial ->
          Result = _{verdict: no_definitive_diabetes, support: partial, details: Support, medications: Meds}
      ; Result = _{verdict: no_diabetes_evidence, details: Support, medications: Meds}
      )
    ).