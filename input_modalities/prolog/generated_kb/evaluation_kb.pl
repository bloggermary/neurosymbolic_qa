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

/*
Predicate design:
- diagnose/1 is the single entrypoint. It returns a dictionary describing the verdict and any supporting evidence.
- The workflow asks only the minimum needed values to reach a conclusion. It stops when a decisive conclusion (diabetes or prediabetes when justified) is reached.
*/

diagnose(Result) :-
    ( random_plasma_glucose_criterion(Result) ->
        true
    ; fasting_glucose_criterion(Result) ->
        true
    ; ogtt_2h_criterion(Result) ->
        true
    ; hba1c_criterion(Result) ->
        true
    ; symptom_assessment(Result) ->
        true
    ; Result = _{verdict: no_evidence_of_diabetes, evidence: []}
    ).

/* Random plasma glucose >= 200 mg/dL (≥ 11.1 mmol/L) */
random_plasma_glucose_criterion(_{verdict: diabetes, evidence: [E]}) :-
    ( ask_boolean('Do you have a random plasma glucose measurement in mg/dL?')
      -> Has = true
      ;  Has = false
    ),
    Has == true,
    ask_numeric('What is the random plasma glucose value in mg/dL?', V),
    ( V >= 200.0 ->
        E = _{type: random_plasma_glucose, value: V, unit: mg_per_dl}
    ;  fail ).

/* Fasting plasma glucose after 8-12 hours fasting:
   - >=126 mg/dL -> diabetes
   - 100-125 mg/dL -> prediabetes unless other diabetes-specific tests are available */
fasting_glucose_criterion(Result) :-
    ( ask_boolean('Do you have a fasting plasma glucose measurement in mg/dL?')
      -> Has = true
      ;  Has = false
    ),
    Has == true,
    ask_numeric('What is the fasting plasma glucose value in mg/dL?', V),
    ( ask_boolean('Was this obtained after 8-12 hours of fasting?')
      -> ProperFast = true
      ;  ProperFast = false
    ),
    ProperFast == true,
    ( V >= 126.0 ->
        Result = _{verdict: diabetes, evidence: [_{type: fasting_plasma_glucose, value: V, unit: mg_per_dl}]}
    ; V >= 100.0, V =< 125.0 ->
        % Prediabetes range; ask whether other diabetes-specific tests are available.
        ( ask_boolean('Do you have other diabetes-specific lab tests available (random glucose, 2-hour OGTT, or HbA1c)?')
          -> Other = true
          ;  Other = false
        ),
        ( Other == false ->
            Result = _{verdict: prediabetes, evidence: [_{type: fasting_plasma_glucose, value: V, unit: mg_per_dl}]}
        ;  fail )
    ; fail ).

/* 2-hour plasma glucose during OGTT >= 200 mg/dL (≥ 11.1 mmol/L) */
ogtt_2h_criterion(_{verdict: diabetes, evidence: [E]}) :-
    ( ask_boolean('Do you have a 2-hour plasma glucose value from an oral glucose tolerance test (OGTT) in mg/dL?')
      -> Has = true
      ;  Has = false
    ),
    Has == true,
    ask_numeric('What is the 2-hour OGTT plasma glucose value in mg/dL?', V),
    ( V >= 200.0 ->
        E = _{type: ogtt_2h_plasma_glucose, value: V, unit: mg_per_dl}
    ;  fail ).

/* HbA1c >= 6.5% (48 mmol/mol) */
hba1c_criterion(_{verdict: diabetes, evidence: [E]}) :-
    ( ask_boolean('Do you have an HbA1c measurement in percent?')
      -> Has = true
      ;  Has = false
    ),
    Has == true,
    ask_numeric('What is the HbA1c value (percent)?', V),
    ( V >= 6.5 ->
        E = _{type: hba1c, value_percent: V}
    ;  fail ).

/* Symptom-based assessment when numeric evidence is absent or non-decisive.
   Symptoms alone do not establish a diagnosis but provide support.
   Present the full symptom checklist at once and allow multiple selection. */
symptom_assessment(_{verdict: possible_diabetes_by_symptoms, support: Support, symptoms: Symptoms, details: Details}) :-
    ask_multiple_category('Please select all current symptoms that apply (excessive thirst, excessive urination, fatigue, blurred vision):',
                          [excessive_thirst, excessive_urination, fatigue, blurred_vision],
                          Symptoms),
    % Determine support level
    ( member(excessive_thirst, Symptoms), member(excessive_urination, Symptoms) ->
        Support = strong
    ; ( member(excessive_thirst, Symptoms) ; member(excessive_urination, Symptoms) ) ->
        Support = partial
    ; Support = none ),
    % Ask additional targeted questions only when relevant
    ( member(fatigue, Symptoms) ->
        ask_range('On a scale of 1 to 10, how severe is your fatigue?', 1.0, 10.0, FatigueScore),
        ( FatigueScore >= 7.0 -> FatigueSeverity = severe
        ; FatigueScore >= 4.0 -> FatigueSeverity = moderate
        ; FatigueSeverity = mild )
    ; FatigueSeverity = not_reported ),
    ( member(excessive_thirst, Symptoms) ->
        ask_category('How would you describe your thirst severity?', [none, mild, moderate, severe], ThirstSeverity)
    ; ThirstSeverity = not_reported ),
    % If more than one symptom is present, ask for order of appearance
    ( length(Symptoms, N), N > 1 ->
        ask_multi_structured_input('Please list the symptoms in the order they first appeared, from earliest to most recent.', 'sequence',
                                   [[excessive_thirst],[excessive_urination],[fatigue],[blurred_vision]],
                                   OnsetOrder)
    ; OnsetOrder = [] ),
    Details = _{fatigue_severity: FatigueSeverity, thirst_severity: ThirstSeverity, onset_order: OnsetOrder}.

/* If diabetes is concluded, optionally record current diabetes medications (one or more structured entries) */
record_medications_if_present(Diagnosis, ResultWithMeds) :-
    Diagnosis = _{verdict: diabetes} ->
        ( ask_boolean('Is the patient currently taking any diabetes medication?')
          -> Taking = true
          ;  Taking = false
        ),
        ( Taking == true ->
            ask_multi_attribute_entity('For each diabetes medication, provide name, dose in mg, and times per day.', medication,
                                       [
                                           [name, 'Medication name', string],
                                           [dose_mg, 'Dose in mg', float],
                                           [times_per_day, 'How many times per day is it taken?', float]
                                       ],
                                       MedList),
            ResultWithMeds = Diagnosis.put(evidence, Diagnosis.evidence ++ [_{medications: MedList}])
        ; ResultWithMeds = Diagnosis )
    ; ResultWithMeds = Diagnosis.