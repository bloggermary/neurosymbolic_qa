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

% emergency_present/0
% Succeeds if the child has any emergency symptoms (nausea, vomiting, abdominal pain, rapid breathing).
emergency_present :-
    ( ask_boolean('Has the child experienced any of the following: nausea, vomiting, abdominal pain, or rapid breathing?')
      -> true
      ;  false
    ).

% collect_dka_parameters(-Dict)
% Asks venous pH and serum bicarbonate only when called (used when emergency suspected).
collect_dka_parameters(_{pH:PH, bicarbonate:Bicarb}) :-
    ( ask_numeric('If available, what is the venous blood pH? (enter numeric value, or -1 if not available)', PH0)
      -> ( PH0 >= 0 -> PH = PH0 ; PH = null )
      ;  PH = null
    ),
    ( ask_numeric('If available, what is the serum bicarbonate (mEq/L)? (enter numeric value, or -1 if not available)', B0)
      -> ( B0 >= 0 -> Bicarb = B0 ; Bicarb = null )
      ;  Bicarb = null
    ).

% glycemic_diagnostic(-Evidence)
% Succeeds if any glycemic threshold for diabetes is met. Evidence includes which test and measured value.
glycemic_diagnostic(_{test:random_plasma, value:Val}) :-
    ( ask_boolean('Do you have a random (non-fasting) plasma glucose value in mg/dL?')
      -> HasRandom = true ; HasRandom = false
    ),
    HasRandom == true,
    ask_numeric('Enter the random plasma glucose in mg/dL', Val),
    Val >= 200.
glycemic_diagnostic(_{test:fasting_plasma, value:Val}) :-
    ( ask_boolean('Do you have a fasting plasma glucose value in mg/dL?')
      -> HasFasting = true ; HasFasting = false
    ),
    HasFasting == true,
    ask_numeric('Enter the fasting plasma glucose in mg/dL', Val),
    Val >= 126.
glycemic_diagnostic(_{test:hba1c_percent, value:Val}) :-
    ( ask_boolean('Do you have an HbA1c value (percent)?')
      -> HasHba1c = true ; HasHba1c = false
    ),
    HasHba1c == true,
    ask_numeric('Enter the HbA1c value (as percent)', Val),
    Val >= 6.5.

% classic_triad_present/0
% Succeeds if the child has the classic symptom triad (polyuria, polydipsia, unexplained weight loss).
classic_triad_present :-
    ( ask_boolean('Does the child have polyuria, polydipsia, and unexplained weight loss (all three present)?')
      -> true
      ;  false
    ).

% rapid_onset/0
% Succeeds if symptoms have been present for less than two weeks.
rapid_onset :-
    ask_duration('How many days have the symptoms been present?', Days),
    Days < 14.

% autoantibody_positive(-Positives)
% Asks which autoantibody tests are positive. Succeeds if any of GAD65, IA-2, or ZnT8 are positive.
autoantibody_positive(Positives) :-
    ask_multiple_category('Which of the following autoantibody tests are positive? Select all that apply.', ['gad65','ia2','znt8','none','not_tested'], AnswerList),
    AnswerList \== [],
    findall(A, (member(A, AnswerList), member(A, ['gad65','ia2','znt8'])), Positives),
    Positives \== [].

% medication_status(-Status)
% Asks current diabetes medication status: none, insulin, or unknown.
medication_status(Status) :-
    ask_category('What is the child''s diabetes medication status?', ['none','insulin','unknown'], Status).

% weight_loss_last_month(-Kg)
% Ask weight loss over the preceding month in kg (asked only when called).
weight_loss_last_month(Kg) :-
    ask_numeric('How much weight has the child lost over the preceding month (kg)? Enter 0 if none or -1 if unknown', V0),
    ( V0 >= 0 -> Kg = V0 ; Kg = unknown ).

% height_weight_percentiles(-HeightP, -WeightP)
% Optional supplementary details; asked only when called.
height_weight_percentiles(HeightP, WeightP) :-
    ( ask_numeric('Enter height percentile-for-age (as a plain number, or -1 if unknown)', H0)
      -> ( H0 >= 0 -> HeightP = H0 ; HeightP = unknown )
      ;  HeightP = unknown
    ),
    ( ask_numeric('Enter weight percentile-for-age (as a plain number, or -1 if unknown)', W0)
      -> ( W0 >= 0 -> WeightP = W0 ; WeightP = unknown )
      ;  WeightP = unknown
    ).

% diagnose(-Result)
% Single entry point for the complete workflow. Returns a dictionary with a verdict and supporting evidence.
diagnose(_{verdict:dka_emergency, evidence:Evidence}) :-
    emergency_present,
    collect_dka_parameters(Params),
    Evidence = [emergency_symptoms_present(true), Params],
    !.
diagnose(_{verdict:type1_diabetes, evidence:Evidence}) :-
    % Glycemic diagnostic criteria met
    glycemic_diagnostic(GlycEvidence),
    % Check supporting features in order; stop when one supports type 1 classification
    ( autoantibody_positive(PosList)
      -> Evidence = [glycemic: GlycEvidence, autoantibodies: PosList]
    ; medication_status(Status),
      Status == insulin
      -> Evidence = [glycemic: GlycEvidence, medication: insulin]
    ; classic_triad_present,
      rapid_onset
      -> Evidence = [glycemic: GlycEvidence, clinical_presentation: rapid_classic_triad]
    ),
    !.
diagnose(_{verdict:diabetes_needs_classification, evidence:[glycemic: GlycEvidence]}) :-
    % Glycemic diagnostic criteria met but no immediate supporting classification features found
    glycemic_diagnostic(GlycEvidence),
    % confirm that prior classification checks fail
    ( \+ autoantibody_positive(_) ),
    medication_status(Status2),
    Status2 \== insulin,
    ( \+ (classic_triad_present, rapid_onset) ),
    !.
diagnose(_{verdict:probable_type1, evidence:Evidence}) :-
    % No glycemic confirmation but clinical picture strongly suggests type 1
    \+ glycemic_diagnostic(_),
    classic_triad_present,
    rapid_onset,
    Evidence = [clinical_presentation: rapid_classic_triad],
    !.
diagnose(_{verdict:no_evidence_for_type1, evidence:[]}) :-
    % No criteria met for type 1 or diabetes from available information
    \+ emergency_present,
    \+ glycemic_diagnostic(_),
    \+ (classic_triad_present, rapid_onset).