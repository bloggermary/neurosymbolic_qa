# Template: Neurosymbolic Diabetes Diagnosis

A minimal working example of a neurosymbolic Q&A system that combines a Prolog knowledge base with a Python/LLM layer.

## Files

- [diabetes_diagnosis.pl](diabetes_diagnosis.pl) — Prolog rules encoding clinical diabetes screening logic (symptoms + lab values)
- [diabetes_diagnosis.py](diabetes_diagnosis.py) — Python entry point that loads the Prolog KB via `janus_swi` and runs a query

## Target Architecture

![Prolog QA System Architecture Overview](Prolog%20QA%20System%20Architecture%20Overview.drawio.svg)

## How it works

1. A Prolog knowledge base encodes the reasoning rules (the symbolic layer)
2. Python and Prolog call each other bidirectionally via [Janus](https://swi-prolog.org/pldoc/man?section=janus): Python uses `janus_swi`, Prolog uses `py_call`. See [Janus data conversion rules](https://www.swi-prolog.org/pldoc/man?section=janus-data) for how types map between the two languages.

   **Python → Prolog** (`janus_swi`): load the KB and run a query
   ```python
   import janus_swi as janus
   janus.consult("diabetes_diagnosis.pl")
   result = janus.query_once("diagnose")
   ```

   **Prolog → Python** (`py_call`): call back into a Python function during reasoning
   ```prolog
   :- use_module(library(janus)).
   ask(Question) :-
       py_call(diabetes_diagnosis:ask(Question), yes).
   ```
   Prolog calls `ask/1` defined in [diabetes_diagnosis.py](diabetes_diagnosis.py); the result `"yes"` is unified with the second argument to determine whether the goal succeeds.

3. The three `TODO` comments in the Python file mark where LLM calls must be added to complete the neurosymbolic pipeline:
   - Generate the `.pl` knowledge base from unstructured medical text
   - Translate a natural-language user question into a Prolog query
   - Translate the Prolog response back into a natural-language answer

## Requirements

- [SWI-Prolog](https://www.swi-prolog.org/) 9.1+ (Janus is built-in)
- [uv](https://docs.astral.sh/uv/) — fast Python package manager (replaces pip/venv)

## Installation

### 1. SWI-Prolog

**macOS**
```bash
brew install swi-prolog
```

**Ubuntu / Debian**
```bash
sudo apt install swi-prolog
```

**Windows** — download the installer from [swi-prolog.org/download](https://www.swi-prolog.org/download/stable).

Verify the install (must be 9.1+):
```bash
swipl --version
```

### 2. Run with uv

[uv](https://docs.astral.sh/uv/) manages the Python environment and executes the script — **a single command is all you need after installing SWI-Prolog:**

```bash
uv run diabetes_diagnosis.py
```

On first run, `uv` creates a virtual environment and installs `janus-swi` automatically. No separate `pip install` or `venv` activation needed.

Install uv itself (once, system-wide) if you don't have it:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
