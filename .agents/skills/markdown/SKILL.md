---
name: markdown
description: Markdown formatting standards for plotly-print. Use when creating or editing Markdown files.
paths:
  - "**/*.md"
---

# Markdown

ASCII only. No emojis, smart quotes, or non-English letters.

Use fenced code blocks with a language tag when the snippet has a language:

```python
from pathlib import Path

Path('data') / 'out.csv'
```

Do not leave unlabeled fences for Python, TOML, shell, or JSON. Plain fences are fine for output or prose examples with no language.

Keep heading levels, lists, and tables consistent within a file: one heading style, one list marker (`-`), one table alignment. Do not mix numbered and bulleted lists for the same kind of items.

Skip extra bold, italics, and emphasis. Highlight a term only when it would otherwise be missed.

Write short, plain sentences. If a technical term is necessary, introduce it in the same sentence.
