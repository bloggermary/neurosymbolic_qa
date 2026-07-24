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

% Standalone criterion: fasting OGTT criterion (>= 92 mg/dL)
gdm_ogtt_fasting :-
    ask_range('What is your current week of gestation in weeks?', 4.0, 42.0, Week),
    ( (Week >= 24.0, Week =< 28.0) ->
        true
    ; ( Week < 24.0 ->
          early_screening_risk
      ; fail
      )
    ),
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 92.0 ->
        nb_setval(gdm_evidence, _{verdict:gestational_diabetes, criterion:fasting, week:Week, fasting:Fasting})
    ; fail ).

% Standalone criterion: 1-hour OGTT criterion (>= 180 mg/dL)
gdm_ogtt_1h :-
    ask_range('What is your current week of gestation in weeks?', 4.0, 42.0, Week),
    ( (Week >= 24.0, Week =< 28.0) ->
        true
    ; ( Week < 24.0 ->
          early_screening_risk
      ; fail
      )
    ),
    ask_numeric('What is your 1-hour post-load plasma glucose in mg/dL?', OneHour),
    ( OneHour >= 180.0 ->
        nb_setval(gdm_evidence, _{verdict:gestational_diabetes, criterion:one_hour, week:Week, one_hour:OneHour})
    ; fail ).

% Standalone criterion: 2-hour OGTT criterion (>= 153 mg/dL)
gdm_ogtt_2h :-
    ask_range('What is your current week of gestation in weeks?', 4.0, 42.0, Week),
    ( (Week >= 24.0, Week =< 28.0) ->
        true
    ; ( Week < 24.0 ->
          early_screening_risk
      ; fail
      )
    ),
    ask_numeric('What is your 2-hour post-load plasma glucose in mg/dL?', TwoHour),
    ( TwoHour >= 153.0 ->
        nb_setval(gdm_evidence, _{verdict:gestational_diabetes, criterion:two_hour, week:Week, two_hour:TwoHour})
    ; fail ).

% Determine whether early screening (before 24 weeks) is warranted by risk factors.
early_screening_risk :-
    ask_category('Have you had gestational diabetes before this or a previous pregnancy?', [none, this_pregnancy, previous_pregnancy], PrevGDM),
    ( PrevGDM == previous_pregnancy ->
        true
    ; true
    ),
    ( PrevGDM == previous_pregnancy -> true
    ; ( ask_boolean('Do you have a history of polycystic ovary syndrome (PCOS)?') -> PCOS = true ; PCOS = false ),
      ( PCOS == true -> true
      ; ask_category('What was your pre-pregnancy body mass index category?', [normal, overweight, obese, severely_obese], BMIcat),
        ( BMIcat == overweight ; BMIcat == obese ; BMIcat == severely_obese ) ->
          true
      ; ( ask_boolean('Do you have a first-degree relative with type 2 diabetes?') -> FDR = true ; FDR = false ),
        ( FDR == true -> true
        ; ask_numeric('What is your age in years?', Age),
          ( Age >= 35.0 -> true
          ; ( ask_boolean('Is this a multiple pregnancy (twins or higher)?') -> Multiple = true ; Multiple = false ),
            Multiple == true
          )
        )
      )
    ).

% Helper that succeeds only when none of the early-screening risk factors are present.
early_screening_risk_false :-
    ask_category('Have you had gestational diabetes before this or a previous pregnancy?', [none, this_pregnancy, previous_pregnancy], PrevGDM),
    PrevGDM == none,
    ( ask_boolean('Do you have a history of polycystic ovary syndrome (PCOS)?') -> PCOS = true ; PCOS = false ),
    PCOS == false,
    ask_category('What was your pre-pregnancy body mass index category?', [normal, overweight, obese, severely_obese], BMIcat),
    BMIcat == normal,
    ( ask_boolean('Do you have a first-degree relative with type 2 diabetes?') -> FDR = true ; FDR = false ),
    FDR == false,
    ask_numeric('What is your age in years?', Age),
    Age < 35.0,
    ( ask_boolean('Is this a multiple pregnancy (twins or higher)?') -> Multiple = true ; Multiple = false ),
    Multiple == false.

% Check whether an OGTT performed now would be interpretable (24-28 weeks, or <24 with risk factors).
ogtt_interpretable_standalone :-
    ask_range('What is your current week of gestation in weeks?', 4.0, 42.0, Week),
    ( (Week >= 24.0, Week =< 28.0) ->
        true
    ; ( Week < 24.0 ->
          early_screening_risk
      ; fail
      )
    ).

% Postpartum classification predicate (standalone)
postpartum_status(Status) :-
    ask_category('What is your postpartum testing status, if tested?', [not_yet_tested, normal, prediabetes, overt_diabetes], Status).

% Predicate answering whether diabetes (overt) is present based on postpartum reclassification
diabetes :-
    postpartum_status(Status),
    Status == overt_diabetes.

% Predicate answering whether prediabetes is present based on postpartum reclassification
prediabetes :-
    postpartum_status(Status),
    Status == prediabetes.

% Predicate for low risk: no OGTT criteria met, no risk factors, no typical symptoms
low_risk :-
    ogtt_interpretable_standalone,
    % ask OGTT values but stop if any diagnostic threshold is met
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Fasting),
    ( Fasting >= 92.0 -> fail ; true ),
    ask_numeric('What is your 1-hour post-load plasma glucose in mg/dL?', OneHour),
    ( OneHour >= 180.0 -> fail ; true ),
    ask_numeric('What is your 2-hour post-load plasma glucose in mg/dL?', TwoHour),
    ( TwoHour >= 153.0 -> fail ; true ),
    early_screening_risk_false,
    ( ask_boolean('Do you have excessive thirst?') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Do you have unusually frequent urination beyond what is typical in pregnancy?') -> Polyuria = true ; Polyuria = false ),
    Thirst == false,
    Polyuria == false.

% Pre-pregnancy weight gain to date (kg) - asked only when called
pre_pregnancy_weight_gain(GainKg) :-
    ask_numeric('What is your pre-pregnancy weight gain to date in kilograms?', GainKg).

% Postpartum test timing: whether retest occurred within 6-12 weeks
postpartum_retest_within_window :-
    ask_numeric('How many weeks after delivery was the postpartum test performed?', WeeksAfter),
    WeeksAfter >= 6.0,
    WeeksAfter =< 12.0.

% Ask for patient confidence in recent dietary control on a 1-10 scale
confidence_in_diet(ControlRating) :-
    ask_range('On a scale from 1 to 10, how confident are you in your recent dietary control?', 1.0, 10.0, ControlRating).

% Symptoms (standalone predicates)
excessive_thirst :-
    ( ask_boolean('Do you experience excessive thirst?') -> true ; fail ).

frequent_urination_beyond_pregnancy_typical :-
    ( ask_boolean('Do you have unusually frequent urination beyond what is typical in pregnancy?') -> true ; fail ).

% Main diagnosis workflow: tries OGTT criteria in order and stops at first diagnostic threshold met.
diagnose(Result) :-
    ( gdm_ogtt_fasting ->
        nb_getval(gdm_evidence, Evidence),
        Result = Evidence
    ; gdm_ogtt_1h ->
        nb_getval(gdm_evidence, Evidence),
        Result = Evidence
    ; gdm_ogtt_2h ->
        nb_getval(gdm_evidence, Evidence),
        Result = Evidence
    ; % No OGTT diagnostic criterion met; gather minimal additional information to classify or rule out
        ( postpartum_status(PostStatus) -> true ; PostStatus = not_yet_tested ),
        ( PostStatus == overt_diabetes ->
            Result = _{verdict:diabetes, source:postpartum, postpartum:PostStatus}
        ; PostStatus == prediabetes ->
            Result = _{verdict:prediabetes, postpartum:PostStatus}
        ; % otherwise report low risk or need for OGTT depending on gestation and risk factors
            ask_range('What is your current week of gestation in weeks?', 4.0, 42.0, Week),
            ( (Week >= 24.0, Week =< 28.0) ->
                % within standard screening window but no diagnostic threshold met
                ( early_screening_risk ->
                    Result = _{verdict:non_diagnostic_but_at_risk, week:Week}
                ; Result = _{verdict:low_risk, week:Week}
                )
            ; ( Week < 24.0 ->
                  ( early_screening_risk ->
                      Result = _{verdict:consider_early_screening, week:Week}
                  ; Result = _{verdict:defer_routine_screening, week:Week}
                  )
              ; % Week >28
                  Result = _{verdict:screening_out_of_typical_window, week:Week}
              )
        )
    )).