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

/*
  Single entry point for the diagnostic workflow.
  Returns a dictionary with at least keys:
    verdict: one of [diabetes, prediabetes, symptom_support, no_diagnostic_evidence]
    evidence: a dictionary or list describing the supporting data
*/
diagnose(Result) :-
    ( random_plasma_glucose_diabetes(E1)
      -> Result = _{verdict: diabetes, evidence: E1}
    ; fasting_plasma_glucose_diabetes(E2)
      -> Result = _{verdict: diabetes, evidence: E2}
    ; ogtt_2hr_diabetes(E3)
      -> Result = _{verdict: diabetes, evidence: E3}
    ; hba1c_diabetes(E4)
      -> Result = _{verdict: diabetes, evidence: E4}
    ; prediabetes_criterion(E5)
      -> Result = _{verdict: prediabetes, evidence: E5}
    ; symptom_support(E6)
      -> Result = _{verdict: symptom_support, evidence: E6}
    ; no_diagnostic_evidence(Result)
    ).

/* Definitive diabetes: random plasma glucose >= 200 mg/dL */
random_plasma_glucose_diabetes(Evidence) :-
    ( ask_boolean('Is a random plasma glucose measurement available in mg/dL?')
      -> ( ask_numeric('Enter the random plasma glucose (mg/dL):', Value)
           -> true
           ; fail )
      ; fail ),
    Value >= 200.0,
    Evidence = _{criterion: random_plasma_glucose, units: 'mg/dL', value: Value, threshold_mg_dl: 200.0}.

/* Definitive diabetes: fasting plasma glucose >= 126 mg/dL after 8-12 hours fasting */
fasting_plasma_glucose_diabetes(Evidence) :-
    ( ask_boolean('Is a fasting plasma glucose measurement available (measured after 8-12 hours fasting) in mg/dL?')
      -> ( ask_numeric('Enter the fasting plasma glucose (mg/dL):', Value)
           -> true
           ; fail )
      ; fail ),
    Value >= 126.0,
    Evidence = _{criterion: fasting_plasma_glucose, units: 'mg/dL', value: Value, threshold_mg_dl: 126.0}.

/* Definitive diabetes: 2-hour plasma glucose during OGTT >= 200 mg/dL */
ogtt_2hr_diabetes(Evidence) :-
    ( ask_boolean('Is a 2-hour plasma glucose measurement from an oral glucose tolerance test (OGTT) available in mg/dL?')
      -> ( ask_numeric('Enter the 2-hour OGTT plasma glucose (mg/dL):', Value)
           -> true
           ; fail )
      ; fail ),
    Value >= 200.0,
    Evidence = _{criterion: ogtt_2hr_plasma_glucose, units: 'mg/dL', value: Value, threshold_mg_dl: 200.0}.

/* Definitive diabetes: HbA1c >= 6.5% */
hba1c_diabetes(Evidence) :-
    ( ask_boolean('Is an HbA1c measurement available (percent)?')
      -> ( ask_numeric('Enter the HbA1c value (percent, e.g. 6.5):', Value)
           -> true
           ; fail )
      ; fail ),
    Value >= 6.5,
    Evidence = _{criterion: hba1c, units: '%', value: Value, threshold_percent: 6.5}.

/* Prediabetes: fasting plasma glucose between 100 and 125 mg/dL (inclusive) after 8-12 hours fasting */
prediabetes_criterion(Evidence) :-
    ( ask_boolean('Is a fasting plasma glucose measurement available (measured after 8-12 hours fasting) in mg/dL?')
      -> ( ask_numeric('Enter the fasting plasma glucose (mg/dL):', Value)
           -> true
           ; fail )
      ; fail ),
    Value >= 100.0,
    Value =< 125.0,
    Evidence = _{criterion: prediabetes_fasting_glucose, units: 'mg/dL', value: Value, range_mg_dl: [100.0,125.0]}.

/*
  Symptom-based support:
  - Strong support: both excessive thirst and excessive urination present.
  - Partial support: one of excessive thirst or excessive urination present.
  Also collects severity and duration details where relevant.
*/
symptom_support(Evidence) :-
    ask_multiple_category('Select all current symptoms that apply from the list: excessive thirst, excessive urination, fatigue, blurred vision', [excessive_thirst, excessive_urination, fatigue, blurred_vision], Symptoms),
    Symptoms \= [],
    collect_symptom_details(Symptoms, Details),
    support_level_from_symptoms(Symptoms, Support),
    Details2 = Details.put(_{support_level: Support}),
    Evidence = _{symptoms: Symptoms}.put(Details2).

/* Determine support level based on symptom list */
support_level_from_symptoms(Symptoms, strong) :-
    member(excessive_thirst, Symptoms),
    member(excessive_urination, Symptoms), !.
support_level_from_symptoms(Symptoms, partial) :-
    ( member(excessive_thirst, Symptoms)
    ; member(excessive_urination, Symptoms) ), !.
support_level_from_symptoms(_, none).

/* Collect additional symptom details: ordering, duration classification, fatigue/thirst severity when present */
collect_symptom_details(Symptoms, Details) :-
    ( length(Symptoms, N), N > 1
      -> ask_multi_structured_input('Please list the symptoms in the order they first appeared, from earliest to most recent.', sequence, Symptoms, Ordered)
      ; Ordered = Symptoms ),
    ask_duration('How long have these symptoms been present (in days)?', DurationDays),
    duration_class(DurationDays, DurationClass),
    ( member(fatigue, Symptoms)
      -> ask_range('On a scale from 1 (mild) to 10 (severe), how would you rate the fatigue?', 1, 10, FatigueScore),
         fatigue_class(FatigueScore, FatigueClass)
      ; FatigueScore = _, FatigueClass = _ ),
    ( member(excessive_thirst, Symptoms)
      -> ask_category('How would you describe the severity of thirst?', [none, mild, moderate, severe], ThirstSeverity)
      ; ThirstSeverity = _ ),
    Base = _{ordered_symptoms: Ordered, duration_days: DurationDays, duration_class: DurationClass},
    Details = Base.put(_{fatigue_score: FatigueScore, fatigue_class: FatigueClass, thirst_severity: ThirstSeverity}).

/* Classify symptom duration in days */
duration_class(Days, recent) :-
    Days < 7.0, !.
duration_class(Days, persistent) :-
    Days >= 7.0,
    Days =< 30.0, !.
duration_class(Days, long_term) :-
    Days > 30.0.

/* Classify fatigue severity from 1-10 */
fatigue_class(Score, mild) :-
    Score >= 1.0,
    Score =< 3.0, !.
fatigue_class(Score, moderate) :-
    Score >= 4.0,
    Score =< 6.0, !.
fatigue_class(Score, severe) :-
    Score >= 7.0,
    Score =< 10.0.

/* If no criteria met and no supportive symptoms, return explicit negative classification.
   Optionally record current diabetes medications if the user wishes; this does not affect diagnosis.
*/
no_diagnostic_evidence(Result) :-
    ( ask_boolean('Would you like to record current diabetes medications (if any)?')
      -> ask_multi_attribute_entity('For each diabetes medication, provide name, dose in mg, and times per day.', medication, [[name, 'Medication name', string], [dose_mg, 'Dose in mg', float], [times_per_day, 'Times per day', float]], Medications),
         Result = _{verdict: no_diagnostic_evidence, evidence: _{medications: Medications}}
      ; Result = _{verdict: no_diagnostic_evidence, evidence: _{}} ).