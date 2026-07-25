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

% Standalone diagnostic criterion predicates (each asks its own question).

% Fasting plasma glucose diagnostic for diabetes: > 126 mg/dL
fasting_glucose_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    ( Value > 126.0 -> true ; fail ).

% HbA1c diagnostic for diabetes: > 6.5 %
hba1c_criterion :-
    ask_numeric('What is your HbA1c (%) value?', Value),
    ( Value > 6.5 -> true ; fail ).

% Random (casual) blood glucose diagnostic for diabetes: > 200 mg/dL
random_glucose_criterion :-
    ask_numeric('What is your random (casual) blood glucose in mg/dL?', Value),
    ( Value > 200.0 -> true ; fail ).

% 2-hour value after oral glucose tolerance test diagnostic for diabetes: > 200 mg/dL
ogtt_2h_criterion :-
    ask_numeric('What is your 2-hour blood glucose after an oral glucose tolerance test in mg/dL?', Value),
    ( Value > 200.0 -> true ; fail ).

% Prediabetes criteria (commonly used thresholds; text did not specify exact numbers,
% these are standard clinical ranges). These are standalone so they can be queried directly.

% Fasting plasma glucose for prediabetes: 100-125 mg/dL inclusive lower bound, exclusive upper
fasting_prediabetes_criterion :-
    ask_numeric('What is your fasting plasma glucose in mg/dL?', Value),
    ( Value >= 100.0, Value < 126.0 -> true ; fail ).

% HbA1c for prediabetes: 5.7% - 6.4%
hba1c_prediabetes_criterion :-
    ask_numeric('What is your HbA1c (%) value?', Value),
    ( Value >= 5.7, Value < 6.5 -> true ; fail ).

% Helper to map test atom to its corresponding diagnostic predicate.
test_abnormal(fasting_glucose) :-
    fasting_glucose_criterion.
test_abnormal(hba1c) :-
    hba1c_criterion.
test_abnormal(random_glucose) :-
    random_glucose_criterion.
test_abnormal(ogtt_2h) :-
    ogtt_2h_criterion.

% Helper to map test atom to its corresponding prediabetes predicate.
test_prediabetes(fasting_glucose) :-
    fasting_prediabetes_criterion.
test_prediabetes(hba1c) :-
    hba1c_prediabetes_criterion.

% diabetes/0 determines whether diagnostic criteria for diabetes are met.
% It follows the rule: at least two independent abnormal test results are needed,
% unless the patient has typical symptoms (strong thirst, frequent urination, persistent fatigue),
% in which case a single clearly elevated test is sufficient.
diabetes :-
    % Ask which tests are available to avoid unnecessary questions.
    ask_multiple_category('Which blood glucose or HbA1c test results are available? Select all that apply.', [fasting_glucose,hba1c,random_glucose,ogtt_2h], AvailableTests),
    ( ask_boolean('Do you have notable symptoms such as strong thirst, frequent urination, or persistent fatigue?') -> Symptoms = true ; Symptoms = false ),
    % If symptoms present, a single clearly elevated available test is sufficient.
    ( Symptoms == true ->
        member(Test, AvailableTests),
        test_abnormal(Test)
    ;
      % No symptoms: prefer two independent abnormal tests.
      collect_abnormal_tests(AvailableTests, AbnormalList),
      length(AbnormalList, Count),
      ( Count >= 2 -> true
      ; Count =:= 1 ->
            % One abnormal test but no symptoms: ask if there is an independent confirmatory result (history or another test).
            ( ask_boolean('Is there another independent high test result (for example a previous separate measurement) that confirms high blood glucose?') -> true ; fail )
      ; % No abnormal tests among those provided -> cannot diagnose diabetes
            fail
      )
    ).

% Collect which of the provided tests are abnormal by calling the appropriate criterion.
collect_abnormal_tests([], []).
collect_abnormal_tests([TestAtom|Rest], Abnormals) :-
    ( test_abnormal(TestAtom) ->
        Abnormals = [TestAtom|Tail],
        collect_abnormal_tests(Rest, Tail)
    ;
        Abnormals = Tail,
        collect_abnormal_tests(Rest, Tail)
    ).

% prediabetes/0: true when diabetes is not present and one of the prediabetes ranges is met.
prediabetes :-
    \+ diabetes,
    % Ask which tests are available to only ask relevant measurements.
    ask_multiple_category('Which blood glucose or HbA1c test results are available to assess for prediabetes? Select all that apply.', [fasting_glucose,hba1c], Available),
    % If any available test meets prediabetes thresholds, classify as prediabetes.
    member(Test, Available),
    test_prediabetes(Test).

% low_risk/0: true when neither diabetes nor prediabetes criteria are met.
low_risk :-
    \+ diabetes,
    \+ prediabetes.

% Main workflow predicate.
% Returns a Janus-safe dict with verdict and evidence summary (list of atoms).
diagnose(Result) :-
    ( diabetes ->
        % Gather which tests were abnormal for evidence reporting if possible.
        ask_multiple_category('Which blood glucose or HbA1c test results are available? Select all that apply.', [fasting_glucose,hba1c,random_glucose,ogtt_2h], Tests1),
        ( Tests1 = [] -> Evidence = [diagnosis_based_on_tests_not_provided]
        ; collect_abnormal_tests(Tests1, Abnormals1),
          ( Abnormals1 = [] -> Evidence = [diagnosis_made_without_recorded_abnormal_tests]
          ; Evidence = Abnormals1
          )
        ),
        Result = _{verdict: diabetes, evidence: Evidence}
    ; prediabetes ->
        ask_multiple_category('Which blood glucose or HbA1c test results are available? Select all that apply.', [fasting_glucose,hba1c], Tests2),
        ( Tests2 = [] -> Evidence = [prediabetes_assessed_but_no_tests_provided]
        ; collect_prediabetes_tests(Tests2, Abnormals2),
          ( Abnormals2 = [] -> Evidence = [prediabetes_suspected_but_no_confirmatory_tests]
          ; Evidence = Abnormals2
          )
        ),
        Result = _{verdict: prediabetes, evidence: Evidence}
    ;
        % Neither diabetes nor prediabetes
        Result = _{verdict: low_risk, evidence: [] }
    ).

% Helper to collect which available tests meet prediabetes ranges.
collect_prediabetes_tests([], []).
collect_prediabetes_tests([TestAtom|Rest], Abnormals) :-
    ( test_prediabetes(TestAtom) ->
        Abnormals = [TestAtom|Tail],
        collect_prediabetes_tests(Rest, Tail)
    ;
        Abnormals = Tail,
        collect_prediabetes_tests(Rest, Tail)
    ).