:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value).

ask_range(Question, Start, Stop, Value) :-
    py_call(main:ask_range(Question, Start, Stop), Value).

ask_duration(Question, Value) :-
    py_call(main:ask_duration(Question), Value).    

% Generic boolean ask wrapper that binds true/false
ask(Question, Answer) :-
    (   ask_boolean(Question)
    ->  Answer = true
    ;   Answer = false).

% Gather all required answers first
gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
               Thirst, Polyuria, Fatigue, BlurredVision) :-
    ask_numeric('Random (casual) plasma glucose in mg/dL?', Random_mgdl),
    ask_numeric('Fasting plasma glucose (8-12 hours fasting) in mg/dL?', Fasting_mgdl),
    ask_numeric('Oral glucose tolerance test: 2-hour plasma glucose in mg/dL?', OGTT_2h_mgdl),
    ask_numeric('HbA1c percent (e.g. 6.5 for 6.5%)?', HbA1c_percent),
    ask_numeric('HbA1c in mmol/mol (e.g. 48)?', HbA1c_mmolmol),
    ask('Excessive thirst?', Thirst),
    ask('Excessive urination (polyuria)?', Polyuria),
    ask('Fatigue?', Fatigue),
    ask('Blurred vision?', BlurredVision).

% Helper numeric comparisons for criteria
random_glucose_diabetes(Random_mgdl) :-
    number(Random_mgdl),
    Random_mgdl >= 200.

fasting_glucose_diabetes(Fasting_mgdl) :-
    number(Fasting_mgdl),
    Fasting_mgdl >= 126.

ogtt_diabetes(OGTT_2h_mgdl) :-
    number(OGTT_2h_mgdl),
    OGTT_2h_mgdl >= 200.

hba1c_percent_diabetes(HbA1c_percent) :-
    number(HbA1c_percent),
    HbA1c_percent >= 6.5.

hba1c_mmol_diabetes(HbA1c_mmolmol) :-
    number(HbA1c_mmolmol),
    HbA1c_mmolmol >= 48.

prediabetes_fasting(Fasting_mgdl) :-
    number(Fasting_mgdl),
    Fasting_mgdl >= 100,
    Fasting_mgdl =< 125.

% Collect all positive diagnostic criteria into a list
positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, Criteria) :-
    (   random_glucose_diabetes(Random_mgdl) -> R = [random_glucose_ge_200] ; R = []),
    (   fasting_glucose_diabetes(Fasting_mgdl) -> F = [fasting_glucose_ge_126] ; F = []),
    (   ogtt_diabetes(OGTT_2h_mgdl) -> O = [ogtt_2h_ge_200] ; O = []),
    (   hba1c_percent_diabetes(HbA1c_percent) -> P = [hba1c_percent_ge_6_5] ; P = []),
    (   hba1c_mmol_diabetes(HbA1c_mmolmol) -> M = [hba1c_mmolmol_ge_48] ; M = []),
    append(R, F, RF),
    append(RF, O, RFO),
    append(RFO, P, RFOP),
    append(RFOP, M, Criteria).

% Symptom support: both excessive thirst and polyuria
symptom_support(Thirst, Polyuria) :-
    Thirst == true,
    Polyuria == true.

% Diagnose collects all answers then evaluates diagnosis
diagnose(diagnosis{status:diabetes, evidence:Criteria, symptom_support:true}) :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   Thirst, Polyuria, _Fatigue, _Blurred),
    positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, Criteria),
    Criteria \= [],
    symptom_support(Thirst, Polyuria), !.

diagnose(diagnosis{status:diabetes, evidence:Criteria, symptom_support:false}) :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   Thirst, Polyuria, _Fatigue, _Blurred),
    positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, Criteria),
    Criteria \= [],
    \+ symptom_support(Thirst, Polyuria), !.

diagnose(diagnosis{status:prediabetes, evidence:[prediabetes_fasting], symptom_support:SymptomSupport}) :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   Thirst, Polyuria, _Fatigue, _Blurred),
    \+ (positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, DiagCriteria), DiagCriteria \= []),
    prediabetes_fasting(Fasting_mgdl),
    (   symptom_support(Thirst, Polyuria) -> SymptomSupport = true ; SymptomSupport = false), !.

diagnose(diagnosis{status:low_risk, evidence:[], symptom_support:SymptomSupport}) :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   Thirst, Polyuria, _Fatigue, _Blurred),
    \+ (positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, DiagCriteria), DiagCriteria \= []),
    \+ prediabetes_fasting(Fasting_mgdl),
    (   symptom_support(Thirst, Polyuria) -> SymptomSupport = true ; SymptomSupport = false).

% Specific predicates for direct queries

% diabetes/0: asks all criteria and succeeds if diabetes criteria met
diabetes :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   _Thirst, _Polyuria, _Fatigue, _Blurred),
    positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, Criteria),
    Criteria \= [].

% prediabetes/0: asks all criteria and succeeds if prediabetes fasting criterion met and diabetes criteria absent
prediabetes :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   _Thirst, _Polyuria, _Fatigue, _Blurred),
    \+ (positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, DiagCriteria), DiagCriteria \= []),
    prediabetes_fasting(Fasting_mgdl).

% low_risk/0: asks all criteria and succeeds if neither diabetes nor prediabetes criteria met
low_risk :-
    gather_answers(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol,
                   _Thirst, _Polyuria, _Fatigue, _Blurred),
    \+ (positive_diabetes_criteria(Fasting_mgdl, Random_mgdl, OGTT_2h_mgdl, HbA1c_percent, HbA1c_mmolmol, DiagCriteria), DiagCriteria \= []),
    \+ prediabetes_fasting(Fasting_mgdl).