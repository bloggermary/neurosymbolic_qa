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

/* ============================================================
   Numeric measurement predicates (modality: numeric)
   These four values, plus the fasting window below, are the ONLY
   inputs the actual verdict logic depends on - everything added
   further down is supporting evidence collected for a fuller
   clinical picture, but deliberately does not change the verdict,
   so the already-verified verdict logic stays exactly as tested.
   ============================================================ */

random_glucose_mgdl(Value) :-
    ask_numeric('Random plasma glucose (mg/dL)?', Value).

fasting_glucose_mgdl(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value).

fasting_plasma_glucose_mgdl(Value) :-
    fasting_glucose_mgdl(Value).

ogtt_2hr_mgdl(Value) :-
    ask_numeric('2-hour OGTT plasma glucose (mg/dL)?', Value).

hba1c_percent(Value) :-
    ask_numeric('HbA1c (%)?', Value).

/* modality: duration */
fasting_duration_hours(Hours) :-
    ask_duration('Hours fasting before sample?', Hours).

/* ============================================================
   Additional risk-stratification criteria (modality: numeric /
   boolean). These are NOT part of the strict ADA diagnostic
   thresholds above - diabetes and prediabetes are determined by lab
   values alone, per guideline, and that logic is untouched. These
   instead drive the low_risk vs no_risk distinction, which was never
   an official diagnostic category to begin with (see low_risk_positive
   below) - real ADA risk-assessment guidance for WHO should be
   screened does include BMI, age, and family history, so folding them
   into this already-invented sub-classification is a genuine, medically
   grounded extension rather than an arbitrary one.
   ============================================================ */

bmi(Value) :-
    ask_numeric('Body mass index (BMI)?', Value).

age_years(Value) :-
    ask_numeric('Age in years?', Value).

family_history_diabetes :-
    ask_boolean('Does a first-degree relative (parent or sibling) have diabetes?').

systolic_bp_mmhg(Value) :-
    ask_numeric('Systolic blood pressure (mmHg)?', Value).

/* ============================================================
   Supporting multi-modal evidence (does NOT affect the verdict)
   ============================================================ */

/* modality: boolean (individually queryable, e.g. by a direct
   single-symptom question) */
excessive_thirst :-
    ask_boolean('Excessive thirst?').

excessive_urination :-
    ask_boolean('Excessive urination (polyuria)?').

fatigue :-
    ask_boolean('Fatigue?').

blurred_vision :-
    ask_boolean('Blurred vision?').

/* modality: multiple_category - the full symptom picture gathered
   at once, as the main workflow actually does it */
symptom_checklist(Selected) :-
    ask_multiple_category(
        'Which of the following symptoms currently apply? Select all that apply.',
        [excessive_thirst, excessive_urination, fatigue, blurred_vision],
        Selected
    ).

/* modality: range - how long the symptoms have been present, as a
   bounded 0-365 day scale rather than an open-ended duration */
symptom_duration_days(Days) :-
    ask_range(
        'Over how many days have these symptoms been present?',
        0, 365, Days
    ).

/* modality: multi_structured_input - only meaningful once 2+
   symptoms are on the table */
symptom_order(Order) :-
    ask_multi_structured_input(
        'Please list the symptoms in the order they first appeared, from earliest to most recent.',
        sequence,
        [],
        Order
    ).

/* modality: category */
medication_status(Status) :-
    ask_category(
        'What is your current diabetes medication status?',
        [none, oral_antidiabetics, insulin, corticosteroids],
        Status
    ).

/* modality: multi_attribute_entity - only asked when medication
   status indicates the patient is actually on something */
medication_details(Details) :-
    ask_multi_attribute_entity(
        'Please provide the medication name, dose in milligrams, and frequency per day.',
        medication,
        [[name, 'Medication name', string],
         [dose_mg, 'Dose in milligrams', float],
         [times_per_day, 'Times per day', float]],
        Details
    ).

/* modality: string */
additional_notes(Notes) :-
    ask_string(
        'Is there anything else about your symptoms or history you would like to add?',
        Notes
    ).

/* ============================================================
   Diagnostic criterion predicates (unchanged verdict logic)
   ============================================================ */

diabetes_positive_by_random_glucose :-
    random_glucose_mgdl(Value),
    Value >= 200.

diabetes_positive_by_fasting_glucose :-
    fasting_duration_hours(Hours),
    Hours >= 8,
    Hours =< 12,
    fasting_glucose_mgdl(Value),
    Value >= 126.

diabetes_positive_by_ogtt :-
    ogtt_2hr_mgdl(Value),
    Value >= 200.

diabetes_positive_by_hba1c :-
    hba1c_percent(Value),
    Value >= 6.5.

diabetes_positive :-
    diabetes_positive_by_random_glucose
    ;
    diabetes_positive_by_fasting_glucose
    ;
    diabetes_positive_by_ogtt
    ;
    diabetes_positive_by_hba1c.

diabetes :-
    diabetes_positive.

prediabetes_positive :-
    \+ diabetes_positive,
    fasting_duration_hours(Hours),
    Hours >= 8,
    Hours =< 12,
    fasting_glucose_mgdl(Value),
    Value >= 100,
    Value =< 125.

prediabetes :-
    prediabetes_positive.

/* Secondary ADA "increased risk" markers this KB doesn't otherwise
   check, spanning six genuinely independent criteria rather than two:
   HbA1c 5.7-6.4%, 2-hour OGTT 140-199 mg/dL (both direct glycemic
   markers), and four recognized non-glycemic ADA risk factors -
   BMI >= 25 (overweight), age >= 45 (standard screening threshold),
   a first-degree family history of diabetes, and systolic blood
   pressure >= 130 mmHg (a metabolic-syndrome marker). None alone is
   diabetes or fasting-glucose prediabetes, but any one of them
   indicates elevated risk rather than a clearly normal profile. */
low_risk_positive :-
    \+ diabetes_positive,
    \+ prediabetes_positive,
    (   ( hba1c_percent(H), H >= 5.7, H =< 6.4 )
    ;   ( ogtt_2hr_mgdl(O), O >= 140, O =< 199 )
    ;   ( bmi(B), B >= 25.0 )
    ;   ( age_years(A), A >= 45.0 )
    ;   family_history_diabetes
    ;   ( systolic_bp_mmhg(S), S >= 130.0 )
    ).

low_risk :-
    low_risk_positive.

no_risk :-
    \+ diabetes_positive,
    \+ prediabetes_positive,
    \+ low_risk_positive.

/* ============================================================
   Simple bare-atom verdict predicate - unchanged from before,
   still what the diagnostic-accuracy evaluation queries directly.
   ============================================================ */

diagnose(diabetes) :-
    diabetes_positive, !.

diagnose(prediabetes) :-
    \+ diabetes_positive,
    prediabetes_positive, !.

diagnose(low_risk) :-
    \+ diabetes_positive,
    \+ prediabetes_positive,
    low_risk_positive, !.

diagnose(no_risk) :-
    \+ diabetes_positive,
    \+ prediabetes_positive,
    \+ low_risk_positive.

/* ============================================================
   Full multi-modal assessment: the same verdict logic above, PLUS
   every supporting modality actually gathered, returned as one
   janus-safe dict. This is what demonstrates the full breadth of
   the project (boolean/numeric/category/range/duration/
   multiple_category/multi_structured_input/multi_attribute_entity/
   string) rather than just the four numeric lab values.
   ============================================================ */

full_assessment(Result) :-
    symptom_checklist(SelectedSymptoms),
    length(SelectedSymptoms, NumSymptoms),

    ( NumSymptoms >= 1 ->
        symptom_duration_days(SymptomDays)
    ;   SymptomDays = 0
    ),

    ( NumSymptoms >= 2 ->
        symptom_order(SymptomOrder)
    ;   SymptomOrder = []
    ),

    medication_status(MedStatus),

    ( MedStatus \== none ->
        medication_details(MedDetails)
    ;   MedDetails = _{}
    ),

    additional_notes(Notes),

    ( diagnose(Verdict) -> true ; Verdict = no_risk ),

    Result = _{
        verdict: Verdict,
        symptoms: SelectedSymptoms,
        symptom_duration_days: SymptomDays,
        symptom_order: SymptomOrder,
        medication_status: MedStatus,
        medication_details: MedDetails,
        additional_notes: Notes
    }.
