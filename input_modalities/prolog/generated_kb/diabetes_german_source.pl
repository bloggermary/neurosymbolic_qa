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

% get_test_value/2
% Asks for the numeric value corresponding to a named test.
get_test_value(nuechternblutzucker, Value) :-
    ask_numeric('Wie hoch ist der nüchternblutzuckerwert in mg/dl?', Value).
get_test_value(hba1c, Value) :-
    ask_numeric('Wie hoch ist der HbA1c-Wert in Prozent (z.B. 6.5)?', Value).
get_test_value(gelegenheitsblutzucker, Value) :-
    ask_numeric('Wie hoch ist der Gelegenheitsblutzuckerwert in mg/dl?', Value).
get_test_value(ogtt, Value) :-
    ask_numeric('Wie hoch war der Blutzuckerwert zwei Stunden nach oraler Glukose in mg/dl?', Value).

% elevated_by_test/2
% True when a given numeric value for a test exceeds the diagnostic threshold.
elevated_by_test(nuechternblutzucker, Value) :-
    number(Value),
    Value > 126.0.
elevated_by_test(hba1c, Value) :-
    number(Value),
    Value > 6.5.
elevated_by_test(gelegenheitsblutzucker, Value) :-
    number(Value),
    Value > 200.0.
elevated_by_test(ogtt, Value) :-
    number(Value),
    Value > 200.0.

% collect_until_needed/3
% Collects measured test values from the list of available tests, asking each value in sequence,
% and stops as soon as Needed independent elevated results have been found or tests exhausted.
collect_until_needed(Tests, Needed, MeasuredOut, ElevatedOut) :-
    collect_until_needed(Tests, Needed, [], [], MeasuredOut, ElevatedOut).

collect_until_needed(_Tests, Needed, MeasuredAcc, ElevatedAcc, MeasuredAcc, ElevatedAcc) :-
    length(ElevatedAcc, L),
    L >= Needed, !.
collect_until_needed([], _Needed, MeasuredAcc, ElevatedAcc, MeasuredAcc, ElevatedAcc) :- !.
collect_until_needed([T|Ts], Needed, MeasuredAcc, ElevatedAcc, MeasuredOut, ElevatedOut) :-
    get_test_value(T, V),
    Entry = _{test:T, value:V},
    append(MeasuredAcc, [Entry], NewMeasuredAcc),
    ( elevated_by_test(T, V)
      -> append(ElevatedAcc, [Entry], NewElevAcc)
      ;  NewElevAcc = ElevatedAcc
    ),
    collect_until_needed(Ts, Needed, NewMeasuredAcc, NewElevAcc, MeasuredOut, ElevatedOut).

% diagnose/1
% Main entry. Returns a dictionary with verdict and evidence.
% Possible verdict atoms:
%  - diabetes (diagnosis reached)
%  - no_diabetes (tested >=2 times, not enough elevated results)
%  - insufficient_data (not enough tests to confirm or exclude)
diagnose(Result) :-
    % Ask about typical symptoms (polydipsia, polyuria, fatigue, reduced energy).
    ( ask_boolean('Hat die Person typische Beschwerden wie starkes Durstgefühl, häufiges Wasserlassen, anhaltende Müdigkeit oder verminderten Antrieb?')
      -> Symptoms = true
      ;  Symptoms = false
    ),
    % Ask which tests are available (user may select multiple).
    ask_multiple_category('Welche der folgenden Blutzuckertests liegen vor? (Wählen Sie alle zutreffenden)', 
                          [nuechternblutzucker, hba1c, gelegenheitsblutzucker, ogtt], AvailableTests),
    ( Symptoms = true ->
        % If symptomatic, a single clearly elevated value suffices.
        ( AvailableTests = [] ->
            Result = _{verdict: insufficient_data, evidence: []}
        ; collect_until_needed(AvailableTests, 1, Measured, Elevated),
          ( Elevated = [FirstElevated|_] ->
                Result = _{verdict: diabetes, evidence: Elevated}
          ;  % No elevated test among provided measurements
                Result = _{verdict: no_diabetes, evidence: Measured}
          )
        )
    ; % Symptoms = false
        % Without symptoms, need at least two independent elevated tests to diagnose.
        collect_until_needed(AvailableTests, 2, MeasuredAll, ElevatedAll),
        length(MeasuredAll, NumMeasured),
        length(ElevatedAll, NumElevated),
        ( NumElevated >= 2 ->
            Result = _{verdict: diabetes, evidence: ElevatedAll}
        ; NumMeasured < 2 ->
            Result = _{verdict: insufficient_data, evidence: MeasuredAll}
        ; % At least two tests available but fewer than two are elevated
            Result = _{verdict: no_diabetes, evidence: MeasuredAll}
        )
    ).