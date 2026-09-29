# Spelling Attempt Classifier

A simple, explainable classifier for deciding whether a child's incorrect typed answer is:

- `genuine_attempt`
- `random_or_meaningless`
- `uncertain`

## Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app has two modes:

1. Type an actual word and a child's attempt and classify it immediately.
2. Upload the assignment CSV and download the classified results.

## Approach

The classifier combines four simple signals:

- edit/spelling similarity
- approximate phonetic similarity
- whether target letters appear in the same order
- keyboard-mashing/repeated-character detection

The `uncertain` class prevents borderline examples from being forced into a binary decision.
