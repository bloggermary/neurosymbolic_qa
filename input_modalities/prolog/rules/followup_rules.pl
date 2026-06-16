%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Follow-up Question Generation Rules (Symbolic Layer)
% Used for structuring medically meaningful dialogue expansion
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Question Types
%%%%%%%%%%%%%%%%%%%%%%%%%%%%

question_type(diagnosis, "Ask about possible diseases from symptoms").
question_type(cause, "Ask about causes or risk factors").
question_type(treatment, "Ask about treatment options").
question_type(comparison, "Compare diseases or conditions").
question_type(severity, "Ask about seriousness or progression").


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Follow-up Generation Logic
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% If a disease has many symptoms → generate diagnostic follow-ups
followup_rule(Disease, diagnostic_followup) :-
    disease(Disease),
    symptom(Disease, S1),
    symptom(Disease, S2),
    S1 \= S2.


% If disease has risk factors → generate causality follow-ups
followup_rule(Disease, risk_followup) :-
    disease(Disease),
    risk_factor(Disease, _).


% If multiple treatments exist → generate treatment comparison follow-ups
followup_rule(Disease, treatment_followup) :-
    disease(Disease),
    treatment(Disease, T1),
    treatment(Disease, T2),
    T1 \= T2.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Question Expansion Rules
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Expand diagnosis reasoning
expand_question(Disease, QType) :-
    followup_rule(Disease, diagnostic_followup),
    QType = diagnosis.


% Expand causality reasoning
expand_question(Disease, QType) :-
    followup_rule(Disease, risk_followup),
    QType = cause.


% Expand treatment reasoning
expand_question(Disease, QType) :-
    followup_rule(Disease, treatment_followup),
    QType = treatment.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Follow-up Templates (Logical Skeletons)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

followup_template(diagnosis,
    "What other diseases could explain these symptoms?"
).

followup_template(cause,
    "What are the possible risk factors that could lead to this condition?"
).

followup_template(treatment,
    "What are the alternative treatment options for this condition?"
).

followup_template(severity,
    "How severe can this condition become if untreated?"
).

followup_template(comparison,
    "How does this disease differ from similar conditions?"
).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% High-level generator rule
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

generate_followup(Type, Question) :-
    followup_template(Type, Question).