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

% Numeric measurement accessors (interactive)
random_plasma_glucose_mgdl(Value) :-
    ask_numeric('Random plasma glucose (mg/dL)?', Value).

fasting_plasma_glucose_mgdl(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value).

ogtt_2h_plasma_glucose_mgdl(Value) :-
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)?', Value).

hba1c_percent(Value) :-
    ask_numeric('HbA1c (%)?', Value).

% Numeric diagnostic checks (single-step thresholds)
diabetes_positive_by_random(Value) :-
    random_plasma_glucose_mgdl(Value),
    Value >= 200.

diabetes_positive_by_fasting(Value) :-
    fasting_plasma_glucose_mgdl(Value),
    Value >= 126.

diabetes_positive_by_ogtt(Value) :-
    ogtt_2h_plasma_glucose_mgdl(Value),
    Value >= 200.

diabetes_positive_by_hba1c(Value) :-
    hba1c_percent(Value),
    Value >= 6.5.

% Prediabetes fasting range (mg/dL 100-125) requires valid fasting hours
prediabetes_fasting(Value) :-
    fasting_plasma_glucose_mgdl(Value),
    Value >= 100,
    Value =< 125.

% Sequential numeric evidence collection that stops after first diagnostic threshold met.
% It also preserves a fasting measurement if it was asked during the sequence.
numeric_evidence(FastingHours, Evidence, FastingMeasured) :-
    % Try random plasma glucose first
    (   random_plasma_glucose_mgdl(RG),
        RG >= 200
    ->  Evidence = random(RG),
        FastingMeasured = unknown
    ;   % If random not diagnostic, attempt fasting test only if fasting hours are appropriate
        (   FastingHours >= 8,
            FastingHours =< 12
        ->  (   fasting_plasma_glucose_mgdl(FG)
            ->  (   FG >= 126
                ->  Evidence = fasting(FG),
                    FastingMeasured = FG
                ;   % fasting measured but not diagnostic; record value and continue
                    FastingMeasured = FG,
                    % continue to OGTT
                    (   ogtt_2h_plasma_glucose_mgdl(OG),
                        OG >= 200
                    ->  Evidence = ogtt2h(OG)
                    ;   (   hba1c_percent(H)
                        ,   H >= 6.5
                        ->  Evidence = hba1c(H)
                        ;   Evidence = none
                        )
                    )
                )
            ;   % failed to obtain fasting measurement (should not normally happen) -> continue
                FastingMeasured = unknown,
                (   ogtt_2h_plasma_glucose_mgdl(OG2),
                    OG2 >= 200
                ->  Evidence = ogtt2h(OG2)
                ;   (   hba1c_percent(H2),
                        H2 >= 6.5
                    ->  Evidence = hba1c(H2)
                    ;   Evidence = none
                    )
                )
            )
        ;   % fasting hours not acceptable -> skip fasting test
            FastingMeasured = unknown,
            (   ogtt_2h_plasma_glucose_mgdl(OG3),
                OG3 >= 200
            ->  Evidence = ogtt2h(OG3)
            ;   (   hba1c_percent(H3),
                    H3 >= 6.5
                ->  Evidence = hba1c(H3)
                ;   Evidence = none
                )
            )
        )
    ).

% Main diagnostic workflow: collects multi-modal clinical picture and numeric evidence.
% Returns a structured summary combining verdict and all supporting information.
diagnose(diagnosis_summary(Verdict, NumericEvidence, Symptoms, Medication, FastingHours, FamilyHistory, HistoryFlags, Lifestyle, NocturiaFreq, RecurrentInfectionsFreq)) :-
    % Collect boolean symptoms
    (   ask_boolean('Excessive thirst?') -> Thirst = true ; Thirst = false ),
    (   ask_boolean('Excessive urination?') -> Polyuria = true ; Polyuria = false ),
    (   ask_boolean('Fatigue?') -> Fatigue = true ; Fatigue = false ),
    (   ask_boolean('Blurred vision?') -> BlurredVision = true ; BlurredVision = false ),

    Symptoms = [excessive_thirst-Thirst, excessive_urination-Polyuria, fatigue-Fatigue, blurred_vision-BlurredVision],

    % Collect history booleans (categorical/boolean history items)
    (   ask_boolean('Obesity?') -> Obesity = true ; Obesity = false ),
    (   ask_boolean('Hypertension?') -> Hypertension = true ; Hypertension = false ),
    (   ask_boolean('Cardiovascular disease?') -> CVD = true ; CVD = false ),
    (   ask_boolean('History of gestational diabetes?') -> Gestational = true ; Gestational = false ),

    HistoryFlags = [obesity-Obesity, hypertension-Hypertension, cardiovascular_disease-CVD, gestational_diabetes-Gestational],

    % Family history (categorical)
    ask_category('Family history of diabetes?', [none, first_degree, second_degree, both], FamilyHistory),

    % Medication status (categorical)
    ask_category('Medication status', [insulin, oral_antidiabetics, corticosteroids, none, other], Medication),

    % Lifestyle (categorical)
    ask_category('Lifestyle (diet/activity)', [healthy, suboptimal, poor], Lifestyle),

    % Frequency modalities for nocturia and recurrent infections
    ask_category('Nocturia frequency', [none, occasional, recurrent, frequent], NocturiaFreq),
    ask_category('Recurrent infections frequency', [none, occasional, recurrent, frequent], RecurrentInfectionsFreq),

    % Temporal/range detail: fasting hours before sample (ask_range as required by the text)
    ask_range('Hours fasting before sample (hours)?', 0, 72, FastingHours),

    % Now perform sequential numeric checks; stop asking further numeric thresholds once one is met
    numeric_evidence(FastingHours, NumericEvidence, FastingMeasured),

    % Determine high-level verdict using numeric evidence and measured fasting when available
    (   NumericEvidence \= none
    ->  Verdict = diabetes
    ;   % No diabetes-level numeric threshold met; check prediabetes fasting range if fasting was measured
        (   FastingMeasured \= unknown,
            number(FastingMeasured),
            FastingMeasured >= 100,
            FastingMeasured =< 125
        ->  Verdict = prediabetes
        ;   Verdict = low_risk
        )
    ).

% Public entry points that run the full dialogue and succeed/fail on the respective classification.
diabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(diabetes, _, _, _, _, _, _, _, _, _).

prediabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(prediabetes, _, _, _, _, _, _, _, _, _).

low_risk :-
    diagnose(Summary),
    Summary = diagnosis_summary(low_risk, _, _, _, _, _, _, _, _, _).