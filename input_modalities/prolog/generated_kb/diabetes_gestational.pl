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


/* OGTT numeric criteria predicates */
fasting_glucose_mgdl(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value).

one_hour_glucose_mgdl(Value) :-
    ask_numeric('1-hour post-load plasma glucose (mg/dL)?', Value).

two_hour_glucose_mgdl(Value) :-
    ask_numeric('2-hour post-load plasma glucose (mg/dL)?', Value).

/* Gestational week bounded between 4 and 42 */
gestational_week(Week) :-
    ask_range('Current week of gestation (weeks)', 4, 42, Week).

/* Risk factor collection */
prior_gdm(Category) :-
    ask_category('Previous gestational diabetes?', [none,this_pregnancy,previous_pregnancy], Category).

pcos_history(Flag) :-
    ( ask_boolean('History of polycystic ovary syndrome (PCOS)?') -> Flag = true ; Flag = false ).

prepregnancy_bmi_category(Category) :-
    ask_category('Pre-pregnancy BMI category?', [normal,overweight,obese,severely_obese], Category).

first_degree_relative_diabetes(Flag) :-
    ( ask_boolean('First-degree relative with type 2 diabetes?') -> Flag = true ; Flag = false ).

/* Symptom booleans */
excessive_thirst(Flag) :-
    ( ask_boolean('Excessive thirst beyond what is typical in pregnancy?') -> Flag = true ; Flag = false ).

frequent_urination(Flag) :-
    ( ask_boolean('Unusually frequent urination beyond what is typical in pregnancy?') -> Flag = true ; Flag = false ).

/* Postpartum testing status */
postpartum_testing_status(Status) :-
    ask_category('Postpartum testing status?', [not_yet_tested,normal,prediabetes,overt_diabetes], Status).

/* Determine if early screening (before 24 weeks) is warranted based on risk factors */
early_screening_warranted :-
    prior_gdm(P) , P == previous_pregnancy.
early_screening_warranted :-
    pcos_history(true).
early_screening_warranted :-
    prepregnancy_bmi_category(C) , member(C, [overweight,obese,severely_obese]).
early_screening_warranted :-
    first_degree_relative_diabetes(true).

/* Check OGTT values in order and stop on first numeric threshold met */
check_ogtt(Result, TriggerValue) :-
    fasting_glucose_mgdl(F),
    ( F >= 92 -> Result = positive_fasting, TriggerValue = fasting(F)
    ; one_hour_glucose_mgdl(H1),
      ( H1 >= 180 -> Result = positive_1h, TriggerValue = one_hour(H1)
      ; two_hour_glucose_mgdl(H2),
        ( H2 >= 153 -> Result = positive_2h, TriggerValue = two_hour(H2)
        ; Result = negative, TriggerValue = all_values(fasting(F), one_hour(H1), two_hour(H2))
        )
      )
    ).

/* Mild elevation heuristic: within 20 mg/dL above the diagnostic threshold */
mildly_elevated(fasting(F)) :-
    F >= 92, F =< 112.
mildly_elevated(one_hour(H1)) :-
    H1 >= 180, H1 =< 200.
mildly_elevated(two_hour(H2)) :-
    H2 >= 153, H2 =< 173.

/* Main diagnostic workflow: single clause performing full multi-modal collection.
   Stops asking further numeric OGTT thresholds as soon as one threshold is met,
   but always collects the supporting clinical picture. */
diagnose(diagnosis_summary(Verdict, Symptoms, RiskProfile, OGTTResult, Week, DietaryConfidence, PostpartumStatus)) :-
    /* collect risk factors before deciding on early screening */
    prior_gdm(PriorGDM),
    pcos_history(PCOSFlag),
    prepregnancy_bmi_category(BMICat),
    first_degree_relative_diabetes(FDRFlag),
    RiskProfile = risk_profile{prior_gdm:PriorGDM, pcos:PCOSFlag, bmi:BMICat, first_degree_relative:FDRFlag},

    /* gestational week (bounded 4-42) */
    gestational_week(Week),

    /* decide whether OGTT screening is interpretable now */
    ( Week >= 24, Week =< 28 -> ScreeningAllowed = true
    ; Week < 24, early_screening_warranted -> ScreeningAllowed = true
    ; ScreeningAllowed = false
    ),

    /* perform OGTT numeric checks only if screening is allowed */
    ( ScreeningAllowed ->
        ( check_ogtt(OGTTOutcome, TriggerValue),
          OGTTResult = ogtt{outcome:OGTTOutcome, trigger:TriggerValue}
        )
    ; OGTTResult = ogtt{outcome:not_interpretable, trigger:none}
    ),

    /* collect symptoms regardless of numeric outcome */
    excessive_thirst(ThirstFlag),
    frequent_urination(UrinationFlag),
    Symptoms = symptoms{excessive_thirst:ThirstFlag, frequent_urination:UrinationFlag},

    /* If OGTT positive and mildly elevated, ask dietary confidence scale; otherwise mark not_asked */
    ( OGTTResult = ogtt{outcome:positive_fasting, trigger:Trigger}, mildly_elevated(Trigger) ->
        ask_scale('On a scale of 1-10, how confident are you in your recent dietary control?', DC),
        DietaryConfidence = some(DC)
    ; OGTTResult = ogtt{outcome:positive_1h, trigger:Trigger}, mildly_elevated(Trigger) ->
        ask_scale('On a scale of 1-10, how confident are you in your recent dietary control?', DC1),
        DietaryConfidence = some(DC1)
    ; OGTTResult = ogtt{outcome:positive_2h, trigger:Trigger2}, mildly_elevated(Trigger2) ->
        ask_scale('On a scale of 1-10, how confident are you in your recent dietary control?', DC2),
        DietaryConfidence = some(DC2)
    ; DietaryConfidence = not_asked
    ),

    /* postpartum testing status (follow-up) */
    postpartum_testing_status(PostpartumStatus),

    /* Final verdict determination */
    ( OGTTResult = ogtt{outcome:positive_fasting, trigger:_}
    ; OGTTResult = ogtt{outcome:positive_1h, trigger:_}
    ; OGTTResult = ogtt{outcome:positive_2h, trigger:_}
    ) -> Verdict = gdm
    ; OGTTResult = ogtt{outcome:negative, trigger:_} -> Verdict = no_gdm
    ; ScreeningAllowed = false -> Verdict = indeterminate
    ; Verdict = no_gdm.

/* Convenience predicates that run the full diagnostic workflow and succeed/fail accordingly */

diabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(Verdict, _, _, _, _, _, _),
    Verdict == gdm.

prediabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(_, _, _, _, _, _, Postpartum),
    Postpartum == prediabetes.

low_risk :-
    diagnose(Summary),
    Summary = diagnosis_summary(Verdict, _, _, OGTTResult, _, _, Postpartum),
    Verdict \== gdm,
    ( OGTTResult = ogtt{outcome:negative, trigger:_} ; OGTTResult = ogtt{outcome:not_interpretable, trigger:_} ),
    ( Postpartum == normal ; Postpartum == not_yet_tested ; Postpartum == not_yet_tested ).