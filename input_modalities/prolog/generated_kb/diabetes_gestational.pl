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
  diagnose/1 is the single entry point.
  It asks whether this is a postpartum reclassification first.
  If postpartum, it performs postpartum logic and returns a dict with the classification and evidence.
  If not postpartum, it asks gestational week and follows screening logic:
    - If week between 24 and 28 inclusive, perform 75-g OGTT interpretation.
    - If week < 24, collect risk factors to decide whether early screening is warranted; if warranted, perform OGTT interpretation.
    - If week > 28, screening interpretation is considered outside the standard window and no OGTT interpretation is performed.
*/
diagnose(Result) :-
    ( ask_boolean('Has delivery already occurred and is this a postpartum reclassification?')
      -> postpartum_reclassification(Result)
      ;  gestational_screening(Result)
    ).

/* Postpartum reclassification.
   Asks for postpartum test category and weeks after delivery.
   If weeks in 6..12 inclusive, the result is considered reliable for reclassification.
   Otherwise it is flagged as outside the reliable window.
*/
postpartum_reclassification(Result) :-
    ask_category('What is the postpartum testing status?',[not_yet_tested,normal,prediabetes,overt_diabetes], Status),
    ask_numeric('How many weeks after delivery was the postpartum test performed?', Weeks),
    ( Weeks >= 6.0, Weeks =< 12.0
      -> Result = _{verdict: postpartum_reclassification, status: Status, weeks_after_delivery: Weeks}
      ;  Result = _{verdict: postpartum_reclassification_unreliable_window, status: Status, weeks_after_delivery: Weeks}
    ).

/* Gestational screening workflow.
   Asks gestational week (4-42) and routes to appropriate logic.
*/
gestational_screening(Result) :-
    ask_range('What is the current week of gestation (4-42)?', 4, 42, Ga),
    ( Ga >= 24.0, Ga =< 28.0
      -> ogtt_diagnosis(Ga, Result)
    ; Ga < 24.0
      -> early_screening_decision(Ga, Result)
    ; Ga > 28.0
      -> Result = _{verdict: gestational_age_outside_screening_window, gestational_week: Ga}
    ).

/* Early screening decision for gestational age < 24 weeks.
   Collects risk factors and decides whether early OGTT screening is warranted.
   If warranted, performs OGTT diagnosis; otherwise returns that screening is not currently warranted.
*/
early_screening_decision(Ga, Result) :-
    early_screening_warranted(Warranted, Evidence),
    ( Warranted = true
      -> ogtt_diagnosis(Ga, OgttResult),
         Result = OgttResult.put(_{early_screening: true, early_screening_evidence: Evidence})
      ;  Result = _{verdict: screening_not_warranted_yet, gestational_week: Ga, early_screening: false, early_screening_evidence: Evidence}
    ).

/* Collects risk-factor inputs needed to decide about early screening.
   Returns Warranted = true if any single listed risk factor is present.
   Evidence is a dict with the collected risk-factor values.
*/
early_screening_warranted(Warranted, Evidence) :-
    ask_category('Previous gestational diabetes?', [none, this_pregnancy, previous_pregnancy], PrevGdm),
    ( ask_boolean('History of polycystic ovary syndrome (PCOS)?')
      -> Pcos = true
      ;  Pcos = false
    ),
    ask_category('Pre-pregnancy body mass index category?', [normal, overweight, obese, severely_obese], BmiCat),
    ( ask_boolean('Is there a first-degree relative with type 2 diabetes?')
      -> FirstDeg = true
      ;  FirstDeg = false
    ),
    ask_numeric('What is the maternal age in years?', AgeYears),
    ( AgeYears >= 35.0
      -> AgeRisk = true
      ;  AgeRisk = false
    ),
    ( ask_boolean('Is this a multiple pregnancy (twins or higher)?')
      -> Multiple = true
      ;  Multiple = false
    ),
    % Determine if any risk factor is present:
    ( PrevGdm \= none -> ByPrevGdm = true ; ByPrevGdm = false ),
    ( BmiCat \= normal -> ByBmi = true ; ByBmi = false ),
    ( ByPrevGdm = true ; Pcos = true ; ByBmi = true ; FirstDeg = true ; AgeRisk = true ; Multiple = true
      -> WarrantedFlag = true
      ;  WarrantedFlag = false
    ),
    Warranted = WarrantedFlag,
    Evidence = _{previous_gdm: PrevGdm, pcos: Pcos, bmi_category: BmiCat, first_degree_t2d: FirstDeg, maternal_age_years: AgeYears, age_risk_35_or_older: AgeRisk, multiple_pregnancy: Multiple}.

/* OGTT interpretation using the 75-g OGTT thresholds.
   Asks fasting, 1-hour, and 2-hour plasma glucose (mg/dL).
   Diagnoses gestational diabetes if any ONE value meets or exceeds the specified thresholds:
     fasting >= 92 mg/dL
     one_hour >= 180 mg/dL
     two_hour >= 153 mg/dL
*/
ogtt_diagnosis(GestationalWeek, Result) :-
    ask_numeric('What was the fasting plasma glucose (mg/dL)?', Fasting),
    ask_numeric('What was the 1-hour plasma glucose after 75-g load (mg/dL)?', OneHour),
    ask_numeric('What was the 2-hour plasma glucose after 75-g load (mg/dL)?', TwoHour),
    ThresholdF = 92.0,
    Threshold1 = 180.0,
    Threshold2 = 153.0,
    ( Fasting >= ThresholdF
      -> Verdict = gdm, Reason = fasting
    ; OneHour >= Threshold1
      -> Verdict = gdm, Reason = one_hour
    ; TwoHour >= Threshold2
      -> Verdict = gdm, Reason = two_hour
    ; Verdict = no_gdm, Reason = none
    ),
    Result = _{verdict: Verdict,
               positive_criterion: Reason,
               gestational_week: GestationalWeek,
               ogtt_values_mg_per_dl: _{fasting: Fasting, one_hour: OneHour, two_hour: TwoHour},
               thresholds_mg_per_dl: _{fasting: ThresholdF, one_hour: Threshold1, two_hour: Threshold2}
              }.