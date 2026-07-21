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

% Main diagnostic workflow. Gathers multimodal clinical picture and applies numeric thresholds.
diagnose(diagnosis_summary(Verdict, Symptoms, Medication, FastingHours, NumericEvidence, DurationCategory, FatigueCategory, ThirstSeverity)) :-
    % Collect boolean symptoms explicitly mentioned in the text
    ( ask_boolean('Is there excessive thirst?') -> ThirstPresent = true ; ThirstPresent = false ),
    ( ask_boolean('Is there excessive urination (frequent urination)?') -> UrinationPresent = true ; UrinationPresent = false ),
    ( ask_boolean('Is there fatigue?') -> FatiguePresent = true ; FatiguePresent = false ),
    ( ask_boolean('Is there blurred vision?') -> BlurredPresent = true ; BlurredPresent = false ),

    % Fatigue severity on a 1-10 scale
    ( ask_scale('Rate fatigue severity on a scale 1-10 (whole number)') -> FatigueScoreRaw = true ; FatigueScoreRaw = false ),
    ( FatigueScoreRaw = true -> ask_scale('Enter fatigue severity (1-10)', FatigueScore) ; FatigueScore = 0 ),

    % Classify fatigue severity into categories per text
    fatigue_category_from_score(FatigueScore, FatigueCategory),

    % Thirst severity categorical: none, mild, moderate, severe
    ask_category('Thirst severity (none, mild, moderate, severe)', [none,mild,moderate,severe], ThirstSeverity),

    % Symptom duration (days) to classify recent/persistent/long-term
    ( ask_duration('Duration of symptoms in days?') -> SymptomDays = true ; SymptomDays = false ),
    ( SymptomDays = true -> ask_duration('Enter number of days symptoms have been present', Days) ; Days = 0 ),
    duration_category_from_days(Days, DurationCategory),

    % Medication / history categorical question
    ask_category('Current medication status (insulin, oral_antidiabetics, corticosteroids, none, other)', [insulin,oral_antidiabetics,corticosteroids,none,other], Medication),

    % Hours of fasting before a fasting glucose sample (asked as a bounded range)
    ask_range('Hours fasting before the glucose sample (0-72)', 0, 72, FastingHours),

    % Determine symptom support strength
    symptom_support(ThirstPresent, UrinationPresent, SupportLevel),

    Symptoms = symptoms(ThirstPresent, UrinationPresent, FatiguePresent, BlurredPresent, SupportLevel),

    % Numeric diagnostic thresholds: stop asking further numeric criteria as soon as one threshold is met.
    diabetes_numeric_evidence(FastingHours, NumericEvidenceTemp),

    ( NumericEvidenceTemp = evidence(Type, Value) ->
        Verdict = diabetes,
        NumericEvidence = NumericEvidenceTemp
    ;
        % No diabetes-level numeric criterion met. Check prediabetes fasting range (100-125 mg/dL).
        % Only check fasting glucose here (may prompt). Use fasting hours as context but still allow check.
        ask_numeric('Fasting plasma glucose (mg/dL) for prediabetes check', FastingForPred),
        ( FastingForPred >= 100, FastingForPred =< 125 ->
            Verdict = prediabetes,
            NumericEvidence = evidence(prediabetes_fasting, FastingForPred)
        ;
            Verdict = low_risk,
            NumericEvidence = none
        )
    ).

% Sequential numeric checks for diabetes criteria. Each ask_numeric is only called when needed.
% Returns evidence(Type, Value) when a diabetes threshold is met, or none.
diabetes_numeric_evidence(FastingHours, Evidence) :-
    % 1) Random plasma glucose ≥ 200 mg/dL
    ( ask_numeric('Random plasma glucose (mg/dL)', RandomG),
      RandomG >= 200 ->
        Evidence = evidence(random_plasma_glucose_mgdl, RandomG)
    ;
      % 2) Fasting plasma glucose ≥ 126 mg/dL after 8–12 hours fasting
      ( FastingHours >= 8, FastingHours =< 12 ->
            ( ask_numeric('Fasting plasma glucose (mg/dL)', FastingG),
              FastingG >= 126 ->
                Evidence = evidence(fasting_plasma_glucose_mgdl, FastingG)
            ;
                % fallback to next check if fasting glucose not diagnostic
                check_ogtt_and_hba1c(Evidence)
            )
        ;
            % If fasting hours not in 8-12, skip the fasting criterion and move on
            check_ogtt_and_hba1c(Evidence)
      )
    ).

check_ogtt_and_hba1c(Evidence) :-
    % 3) 2-hour OGTT ≥ 200 mg/dL
    ( ask_numeric('2-hour plasma glucose during OGTT (mg/dL)', OGTT2h),
      OGTT2h >= 200 ->
        Evidence = evidence(ogtt_2h_plasma_glucose_mgdl, OGTT2h)
    ;
      % 4) HbA1c ≥ 6.5%
      ( ask_numeric('HbA1c (%)', HbA1c),
        HbA1c >= 6.5 ->
          Evidence = evidence(hba1c_percent, HbA1c)
      ;
        Evidence = none
      )
    ).

% Symptom pattern support determination
symptom_support(true, true, strong) :- !.
symptom_support(true, false, partial) :- !.
symptom_support(false, true, partial) :- !.
symptom_support(_, _, none).

% Fatigue category mapping from numeric score
fatigue_category_from_score(Score, none) :-
    Score =< 0, !.
fatigue_category_from_score(Score, mild) :-
    Score >= 1, Score =< 3, !.
fatigue_category_from_score(Score, moderate) :-
    Score >= 4, Score =< 6, !.
fatigue_category_from_score(Score, severe) :-
    Score >= 7, Score =< 10, !.
fatigue_category_from_score(_, unknown).

% Duration category mapping
duration_category_from_days(Days, recent) :-
    Days > 0, Days < 7, !.
duration_category_from_days(Days, persistent) :-
    Days >= 7, Days =< 30, !.
duration_category_from_days(Days, long_term) :-
    Days > 30, !.
duration_category_from_days(_, unknown).

% Public predicates to query final logical labels. They run the diagnostic workflow and succeed only if matching.
diabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(diabetes, _, _, _, _, _, _, _).

prediabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(prediabetes, _, _, _, _, _, _, _).

low_risk :-
    diagnose(Summary),
    Summary = diagnosis_summary(low_risk, _, _, _, _, _, _, _).