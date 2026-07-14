:- use_module(library(janus)).

ask_boolean(Key, Question) :-
    py_call(main:ask_boolean(Key, Question), true).

ask_numeric(Key, Question, Value) :-
    py_call(main:ask_numeric(Key, Question), Value).

ask_string(Key, Question, Value) :-
    py_call(main:ask_string(Key, Question), Value).

ask_category(Key, Question, Categories, Answer) :-
    py_call(main:ask_category(Key, Question, Categories), Answer).

ask_range(Key, Question, Start, Stop, Value) :-
    py_call(main:ask_range(Key, Question, Start, Stop), Value).

ask_duration(Key, Question, Value) :-
    py_call(main:ask_duration(Key, Question), Value).    

% Generic ask wrapper using a descriptive key
ask(Question) :-
    ask_boolean(diabetes_confirmation, Question).

% Overall diagnostic entry point: prefer diagnosing diabetes first
diagnose(diabetes_mellitus) :-
    diabetes_mellitus,
    !.
diagnose(prediabetes) :-
    prediabetes,
    !.

% Diagnostic criteria for diabetes mellitus (any one suffices)

% Random plasma glucose >= 200 mg/dL
diabetes_mellitus :-
    ask_numeric(random_plasma_glucose_mgdl, "What is the random plasma glucose (mg/dL)?", Random),
    Random >= 200.

% Fasting plasma glucose >= 126 mg/dL (after appropriate fasting)
diabetes_mellitus :-
    ask_numeric(fasting_plasma_glucose_mgdl, "What is the fasting plasma glucose (mg/dL)? (after 8-12 hours fasting)", Fasting),
    Fasting >= 126.

% 2-hour plasma glucose during OGTT >= 200 mg/dL
diabetes_mellitus :-
    ask_numeric(ogtt_2h_plasma_glucose_mgdl, "What is the 2-hour plasma glucose during OGTT (mg/dL)?", Ogtt2),
    Ogtt2 >= 200.

% HbA1c >= 6.5%
diabetes_mellitus :-
    ask_numeric(hba1c_percent, "What is the HbA1c (%)?", Hba1c),
    Hba1c >= 6.5.

% Prediabetes: fasting plasma glucose between 100 and 125 mg/dL (inclusive)
prediabetes :-
    ask_numeric(fasting_plasma_glucose_mgdl, "What is the fasting plasma glucose (mg/dL)? (after 8-12 hours fasting)", Fasting),
    Fasting >= 100,
    Fasting =< 125.

% Symptom queries (supportive information, not diagnostic on their own)

excessive_thirst_present :-
    ask_boolean(symptom_excessive_thirst, "Do you have excessive thirst?").

frequent_urination_present :-
    ask_boolean(symptom_frequent_urination, "Do you have frequent urination (excessive urination)?").

blurred_vision_present :-
    ask_boolean(symptom_blurred_vision, "Do you have blurred vision?").

fatigue_present :-
    ask_boolean(symptom_fatigue_present, "Are you experiencing fatigue?").

% Supportive symptom patterns

% Strongly supportive when both excessive thirst and frequent urination are present
strong_supportive_symptoms :-
    excessive_thirst_present,
    frequent_urination_present.

% Partial support when one (but not both) of thirst or urination is present
partial_supportive_symptoms :-
    ( excessive_thirst_present ; frequent_urination_present ),
    \+ strong_supportive_symptoms.

% Symptom duration classification (days)
symptom_duration_class(recent) :-
    ask_duration(symptom_duration_days, "For how many days have symptoms been present?", Days),
    Days < 7.

symptom_duration_class(persistent) :-
    ask_duration(symptom_duration_days, "For how many days have symptoms been present?", Days),
    Days >= 7,
    Days =< 30.

symptom_duration_class(long_term) :-
    ask_duration(symptom_duration_days, "For how many days have symptoms been present?", Days),
    Days > 30.

% Fatigue severity classification (1-10 scale)
fatigue_severity_class(none) :-
    \+ fatigue_present.

fatigue_severity_class(mild) :-
    fatigue_present,
    ask_range(fatigue_severity_score, "On a scale of 1-10, what is the fatigue severity?", 1, 10, Score),
    Score >= 1,
    Score =< 3.

fatigue_severity_class(moderate) :-
    fatigue_present,
    ask_range(fatigue_severity_score, "On a scale of 1-10, what is the fatigue severity?", 1, 10, Score),
    Score >= 4,
    Score =< 6.

fatigue_severity_class(severe) :-
    fatigue_present,
    ask_range(fatigue_severity_score, "On a scale of 1-10, what is the fatigue severity?", 1, 10, Score),
    Score >= 7,
    Score =< 10.

% Thirst severity (none, mild, moderate, severe)
thirst_severity(Level) :-
    ask_category(thirst_severity_level, "How would you describe the severity of thirst?", [none,mild,moderate,severe], Level).

% Combined supportive clinical information predicate
supportive_clinical_information(SupportLevel) :-
    ( strong_supportive_symptoms -> SupportLevel = strong
    ; partial_supportive_symptoms -> SupportLevel = partial
    ; SupportLevel = none
    ).