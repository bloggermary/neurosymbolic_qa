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

ask_multiple_category(Question, Categories, Answer) :-
    py_call(prolog_bridge:ask_multiple_category(Question, Categories), Answer).

ask_multi_structured_input(Question, Mode, Groups, Answer) :-
    py_call(prolog_bridge:ask_multi_structured_input(Question, Mode, Groups), Answer).

ask_multi_attribute_entity(Question, Entity, Fields, Answer) :-
    py_call(prolog_bridge:ask_multi_attribute_entity(Question, Entity, Fields), Answer).

/* ---------- Standalone numeric/diagnostic criteria (each self-contained) ---------- */

random_plasma_glucose_positive :-
    ask_numeric('What is your random (non-fasting) plasma glucose in mg/dL?', Value),
    Value >= 200.0.

fasting_plasma_glucose_positive :-
    ask_range('How many hours did you fast before this blood sample?', 0.0, 72.0, Hours),
    Hours >= 8.0, Hours =< 12.0,
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 126.0.

ogtt_2hour_positive :-
    ask_numeric('What is your 2-hour plasma glucose during an oral glucose tolerance test in mg/dL?', Value),
    Value >= 200.0.

hba1c_positive :-
    ask_numeric('What is your hemoglobin A1c percentage (HbA1c)?', Value),
    Value >= 6.5.

prediabetes_fasting_positive :-
    ask_range('How many hours did you fast before this blood sample?', 0.0, 72.0, Hours),
    Hours >= 8.0, Hours =< 12.0,
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0, Value =< 125.0.

/* ---------- Public logical predicates ---------- */

diabetes :-
    random_plasma_glucose_positive
    ;
    fasting_plasma_glucose_positive
    ;
    ogtt_2hour_positive
    ;
    hba1c_positive.

prediabetes :-
    \+ diabetes,
    prediabetes_fasting_positive.

low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* ---------- Helpers for medication collection ---------- */

collect_medications(CountFloat, Meds) :-
    Round is round(CountFloat),
    ( Round =< 0 ->
        Meds = []
    ;
        collect_medications_n(Round, Meds)
    ).

collect_medications_n(0, []) :- !.
collect_medications_n(N, [MedPairs|Rest]) :-
    N > 0,
    atomic_list_concat(['What is the name of medication #', N, '?'], '', Q1Temp),
    % Above Q1Temp will be something like "What is the name of medication #3?" but we want ordinal from 1..N.
    % To provide a clearer prompt, compute index:
    Index is N,
    atomic_list_concat(['What is the name of medication #', Index, '?'], QName),
    ask_string(QName, Name),
    ask_numeric('What is the dose in milligrams for this medication?', Dose),
    ask_numeric('How many times per day is this medication taken?', Times),
    MedPairs = [name-Name, dose-Dose, times_per_day-Times],
    N1 is N - 1,
    collect_medications_n(N1, Rest).

/* ---------- Main diagnosis workflow ---------- */

diagnose(Result) :-
    % Collect symptom booleans (must ask each explicitly)
    ( ask_boolean('Do you experience excessive thirst?') -> ExcessiveThirst = true ; ExcessiveThirst = false ),
    ( ask_boolean('Do you experience excessive urination (frequent urination)?') -> ExcessiveUrination = true ; ExcessiveUrination = false ),
    ( ask_boolean('Do you experience fatigue?') -> FatiguePresent = true ; FatiguePresent = false ),
    ( ask_boolean('Do you experience blurred vision?') -> BlurredVision = true ; BlurredVision = false ),

    % If thirst present, ask severity; otherwise set none
    ( ExcessiveThirst = true ->
        ask_category('How would you describe your thirst severity?', [none, mild, moderate, severe], ThirstSeverity)
    ;
        ThirstSeverity = none
    ),

    % If fatigue present, ask numeric severity on scale 1-10 and classify; otherwise none
    ( FatiguePresent = true ->
        ask_scale('On a scale of 1 to 10, how severe is your fatigue?', FatigueScale),
        ( FatigueScale >= 1.0, FatigueScale =< 3.0 -> FatigueSeverity = mild
        ; FatigueScale >= 4.0, FatigueScale =< 6.0 -> FatigueSeverity = moderate
        ; FatigueScale >= 7.0 -> FatigueSeverity = severe
        ; FatigueSeverity = mild
        )
    ;
        FatigueSeverity = none
    ),

    % Ask symptom duration in days and categorize
    ask_duration('How many days have these symptoms been present?', SymptomDays),
    ( SymptomDays < 7.0 -> DurationCategory = recent
    ; SymptomDays >= 7.0, SymptomDays =< 30.0 -> DurationCategory = persistent
    ; SymptomDays > 30.0 -> DurationCategory = long_term
    ; DurationCategory = recent
    ),

    % Medication categorical status
    ask_category('What is your current medication status?', [insulin, oral_antidiabetics, corticosteroids, none], MedicationStatus),

    % If medication status indicates medications, ask how many and collect each as structured entries
    ( MedicationStatus \= none ->
        ask_numeric('How many diabetes medications do you currently take?', MedCountFloat),
        collect_medications(MedCountFloat, Medications)
    ;
        Medications = []
    ),

    % If more than one symptom present, ask for ordering (as a free-text ordered list)
    SymptomCount0 = 0,
    ( ExcessiveThirst = true -> SymptomCount1 is SymptomCount0 + 1 ; SymptomCount1 is SymptomCount0 ),
    ( ExcessiveUrination = true -> SymptomCount2 is SymptomCount1 + 1 ; SymptomCount2 is SymptomCount1 ),
    ( FatiguePresent = true -> SymptomCount3 is SymptomCount2 + 1 ; SymptomCount3 is SymptomCount2 ),
    ( BlurredVision = true -> SymptomCount is SymptomCount3 + 1 ; SymptomCount is SymptomCount3 ),
    ( SymptomCount >= 2 ->
        ask_string('Please list the symptoms in the order they first appeared, from earliest to most recent, separated by commas', SymptomOrder)
    ;
        SymptomOrder = ""
    ),

    % Now evaluate numeric diagnostic criteria sequentially, stopping when one numeric threshold alone justifies diabetes.
    ( random_plasma_glucose_positive ->
        Verdict = diabetes,
        Evidence = random_plasma_glucose
    ; fasting_plasma_glucose_positive ->
        Verdict = diabetes,
        Evidence = fasting_plasma_glucose
    ; ogtt_2hour_positive ->
        Verdict = diabetes,
        Evidence = ogtt_2hour_glucose
    ; hba1c_positive ->
        Verdict = diabetes,
        Evidence = hba1c
    ; prediabetes_fasting_positive ->
        Verdict = prediabetes,
        Evidence = prediabetes_fasting
    ;
        Verdict = low_risk,
        Evidence = none
    ),

    % Build janus-safe result dict (only atoms, numbers, strings, lists, pairs)
    Result = _{
        verdict: Verdict,
        evidence: Evidence,
        symptoms: [excessive_thirst-ExcessiveThirst, excessive_urination-ExcessiveUrination, fatigue-FatiguePresent, blurred_vision-BlurredVision],
        thirst_severity: ThirstSeverity,
        fatigue_severity: FatigueSeverity,
        symptom_duration_days: SymptomDays,
        duration_category: DurationCategory,
        medication_status: MedicationStatus,
        medications: Medications,
        symptom_order: SymptomOrder
    }.