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

/* --- Lab-based diagnostic criteria (standalone, no arguments) --- */

fasting_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 126.0.

random_criterion :-
    ask_numeric('What is your random (non-fasting) plasma glucose in mg/dL?', Value),
    Value >= 200.0.

hba1c_criterion :-
    ask_numeric('What is your HbA1c percentage?', Value),
    Value >= 6.5.

/* --- Prediabetes standalone criteria --- */

fasting_prediabetes_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0,
    Value < 126.0.

hba1c_prediabetes_criterion :-
    ask_numeric('What is your HbA1c percentage?', Value),
    Value >= 5.7,
    Value < 6.5.

/* --- Lifestyle, symptom and risk-item predicates (standalone) --- */

bmi_risk :-
    ask_numeric('What is your body mass index (BMI)?', Bmi),
    Bmi >= 30.0.

waist_risk :-
    ask_numeric('What is your waist circumference in centimeters?', Waist),
    Waist >= 100.0.

physical_activity_insufficient :-
    ask_numeric('How many minutes of moderate physical activity do you get in a typical week?', Minutes),
    Minutes < 150.0.

diet_unhealthy :-
    ask_category('How would you describe your diet quality?', [mostly_whole_foods, mixed, mostly_processed, unknown], Answer),
    Answer == mostly_processed.

smoker :-
    ( ask_boolean('Do you currently smoke?') -> Smokes = true ; Smokes = false ),
    Smokes == true.

alcohol_heavy :-
    ask_numeric('How many alcoholic drinks do you have in a typical week?', Drinks),
    Drinks >= 14.0.

thirst_or_urination_duration_long :-
    ask_numeric('For how many weeks have you noticed increased thirst or urination?', Weeks),
    Weeks >= 12.0.

fatigue_present :-
    ( ask_boolean('Do you experience increased fatigue?') -> Fat = true ; Fat = false ),
    Fat == true.

blurred_vision_present :-
    ( ask_boolean('Do you experience blurred vision?') -> Bv = true ; Bv = false ),
    Bv == true.

family_history_any :-
    ask_category('Has a parent or sibling been diagnosed with type 2 diabetes?', [none, one_relative, multiple_relatives], FH),
    FH \== none.

prior_prediabetes_reported :-
    ( ask_boolean('Have you ever been told you have prediabetes or borderline blood sugar?') -> P = true ; P = false ),
    P == true.

motivation_rating(R) :-
    ask_range('On a scale from 1 to 10, how motivated are you to make dietary and activity changes?', 1, 10, R).

resting_bp_high :-
    ask_numeric('What is your resting systolic blood pressure in mmHg?', BP),
    BP >= 130.0.

sleep_short :-
    ask_numeric('How many hours of sleep do you typically get per night?', Hours),
    Hours < 6.0.

/* --- High-level boolean predicates required by the spec --- */

diabetes :-
    fasting_criterion.
diabetes :-
    random_criterion.
diabetes :-
    hba1c_criterion.

prediabetes :-
    fasting_prediabetes_criterion.
prediabetes :-
    hba1c_prediabetes_criterion.
prediabetes :-
    prior_prediabetes_reported.

low_risk :-
    \+ diabetes,
    \+ prediabetes,
    ask_numeric('What is your body mass index (BMI)?', Bmi),
    Bmi < 25.0,
    ask_numeric('How many minutes of moderate physical activity do you get in a typical week?', Minutes),
    Minutes >= 150.0,
    ask_category('How would you describe your diet quality?', [mostly_whole_foods, mixed, mostly_processed, unknown], Diet),
    Diet == mostly_whole_foods,
    ( ask_boolean('Do you currently smoke?') -> Smokes = true ; Smokes = false ),
    Smokes == false,
    ask_category('Has a parent or sibling been diagnosed with type 2 diabetes?', [none, one_relative, multiple_relatives], FH),
    FH == none.

/* --- Main adaptive diagnostic workflow (single entry point) --- */

diagnose(Result) :-
    /* 1) Immediate lab-based confirmations (stop as soon as one is met) */
    (   fasting_criterion
    ->  Result = _{verdict: diabetes, evidence: [fasting_plasma_glucose]}
    ;   random_criterion
    ->  Result = _{verdict: diabetes, evidence: [random_glucose]}
    ;   hba1c_criterion
    ->  Result = _{verdict: diabetes, evidence: [hba1c]}
    ;   /* 2) Clear prediabetes by lab or prior diagnosis */
        ( fasting_prediabetes_criterion
        -> Result = _{verdict: prediabetes, evidence: [fasting_prediabetes]}
        ; hba1c_prediabetes_criterion
        -> Result = _{verdict: prediabetes, evidence: [hba1c_prediabetes]}
        ; ( prior_prediabetes_reported
          -> Result = _{verdict: prediabetes, evidence: [prior_prediabetes_reported]}
          ; /* 3) No decisive labs: gather a focused lifestyle/symptom snapshot */
            ask_numeric('What is your body mass index (BMI)?', Bmi),
            ask_numeric('What is your waist circumference in centimeters?', Waist),
            ask_numeric('How many minutes of moderate physical activity do you get in a typical week?', ActivityMins),
            ask_category('How would you describe your diet quality?', [mostly_whole_foods, mixed, mostly_processed, unknown], Diet),
            ( ask_boolean('Do you currently smoke?') -> Smokes = true ; Smokes = false ),
            ask_numeric('How many alcoholic drinks do you have in a typical week?', AlcoholDrinks),
            ask_numeric('For how many weeks have you noticed increased thirst or urination?', ThirstWeeks),
            ( ask_boolean('Do you experience increased fatigue?') -> Fatigue = true ; Fatigue = false ),
            ( ask_boolean('Do you experience blurred vision?') -> Blurred = true ; Blurred = false ),
            ask_category('Has a parent or sibling been diagnosed with type 2 diabetes?', [none, one_relative, multiple_relatives], FamilyHx),
            /* Build a simple risk list for explanation */
            ( Bmi >= 30.0 -> BmiFlag = bmi_risk ; BmiFlag = none ),
            ( Waist >= 100.0 -> WaistFlag = waist_risk ; WaistFlag = none ),
            ( ActivityMins < 150.0 -> ActivityFlag = low_activity ; ActivityFlag = none ),
            ( Diet == mostly_processed -> DietFlag = diet_unhealthy ; DietFlag = none ),
            ( Smokes == true -> SmokeFlag = smoker ; SmokeFlag = none ),
            ( AlcoholDrinks >= 14.0 -> AlcFlag = alcohol_heavy ; AlcFlag = none ),
            ( FamilyHx \== none -> FamFlag = family_history ; FamFlag = none ),
            findall(Label, member(Label, [BmiFlag, WaistFlag, ActivityFlag, DietFlag, SmokeFlag, AlcFlag, FamFlag]), RawFlags),
            exclude(==(none), RawFlags, PositiveFlags),
            /* 4) Use symptoms + risk count to decide */
            ( (ThirstWeeks >= 12.0 ; Fatigue == true ; Blurred == true),
              PositiveFlags \== []
            -> Result = _{verdict: prediabetes, evidence: PositiveFlags}
            ; /* 5) Low-risk shortcut when healthy lifestyle and no family history */
              Bmi < 25.0, ActivityMins >= 150.0, Diet == mostly_whole_foods, Smokes == false, FamilyHx == none
            -> Result = _{verdict: low_risk, evidence: [healthy_lifestyle]}
            ; /* 6) Otherwise conservative classification as prediabetes (borderline risk) */
              Result = _{verdict: prediabetes, evidence: PositiveFlags}
          )
        )
    )).