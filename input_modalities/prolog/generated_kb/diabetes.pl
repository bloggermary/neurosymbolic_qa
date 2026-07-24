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


/* ---------- Standalone numeric and diagnostic criterion predicates ---------- */

random_glucose_criterion :-
    ask_numeric('What is your random plasma glucose in mmol/L?', Value),
    ( Value >= 11.1 -> true ; fail ).

fasting_glucose_criterion :-
    ask_range('How many hours did you fast before this blood sample?', 0, 24, Hours),
    ( Hours >= 8.0, Hours =< 12.0 ->
        ask_numeric('What is your fasting plasma glucose in mg/dL?', Glucose),
        ( Glucose >= 126.0 -> true ; fail )
    ; fail ).

ogtt_2h_criterion :-
    ask_numeric('What is your 2-hour plasma glucose during an oral glucose tolerance test (OGTT) in mmol/L?', Value),
    ( Value >= 11.1 -> true ; fail ).

hba1c_criterion :-
    ask_numeric('What is your HbA1c in percent (%)?', Value),
    ( Value >= 6.5 -> true ; fail ).

prediabetes_fasting_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    ( Value >= 100.0, Value =< 125.0 -> true ; fail ).

/* Symptom-based diabetes criterion: at least 3 of the 4 listed symptoms */
symptom_count_criterion :-
    ask_multiple_category('Which of the following symptoms currently apply? Please select all that apply: excessive thirst, excessive urination, fatigue, and blurred vision.', ['excessive_thirst','excessive_urination','fatigue','blurred_vision'], Selected),
    length(Selected, Count),
    ( Count >= 3.0 -> true ; fail ).

/* Strong and partial support predicates */
symptom_strong_support_criterion :-
    ask_multiple_category('Which of the following symptoms currently apply? Please select all that apply: excessive thirst, excessive urination, fatigue, and blurred vision.', ['excessive_thirst','excessive_urination','fatigue','blurred_vision'], Selected),
    member('excessive_thirst', Selected),
    member('excessive_urination', Selected).

symptom_partial_support_criterion :-
    ask_multiple_category('Which of the following symptoms currently apply? Please select all that apply: excessive thirst, excessive urination, fatigue, and blurred vision.', ['excessive_thirst','excessive_urination','fatigue','blurred_vision'], Selected),
    ( member('excessive_thirst', Selected) ; member('excessive_urination', Selected) ),
    \+ ( member('excessive_thirst', Selected), member('excessive_urination', Selected) ).

/* ---------- Helper predicates for collecting detailed supporting clinical picture ---------- */

collect_symptom_data(SymptomPairs, SymptomOrder, DurationCategory, FatigueScore, FatigueCategory, ThirstSeverity, Medications) :-
    ask_multiple_category('Which of the following symptoms currently apply? Please select all that apply: excessive thirst, excessive urination, fatigue, and blurred vision.', ['excessive_thirst','excessive_urination','fatigue','blurred_vision'], Selected),
    ( Selected = [] -> SelectedList = [] ; SelectedList = Selected ),
    % Build explicit symptom presence pairs
    ( member('excessive_thirst', SelectedList) -> ThirstPresentAtom = true ; ThirstPresentAtom = false ),
    ( member('excessive_urination', SelectedList) -> UrinationPresentAtom = true ; UrinationPresentAtom = false ),
    ( member('fatigue', SelectedList) -> FatiguePresentAtom = true ; FatiguePresentAtom = false ),
    ( member('blurred_vision', SelectedList) -> BlurredPresentAtom = true ; BlurredPresentAtom = false ),
    SymptomPairs = ['excessive_thirst'-ThirstPresentAtom, 'excessive_urination'-UrinationPresentAtom, 'fatigue'-FatiguePresentAtom, 'blurred_vision'-BlurredPresentAtom],
    % If more than one symptom present, get order
    length(SelectedList, SelCount),
    ( SelCount > 1.0 ->
        ask_multi_structured_input('Please list the selected symptoms in the order they first appeared, from earliest to most recent.', sequence, SelectedList, SymptomOrder)
    ; SymptomOrder = SelectedList ),
    % Duration in days and category
    ask_duration('For how many days have the symptoms been present?', Days),
    ( Days < 7.0 -> DurationCategory = recent ; ( Days =< 30.0 -> DurationCategory = persistent ; DurationCategory = long_term ) ),
    % Fatigue severity (1-10)
    ask_range('On a scale from 1 to 10, how severe is your fatigue?', 1, 10, FatigueScore),
    ( FatigueScore =< 3.0 -> FatigueCategory = mild ; ( FatigueScore =< 6.0 -> FatigueCategory = moderate ; FatigueCategory = severe ) ),
    % Thirst severity categorical
    ask_category('How would you describe your thirst severity?', [none, mild, moderate, severe], ThirstSeverity),
    % Medications collection
    ( ask_boolean('Are you currently taking any diabetes medication?') -> TakingMed = true ; TakingMed = false ),
    ( TakingMed == true ->
        ask_numeric('How many diabetes medications are you currently taking?', CountFloat),
        ( CountFloat >= 1.0 ->
            round(CountFloat, Count),
            collect_medications_n(Count, Medications)
        ; Medications = [] )
    ; Medications = [] ).

collect_medications_n(0, []) :- !.
collect_medications_n(N, [MedPairs|Rest]) :-
    N > 0,
    number(N),
    format(atom(PromptName), 'What is the name of medication #~w?', [N]),
    ask_string(PromptName, Name),
    format(atom(PromptDose), 'What is the dose in mg for medication #~w?', [N]),
    ask_numeric(PromptDose, Dose),
    format(atom(PromptTimes), 'How many times per day is medication #~w taken?', [N]),
    ask_numeric(PromptTimes, TimesPerDay),
    MedPairs = [name-Name, dose_mg-Dose, times_per_day-TimesPerDay],
    N1 is N - 1,
    collect_medications_n(N1, Rest).

/* ---------- Top-level predicates ---------- */

diabetes :-
    ( random_glucose_criterion -> true
    ; fasting_glucose_criterion -> true
    ; ogtt_2h_criterion -> true
    ; hba1c_criterion -> true
    ; symptom_count_criterion -> true ).

prediabetes :-
    prediabetes_fasting_criterion.

low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* ---------- Main diagnostic workflow ---------- */

diagnose(Result) :-
    % Check numeric thresholds in order, stop at first that applies
    ( random_glucose_criterion ->
        NumericEvidence = 'random_plasma_glucose'
    ; fasting_glucose_criterion ->
        NumericEvidence = 'fasting_plasma_glucose'
    ; ogtt_2h_criterion ->
        NumericEvidence = 'ogtt_2h_plasma_glucose'
    ; hba1c_criterion ->
        NumericEvidence = 'hba1c'
    ; NumericEvidence = none ),
    % If no numeric threshold met, check symptom-count and prediabetes criteria
    ( NumericEvidence == none ->
        ( symptom_count_criterion ->
            Verdict = diabetes,
            DiagnosticBasis = symptom_based
        ; prediabetes_fasting_criterion ->
            Verdict = prediabetes,
            DiagnosticBasis = prediabetes_fasting
        ; Verdict = low_risk,
          DiagnosticBasis = none )
    ; % Numeric threshold met -> diagnose diabetes but still collect supporting picture
      Verdict = diabetes,
      DiagnosticBasis = NumericEvidence ),
    % Collect detailed supporting clinical picture regardless of which threshold was met
    collect_symptom_data(SymptomPairs, SymptomOrder, DurationCategory, FatigueScore, FatigueCategory, ThirstSeverity, Medications),
    % Build a janus-safe top-level dict result
    Result = _{verdict: Verdict,
               diagnostic_basis: DiagnosticBasis,
               numeric_evidence: NumericEvidence,
               symptoms: SymptomPairs,
               symptom_order: SymptomOrder,
               symptom_duration_category: DurationCategory,
               fatigue_score: FatigueScore,
               fatigue_category: FatigueCategory,
               thirst_severity: ThirstSeverity,
               medications: Medications }.