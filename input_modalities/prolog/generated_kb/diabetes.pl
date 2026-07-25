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

% ---------- Diagnostic criteria (standalone predicates) ----------

% Random plasma glucose ≥ 200 mg/dL
random_glucose_criterion :-
    ask_numeric('What is your random (non-fasting) plasma glucose in mg/dL?', Value),
    Value >= 200.0.

% Fasting plasma glucose ≥ 126 mg/dL after 8–12 hours fasting
fasting_glucose_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    ask_range('How many hours did you fast before this blood sample?', 0.0, 72.0, Hours),
    Hours >= 8.0,
    Hours =< 12.0,
    Value >= 126.0.

% 2-hour plasma glucose during OGTT ≥ 200 mg/dL
ogtt_2hr_criterion :-
    ask_numeric('What was your 2-hour plasma glucose during an oral glucose tolerance test (mg/dL)?', Value),
    Value >= 200.0.

% HbA1c ≥ 6.5%
hba1c_criterion :-
    ask_numeric('What is your hemoglobin A1c (HbA1c) percent?', Value),
    Value >= 6.5.

% Prediabetes: fasting plasma glucose 100–125 mg/dL
prediabetes_fasting_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0,
    Value =< 125.0.

% ---------- Symptom and supporting evidence helpers ----------

% Ask the core symptom checklist (excessive thirst, excessive urination, fatigue, blurred vision)
ask_core_symptoms(Symptoms) :-
    ask_multiple_category(
      'Which of the following symptoms currently apply? Select all that apply: excessive thirst, excessive urination, fatigue, blurred vision.',
      [excessive_thirst, excessive_urination, fatigue, blurred_vision],
      Symptoms).

% Determine support level from core symptoms:
% strong if both excessive thirst and excessive urination present,
% partial if one of them present,
% none otherwise.
symptom_support(Symptoms, strong) :-
    member(excessive_thirst, Symptoms),
    member(excessive_urination, Symptoms), !.
symptom_support(Symptoms, partial) :-
    ( member(excessive_thirst, Symptoms) ; member(excessive_urination, Symptoms) ), !.
symptom_support(_, none).

% Ask for symptom order when more than one symptom is present
ask_symptom_order(Order, SelectedSymptoms) :-
    length(SelectedSymptoms, Count),
    ( Count > 1 ->
        ask_multi_structured_input(
          'Please list the symptoms in the order they first appeared, from earliest to most recent.',
          sequence,
          [excessive_thirst, excessive_urination, fatigue, blurred_vision],
          Order)
    ; Order = []
    ).

% Ask fatigue severity on 1-10 scale and map to mild/moderate/severe
ask_fatigue_severity(FatigueSeverity) :-
    ask_range('On a scale from 1 to 10, how severe is your fatigue?', 1.0, 10.0, Val),
    ( Val >= 1.0, Val =< 3.0 -> FatigueSeverity = mild
    ; Val =< 6.0 -> FatigueSeverity = moderate
    ; FatigueSeverity = severe ).

% Ask thirst severity as categorical
ask_thirst_severity(ThirstSeverity) :-
    ask_category('How would you describe your thirst severity?', [none, mild, moderate, severe], ThirstSeverity).

% Ask duration of symptoms in days and classify
symptom_duration_category(Category) :-
    ask_duration('How long have these symptoms been present (in days)?', Days),
    ( Days < 7.0 -> Category = recent
    ; Days =< 30.0 -> Category = persistent
    ; Category = long_term ).

% ---------- Medication collection ----------

% Collect N medication entries, each with name (string), dose_mg (float), times_per_day (float)
collect_medications(Count, Meds) :-
    collect_medications_helper(1, Count, [], RevMeds),
    reverse(RevMeds, Meds).

collect_medications_helper(Index, Count, Acc, Acc) :-
    Index > Count, !.
collect_medications_helper(Index, Count, Acc, Meds) :-
    Index =< Count,
    atomic_list_concat(['Please provide details for medication number ', Index, ': name, dose (mg), and times per day.'], Prompt),
    Fields = [
      ['name', 'Medication name', string],
      ['dose_mg', 'Dose in milligrams', float],
      ['times_per_day', 'How many times per day is it taken?', float]
    ],
    ask_multi_attribute_entity(Prompt, med, Fields, Answer),
    ( Answer = _{data: Data} -> Entry = Data ; Entry = Answer ),
    Next is Index + 1,
    collect_medications_helper(Next, Count, [Entry|Acc], Meds).

% Ask whether the patient is currently taking any diabetes medication and collect entries if yes
maybe_collect_medications(Meds) :-
    ( ask_boolean('Are you currently taking any diabetes medication?') -> Taking = true ; Taking = false ),
    ( Taking == true ->
        ask_numeric('How many different diabetes medications are you currently taking?', Nf),
        ( Nf >= 1.0 ->
            Nint is round(Nf),
            collect_medications(Nint, Meds)
        ; Meds = [] )
    ; Meds = [] ).

% ---------- Public predicates ----------

% diabetes/0 succeeds if any diagnostic diabetes criterion is met
diabetes :-
    ( random_glucose_criterion
    ; fasting_glucose_criterion
    ; ogtt_2hr_criterion
    ; hba1c_criterion ).

% prediabetes/0 succeeds if fasting glucose in prediabetes range
prediabetes :-
    prediabetes_fasting_criterion.

% low_risk/0 succeeds when neither diabetes nor prediabetes criteria are met
low_risk :-
    \+ diabetes,
    \+ prediabetes.

% ---------- Main workflow (diagnose/1) ----------

diagnose(Result) :-
    % First, attempt to establish diabetes by any single numeric criterion.
    ( ( random_glucose_criterion -> Criterion = random_plasma_glucose
      ; fasting_glucose_criterion -> Criterion = fasting_plasma_glucose
      ; ogtt_2hr_criterion -> Criterion = ogtt_2_hour
      ; hba1c_criterion -> Criterion = hba1c
      ),
      % Numeric evidence is sufficient for diabetes; do not ask symptoms.
      maybe_collect_medications(Medications),
      Result = _{verdict: diabetes, criterion: Criterion, medications: Medications}
    ;
      % No diabetes criterion met. Check for prediabetes.
      ( prediabetes_fasting_criterion ->
          maybe_collect_medications(Medications2),
          Result = _{verdict: prediabetes, criterion: fasting_prediabetes, medications: Medications2}
      ;
          % Neither diabetes nor prediabetes: gather focused symptom information only.
          ask_core_symptoms(Symptoms),
          symptom_support(Symptoms, SupportLevel),
          ask_symptom_order(SymptomOrder, Symptoms),
          ( member(fatigue, Symptoms) -> ask_fatigue_severity(FatigueSeverity) ; FatigueSeverity = none ),
          ( member(excessive_thirst, Symptoms) -> ask_thirst_severity(ThirstSeverity) ; ThirstSeverity = none ),
          maybe_collect_medications(Medications3),
          Result = _{
            verdict: low_risk,
            symptoms: Symptoms,
            support: SupportLevel,
            symptom_order: SymptomOrder,
            fatigue_severity: FatigueSeverity,
            thirst_severity: ThirstSeverity,
            medications: Medications3
          }
      )
    ).