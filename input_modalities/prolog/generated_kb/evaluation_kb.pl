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

% Criterion: random plasma glucose >= 11.1 mmol/L (200 mg/dL)
random_plasma_glucose_diabetes(Evidence) :-
    ask_numeric('What is the random plasma glucose in mmol/L?', GlucoseMmol),
    GlucoseMmol >= 11.1,
    Evidence = _{criterion: random_plasma_glucose, value_mmol_per_l: GlucoseMmol}.

% Criterion: fasting plasma glucose >= 7.0 mmol/L (126 mg/dL) after 8-12 hours fasting
fasting_plasma_glucose_diabetes(Evidence) :-
    ( ask_boolean('Was the plasma sample obtained after 8 to 12 hours of fasting?')
      -> Fasting_ok = true
      ;  Fasting_ok = false
    ),
    Fasting_ok == true,
    ask_category('Which units will you provide for the fasting plasma glucose?', ['mmol_per_l','mg_per_dl'], Unit),
    ( Unit = mmol_per_l ->
        ask_numeric('What is the fasting plasma glucose in mmol/L?', ValueMmol),
        ValueMmol >= 7.0,
        Evidence = _{criterion: fasting_plasma_glucose, value_mmol_per_l: ValueMmol}
    ; Unit = mg_per_dl ->
        ask_numeric('What is the fasting plasma glucose in mg/dL?', ValueMg),
        ValueMg >= 126,
        Evidence = _{criterion: fasting_plasma_glucose, value_mg_per_dl: ValueMg}
    ).

% Criterion: 2-hour plasma glucose during OGTT >= 11.1 mmol/L (200 mg/dL)
ogtt_2h_diabetes(Evidence) :-
    ( ask_boolean('Was a 2-hour oral glucose tolerance test (OGTT) performed?')
      -> Ogtt_done = true
      ;  Ogtt_done = false
    ),
    Ogtt_done == true,
    ask_numeric('What is the 2-hour plasma glucose during the OGTT in mmol/L?', ValueMmol),
    ValueMmol >= 11.1,
    Evidence = _{criterion: ogtt_2h_plasma_glucose, value_mmol_per_l: ValueMmol}.

% Criterion: HbA1c >= 6.5% (48 mmol/mol)
hba1c_diabetes(Evidence) :-
    ask_numeric('What is the HbA1c percent value (%)?', HbA1cPercent),
    HbA1cPercent >= 6.5,
    Evidence = _{criterion: hba1c, value_percent: HbA1cPercent}.

% Prediabetes: fasting plasma glucose between 100 and 125 mg/dL (requires fasting)
prediabetes_fasting(Evidence) :-
    ( ask_boolean('Was the plasma sample obtained after fasting? (Yes if fasting)')
      -> Fast_ok = true
      ;  Fast_ok = false
    ),
    Fast_ok == true,
    ask_category('Which units will you provide for the fasting plasma glucose?', ['mmol_per_l','mg_per_dl'], Unit),
    Unit = mg_per_dl,
    ask_numeric('What is the fasting plasma glucose in mg/dL?', ValueMg),
    ValueMg >= 100,
    ValueMg =< 125,
    Evidence = _{classification: prediabetes, criterion: fasting_plasma_glucose, value_mg_per_dl: ValueMg}.

% Symptom support assessment (supportive but not diagnostic)
symptom_support(Evidence) :-
    ask_multiple_category(
        'Please select all current symptoms from this list: excessive thirst, excessive urination, fatigue, blurred vision.',
        ['excessive_thirst','excessive_urination','fatigue','blurred_vision'],
        Symptoms),
    Symptoms \= [],
    ( member(fatigue, Symptoms) ->
        ask_range('On a scale from 1 to 10, how severe is the fatigue (whole number)?', 1, 10, FatigueScore),
        ( FatigueScore >= 7 -> FatigueSeverity = severe
        ; FatigueScore >= 4 -> FatigueSeverity = moderate
        ; FatigueScore >= 1 -> FatigueSeverity = mild
        ; FatigueSeverity = none
        )
    ; FatigueSeverity = not_reported,
      FatigueScore = false
    ),
    ask_duration('For how many days have the symptoms been present?', DurationDays),
    ( DurationDays < 7 -> DurationCategory = recent
    ; DurationDays =< 30 -> DurationCategory = persistent
    ; DurationCategory = long_term
    ),
    ( member(excessive_thirst, Symptoms), member(excessive_urination, Symptoms) -> SupportLevel = strong
    ; SupportLevel = partial
    ),
    length(Symptoms, SymptomCount),
    Evidence = _{
        evidence_type: symptom_assessment,
        symptoms: Symptoms,
        symptom_count: SymptomCount,
        fatigue_reported: (FatigueScore =\= false),
        fatigue_severity: FatigueSeverity,
        duration_days: DurationDays,
        duration_category: DurationCategory,
        support_level: SupportLevel
    }.

% Main entry: diagnose/1 returns a dictionary with verdict and evidence
diagnose(Result) :-
    ( random_plasma_glucose_diabetes(E1)
      -> Result = _{verdict: diabetes, evidence: E1}
    ; fasting_plasma_glucose_diabetes(E2)
      -> Result = _{verdict: diabetes, evidence: E2}
    ; ogtt_2h_diabetes(E3)
      -> Result = _{verdict: diabetes, evidence: E3}
    ; hba1c_diabetes(E4)
      -> Result = _{verdict: diabetes, evidence: E4}
    ; prediabetes_fasting(E5)
      -> Result = _{verdict: prediabetes, evidence: E5}
    ; symptom_support(E6)
      -> Result = _{verdict: symptom_supporting_diabetes, evidence: E6}
    ; Result = _{verdict: no_diabetes, evidence: _{}}
    ).