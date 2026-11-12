# Thoughts

Each piece on the Thoughts page (divyaduraisamy.org/thoughts) is one `.txt` file in this folder.
The Streamlit site doesn't show them.

## Writing a piece

Make a file such as `on-autonomy.txt`. The file name becomes the web address
(`divyaduraisamy.org/thoughts/on-autonomy/`), so keep it short, lowercase, with hyphens.

```
Title: On autonomy
Date: 2026-11-20
Description: One sentence for Google to show under the link (optional).
Show: full
Draft: yes

The first paragraph.

The second paragraph. A single line break
stays a line break; a blank line starts a new paragraph.
```

- **Title** and **Date** (year-month-day) are required.
- **Description** is optional. Without it, Google is shown the start of the first paragraph.
- **Show: full** puts the whole piece on the Thoughts page (good for short pieces). Without it,
  the page shows the title, date and a preview, and readers click through for the rest.
- **Draft: yes** keeps the piece off the site. Delete that line when it's ready.
- The lines at the top end at the first blank line; everything after it is the piece.

The Thoughts page lists pieces newest first.

## Putting it on the site

    uv run python build_static.py

That rebuilds `docs/`. Then push as usual (dev first, then main).
