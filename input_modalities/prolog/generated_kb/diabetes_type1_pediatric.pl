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

/* Numeric criteria predicates (each will ask the relevant numeric question when invoked) */

diabetes_positive_by_random(Value) :-
    ask_numeric('Random plasma glucose (mg/dL)?', Value),
    Value >= 200.

diabetes_positive_by_fasting(Value) :-
    ask_numeric('Fasting plasma glucose (mg/dL)?', Value),
    Value >= 126.

diabetes_positive_by_hba1c(Value) :-
    ask_numeric('Hemoglobin A1c (%)?', Value),
    Value >= 6.5.

/* Main numeric checker: tries criteria in order and stops when one criterion alone justifies diabetes.
   Returns Evidence term describing which numeric test was positive (random(Value), fasting(Value), hba1c(Value))
   or none if no numeric threshold met. */

numeric_evidence(Evidence) :-
    (   diabetes_positive_by_random(VR)
    ->  Evidence = random(VR)
    ;   (   diabetes_positive_by_fasting(VF)
        ->  Evidence = fasting(VF)
        ;   (   diabetes_positive_by_hba1c(VH)
            ->  Evidence = hba1c(VH)
            ;   Evidence = none
            )
        )
    ).

/* Single diagnose/1 workflow: collects multimodal clinical picture AND determines numeric evidence.
   It gathers boolean symptoms, categorical items, duration/range/scale details, and then runs numeric check.
   It constructs a diagnosis_summary/10 term:
     diagnosis_summary(Verdict, SymptomsList, Medication, Antibodies, FamilyHistory, SymptomDays, FastingHours, DehydrationScore, NumericEvidence, EmergencyFlags)
*/

diagnose(diagnosis_summary(Verdict, Symptoms, Medication, Antibodies, FamilyHistory, SymptomDaysDays, FastingHoursHours, DehydrationScoreScore, NumericEvidence, Emergency)) :-
    % Collect boolean symptoms (capture answers into true/false)
    ( ask_boolean('Excessive urination (polyuria)?') -> Polyuria = true ; Polyuria = false ),
    ( ask_boolean('Excessive thirst (polydipsia)?') -> Polydipsia = true ; Polydipsia = false ),
    ( ask_boolean('Unexplained weight loss?') -> WeightLoss = true ; WeightLoss = false ),
    ( ask_boolean('Nocturnal bedwetting in a previously toilet-trained child?') -> Bedwetting = true ; Bedwetting = false ),
    ( ask_boolean('Lethargy?') -> Lethargy = true ; Lethargy = false ),

    % Emergency features: presence of any triggers immediate referral (recorded separately)
    ( ask_boolean('Nausea?') -> Nausea = true ; Nausea = false ),
    ( ask_boolean('Vomiting?') -> Vomiting = true ; Vomiting = false ),
    ( ask_boolean('Abdominal pain?') -> AbdominalPain = true ; AbdominalPain = false ),
    ( ask_boolean('Rapid or deep breathing?') -> RapidBreathing = true ; RapidBreathing = false ),

    % Categorical data: medication status and family history
    ask_category('Medication status (none / insulin / unknown)?', [none, insulin, unknown], Medication),
    ask_category('Family history of type 1 diabetes (none / first_degree / second_degree)?', [none, first_degree, second_degree], FamilyHistory),

    % Autoantibody results for GAD65, IA-2, ZnT8 (each: positive / negative / not_tested)
    ask_category('GAD65 antibody result (positive / negative / not_tested)?', [positive, negative, not_tested], GAD65),
    ask_category('IA-2 antibody result (positive / negative / not_tested)?', [positive, negative, not_tested], IA2),
    ask_category('ZnT8 antibody result (positive / negative / not_tested)?', [positive, negative, not_tested], ZnT8),
    Antibodies = [gad65-GAD65, ia2-IA2, znt8-ZnT8],

    % Duration and range details
    ask_duration('How many days have symptoms been present? (enter number of days)', SymptomDays),
    ask_range('Hours fasting before plasma glucose sample (0-48)?', 0, 48, FastingHours),
    ask_scale('Severity of dehydration (1 mild - 10 severe)?', DehydrationScore),

    % Compose symptoms list and emergency flag
    Symptoms = [polyuria-Polyuria, polydipsia-Polydipsia, weight_loss-WeightLoss, bedwetting-Bedwetting, lethargy-Lethargy],
    ( Nausea = true ; Vomiting = true ; AbdominalPain = true ; RapidBreathing = true -> Emergency = true ; Emergency = false ),

    % Numeric evidence: stop asking further numeric criteria once one threshold is met
    numeric_evidence(NumericEvidence),

    % Determine overall verdict:
    % - If any numeric evidence meets diabetes thresholds -> diabetes
    % - Otherwise, if emergency features present -> emergency (flagged but not labeled diabetes)
    % - Otherwise low_risk
    ( NumericEvidence = random(_) ; NumericEvidence = fasting(_) ; NumericEvidence = hba1c(_) ->
        Verdict = diabetes
    ; Emergency = true ->
        Verdict = emergency
    ; Verdict = low_risk
    ),

    % Expose duration and fasting hours and dehydration score in output term with clear names
    SymptomDaysDays = SymptomDays,
    FastingHoursHours = FastingHours,
    DehydrationScoreScore = DehydrationScore.

/* Convenience predicates */

diabetes :-
    diagnose(Summary),
    Summary = diagnosis_summary(diabetes, _, _, _, _, _, _, _, _, _).

prediabetes :-
    % Not defined in the provided text: no explicit prediabetes criteria are given.
    % This predicate is left to fail unless otherwise extended with validated criteria.
    fail.

low_risk :-
    diagnose(Summary),
    Summary = diagnosis_summary(low_risk, _, _, _, _, _, _, _, _, _).