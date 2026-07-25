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

% Criterion: Gestational diabetes by 75g OGTT thresholds.
% Asks fasting first, then 1-hour, then 2-hour, stopping as soon as a diagnostic threshold is met.
gdm_by_ogtt :-
    ask_numeric('What is the fasting plasma glucose in mg/dL from the 75-gram OGTT?', Fasting),
    ( Fasting >= 92.0 ->
        true
    ;
        ask_numeric('What is the 1-hour plasma glucose in mg/dL from the 75-gram OGTT?', OneHour),
        ( OneHour >= 180.0 ->
            true
        ;
            ask_numeric('What is the 2-hour plasma glucose in mg/dL from the 75-gram OGTT?', TwoHour),
            TwoHour >= 153.0
        )
    ).

% Collect risk factors categorically and decide if any are present.
% Asks all listed items before making the decision.
risk_factors_present :-
    ask_category('Have you had gestational diabetes in a previous pregnancy or this pregnancy?', [none, this_pregnancy, previous_pregnancy], PrevGDM),
    ( ask_boolean('Do you have a history of polycystic ovary syndrome (PCOS)?') -> PCOS = true ; PCOS = false ),
    ask_category('What was your pre-pregnancy body mass index category?', [normal, overweight, obese, severely_obese], BMIcat),
    ( ask_boolean('Do you have a first-degree relative with type 2 diabetes?') -> FirstDeg = true ; FirstDeg = false ),
    ask_numeric('What is your age in years?', MaternalAge),
    ( ask_boolean('Is this a multiple pregnancy (twins or higher)?') -> Multiple = true ; Multiple = false ),
    ( PrevGDM == previous_pregnancy
    ; PCOS == true
    ; BMIcat == overweight
    ; BMIcat == obese
    ; BMIcat == severely_obese
    ; FirstDeg == true
    ; MaternalAge >= 35.0
    ; Multiple == true
    ).

% Postpartum classification: true if postpartum test returned prediabetes.
prediabetes :-
    ask_category('After delivery, what was the postpartum glucose testing result?', [not_yet_tested, normal, prediabetes, overt_diabetes], Status),
    Status == prediabetes,
    ask_numeric('How many weeks after delivery was the postpartum glucose test performed?', WeeksAfterDelivery),
    ( WeeksAfterDelivery >= 6.0, WeeksAfterDelivery =< 12.0 -> true ; true ).

% Diabetes true if OGTT diagnostic in pregnancy or postpartum reclassification to overt diabetes.
diabetes :-
    ( gdm_by_ogtt -> true
    ;
      ask_category('After delivery, what was the postpartum glucose testing result?', [not_yet_tested, normal, prediabetes, overt_diabetes], PostStatus),
      PostStatus == overt_diabetes
    ).

% Low risk: no diagnostic OGTT, and no risk factors suggesting early screening or concern.
low_risk :-
    ask_range('How many weeks of gestation are you currently at (enter a value between 4 and 42)?', 4.0, 42.0, Week),
    ( Week >= 24.0, Week =< 28.0 ->
        ( gdm_by_ogtt -> fail
        ; ( risk_factors_present -> fail ; true )
        )
    ; Week < 24.0 ->
        ( risk_factors_present -> fail ; true )
    ; % Week > 28.0
        ( ask_boolean('Have you already had a 75-gram OGTT during this pregnancy?') ->
            ( gdm_by_ogtt -> fail ; ( risk_factors_present -> fail ; true ) )
        ;
            true
        )
    ).

% Main workflow: adaptive questioning and concise conclusions.
diagnose(Result) :-
    ask_range('How many weeks of gestation are you currently at (enter a value between 4 and 42)?', 4.0, 42.0, Week),
    ( Week >= 24.0, Week =< 28.0 ->
        % Standard screening window: perform/interprete OGTT now.
        ( gdm_by_ogtt ->
            Result = _{verdict: gdm, evidence: ['OGTT positive']}
        ;
            % OGTT negative in-window: assess background risk to inform classification
            ( risk_factors_present ->
                Result = _{verdict: low_risk, evidence: ['OGTT negative','risk_factors_present']}
            ;
                Result = _{verdict: low_risk, evidence: ['OGTT negative']}
            )
        )
    ; Week < 24.0 ->
        % Early pregnancy: collect risk factors to decide on early screening
        ( risk_factors_present ->
            ( gdm_by_ogtt ->
                Result = _{verdict: gdm, evidence: ['early_OGTT_positive']}
            ;
                % Early OGTT negative but symptoms may prompt a confidence rating
                ( ask_boolean('Do you experience excessive thirst beyond what is typical for pregnancy?') -> Thirst = true ; Thirst = false ),
                ( ask_boolean('Do you have unusually frequent urination beyond what is typical for pregnancy?') -> Polyuria = true ; Polyuria = false ),
                ( (Thirst == true ; Polyuria == true) ->
                    ask_range('On a scale from 1 to 10, how confident are you in your recent dietary control?', 1.0, 10.0, Confidence),
                    Result = _{verdict: low_risk, evidence: ['early_OGTT_negative', confidence-Confidence]}
                ;
                    Result = _{verdict: low_risk, evidence: ['early_OGTT_negative']}
                )
            )
        ;
            Result = _{verdict: low_risk, note: 'no_early_screening_indicated'}
        )
    ;
        % Week > 28.0: screening window passed; check whether OGTT was already performed
        ( ask_boolean('Have you already had a 75-gram OGTT during this pregnancy?') ->
            ( gdm_by_ogtt ->
                Result = _{verdict: gdm, evidence: ['OGTT positive'], gestational_week: Week}
            ;
                Result = _{verdict: low_risk, evidence: ['OGTT negative'], gestational_week: Week}
            )
        ;
            Result = _{verdict: low_risk, note: 'screening_window_passed_no_test', gestational_week: Week}
        )
    ).