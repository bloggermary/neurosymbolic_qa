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

/* Criterion predicates: each asks internally for needed values and returns one of:
   positive_reliable, positive_unreliable, negative, unknown
*/

fasting_criterion(Result) :-
    ( ask_boolean('Is a fasting plasma glucose result available? (yes/no)')
      -> Has = true
      ;  Has = false
    ),
    ( Has == true ->
        ask_numeric('Enter fasting plasma glucose (mg/dL):', Value),
        ( Value >= 126.0 -> Result = positive_reliable ; Result = negative )
    ; Result = unknown
    ).

random_criterion(Result) :-
    ( ask_boolean('Is a random plasma glucose result available? (yes/no)')
      -> Has = true
      ;  Has = false
    ),
    ( Has == true ->
        ask_numeric('Enter random plasma glucose (mg/dL):', Value),
        ( Value >= 200.0 -> Result = positive_reliable ; Result = negative )
    ; Result = unknown
    ).

ogtt_criterion(Result) :-
    ( ask_boolean('Is a 2-hour OGTT (oral glucose tolerance test) result available? (yes/no)')
      -> Has = true
      ;  Has = false
    ),
    ( Has == true ->
        ask_numeric('Enter 2-hour OGTT plasma glucose (mg/dL):', Value),
        ( Value >= 200.0 -> Result = positive_reliable ; Result = negative )
    ; Result = unknown
    ).

hba1c_criterion(Result) :-
    ( ask_boolean('Is an HbA1c result available? (yes/no)')
      -> Has = true
      ;  Has = false
    ),
    ( Has == true ->
        ask_numeric('Enter HbA1c (%):', Value),
        ( ( Value >= 6.5 ) ->
            ( ( ask_boolean('Does the patient have chronic kidney disease? (yes/no)') -> CKD = true ; CKD = false ),
              ( ask_boolean('Does the patient have anemia? (yes/no)') -> Anemia = true ; Anemia = false ),
              ( (CKD == true ; Anemia == true) -> Result = positive_unreliable ; Result = positive_reliable )
            )
        ; Result = negative )
    ; Result = unknown
    ).

/* Medication selection and grouping */
medication_selection(Meds) :-
    ask_multiple_category('Select all current contributors that apply (choose all that apply):', ['corticosteroids','thiazide_diuretics','atypical_antipsychotics','none'], Meds).

medication_timing_grouping(Grouping) :-
    ask_multi_structured_input('Group current medications by when they are taken (provide medication names for each group):', grouping, ['morning','afternoon','evening','bedtime'], Grouping).

/* Additional routinely captured items */
capture_egfr(EGFR) :-
    ask_numeric('Enter estimated glomerular filtration rate (eGFR) in mL/min/1.73m2:', EGFR).

capture_chronic_conditions_count(Count) :-
    ask_numeric('How many distinct chronic conditions does the patient have? (plain count):', Count).

capture_cognitive_function(Status) :-
    ask_range('Rate overall cognitive/functional status on a scale 1 (fully independent) to 10 (fully dependent):', 1.0, 10.0, Status).

capture_classic_symptoms(Symptoms) :-
    ( ask_boolean('Excessive thirst? (yes/no)') -> Thirst = true ; Thirst = false ),
    ( ask_boolean('Frequent urination? (yes/no)') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Fatigue? (yes/no)') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Blurred vision? (yes/no)') -> Blurred = true ; Blurred = false ),
    Symptoms = _{thirst:Thirst, frequent_urination:Polyuria, fatigue:Fatigue, blurred_vision:Blurred}.

/* Optional history of prior glucose abnormality */
known_glucose_abnormality_years(Years) :-
    ( ask_boolean('Has the patient had any known glucose abnormality previously? (yes/no)') -> Has = true ; Has = false ),
    ( Has == true ->
        ask_numeric('How many years has the patient had any known glucose abnormality?', Years)
    ; Years = 0.0
    ).

/* Additional numeric checks when evidence is inconclusive */
inconclusive_followup(Assessment) :-
    ask_numeric('Enter systolic blood pressure (mmHg):', Systolic),
    ask_numeric('Enter unintentional weight loss over past 6 months (kg):', WeightLoss),
    Assessment = _{systolic_mmHg:Systolic, weight_loss_kg:WeightLoss}.

/* Helper to determine final decision from criterion results */
any_positive([H|_]) :-
    H = positive_reliable.
any_positive([H|T]) :-
    H \= positive_reliable,
    any_positive(T).

all_known_and_negative([]) :- false.
all_known_and_negative(List) :-
    List \= [],
    forall(member(X, List), X == negative).

/* The single entrypoint for the workflow */
diagnose(Result) :-
    /* capture routine baseline items */
    capture_egfr(EGFR),
    capture_chronic_conditions_count(ChronicCount),
    capture_cognitive_function(CognitiveStatus),
    capture_classic_symptoms(Symptoms),
    known_glucose_abnormality_years(YearsKnown),

    /* evaluate diagnostic criteria */
    fasting_criterion(FastingR),
    random_criterion(RandomR),
    ogtt_criterion(OGTTR),
    hba1c_criterion(HbA1cR),

    Criteria = [FastingR, RandomR, OGTTR, HbA1cR],

    ( % any definitive non-HbA1c glucose test positive -> provisional diagnosis
      ( member(positive_reliable, [FastingR, RandomR, OGTTR]) ) ->
        Provisional = diabetes_by_glucose_test,
        Evidence = [fasting:FastingR, random:RandomR, ogtt:OGTTR, hba1c:HbA1cR]
    ; % HbA1c reliable positive
      HbA1cR == positive_reliable ->
        Provisional = diabetes_by_hba1c,
        Evidence = [fasting:FastingR, random:RandomR, ogtt:OGTTR, hba1c:HbA1cR]
    ; % HbA1c positive but unreliable because of CKD or anemia
      HbA1cR == positive_unreliable ->
        Provisional = inconclusive_hba1c_unreliable,
        Evidence = [fasting:FastingR, random:RandomR, ogtt:OGTTR, hba1c:HbA1cR]
    ; % no available positive results but at least one known negative -> likely no diabetes
      all_known_and_negative([FastingR, RandomR, OGTTR, HbA1cR]) ->
        Provisional = no_diabetes,
        Evidence = [fasting:FastingR, random:RandomR, ogtt:OGTTR, hba1c:HbA1cR]
    ; % insufficient data
        Provisional = insufficient_data,
        Evidence = [fasting:FastingR, random:RandomR, ogtt:OGTTR, hba1c:HbA1cR]
    ),

    /* If provisional diagnosis suggests diabetes, check medication confounders */
    ( (Provisional == diabetes_by_glucose_test ; Provisional == diabetes_by_hba1c) ->
        medication_selection(MedsSelected),
        ( member(none, MedsSelected) , length(MedsSelected, L), L =:= 1 ->
            % no confounding medications reported -> final diagnosis diabetes
            Result = _{verdict:diabetes, reason:Provisional, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown}
        ; % one or more potential glucose-raising medications reported -> grouping and inconclusive result
            ( MedsSelected = [] ->
                % defensive: treat as no meds
                Result = _{verdict:diabetes, reason:Provisional, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown}
            ; medication_timing_grouping(MedTiming),
              Result = _{verdict:inconclusive_due_to_medication, reason:Provisional, medications:MedSelectList, medication_timing:MedTiming, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown},
              ( MedSelectList = MedsSelected -> true ; true )
            )
        )
    ; Provisional == inconclusive_hba1c_unreliable ->
        inconclusive_followup(Followup),
        Result = _{verdict:inconclusive_hba1c_unreliable, reason:Provisional, followup:Followup, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown}
    ; Provisional == no_diabetes ->
        Result = _{verdict:no_diabetes, reason:Provisional, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown}
    ; Provisional == insufficient_data ->
        % when insufficient, ask optional additional checks per guidance
        inconclusive_followup(Followup2),
        Result = _{verdict:insufficient_data, reason:Provisional, followup:Followup2, evidence:Evidence, egfr:EGFR, chronic_conditions:ChronicCount, cognitive_status:CognitiveStatus, symptoms:Symptoms, years_known:YearsKnown}
    ).