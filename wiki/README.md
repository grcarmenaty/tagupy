# Wiki source

This directory contains the source markdown for the project's GitHub wiki.

## Layout

GitHub-wiki conventions are used:

| File | Purpose |
|---|---|
| `Home.md` | Wiki landing page. |
| `_Sidebar.md` | Navigation panel rendered on every page. |
| `_Footer.md` | Footer rendered on every page. |
| `<Page-Name>.md` | Individual wiki pages. Filenames use `Title-Case-With-Hyphens`; inter-page links use `[[Page Name]]` (spaces, no `.md`). |

## Pages

- `Home` — overview and entry point.
- `Getting-Started` — install + run the bundled example.
- `Concepts` — orthogonal arrays, factor letters, interactions, additive model.
- `Workflow` — the canonical design → run → analyse → plot → save sequence.
- `Orthogonal-Arrays` — L8 / L16 / L32 / L32-inv specs and selection guide.
- `API-Reference` — every public class, method, and module.
- `Examples` — bundled script + notebook walkthrough.
- `MCP-Server` — exposing the library to AI assistants.
- `Testing` — running the suite, what each module covers.
- `Contributing` — coding conventions and PR process.
- `FAQ` — common pitfalls and questions.

## Publishing to the GitHub wiki

GitHub stores wikis in a separate repository (`<repo>.wiki.git`). To publish these pages:

```bash
git clone https://github.com/grcarmenaty/tagupy.wiki.git
cp wiki/*.md tagupy.wiki/
cd tagupy.wiki
git add .
git commit -m "Sync wiki from main repo"
git push origin master
```

Or wire up an Action that mirrors `wiki/` into the wiki repo on every merge to `main`.
