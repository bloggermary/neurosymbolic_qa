:- module(diabetes_diagnosis, [ask/1, diagnose/1]).
:- use_module(library(janus)).

% Bridge to an external yes/no question provider (Python UI).
ask(Question) :-
    py_call(diabetes_diagnosis:ask(Question), yes).

% Questions (only yes/no)
criterion(random_plasma_glucose,
          'Is the patient''s random plasma glucose >= 11.1 mmol/l (200 mg/dl)?').
criterion(fasting_plasma_glucose,
          'Is the patient''s fasting plasma glucose (after 8-12 hours fast) >= 7.0 mmol/l (126 mg/dl)?').
criterion(ogtt_2hour,
          'Is the patient''s 2-hour value in an oral glucose tolerance test >= 11.1 mmol/l?').
criterion(hba1c,
          'Is the patient''s HbA1c >= 48 mmol/mol (6.5%)?').

% Dynamic storage for collected answers
:- dynamic answer/2.

% Reset stored answers before each diagnostic session
reset_answers :-
    retractall(answer(_Question, _Answer)).

% Ask a single question exactly once and store the yes/no answer
ask_once(QuestionText) :-
    (   ask(QuestionText)
    ->  assertz(answer(QuestionText, yes))
    ;   assertz(answer(QuestionText, no))
    ).

% Ask all diagnostic questions (ensures every question is asked)
ask_all_questions :-
    forall(criterion(_Name, QuestionText),
           ask_once(QuestionText)).

% Collect which criteria are met based on stored answers
met_criteria(MetList) :-
    findall(Name,
            (   criterion(Name, QuestionText),
                answer(QuestionText, yes)
            ),
            MetList).

% Diagnose after collecting all answers. Returns diabetes(ListOfMetCriteria) or no_diabetes
diagnose(Diagnosis) :-
    reset_answers,
    ask_all_questions,
    met_criteria(Met),
    (   Met = []
    ->  Diagnosis = no_diabetes
    ;   Diagnosis = diabetes(Met)
    ).

% Support predicates for future extension (follow-up questions can be added)
% follow_up(CriterionName, QuestionText).
% Example usage in future extension:
% - Add follow_up/2 facts and modify ask_all_questions to ask them conditionally.