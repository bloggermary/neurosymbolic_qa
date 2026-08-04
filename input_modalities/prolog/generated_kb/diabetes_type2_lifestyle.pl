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

/*
  Criterion: lab-based diagnosis.
  Asks which lab is available, then its numeric value, and returns a dict:
    _{verdict: positive|negative|unknown, method: AtomOrNone, value: NumberOrNone}
*/
criterion_lab(Result) :-
    ask_category('Which lab result is available?', ['fasting_plasma_glucose','random_glucose','hba1c','none'], LabType),
    ( LabType = fasting_plasma_glucose ->
        ask_numeric('Fasting plasma glucose (mg/dL)?', F),
        ( F >= 126.0 ->
            Result = _{verdict: positive, method: fasting_plasma_glucose, value: F}
        ;
            Result = _{verdict: negative, method: fasting_plasma_glucose, value: F}
        )
    ; LabType = random_glucose ->
        ask_numeric('Random plasma glucose (mg/dL)?', R),
        ( R >= 200.0 ->
            Result = _{verdict: positive, method: random_glucose, value: R}
        ;
            Result = _{verdict: negative, method: random_glucose, value: R}
        )
    ; LabType = hba1c ->
        ask_numeric('Hemoglobin A1c (%)?', H),
        ( H >= 6.5 ->
            Result = _{verdict: positive, method: hba1c, value: H}
        ;
            Result = _{verdict: negative, method: hba1c, value: H}
        )
    ; % none
        Result = _{verdict: unknown, method: none, value: none}
    ).

/*
  Criterion: prediabetes history (yes/no)
*/
criterion_prediabetes(Result) :-
    ( ask_boolean('Have you ever been told you have prediabetes or "borderline" blood sugar?') ->
        Result = _{prediabetes: true}
    ;
        Result = _{prediabetes: false}
    ).

/*
  Criterion: symptom duration and related symptoms.
  Asks weeks of increased thirst/urination, fatigue, blurred vision.
  Returns: _{duration_weeks: Num, gradual: true|false, fatigue: true|false, blurred_vision: true|false}
  (Using 12 weeks as the threshold for "gradual" consistent with "months".)
*/
criterion_symptoms(Result) :-
    ask_duration('How long have you noticed increased thirst or urination, in weeks?', Weeks),
    ( Weeks >= 12.0 ->
        Gradual = true
    ;
        Gradual = false
    ),
    ( ask_boolean('Do you have increased fatigue (yes/no)?') ->
        Fatigue = true
    ;
        Fatigue = false
    ),
    ( ask_boolean('Do you have blurred vision (yes/no)?') ->
        Blurred = true
    ;
        Blurred = false
    ),
    Result = _{duration_weeks: Weeks, gradual: Gradual, fatigue: Fatigue, blurred_vision: Blurred}.

/*
  Criterion: lifestyle and basic anthropometrics.
  Asks BMI, waist circumference (cm), minutes of moderate activity per week,
  diet category, current smoking (yes/no), typical alcoholic drinks per week,
  and motivation (1-10).
  Returns a dict with raw values and a computed flag activity_insufficient (true if <150).
*/
criterion_lifestyle(Result) :-
    ask_numeric('What is your body mass index (BMI)?', Bmi),
    ask_numeric('What is your waist circumference (cm)?', WaistCm),
    ask_numeric('How many minutes of moderate physical activity do you get in a typical week?', ActivityMin),
    ( ActivityMin < 150.0 ->
        ActivityInsufficient = true
    ;
        ActivityInsufficient = false
    ),
    ask_category('How would you describe your diet quality?', ['mostly_whole_foods','mixed','mostly_processed','unknown'], Diet),
    ( ask_boolean('Do you currently smoke (yes/no)?') ->
        Smoking = true
    ;
        Smoking = false
    ),
    ask_numeric('How many alcoholic drinks do you have in a typical week?', DrinksPerWeek),
    ask_range('On a scale from 1 to 10, how motivated are you to make dietary and activity changes?', 1.0, 10.0, Motivation),
    Result = _{
        bmi: Bmi,
        waist_cm: WaistCm,
        activity_min_per_week: ActivityMin,
        activity_insufficient: ActivityInsufficient,
        diet: Diet,
        smoking: Smoking,
        alcohol_drinks_per_week: DrinksPerWeek,
        motivation: Motivation
    }.

/*
  Criterion: family history of type 2 diabetes.
  Categories: none, one_relative, multiple_relatives
*/
criterion_family_history(Result) :-
    ask_category('Does a parent or sibling have type 2 diabetes?', ['none','one_relative','multiple_relatives'], FH),
    Result = _{family_history: FH}.

/*
  Optional: blood pressure and sleep asked only when prior evidence leaves uncertainty.
  Returns _{systolic_mmHg: Num, sleep_hours: Num}
*/
criterion_bp_sleep(Result) :-
    ask_numeric('What is your resting systolic blood pressure (mmHg)?', Systolic),
    ask_numeric('How many hours of sleep do you typically get per night?', SleepHours),
    Result = _{systolic_mmHg: Systolic, sleep_hours: SleepHours}.

/*
  Helper: count lifestyle risk features used in secondary decision rules.
  We consider these as risk items grounded in the text:
    - activity_insufficient true
    - diet mostly_processed
    - smoking true
    - family_history not none
  Returns integer count (as a number).
*/
count_risk_features(Lifestyle, FamilyHistory, Count) :-
    get_dict(activity_insufficient, Lifestyle, ActIns),
    ( ActIns = true -> A = 1.0 ; A = 0.0 ),
    get_dict(diet, Lifestyle, Diet),
    ( Diet = mostly_processed -> D = 1.0 ; D = 0.0 ),
    get_dict(smoking, Lifestyle, SmokingFlag),
    ( SmokingFlag = true -> S = 1.0 ; S = 0.0 ),
    ( FamilyHistory = none -> F = 0.0 ; F = 1.0 ),
    Sum is A + D + S + F,
    Count = Sum.

/*
  Main diagnose/1 predicate.
  Returns a dictionary with:
    verdict: one of type_2_diabetes | probable_type_2_diabetes | possible_type_2_diabetes | no_type_2_diabetes | uncertain
    evidence: list of criteria dicts collected
*/
diagnose(Result) :-
    % 1) Check labs first (decisive if positive)
    criterion_lab(Lab),
    ( get_dict(verdict, Lab, positive) ->
        Result = _{verdict: type_2_diabetes, evidence: [lab-Lab]}
    ;
        % 2) Gather targeted history/lifestyle to decide if probable/possible
        criterion_prediabetes(Prediabetes),
        criterion_symptoms(Symptoms),
        criterion_lifestyle(Lifestyle),
        criterion_family_history(Family),
        % Count risk features
        get_dict(prediabetes, Prediabetes, PredFlag),
        get_dict(gradual, Symptoms, GradualFlag),
        get_dict(family_history, Family, FamilyHist),
        count_risk_features(Lifestyle, FamilyHist, RiskCount),
        ( PredFlag = true, GradualFlag = true, RiskCount >= 2.0 ->
            Result = _{
                verdict: probable_type_2_diabetes,
                evidence: [lab-Lab, prediabetes-Prediabetes, symptoms-Symptoms, lifestyle-Lifestyle, family_history-Family]
            }
        ; PredFlag = true, GradualFlag = true, (FamilyHist = multiple_relatives) ->
            Result = _{
                verdict: probable_type_2_diabetes,
                evidence: [lab-Lab, prediabetes-Prediabetes, symptoms-Symptoms, lifestyle-Lifestyle, family_history-Family]
            }
        ; GradualFlag = true, RiskCount >= 1.0 ->
            Result = _{
                verdict: possible_type_2_diabetes,
                evidence: [lab-Lab, prediabetes-Prediabetes, symptoms-Symptoms, lifestyle-Lifestyle, family_history-Family]
            }
        ; PredFlag = false, GradualFlag = false, RiskCount =:= 0.0 ->
            Result = _{
                verdict: no_type_2_diabetes,
                evidence: [lab-Lab, prediabetes-Prediabetes, symptoms-Symptoms, lifestyle-Lifestyle, family_history-Family]
            }
        ;
            % Remaining uncertainty: ask BP and sleep for additional context, but do not force a definitive diagnosis
            criterion_bp_sleep(BpSleep),
            Result = _{
                verdict: uncertain,
                evidence: [lab-Lab, prediabetes-Prediabetes, symptoms-Symptoms, lifestyle-Lifestyle, family_history-Family, bp_sleep-BpSleep]
            }
        )
    ).