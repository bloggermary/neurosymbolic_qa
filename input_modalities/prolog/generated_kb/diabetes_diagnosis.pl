:- use_module(library(janus)).


% =========================================================
% Python interaction wrappers
% =========================================================

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



% =========================================================
% Scale example
% =========================================================

symptom_scale(Value) :-
    ask_scale(
        'Rate symptom severity from 1-10:',
        Value
    ).



% =========================================================
% Raw clinical measurements
% =========================================================

ask_random_plasma_glucose_mgdl(Value) :-
    ask_numeric(
        'Random plasma glucose (mg/dL):',
        Value
    ).


ask_fasting_plasma_glucose_mgdl(Value) :-
    ask_numeric(
        'Fasting plasma glucose (mg/dL):',
        Value
    ).


ask_fasting_duration_hours(Value) :-
    ask_numeric(
        'Fasting duration in hours:',
        Value
    ).


ask_ogtt_2h_plasma_glucose_mgdl(Value) :-
    ask_numeric(
        '2-hour OGTT plasma glucose (mg/dL):',
        Value
    ).


ask_hba1c_percent(Value) :-
    ask_numeric(
        'HbA1c percentage:',
        Value
    ).



% =========================================================
% Benchmark-compatible measurement predicates
% =========================================================

fasting_glucose_mgdl(Value) :-
    ask_fasting_plasma_glucose_mgdl(Value).


hba1c_percent(Value) :-
    ask_hba1c_percent(Value).


random_glucose_mgdl(Value) :-
    ask_random_plasma_glucose_mgdl(Value).


ogtt_2hr_mgdl(Value) :-
    ask_ogtt_2h_plasma_glucose_mgdl(Value).



% =========================================================
% Diagnostic criteria predicates
% =========================================================

diabetes_positive_by_fasting_glucose :-
    fasting_glucose_mgdl(Value),
    number(Value),
    Value >= 126.



diabetes_positive_by_hba1c :-
    hba1c_percent(Value),
    number(Value),
    Value >= 6.5.



diabetes_positive_by_random_glucose :-
    random_glucose_mgdl(Value),
    number(Value),
    Value >= 200.



diabetes_positive_by_ogtt :-
    ogtt_2hr_mgdl(Value),
    number(Value),
    Value >= 200.



% =========================================================
% Overall classification predicates
% =========================================================

diabetes_positive :-
    (
        diabetes_positive_by_fasting_glucose
        ;
        diabetes_positive_by_hba1c
        ;
        diabetes_positive_by_random_glucose
        ;
        diabetes_positive_by_ogtt
    ).



diabetes :-
    diabetes_positive.



prediabetes :-
    fasting_glucose_mgdl(Value),
    number(Value),
    Value >= 100,
    Value < 126.



low_risk :-
    fasting_glucose_mgdl(Value),
    number(Value),
    Value < 100.



% =========================================================
% Main diagnostic workflow
% =========================================================

diagnose(Result) :-

    ask_random_plasma_glucose_mgdl(Random),

    (
        number(Random),
        Random >= 200
    ->
        Result =
            diabetes(random_glucose_mgdl(Random))

    ;

        ask_fasting_plasma_glucose_mgdl(Fasting),

        (
            number(Fasting),
            Fasting >=126
        ->
            Result =
                diabetes(fasting_glucose_mgdl(Fasting))

        ;

            ask_hba1c_percent(HbA1c),

            (
                number(HbA1c),
                HbA1c >=6.5
            ->
                Result =
                    diabetes(hba1c_percent(HbA1c))

            ;

                ask_ogtt_2h_plasma_glucose_mgdl(OGTT),

                (
                    number(OGTT),
                    OGTT >=200
                ->
                    Result =
                        diabetes(ogtt_2hr_mgdl(OGTT))

                ;

                    (
                        number(Fasting),
                        Fasting >=100,
                        Fasting <126
                    ->
                        Result =
                            prediabetes(fasting_glucose_mgdl(Fasting))

                    ;
                        Result = no_diabetes
                    )
                )
            )
        )
    ).



% =========================================================
% Symptoms
% =========================================================

symptom(excessive_thirst, yes) :-
    ask_boolean(
        'Does the patient have excessive thirst?'
    ).


symptom(excessive_urination, yes) :-
    ask_boolean(
        'Does the patient have excessive urination (polyuria)?'
    ).


symptom(fatigue, yes) :-
    ask_boolean(
        'Does the patient have fatigue?'
    ).


symptom(blurred_vision, yes) :-
    ask_boolean(
        'Does the patient have blurred vision?'
    ).



% =========================================================
% Medical history
% =========================================================

history(obesity) :-
    ask_boolean(
        'Does the patient have obesity?'
    ).


history(hypertension) :-
    ask_boolean(
        'Does the patient have hypertension?'
    ).


history(cardiovascular_disease) :-
    ask_boolean(
        'Does the patient have cardiovascular disease?'
    ).



% =========================================================
% Family history
% =========================================================

family_history(first_degree, diabetes) :-
    ask_boolean(
        'Is there a first-degree relative with diabetes?'
    ).


family_history(second_degree, diabetes) :-
    ask_boolean(
        'Is there a second-degree relative with diabetes?'
    ).



% =========================================================
% Medication
% =========================================================

medication_status(insulin) :-
    ask_boolean(
        'Is the patient on insulin therapy?'
    ).


medication_status(oral_antidiabetics) :-
    ask_boolean(
        'Is the patient on oral antidiabetic medication?'
    ).


medication_status(corticosteroids) :-
    ask_boolean(
        'Is the patient on corticosteroid therapy?'
    ).


medication_status(none) :-
    ask_boolean(
        'Is the patient taking no relevant medication?'
    ).