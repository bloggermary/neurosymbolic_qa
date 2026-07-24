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

/* Standalone diagnostic criteria predicates (no arguments) */

fasting_high :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value > 126.0.

hba1c_high :-
    ask_numeric('What is your HbA1c percentage (%)?', Value),
    Value > 6.5.

random_high :-
    ask_numeric('What is your random (casual) blood glucose in mg/dL?', Value),
    Value > 200.0.

ogtt2h_high :-
    ask_numeric('What is your 2-hour blood glucose after an oral glucose tolerance test in mg/dL?', Value),
    Value > 200.0.

/* Prediabetes criterion predicates (standalone) */

fasting_prediabetes :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    Value >= 100.0,
    Value < 126.0.

hba1c_prediabetes :-
    ask_numeric('What is your HbA1c percentage (%)?', Value),
    Value >= 5.7,
    Value < 6.5.

ogtt2h_prediabetes :-
    ask_numeric('What is your 2-hour blood glucose after an oral glucose tolerance test in mg/dL?', Value),
    Value >= 140.0,
    Value < 200.0.

/* Symptomatic exception: intense thirst (minimal question per text) */
symptomatic_exception :-
    ( ask_boolean('Do you experience marked (intense) thirst?') -> true ; false ).

/* diabetes/0 implements the diagnostic algorithm:
   - If any diagnostic test is positive and the patient has marked thirst, a single test suffices.
   - Otherwise require two independent positive diagnostic tests.
   The order of asking is chosen to minimize questions: fasting, HbA1c, random, then oGTT.
*/
diabetes :-
    % collect positives as we go; stop early when possible
    ( fasting_high ->
        ( symptomatic_exception -> true
        ; ( hba1c_high -> true
          ; random_high -> true
          ; ogtt2h_high -> true
          ; false
          )
        )
    ; hba1c_high ->
        ( symptomatic_exception -> true
        ; ( random_high -> true
          ; ogtt2h_high -> true
          ; false
          )
        )
    ; random_high ->
        ( symptomatic_exception -> true
        ; ( ogtt2h_high -> true
          ; false
          )
        )
    ; ogtt2h_high ->
        ( symptomatic_exception -> true
        ; false
        )
    ).

/* prediabetes/0: true if any prediabetes criterion is met and diabetes is not present.
   Uses standalone predicates that ask only the needed questions. */
prediabetes :-
    \+ diabetes,
    ( fasting_prediabetes
    ; hba1c_prediabetes
    ; ogtt2h_prediabetes
    ).

/* low_risk/0: neither diabetes nor prediabetes */
low_risk :-
    \+ diabetes,
    \+ prediabetes.

/* Main workflow predicate.
   Returns a janus-safe dict with a concise verdict.
*/
diagnose(Result) :-
    ( diabetes ->
        Result = _{verdict: diabetes}
    ; prediabetes ->
        Result = _{verdict: prediabetes}
    ; Result = _{verdict: low_risk}
    ).