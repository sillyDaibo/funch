# FUNction searCH (funch)

A simple yet powerful evolutionary function search framework inspired by [FunSearch](https://github.com/google-deepmind/funsearch).

## Program Templates

funch works with template programs that define:
1. A main function decorated with `@funch.run` that will be evaluated
2. Evolving functions decorated with `@funch.evolve` that will be optimized
3. Validation functions decorated with `@funch.validate` (optional)

Example template (from tests/integration/cap_set/program.py):
```python
@funch.run
def basic(n: int) -> float:
    """Returns size of an n-dimensional cap set."""
    capset = solve(n)
    return len(capset)

@funch.evolve
def priority(el: tuple[int, ...], n: int) -> float:
    """Priority for adding element to cap set."""
    return 0.0

@funch.validate
def is_valid():
    assert isinstance(priority((1, 2, 3, 4, 5), 3), float | int)
```

## Key Components

- **Storage & Databases**: 
  - `ItemStorage` provides a high-level interface
  - `SQLiteStringDatabase` persists function candidates
  - Data persists between runs using `--db-file`

- **LLM Integration**:
  - `LLMClient` provides unified access to models
  - Supports OpenAI API and compatible endpoints
  - Configure model, temperature, and other params

- **FromTemplate**:
  - Parses template programs
  - Builds validation and scoring evaluators
  - Generates prompts from template structure

## CLI Usage

Basic command structure:
```bash
funch template.py --model MODEL_NAME [OPTIONS]
```

Example:
```bash
funch program.py \
  --model deepseek/deepseek-chat \
  --score-input 8 \
  --temperature 1.0 \
  --batch-size 3 \
  --iterations 3 \
  -v 1 \
  --workflow island \
  --num-islands 3 \
  --db-file data.db
```

Key options:
- `--model`: LLM model to use
- `--score-input`: Input value(s) to score against in JSON format
- `--temperature`: LLM creativity (0-2)
- `--batch-size`: Candidates generated per iteration  
- `--iterations`: Evolutionary iterations to run
- `--workflow`: "basic" or "island" workflow
- `--num-islands`: For island workflow
- `--db-file`: SQLite database file

For help:
```bash
funch -h
```
