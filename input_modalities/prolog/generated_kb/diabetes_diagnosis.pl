:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
<<<<<<< HEAD
    py_call(main:ask_string(Question), Value). 

ask_category_multiple(Question, Categories, Answers) :-
    py_call(main:ask_category_multiple(Question, Categories), Answers).

ask_multi_attribute_entity(Question, Entity, Fields, Result) :-
    py_call(main:ask_multi_attribute_entity(Question, Entity, Fields), Result).

ask_multi_structured_input(Question, Mode, Groups, Result) :-
    py_call(main:ask_multi_structured_input(Question, Mode, Groups), Result).

% Gather all relevant clinical inputs before evaluating diagnoses.
ask_all(Answers) :-
    % Numeric diagnostic criteria (mg/dL for glucose, % for HbA1c)
    ask_numeric('Fasting plasma glucose (mg/dL) after 8-12 hours fast', Fasting),
    ask_numeric('Random (casual) plasma glucose (mg/dL)', RandomGlucose),
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)', OGTT2h),
    ask_numeric('HbA1c percent (%)', HbA1cPercent),
    % Symptoms (boolean). ask_boolean/1 succeeds only if true, so capture false explicitly.
    (ask_boolean('Excessive thirst?') -> Thirst=true ; Thirst=false),
    (ask_boolean('Excessive urination (polyuria)?') -> Polyuria=true ; Polyuria=false),
    (ask_boolean('Fatigue?') -> Fatigue=true ; Fatigue=false),
    (ask_boolean('Blurred vision?') -> BlurredVision=true ; BlurredVision=false),
    Answers = answers{
        fasting_mgdl: Fasting,
        random_mgdl: RandomGlucose,
        ogtt2h_mgdl: OGTT2h,
        hba1c_percent: HbA1cPercent,
        symptom_thirst: Thirst,
        symptom_polyuria: Polyuria,
        symptom_fatigue: Fatigue,
        symptom_blurred_vision: BlurredVision
    }.

% Diagnostic predicates based on numeric thresholds from the provided guidance.
meets_random_glucose_diabetes(RandomMgDl) :-
    number(RandomMgDl),
    RandomMgDl >= 200.

meets_fasting_glucose_diabetes(FastingMgDl) :-
    number(FastingMgDl),
    FastingMgDl >= 126.

meets_ogtt2h_glucose_diabetes(OGTT2hMgDl) :-
    number(OGTT2hMgDl),
    OGTT2hMgDl >= 200.

meets_hba1c_diabetes(HbA1cPercent) :-
    number(HbA1cPercent),
    HbA1cPercent >= 6.5.

meets_any_lab_criteria_diabetes(Answers) :-
    Answers.fasting_mgdl = F, meets_fasting_glucose_diabetes(F);
    Answers.random_mgdl = R, meets_random_glucose_diabetes(R);
    Answers.ogtt2h_mgdl = O, meets_ogtt2h_glucose_diabetes(O);
    Answers.hba1c_percent = H, meets_hba1c_diabetes(H).

% Prediabetes: fasting blood glucose between 100 and 125 mg/dL (inclusive)
meets_prediabetes_fasting(Answers) :-
    F = Answers.fasting_mgdl,
    number(F),
    F >= 100,
    F =< 125.

% Low risk: none of the diabetes criteria met and fasting < 100 mg/dL
meets_low_risk(Answers) :-
    \+ meets_any_lab_criteria_diabetes(Answers),
    F = Answers.fasting_mgdl,
    number(F),
    F < 100.

% Symptom-based observation: both excessive thirst and excessive urination often seen together.
has_thirst_and_polyuria(Answers) :-
    Answers.symptom_thirst = true,
    Answers.symptom_polyuria = true.

% Assemble diagnoses after collecting all inputs.
compute_diagnoses(Answers, Diagnoses) :-
    findall(D,
        (
            (meets_any_lab_criteria_diabetes(Answers) -> D = diabetes ; fail)
            ;
            (meets_prediabetes_fasting(Answers),
             \+ meets_any_lab_criteria_diabetes(Answers) -> D = prediabetes ; fail)
            ;
            (meets_low_risk(Answers) -> D = low_risk ; fail)
            ;
            (has_thirst_and_polyuria(Answers) -> D = symptoms_thirst_and_polyuria ; fail)
        ),
        Ds),
    % Remove duplicates and keep order
    sort(Ds, SortedDs),
    Diagnoses = SortedDs.

% Main entry: ask all available diagnostic criteria before producing a result.
% Returns a list of applicable diagnoses/observations (possibly empty).
diagnose(Diagnoses) :-
    ask_all(Answers),
    compute_diagnoses(Answers, Diagnoses).

% Specific predicate: diabetes(Boolean).
% Ask the relevant numeric criteria and return true if any diagnostic threshold is met.
diabetes(true) :-
    ask_numeric('Fasting plasma glucose (mg/dL) after 8-12 hours fast', Fasting),
    ask_numeric('Random (casual) plasma glucose (mg/dL)', RandomGlucose),
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)', OGTT2h),
    ask_numeric('HbA1c percent (%)', HbA1cPercent),
    (   meets_fasting_glucose_diabetes(Fasting)
    ;   meets_random_glucose_diabetes(RandomGlucose)
    ;   meets_ogtt2h_glucose_diabetes(OGTT2h)
    ;   meets_hba1c_diabetes(HbA1cPercent)
    ), !.
diabetes(false).

% Specific predicate: prediabetes(Boolean).
% Ask fasting glucose and report prediabetes if fasting in 100-125 mg/dL and not diabetic per lab thresholds.
prediabetes(true) :-
    ask_numeric('Fasting plasma glucose (mg/dL) after 8-12 hours fast', Fasting),
    % also collect other lab values to confirm not diabetic by other criteria
    ask_numeric('Random (casual) plasma glucose (mg/dL)', RandomGlucose),
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)', OGTT2h),
    ask_numeric('HbA1c percent (%)', HbA1cPercent),
    number(Fasting),
    Fasting >= 100, Fasting =< 125,
    \+ (meets_fasting_glucose_diabetes(Fasting);
        meets_random_glucose_diabetes(RandomGlucose);
        meets_ogtt2h_glucose_diabetes(OGTT2h);
        meets_hba1c_diabetes(HbA1cPercent)
       ), !.
prediabetes(false).

% Specific predicate: low_risk(Boolean).
low_risk(true) :-
    ask_numeric('Fasting plasma glucose (mg/dL) after 8-12 hours fast', Fasting),
    ask_numeric('Random (casual) plasma glucose (mg/dL)', RandomGlucose),
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)', OGTT2h),
    ask_numeric('HbA1c percent (%)', HbA1cPercent),
    number(Fasting), Fasting < 100,
    \+ meets_random_glucose_diabetes(RandomGlucose),
    \+ meets_ogtt2h_glucose_diabetes(OGTT2h),
    \+ meets_hba1c_diabetes(HbA1cPercent), !.
low_risk(false).
=======
    py_call(main:ask_string(Question), Value).

ask_category(Question, Categories, Answer) :-
    py_call(main:ask_category(Question, Categories), Answer).

ask_range(Question, Start, Stop, Value) :-
    py_call(main:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(main:ask_duration(Question), Value).    

% Collect all inputs (all diagnostic criteria and common symptoms).
collect_all_answers(answers(RandomMgdl, FastingMgdl, FastingHours, OGTT2hMmol, Hba1cPercent, Hba1cMmol, Thirst, Polyuria, Fatigue, Blurred)) :-
    ask_numeric('Random (casual) plasma glucose in mg/dL? (enter -1 if unknown)', RandomMgdl),
    ask_numeric('Fasting plasma glucose in mg/dL? (enter -1 if unknown)', FastingMgdl),
    ask_numeric('Hours fasting before the fasting glucose measurement? (enter 0 if not fasting)', FastingHours),
    ask_numeric('2-hour OGTT plasma glucose in mmol/L? (enter -1 if unknown)', OGTT2hMmol),
    ask_numeric('HbA1c in percent? (enter -1 if unknown)', Hba1cPercent),
    ask_numeric('HbA1c in mmol/mol? (enter -1 if unknown)', Hba1cMmol),
    ( ask_boolean('Excessive thirst? ') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Excessive urination (polyuria)? (yes/no)') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Fatigue?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Blurred vision? ') -> Blurred = true ; Blurred = false ).

% Criterion predicates that can be asked individually.

% Random (casual) plasma glucose >= 200 mg/dL.
random_plasma_glucose_high :-
    ask_numeric('Random (casual) plasma glucose in mg/dL?', V),
    V >= 200.

% Fasting plasma glucose diagnostic for diabetes: >=126 mg/dL after 8-12 hours fasting.
fasting_plasma_glucose_diabetes :-
    ask_numeric('Fasting plasma glucose in mg/dL?', F),
    ask_numeric('Hours fasting before the fasting glucose measurement?', H),
    H >= 8, H =< 12,
    F >= 126.

% Fasting plasma glucose in the prediabetes range: 100-125 mg/dL after 8-12 hours fasting.
fasting_plasma_glucose_prediabetes :-
    ask_numeric('Fasting plasma glucose in mg/dL?', F),
    ask_numeric('Hours fasting before the fasting glucose measurement?', H),
    H >= 8, H =< 12,
    F >= 100, F =< 125.

% 2-hour OGTT plasma glucose >= 11.1 mmol/L.
ogtt_2h_high :-
    ask_numeric('2-hour OGTT plasma glucose in mmol/L?', V),
    V >= 11.1.

% HbA1c diagnostic for diabetes: >= 6.5% (or >= 48 mmol/mol).
hba1c_high_percent :-
    ask_numeric('HbA1c in percent (%)?', P),
    P >= 6.5.

hba1c_high_mmolmol :-
    ask_numeric('HbA1c in mmol/mol?', M),
    M >= 48.

% Symptom predicates (succeed if the symptom is present).
symptom_thirst :-
    ask_boolean('Excessive thirst?').

symptom_polyuria :-
    ask_boolean('Excessive urination (polyuria)?').

symptom_fatigue :-
    ask_boolean('Fatigue?').

symptom_blurred_vision :-
    ask_boolean('Blurred vision?').

% Evaluate diabetes from collected answers.
diabetes_from_answers(answers(RandomMgdl, FastingMgdl, FastingHours, OGTT2hMmol, Hba1cPercent, Hba1cMmol, _Thirst, _Polyuria, _Fatigue, _Blurred)) :-
    ( number(RandomMgdl), RandomMgdl >= 200 )
    ;
    ( number(FastingMgdl), number(FastingHours), FastingHours >= 8, FastingHours =< 12, FastingMgdl >= 126 )
    ;
    ( number(OGTT2hMmol), OGTT2hMmol >= 11.1 )
    ;
    ( number(Hba1cPercent), Hba1cPercent >= 6.5 )
    ;
    ( number(Hba1cMmol), Hba1cMmol >= 48 ).

% Evaluate prediabetes from collected answers (fasting 100-125 mg/dL after 8-12 h),
% only true if diabetes criteria are not met.
prediabetes_from_answers(Answers) :-
    Answers = answers(_RandomMgdl, FastingMgdl, FastingHours, _OGTT2hMmol, _Hba1cPercent, _Hba1cMmol, _Thirst, _Polyuria, _Fatigue, _Blurred),
    number(FastingMgdl), number(FastingHours),
    FastingHours >= 8, FastingHours =< 12,
    FastingMgdl >= 100, FastingMgdl =< 125,
    \+ diabetes_from_answers(Answers).

% Symptom combination commonly seen in diabetes: thirst and polyuria together.
diabetes_symptoms_from_answers(answers(_RandomMgdl, _FastingMgdl, _FastingHours, _OGTT2hMmol, _Hba1cPercent, _Hba1cMmol, Thirst, Polyuria, _Fatigue, _Blurred)) :-
    Thirst == true,
    Polyuria == true.

% Public predicates that evaluate diagnosis by asking the necessary inputs.

% diagnose/1 asks all available diagnostic criteria (and symptoms) before producing a result.
% Result is one of: diabetes, prediabetes, low_risk.
diagnose(diabetes) :-
    collect_all_answers(Answers),
    diabetes_from_answers(Answers), !.

diagnose(prediabetes) :-
    collect_all_answers(Answers),
    prediabetes_from_answers(Answers), !.

diagnose(low_risk) :-
    collect_all_answers(Answers),
    \+ diabetes_from_answers(Answers),
    \+ prediabetes_from_answers(Answers).

% Specific predicates for user queries about overall conditions.
% If someone queries diabetes directly, these will ask the full set of inputs as required.
diabetes :-
    collect_all_answers(Answers),
    diabetes_from_answers(Answers).

prediabetes :-
    collect_all_answers(Answers),
    prediabetes_from_answers(Answers).

low_risk :-
    collect_all_answers(Answers),
    \+ diabetes_from_answers(Answers),
    \+ prediabetes_from_answers(Answers).
>>>>>>> origin/main
