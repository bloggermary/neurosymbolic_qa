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

/* Standalone numeric diagnostic threshold criteria.
   Each predicate asks what it needs and succeeds only if the threshold is met.
*/

random_glucose_criterion :-
    ask_numeric('What is the random plasma glucose in mg/dL?', Value),
    ( Value >= 200.0 -> true ; fail ).

fasting_glucose_criterion :-
    ask_numeric('What is the fasting plasma glucose in mg/dL?', Value),
    ( Value >= 126.0 -> true ; fail ).

hba1c_criterion :-
    ask_numeric('What is the HbA1c percentage?', Value),
    ( Value >= 6.5 -> true ; fail ).

/* Diabetic ketoacidosis (DKA) emergency symptom check.
   Succeeds if any emergency symptom is present.
*/
diabetic_ketoacidosis_suspected :-
    ask_multiple_category(
      'Has the child experienced any of the following symptoms: nausea, vomiting, abdominal pain, or rapid breathing?',
      [nausea, vomiting, abdominal_pain, rapid_breathing],
      Answer),
    ( Answer = [] -> fail ; true ).

/* Autoantibody testing status. Asks results for three antibodies and succeeds if any is positive. */
autoantibodies_positive :-
    Fields = [
      [gad65, 'Result for GAD65 antibody (positive/negative/not_tested)?', category],
      [ia2,   'Result for IA-2 antibody (positive/negative/not_tested)?', category],
      [znt8,  'Result for ZnT8 antibody (positive/negative/not_tested)?', category]
    ],
    ask_multi_attribute_entity('Please provide antibody test results for the child', antibodies, Fields, Resp),
    Data = Resp.data,
    ( Data.gad65 == positive ; Data.ia2 == positive ; Data.znt8 == positive ).

/* Classic symptom triad (polyuria, polydipsia, unexplained weight loss).
   Succeeds only if all three are reported. */
classic_symptom_triad :-
    ask_multiple_category(
      'Which of these classic symptoms does the child have: polyuria, polydipsia, unexplained weight loss?',
      [polyuria, polydipsia, unexplained_weight_loss],
      Answer),
    member(polyuria, Answer),
    member(polydipsia, Answer),
    member(unexplained_weight_loss, Answer).

/* Additional boolean symptoms that may be checked individually. */
nocturnal_bedwetting_present :-
    ( ask_boolean('Has the child had nocturnal bedwetting despite previous toilet training?') -> true ; fail ).

lethargy_present :-
    ( ask_boolean('Has the child been unusually lethargic or drowsy?') -> true ; fail ).

/* Severity of dehydration on a 1-10 scale. Standalone asks and succeeds (value not returned). */
dehydration_severity_reported :-
    ask_range('On a scale of 1 to 10, how severe is the child''s dehydration (1 = mild, 10 = severe shock)?', 1.0, 10.0, _).

/* Family history and medication status as categorical standalone checks. */
family_history_status(Status) :-
    ask_category('Does the child have a family history of type 1 diabetes?', [none, first_degree, second_degree], Status).

medication_status(Status) :-
    ask_category('What is the child''s diabetes medication status?', [none, insulin, unknown], Status).

/* Weight loss amount over preceding month (asked only when helpful). */
weight_loss_amount_reported :-
    ask_numeric('How many kilograms of unexplained weight loss have occurred over the preceding month?', _).

/* Prediabetes standalone check (uses commonly accepted thresholds; asked only if invoked). */
prediabetes :-
    ( ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting),
      Fasting >= 100.0, Fasting < 126.0 -> true
    ; ask_numeric('What is the HbA1c percentage?', HbA1c),
      HbA1c >= 5.7, HbA1c < 6.5 -> true
    ; ask_numeric('What is the random plasma glucose in mg/dL?', Random),
      Random >= 140.0, Random < 200.0 -> true
    ).

/* Low risk: neither diabetes nor prediabetes and no acute/emergency picture.
   This asks only what's necessary to exclude the others. */
low_risk :-
    \+ random_glucose_criterion,
    \+ fasting_glucose_criterion,
    \+ hba1c_criterion,
    \+ diabetic_ketoacidosis_suspected,
    \+ classic_symptom_triad,
    \+ prediabetes.

/* Main diagnostic workflow.
   Returns a janus-safe result (atom or top-level dict built from atoms/numbers/lists/pairs).
   The dialogue is adaptive: it asks emergency symptoms first, then the simplest numeric thresholds
   in sequence and stops as soon as a decisive threshold is met. Only when numeric criteria are
   not diagnostic does it ask for symptom-based supporting information.
*/
diagnose(Result) :-
    /* 1) Emergency check for DKA signs - immediate referral if present. */
    ask_multiple_category(
      'Has the child experienced any of the following symptoms: nausea, vomiting, abdominal pain, or rapid breathing?',
      [nausea, vomiting, abdominal_pain, rapid_breathing],
      EmergencySymptoms),
    ( EmergencySymptoms \= [] ->
        /* Ask DKA grading labs only when emergency symptoms are present. */
        ask_numeric('If available, what is the child''s venous blood pH?', PH),
        ask_numeric('If available, what is the child''s serum bicarbonate in mEq/L?', Bicarb),
        Result = _{verdict: dka_suspected,
                   immediate_referral: true,
                   emergency_symptoms: EmergencySymptoms,
                   venous_pH: PH,
                   serum_bicarbonate_mEq_per_L: Bicarb}
    ;
        /* 2) Sequential numeric diagnostic thresholds (stop when one proves diagnosis). */
        ( ask_numeric('What is the random plasma glucose in mg/dL?', Random) ,
          ( Random >= 200.0 ->
                Result = _{verdict: diabetes, evidence: [random_plasma_glucose]}
          ;
                /* Only ask fasting if random not diagnostic. */
                ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting),
                ( Fasting >= 126.0 ->
                      Result = _{verdict: diabetes, evidence: [fasting_plasma_glucose]}
                ;
                      /* Only ask HbA1c if fasting not diagnostic. */
                      ask_numeric('What is the HbA1c percentage?', HbA1c),
                      ( HbA1c >= 6.5 ->
                            Result = _{verdict: diabetes, evidence: [hba1c]}
                      ;
                            /* 3) Numeric thresholds not met — gather targeted supporting evidence adaptively. */
                            /* Check classic triad and duration (rapid onset <2 weeks supports type 1). */
                            ( ask_multiple_category(
                                'Which of these classic symptoms does the child have: polyuria, polydipsia, unexplained weight loss?',
                                [polyuria, polydipsia, unexplained_weight_loss],
                                TriadAns),
                              member(polyuria, TriadAns),
                              member(polydipsia, TriadAns),
                              member(unexplained_weight_loss, TriadAns) ->
                                  /* Ask duration in days to assess rapid onset. */
                                  ask_duration('How many days have these symptoms been present?', Days),
                                  ( Days < 14.0 ->
                                        Result = _{verdict: probable_type1, evidence: [classic_triads, rapid_onset]}
                                  ;
                                        /* If triad present but not rapid, check autoantibodies as supporting evidence. */
                                        ( autoantibodies_positive ->
                                              Result = _{verdict: probable_type1, evidence: [classic_triads, autoantibodies_positive]}
                                        ;
                                              /* Ask for weight loss amount as additional supporting data. */
                                              ask_boolean('Has there been unexplained weight loss noted by caregivers?') ->
                                                  ask_numeric('How many kilograms of unexplained weight loss have occurred over the preceding month?', WL),
                                                  ( WL > 0.0 ->
                                                        Result = _{verdict: possible_type1, evidence: [classic_triads, weight_loss]}
                                                  ;
                                                        Result = _{verdict: unclear, evidence: [classic_triads]}
                                                  )
                                              ;
                                                  Result = _{verdict: unclear, evidence: [classic_triads]}
                                        )
                                  )
                              ;
                                  /* No triad — consider prediabetes, otherwise low risk. */
                                  ( preding_check(Result) )
                            )
                      )
                )
          )
        )
    ).

/* Helper used only inside diagnose/1 when numeric thresholds and classic triad checks are negative.
   It determines prediabetes or low risk adaptively and produces a janus-safe Result dict. */
preding_check(Result) :-
    /* Ask only what is necessary to evaluate prediabetes: fasting then HbA1c then random. */
    ( ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting) ,
      Fasting >= 100.0, Fasting < 126.0 ->
          Result = _{verdict: prediabetes, evidence: [fasting_plasma_glucose]}
    ; ask_numeric('What is the HbA1c percentage?', HbA1c),
      HbA1c >= 5.7, HbA1c < 6.5 ->
          Result = _{verdict: prediabetes, evidence: [hba1c]}
    ; ask_numeric('What is the random plasma glucose in mg/dL?', Random),
      Random >= 140.0, Random < 200.0 ->
          Result = _{verdict: prediabetes, evidence: [random_plasma_glucose]}
    ;
      /* If none of the above, classify as low risk for diabetes on current information. */
      Result = _{verdict: low_risk}
    ).

/* Convenience wrapper predicates for external queries as requested. */
diabetes :-
    ( random_glucose_criterion ; fasting_glucose_criterion ; hba1c_criterion ).

prediabetes_check :-
    predip_helper.

predip_helper :-
    ( ask_numeric('What is the fasting plasma glucose in mg/dL?', Fasting),
      Fasting >= 100.0, Fasting < 126.0 -> true
    ; ask_numeric('What is the HbA1c percentage?', HbA1c),
      HbA1c >= 5.7, HbA1c < 6.5 -> true
    ; ask_numeric('What is the random plasma glucose in mg/dL?', Random),
      Random >= 140.0, Random < 200.0 -> true
    ; fail ).

/* low_risk/0 public predicate */
low_risk :-
    \+ diabetes,
    \+ predip_helper,
    \+ diabetic_ketoacidosis_suspected.