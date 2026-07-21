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

/* Clinical picture gathering */
gather_clinical_picture(Symptoms, Medication, FastingHours, SymptomDurationDays, SymptomDurationCategory, SymptomSupport, FatigueCategory, ThirstSeverity, FatigueScale) :-
    ( ask_boolean('Do you have excessive thirst?') -> ThirstPresent = true ; ThirstPresent = false ),
    ( ask_boolean('Do you have excessive urination (frequent urination)?') -> UrinationPresent = true ; UrinationPresent = false ),
    ( ask_boolean('Are you experiencing fatigue?') -> FatiguePresent = true ; FatiguePresent = false ),
    ( ask_boolean('Do you have blurred vision?') -> BlurredVisionPresent = true ; BlurredVisionPresent = false ),
    Symptoms = symptoms{thirst:ThirstPresent, urination:UrinationPresent, fatigue:FatiguePresent, blurred_vision:BlurredVisionPresent},
    ask_category('Current medication status (choose one)', [insulin, oral_antidiabetics, corticosteroids, none], Medication),
    ask_range('How many hours were you fasting before the fasting plasma glucose sample? (enter hours)', 0, 168, FastingHours),
    ask_duration('For how many days have the symptoms been present? (enter whole days)', SymptomDurationDays),
    classify_duration(SymptomDurationDays, SymptomDurationCategory),
    classify_symptom_support(ThirstPresent, UrinationPresent, SymptomSupport),
    ask_scale('On a scale 1-10, how severe is your fatigue (whole number)?', FatigueScale),
    classify_fatigue(FatigueScale, FatigueCategory),
    ask_category('How would you describe thirst severity?', [none, mild, moderate, severe], ThirstSeverity).

classify_duration(Days, recent) :-
    Days < 7.
classify_duration(Days, persistent) :-
    Days >= 7,
    Days =< 30.
classify_duration(Days, long_term) :-
    Days > 30.

classify_symptom_support(true, true, strong) :- !.
classify_symptom_support(true, false, partial) :- !.
classify_symptom_support(false, true, partial) :- !.
classify_symptom_support(false, false, none).

classify_fatigue(Scale, mild) :-
    Scale >= 1,
    Scale =< 3.
classify_fatigue(Scale, moderate) :-
    Scale >= 4,
    Scale =< 6.
classify_fatigue(Scale, severe) :-
    Scale >= 7,
    Scale =< 10.

/* Numeric diagnostic criteria (each asks only the numeric value it needs) */
diabetes_by_random(Value) :-
    ask_numeric('Random plasma glucose (mg/dL)?', Value),
    Value >= 200.

diabetes_by_fasting(Value, FastingHours) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value),
    FastingHours >= 8,
    FastingHours =< 12,
    Value >= 126.

diabetes_by_ogtt(Value) :-
    ask_numeric('2-hour plasma glucose during OGTT (mg/dL)?', Value),
    Value >= 200.

diabetes_by_hba1c(Value) :-
    ask_numeric('HbA1c (%)?', Value),
    Value >= 6.5.

prediabetes_by_fasting(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value),
    Value >= 100,
    Value =< 125.

/* Main diagnostic workflow:
   - Always gather the clinical picture first (symptoms, medication, durations, fasting hours, scales).
   - Then evaluate numeric criteria in sequence and stop at the first numeric criterion that proves diabetes.
   - Still collect all clinical picture data regardless of numeric short-circuiting.
*/
diagnose(diagnosis_summary(Verdict, Symptoms, Medication, FastingHours, SymptomDurationCategory, SymptomSupport, FatigueCategory, ThirstSeverity, NumericFinding)) :-
    gather_clinical_picture(Symptoms, Medication, FastingHours, _SymptomDurationDays, SymptomDurationCategory, SymptomSupport, FatigueCategory, ThirstSeverity, _FatigueScale),
    (
        ( diabetes_by_random(RandVal) ->
            Verdict = diabetes,
            NumericFinding = random_glucose_mgdl(RandVal)
        ) ;
        ( diabetes_by_fasting(FastVal, FastingHours) ->
            Verdict = diabetes,
            NumericFinding = fasting_glucose_mgdl(FastVal)
        ) ;
        ( diabetes_by_ogtt(OGTTVal) ->
            Verdict = diabetes,
            NumericFinding = ogtt_2h_glucose_mgdl(OGTTVal)
        ) ;
        ( diabetes_by_hba1c(HbA1cVal) ->
            Verdict = diabetes,
            NumericFinding = hba1c_percent(HbA1cVal)
        ) ;
        ( prediabetes_by_fasting(PrediabVal) ->
            Verdict = prediabetes,
            NumericFinding = prediabetes_fasting_glucose_mgdl(PrediabVal)
        ) ;
        ( Verdict = low_risk,
          NumericFinding = none
        )
    ).

/* Convenience entry points that trigger the interactive diagnose workflow */
diabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(diabetes, _, _, _, _, _, _, _, _).

prediabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(prediabetes, _, _, _, _, _, _, _, _).

low_risk :-
    diagnose(Summary),
    Summary = diagnosis_summary(low_risk, _, _, _, _, _, _, _, _).