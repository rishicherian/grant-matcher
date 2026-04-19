# Grant Matcher Agent

## Project layout

```

## Quick start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Set your Mistral API key as an environment variable:

```bash
export MISTRAL_API_KEY="ajTRTk18MnL7y8kd39uiVY8lSBuGC3mb"
```

3. Implement `build_memory_store()` in `src/memory_store.py`, then run:

```bash
python3 -m src.memory_store
```

4. Run the agent:

```bash
python3 -m src.run_agent
```

## Notes

- `sample_sources.json` contains example source objects.
- `sample_index.json` contains an example memory index format.
- Minimal expected fields are `text` plus optional metadata such as `url`, `title`, or `source`.
- This scaffold is intentionally simple so you can replace each module with stronger logic later (e.g., embeddings, LLM prompting, richer state).
