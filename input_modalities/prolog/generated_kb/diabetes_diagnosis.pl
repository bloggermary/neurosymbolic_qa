:- use_module(library(janus)).

ask_boolean(Question) :-
    py_call(main:ask_boolean(Question), true).

ask_numeric(Question, Value) :-
    py_call(main:ask_numeric(Question), Value).

ask_string(Question, Value) :-
    py_call(main:ask_string(Question), Value).

% --- Numeric measurement predicates (asking values from the user) ---
% All glucose measurements are requested in mg/dL (unit chosen from the text).
gelegenheits_plasmaglukose_mgdl(Value) :-
    ask_numeric('Gelegenheits-Plasmaglukose in mg/dL?', Value).

fasten_plasmaglukose_mgdl(Value) :-
    ask_numeric('Nüchtern-Plasmaglukose nach 8-12 Stunden Fasten in mg/dL?', Value).

ogtt_2h_plasmaglukose_mgdl(Value) :-
    ask_numeric('2-Stunden-Plasmaglukose (oraler Glukosetoleranztest) in mg/dL?', Value).

% HbA1c is requested in percent (%%), as given in the text (6.5% threshold).
hba1c_percent(Value) :-
    ask_numeric('HbA1c in Prozent (%)?', Value).

% --- Criteria predicates derived from the medical text ---
% Casual (Gelegenheits-) plasma glucose >= 200 mg/dL indicates diabetes.
gelegenheits_plasmaglukose_diabetes :-
    gelegenheits_plasmaglukose_mgdl(V),
    V >= 200.

% Fasting plasma glucose >= 126 mg/dL after 8-12 h fasting indicates diabetes.
fasten_plasmaglukose_diabetes :-
    fasten_plasmaglukose_mgdl(V),
    V >= 126.

% 2-hour OGTT plasma glucose >= 200 mg/dL indicates diabetes.
ogtt_2h_diabetes :-
    ogtt_2h_plasmaglukose_mgdl(V),
    V >= 200.

% HbA1c >= 6.5% (48 mmol/mol) indicates diabetes.
hba1c_diabetes :-
    hba1c_percent(V),
    V >= 6.5.

% Prediabetes fasting: fasting glucose between 100 and 125 mg/dL (inclusive).
prediabetes_fasting :-
    fasten_plasmaglukose_mgdl(V),
    V >= 100,
    V =< 125.

% --- Symptom collection ---
% Collect all common diabetes symptoms first before evaluating symptom patterns.
collect_symptoms(ExcessiveThirst, ExcessiveUrination, Fatigue, BlurredVision) :-
    ( ask_boolean('Haben Sie übermäßigen Durst (excessive thirst)?') -> ExcessiveThirst = true ; ExcessiveThirst = false ),
    ( ask_boolean('Haben Sie vermehrtes Wasserlassen (excessive urination)?') -> ExcessiveUrination = true ; ExcessiveUrination = false ),
    ( ask_boolean('Leiden Sie unter Müdigkeit/Fatigue (fatigue)?') -> Fatigue = true ; Fatigue = false ),
    ( ask_boolean('Haben Sie unscharfes Sehen (blurred vision)?') -> BlurredVision = true ; BlurredVision = false ).

% Supportive symptom pattern: both excessive thirst and excessive urination often occur in diabetes.
supportive_symptoms_thirst_and_urination :-
    collect_symptoms(Thirst, Urination, _Fatigue, _Blurred),
    Thirst == true,
    Urination == true.

% --- Final diagnostic rules ---
% Diabetes mellitus is present if any of the laboratory criteria are met.
diabetes_mellitus_laboratory :-
    gelegenheits_plasmaglukose_diabetes
    ;
    fasten_plasmaglukose_diabetes
    ;
    ogtt_2h_diabetes
    ;
    hba1c_diabetes.

% High-level diagnosis predicate that returns a concise reason atom.
% It checks laboratory criteria first; if not met, it can still report supportive symptoms.
diabetes_mellitus(laboratory_criteria_met) :-
    diabetes_mellitus_laboratory.

diabetes_mellitus(supportive_symptoms_thirst_and_urination) :-
    \+ diabetes_mellitus_laboratory,
    supportive_symptoms_thirst_and_urination.

% Prediabetes detection predicate (returns an atom when criteria met).
prediabetes(prediabetes_fasting) :-
    prediabetes_fasting.