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


/* Standalone numeric diagnostic criteria (each asks what it needs itself) */

fasting_glucose_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 126.0 ).

random_glucose_criterion :-
    ask_numeric('What is a recent random (non-fasting) plasma glucose in mg/dL?', Random),
    ( Random >= 200.0 ).

hba1c_criterion :-
    ask_numeric('What is your hemoglobin A1c (HbA1c) percentage?', A1c),
    ( A1c >= 6.5 ).

/* Standalone prediabetes criteria */

fasting_prediabetes_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 100.0, Fasting =< 125.0 ).

hba1c_prediabetes_criterion :-
    ask_numeric('What is your hemoglobin A1c (HbA1c) percentage?', A1c),
    ( A1c >= 5.7, A1c < 6.5 ).

/* Clinical (lifestyle + symptoms + family history) probability assessment.
   This collects a compact set of high-yield questions and computes a simple
   score. It returns true if the aggregated picture strongly suggests diabetes.
   It asks extra items (blood pressure, sleep) only when the initial score is borderline. */

clinical_probable_diabetes :-
    ask_numeric('What is your body mass index (BMI)?', BMI),
    ask_numeric('What is your waist circumference in centimeters?', Waist),
    ask_numeric('How many minutes of moderate physical activity do you get in a typical week?', ActivityMin),
    ask_category('How would you describe your usual diet quality?', [mostly_whole_foods, mixed, mostly_processed, unknown], DietQuality),
    ( ask_boolean('Do you currently smoke?') -> Smoker = true ; Smoker = false ),
    ask_numeric('How many alcoholic drinks do you have in a typical week?', AlcoholDrinks),
    ask_duration('How many weeks have you noticed increased thirst or urination?', SymptomWeeks),
    ( ask_boolean('Do you feel unusually fatigued recently?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Have you had episodes of blurred vision recently?') -> Blurred = true ; Blurred = false ),
    ask_category('Has a parent or sibling been diagnosed with type 2 diabetes?', [none, one_relative, multiple_relatives], FamilyHistory),
    ( ask_boolean('Have you ever been told you have prediabetes or borderline blood sugar?') -> PriorPrediabetes = true ; PriorPrediabetes = false ),
    % motivation is collected for context but not used in scoring
    ask_range('On a scale from 1 to 10, how motivated are you to make dietary and activity changes?', 1, 10, _Motivation),
    % compute score from the gathered items
    Score0 = 0,
    ( BMI >= 30.0 -> Score1 is Score0 + 1 ; Score1 is Score0 ),
    ( Waist >= 100.0 -> Score2 is Score1 + 1 ; Score2 is Score1 ),
    ( ActivityMin < 150.0 -> Score3 is Score2 + 1 ; Score3 is Score2 ),
    ( DietQuality == mostly_processed -> Score4 is Score3 + 1 ; Score4 is Score3 ),
    ( Smoker == true -> Score5 is Score4 + 1 ; Score5 is Score4 ),
    ( AlcoholDrinks >= 14.0 -> Score6 is Score5 + 1 ; Score6 is Score5 ),
    ( FamilyHistory == one_relative -> Score7 is Score6 + 1 ; ( FamilyHistory == multiple_relatives -> Score7 is Score6 + 2 ; Score7 is Score6 ) ),
    ( PriorPrediabetes == true -> Score8 is Score7 + 1 ; Score8 is Score7 ),
    ( SymptomWeeks >= 12.0 -> Score9 is Score8 + 1 ; Score9 is Score8 ),
    ( Fatigue == true -> Score10 is Score9 + 1 ; Score10 is Score9 ),
    ( Blurred == true -> Score11 is Score10 + 1 ; Score11 is Score10 ),
    % If score is clearly high, conclude probable diabetes.
    ( Score11 >= 4.0 ->
        true
    ;
        % borderline zone: ask resting systolic BP and sleep duration to refine
        ( Score11 >= 2.0 ->
            ask_numeric('What is your typical resting systolic blood pressure in mmHg?', Systolic),
            ask_numeric('How many hours of sleep do you typically get per night?', SleepHours),
            ( Systolic >= 140.0 -> Score12 is Score11 + 1 ; Score12 is Score11 ),
            ( SleepHours < 6.0 -> Score13 is Score12 + 1 ; Score13 is Score12 ),
            ( Score13 >= 4.0 )
        ;
            % low score -> not probable
            fail
        )
    ).

/* Public predicates that can be called directly */

diabetes :-
    ( fasting_glucose_criterion -> true
    ; random_glucose_criterion -> true
    ; hba1c_criterion -> true
    ; clinical_probable_diabetes
    ).

prediabetes :-
    ( fasting_prediabetes_criterion -> true
    ; hba1c_prediabetes_criterion -> true
    ).

low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* Main workflow: ask only as much as needed, stop as soon as a decisive threshold is met.
   Returns a janus-safe dict with verdict and brief evidence tags. */

diagnose(Result) :-
    % Check fasting glucose first (numeric diagnostic threshold). If met, stop.
    ( ( ask_numeric('What is your fasting plasma glucose in mg/dL?', FastingVal),
        FastingVal >= 126.0 ) ->
        Result = _{verdict: diabetes, evidence: [fasting_glucose]}
    ;
      % Fasting not diagnostic: check random glucose next.
      ( ask_numeric('What is a recent random (non-fasting) plasma glucose in mg/dL?', RandomVal),
        RandomVal >= 200.0 ) ->
        Result = _{verdict: diabetes, evidence: [random_glucose]}
    ;
      % Random not diagnostic: check HbA1c.
      ( ask_numeric('What is your hemoglobin A1c (HbA1c) percentage?', A1cVal),
        A1cVal >= 6.5 ) ->
        Result = _{verdict: diabetes, evidence: [hba1c]}
    ;
      % No definitive lab diagnosis from single numeric thresholds. Check for prediabetes.
      ( % Check fasting prediabetes range
        ( ask_numeric('What is your fasting plasma glucose in mg/dL?', FastingVal2),
          FastingVal2 >= 100.0, FastingVal2 =< 125.0 ) ->
          Result = _{verdict: prediabetes, evidence: [fasting_prediabetes]}
      ;
        % Check HbA1c prediabetes range
        ( ask_numeric('What is your hemoglobin A1c (HbA1c) percentage?', A1cVal2),
          A1cVal2 >= 5.7, A1cVal2 < 6.5 ) ->
          Result = _{verdict: prediabetes, evidence: [hba1c_prediabetes]}
      ;
        % Labs inconclusive for prediabetes/diabetes: use clinical picture.
        ( clinical_probable_diabetes ->
            Result = _{verdict: diabetes, evidence: [clinical_risk_profile]}
        ;
            % If neither lab nor clinical picture suggests disease, label low risk.
            Result = _{verdict: low_risk, evidence: []}
        )
      )
    ).