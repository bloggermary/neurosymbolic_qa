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

/*
  diagnose/1
  Returns a dictionary with keys:
    verdict: one of {diabetes, possible_drug_induced_hyperglycemia, no_diabetes, inconclusive_need_glucose_tests}
    evidence: list of atoms describing decisive findings
    next_steps: list of recommended next steps (may be empty)
*/
diagnose(Result) :-
    criterion_test_results(Test_dict),
    criterion_hba1c_unreliable(Hba_unreliable),
    criterion_medication_list(Med_list),
    ( Med_list \= [] -> ( exclude(==(none), Med_list, Meds_filtered), Meds_filtered \= [] -> criterion_medication_grouping(Med_groups) ; Med_groups = _{morning:[],afternoon:[],evening:[],bedtime:[]} ) ; Med_groups = _{morning:[],afternoon:[],evening:[],bedtime:[]} ),
    criterion_symptoms(Symptoms),
    criterion_egfr(Egfr),
    criterion_chronic_conditions_count(Comorbidity_count),
    criterion_cognitive_function(Cognitive_score),
    criterion_years_known_abnormality(Years_known),
    evaluate_tests_and_classify(Test_dict, Hba_unreliable, Med_list, Symptoms, Egfr, Comorbidity_count, Cognitive_score, Years_known, Med_groups, Result).

/* ---------- Criterion: which diagnostic tests are available and their numeric values ---------- */

criterion_test_results(Test_dict) :-
    ask_multiple_category('Which diagnostic test results are available? Select all that apply.', [fasting, random, ogtt, hba1c, none], Selected),
    ( Selected = [] -> Selected2 = [none] ; Selected2 = Selected ),
    ( member(none, Selected2) ->
        Test_dict = _{ }
    ;
        build_test_values(Selected2, Test_dict)
    ).

build_test_values(Selected, Test_dict) :-
    ( member(fasting, Selected) ->
        ask_numeric('Enter fasting plasma glucose in mg/dL', Fasting)
    ;
        Fasting = none
    ),
    ( member(random, Selected) ->
        ask_numeric('Enter random (any time) plasma glucose in mg/dL', Random)
    ;
        Random = none
    ),
    ( member(ogtt, Selected) ->
        ask_numeric('Enter 2-hour oral glucose tolerance test (OGTT) plasma glucose in mg/dL', Ogtt)
    ;
        Ogtt = none
    ),
    ( member(hba1c, Selected) ->
        ask_numeric('Enter HbA1c in percent (e.g. 6.5)', Hba1c)
    ;
        Hba1c = none
    ),
    Test_dict = _{ fasting: Fasting, random: Random, ogtt: Ogtt, hba1c: Hba1c }.

/* ---------- Criterion: is HbA1c unreliable because of CKD or anemia? ---------- */

criterion_hba1c_unreliable(Unreliable) :-
    ( ask_boolean('Does the patient have chronic kidney disease or anemia (this makes HbA1c potentially unreliable)?') ->
        Unreliable = true
    ;
        Unreliable = false
    ).

/* ---------- Criterion: medication list (multiple choice of glucose-raising meds) ---------- */

criterion_medication_list(Med_list) :-
    ask_multiple_category('Select ALL of the following that currently apply (medications that can raise blood glucose).', [corticosteroids, thiazide_diuretics, atypical_antipsychotics, none], Meds),
    ( Meds = [] -> Med_list = [none] ; Med_list = Meds ).

/* ---------- Criterion: group current medications by time of day (only asked if relevant meds present) ---------- */

criterion_medication_grouping(Med_groups) :-
    Structure = [
        [morning, 'List medications taken in the morning (comma-separated)', string],
        [afternoon, 'List medications taken in the afternoon (comma-separated)', string],
        [evening, 'List medications taken in the evening (comma-separated)', string],
        [bedtime, 'List medications taken at bedtime (comma-separated)', string]
    ],
    ask_multi_structured_input('Group your current medications by when they are taken (morning/afternoon/evening/bedtime).', group, Structure, Groups),
    % Groups is expected to be a list of key-value pairs matching Structure; normalize to dict
    ( is_dict(Groups) ->
        Med_groups = Groups
    ;
        ( Groups = [_|_] ->
            list_to_med_groups(Groups, Med_groups)
        ;
            Med_groups = _{morning:'',afternoon:'',evening:'',bedtime:''}
        )
    ).

list_to_med_groups(Pairs, Dict) :-
    pair_list_to_dict(Pairs, Dict).

pair_list_to_dict([], _{morning:'',afternoon:'',evening:'',bedtime:''}).
pair_list_to_dict(Pairs, Dict) :-
    foldl(pair_to_kv, Pairs, _{morning:'',afternoon:'',evening:'',bedtime:''}, Dict).

pair_to_kv([Key, ValueString], Acc, NewAcc) :-
    put_dict(Key, Acc, ValueString, NewAcc).
pair_to_kv(_Other, Acc, Acc).

/* ---------- Criterion: classic symptoms (ask each as yes/no) ---------- */

criterion_symptoms(Symptoms) :-
    ( ask_boolean('Does the patient have excessive thirst (yes/no)?') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Does the patient have frequent urination (yes/no)?') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Does the patient have fatigue (yes/no)?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Does the patient have blurred vision (yes/no)?') -> Blurred = true ; Blurred = false ),
    Symptoms = _{ thirst: Thirst, polyuria: Polyuria, fatigue: Fatigue, blurred_vision: Blurred }.

/* ---------- Criterion: renal function (eGFR numeric) ---------- */

criterion_egfr(Egfr) :-
    ask_numeric('Enter estimated glomerular filtration rate (eGFR) in mL/min/1.73m2', Egfr).

/* ---------- Criterion: number of distinct chronic conditions (count numeric) ---------- */

criterion_chronic_conditions_count(Count) :-
    ask_numeric('How many distinct chronic conditions does the patient have (plain count)?', Count).

/* ---------- Criterion: cognitive and functional status (1-10) ---------- */

criterion_cognitive_function(Score) :-
    ask_range('Rate cognitive/functional status from 1 (fully independent) to 10 (fully dependent)', 1, 10, Score).

/* ---------- Criterion: years with any known glucose abnormality (numeric, if applicable) ---------- */

criterion_years_known_abnormality(Years) :-
    ask_numeric('How many years has the patient had any known glucose abnormality (enter 0 if none or unknown)?', Years).

/* ---------- Optional criterion for additional vitals when inconclusive ---------- */

criterion_additional_vitals(Systolic_bp, Weight_loss) :-
    ask_numeric('Enter systolic blood pressure in mmHg', Systolic_bp),
    ask_numeric('Enter unintentional weight loss over the past 6 months in kg', Weight_loss).

/* ---------- Evaluation logic and classification ---------- */

evaluate_tests_and_classify(Test_dict, Hba_unreliable, Med_list, Symptoms, _Egfr, _Comorbidity_count, _Cognitive_score, _Years_known, _Med_groups, Result) :-
    % Extract values if present
    ( get_dict(fasting, Test_dict, F) -> true ; F = none ),
    ( get_dict(random, Test_dict, R) -> true ; R = none ),
    ( get_dict(ogtt, Test_dict, O) -> true ; O = none ),
    ( get_dict(hba1c, Test_dict, H) -> true ; H = none ),
    % thresholds
    ( is_number_and_ge(F, 126.0) -> Test_pos = [fasting] ; Test_pos = [] ),
    ( is_number_and_ge(R, 200.0) -> append(Test_pos, [random], Test_pos2) ; Test_pos2 = Test_pos ),
    ( is_number_and_ge(O, 200.0) -> append(Test_pos2, [ogtt], Test_pos3) ; Test_pos3 = Test_pos2 ),
    ( Test_pos3 \= [] ->
        % definite glucose test positive
        ( meds_may_raise_glucose(Med_list) ->
            Result = _{ verdict: possible_drug_induced_hyperglycemia, evidence: Test_pos3, next_steps: ['Consider repeating glucose testing off offending medications if possible; assess medication timing and grouping.'] }
        ;
            collect_symptom_support(Symptoms, SymList),
            Result = _{ verdict: diabetes, evidence: Test_pos3, next_steps: ( SymList = [] -> ['Proceed with diabetes management tailored to older adult with comorbidity.'] ; ['Symptoms support diagnosis: ' | [] ] ) }
        )
    ;
        % No fasting/random/ogtt meeting thresholds
        ( is_number_and_ge(H, 6.5) ->
            ( Hba_unreliable = true ->
                % HbA1c elevated but unreliable -> need glucose confirmation
                ask_for_confirmatory_glucose(Test_dict, NewTest_dict, New_pos),
                ( New_pos \= [] ->
                    ( meds_may_raise_glucose(Med_list) ->
                        Result = _{ verdict: possible_drug_induced_hyperglycemia, evidence: New_pos, next_steps: ['Consider medication effects and repeat confirmatory testing.'] }
                    ;
                        Result = _{ verdict: diabetes, evidence: New_pos, next_steps: ['HbA1c unreliable; diagnosis confirmed by glucose test.'] }
                    )
                ;
                    % still inconclusive after seeking glucose tests
                    criterion_additional_vitals(SBP, WeightLoss),
                    Result = _{ verdict: inconclusive_need_glucose_tests, evidence: [hba1c_unreliable, hba1c_value-H], next_steps: ['Obtain fasting or 2-hour OGTT; consider weight loss and blood pressure in further assessment', systolic_bp-SBP, weight_loss_kg-WeightLoss] }
                )
            ;
                % HbA1c elevated and reliable
                ( meds_may_raise_glucose(Med_list) ->
                    Result = _{ verdict: possible_drug_induced_hyperglycemia, evidence: [hba1c], next_steps: ['Consider medication effects; correlate with glucose testing.'] }
                ;
                    Result = _{ verdict: diabetes, evidence: [hba1c], next_steps: ['HbA1c >= 6.5% meets diagnostic threshold; proceed with management appropriate for older adults.'] }
                )
            )
        ;
            % No tests meet thresholds and HbA1c not elevated
            Result = _{ verdict: no_diabetes, evidence: [], next_steps: ['No diagnostic criteria met based on provided results; if clinical suspicion remains consider repeat testing or OGTT.'] }
        )
    ).

is_number_and_ge(Value, Threshold) :-
    number(Value),
    Value >= Threshold.

meds_may_raise_glucose(Med_list) :-
    Med_list \= [],
    exclude(==(none), Med_list, Filtered),
    Filtered \= [].

ask_for_confirmatory_glucose(Orig_dict, New_dict, Positive_tests) :-
    % ask for fasting/random/ogtt if not already present or if user can provide now
    ( get_dict(fasting, Orig_dict, F0), number(F0) -> F = F0 ; ( ask_boolean('Do you have a fasting plasma glucose value to provide now?') -> ask_numeric('Enter fasting plasma glucose in mg/dL', F) ; F = none ) ),
    ( get_dict(random, Orig_dict, R0), number(R0) -> R = R0 ; ( ask_boolean('Do you have a random plasma glucose value to provide now?') -> ask_numeric('Enter random plasma glucose in mg/dL', R) ; R = none ) ),
    ( get_dict(ogtt, Orig_dict, O0), number(O0) -> O = O0 ; ( ask_boolean('Do you have a 2-hour OGTT glucose value to provide now?') -> ask_numeric('Enter 2-hour OGTT plasma glucose in mg/dL', O) ; O = none ) ),
    New_dict = _{ fasting: F, random: R, ogtt: O },
    find_positive_tests(F, R, O, Positive_tests).

find_positive_tests(F, R, O, Pos) :-
    findall(Test, (
        ( number(F), F >= 126.0, Test = fasting ) ;
        ( number(R), R >= 200.0, Test = random ) ;
        ( number(O), O >= 200.0, Test = ogtt )
    ), Pos).