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

/* Diagnostic entry point. Returns a dictionary with a verdict and supporting evidence.
   Possible verdicts:
     - diabetes
     - prediabetes
     - no_definitive_laboratory_diagnosis  (when symptoms provide support but labs do not)
     - no_definitive_evidence
*/
diagnose(Result) :-
    ( criterion_random_glucose(Ev)
      -> Result = _{verdict: diabetes, evidence: [Ev]}
    ; criterion_fasting_diabetes(EvF)
      -> Result = _{verdict: diabetes, evidence: [EvF]}
    ; criterion_ogtt_2hr(EvO)
      -> Result = _{verdict: diabetes, evidence: [EvO]}
    ; criterion_hba1c(EvH)
      -> Result = _{verdict: diabetes, evidence: [EvH]}
    ; criterion_prediabetes_fasting(EvP)
      -> Result = _{verdict: prediabetes, evidence: [EvP]}
    ; symptom_support(EvS)
      -> Result = _{verdict: no_definitive_laboratory_diagnosis, symptom_support: EvS}
    ; Result = _{verdict: no_definitive_evidence, evidence: []}
    ).

/* Criterion: random plasma glucose >= 200 mg/dL */
criterion_random_glucose(Evidence) :-
    ask_numeric('What is the random plasma glucose in mg/dL?', Value),
    Value >= 200.0,
    Evidence = _{criterion: random_plasma_glucose, value_mg_dl: Value}.

/* Criterion: fasting plasma glucose after 8-12 hours >= 126 mg/dL */
criterion_fasting_diabetes(Evidence) :-
    ask_numeric('How many hours fasting before the plasma glucose sample?', HoursRaw),
    HoursRaw >= 8.0,
    HoursRaw =< 12.0,
    ask_numeric('What is the fasting plasma glucose in mg/dL?', FastingValue),
    FastingValue >= 126.0,
    Evidence = _{criterion: fasting_plasma_glucose_diabetes, hours_fasted: HoursRaw, value_mg_dl: FastingValue}.

/* Criterion: 2-hour plasma glucose during OGTT >= 200 mg/dL */
criterion_ogtt_2hr(Evidence) :-
    ask_numeric('What is the 2-hour plasma glucose during the oral glucose tolerance test (mg/dL)?', OgttValue),
    OgttValue >= 200.0,
    Evidence = _{criterion: ogtt_2hr_plasma_glucose, value_mg_dl: OgttValue}.

/* Criterion: HbA1c >= 6.5% */
criterion_hba1c(Evidence) :-
    ask_numeric('What is the HbA1c percent (%)?', Hba1cValue),
    Hba1cValue >= 6.5,
    Evidence = _{criterion: hba1c, value_percent: Hba1cValue}.

/* Prediabetes: fasting plasma glucose 100-125 mg/dL after any fasting (text implies fasting context) */
criterion_prediabetes_fasting(Evidence) :-
    ask_numeric('How many hours fasting before the plasma glucose sample?', HoursFRaw),
    % Accept any fasting duration; the diagnostic note for diabetes requires 8-12 hours,
    % but prediabetes range is defined for fasting plasma glucose in mg/dL.
    ask_numeric('What is the fasting plasma glucose in mg/dL?', FastingValP),
    FastingValP >= 100.0,
    FastingValP =< 125.0,
    Evidence = _{criterion: prediabetes_fasting_plasma_glucose, hours_fasted: HoursFRaw, value_mg_dl: FastingValP}.

/* Symptom-based support when laboratory criteria are not decisive.
   Asks only if needed. Returns a dictionary describing symptom presence and support strength.
*/
symptom_support(Evidence) :-
    SymptomsOptions = [excessive_thirst, excessive_urination, fatigue, blurred_vision, unexplained_weight_loss, increased_hunger, slow_healing_wounds, frequent_infections, tingling_numbness],
    ask_multiple_category('Please select the symptoms that currently apply (select all that apply): excessive thirst, excessive urination, fatigue, and blurred vision are core options.', SymptomsOptions, Selected),
    Selected \= [],
    ( member(excessive_thirst, Selected), member(excessive_urination, Selected)
      -> Support = strong
      ; ( member(excessive_thirst, Selected) ; member(excessive_urination, Selected) )
        -> Support = partial
        ; Support = minimal
    ),
    ( member(fatigue, Selected)
      -> ask_range('On a scale of 1 to 10, what is the fatigue severity?', 1, 10, FatigueSeverity)
      ; FatigueSeverity = null
    ),
    ( member(excessive_thirst, Selected)
      -> ask_category('How would you describe the thirst severity?', [none, mild, moderate, severe], ThirstSeverity)
      ; ThirstSeverity = null
    ),
    ask_duration('For how many days have these symptoms been present?', DaysRaw),
    ( DaysRaw < 7.0
      -> DurationClass = recent
      ; DaysRaw =< 30.0
        -> DurationClass = persistent
        ; DurationClass = long_term
    ),
    % Optional medication recording if the user indicates current diabetes medication.
    ( ask_boolean('Is the patient currently taking any diabetes medication?')
      -> ( ask_numeric('How many diabetes medications would you like to record?', MedCountRaw),
           MedCountInt is round(MedCountRaw),
           collect_meds(MedCountInt, MedsList)
         )
      ; MedsList = []
    ),
    Evidence = _{symptoms: Selected, support_strength: Support, duration_days: DaysRaw, duration_class: DurationClass, thirst_severity: ThirstSeverity, fatigue_severity: FatigueSeverity, medications: MedsList}.

/* Collect N medication entries using ask_multi_attribute_entity. */
collect_meds(0, []) :- !.
collect_meds(N, [Med|Rest]) :-
    N > 0,
    Fields = [
      [name, 'What is the medication name?', string],
      [dose_mg, 'What is the dose in mg?', float],
      [times_per_day, 'How many times per day is it taken?', float]
    ],
    ask_multi_attribute_entity('Please enter medication details', medication, Fields, Med),
    N1 is N - 1,
    collect_meds(N1, Rest).