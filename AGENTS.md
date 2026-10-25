# AGENTS.md

The brief is `../issues/101.md`. Read it before planning anything.

## Scope & layout

- Put project deliverables inside this `mcruft/` repo. The parent `mcruft-project/` is not under version control; vendor repositories have independent histories.
- `../vendors/*` is reference material only. Never path-import from it or path-depend on it. Depend on pinned git revisions instead.
- `README.md` still says "artcruft". The name is **mcruft**: the metapackage is `mcruft`, and each product gets `mcruft_<product>`. Don't use ArtCraft product names or trademarks as branding.

## Landmines

- `../vendors/storytold` is a symlink to an external volume (`/Volumes/Puck4T-Data/...`). Its `repos/` folder holds about 14 GB across 80+ repos. Never grep or index the whole tree; go straight to `repos/<app>/`. If the volume is unmounted, the path is dead.
- Don't edit anything under `storytold/repos/`. `craft-macupdate` fast-forwards only clean checkouts, so a local edit silently stops that repo from updating.
- Each product repo (`repos/<app>/`) has its own `AGENTS.md`. Read it before you bind that repo's crates.
- `../vendors/pydoccraft` already binds PdfCraft, WordCraft and DeckCraft crates with PyO3. Copy its rules:
  - Link only the format/engine crates. Never link UI, CLI, MCP, updater or network crates.
  - Pin every crate to a commit SHA.
  - Keep all crates from one repo on the same revision.
  - WordCraft and DeckCraft PDF export need `craft-libs`.
- `../vendors/craft-suite-api` targets the ArtCraft Services backend, not the desktop editors or their document APIs. Do not treat its MCP tools as proof of desktop-product coverage.
- The prebuilt CLIs are on PATH as `~/bin/craft-cli/<app>-cli`; the versioned zips are in `../vendors/storytold/craft-maccli/`. **Their flags differ per app**, so check `<app>-cli --help` instead of assuming one shape:
  - `vectorcraft-cli mcp` without `--headless` first tries to attach to a running GUI on 127.0.0.1. In tests, pass `--headless`, or a read/write root, which implies it.
  - `--automation-read-root` / `--automation-write-root` confine file access. If you omit the write root, the server can't write at all.
  - `photocraft-cli mcp` takes the read/write roots too, but attaches to a running app with `--bridge <127.0.0.1:port>` (plus `--control-token`) rather than `--connect`.
  - Batch syntax differs: `deckcraft-cli run --cmd 'id={json}'` versus `vectorcraft-cli run --cmd id --params '{json}'`. Index bases and rect conventions also differ per app (see `docs/research/products/README.md`).
  - The installed CLIs (0.10–0.16) are newer than the local checkouts' workspace versions. CLI facts describe the binaries; crate facts describe the checkouts.
  - The user's MCP configs in `~/.claude.json` show the working launch line for each app.

## Agent tooling & cost

- Work directly in one agent unless the user's current request explicitly asks for agents or delegation. Available CLIs are not permission to spawn agents.
- If delegation is requested, prefer the subscription CLIs `codex` and `claude`; use at most two concurrent agents with bounded tasks. The loop (brief → dispatch → independent review → controller commits) is in `docs/workflow.md`.
- Codex workers never commit (their sandbox cannot reliably write `.git`); the controller lands their diffs after re-running the gates.
- `SPEC.md` is the binding authority for design questions; `PLAN.md` lists the tasks. Change the spec first, then the code.
- `gemini-api` is billed per token. Use it only when the others can't do the job.
- For research, use `nlm` (NotebookLM) and `gdr` (Google Deep Research).
- Many of the configured MCP search servers are pay-per-use. Prefer the ones included in a subscription.

## Task constraints

- Spec first. Write the spec of the unified API and the `.mcruft` package format before implementing anything. Don't over-engineer, over-test or over-document.
- Model documents, pages, frames and embedded media first; products are engines selected for capabilities, not the top-level API structure.
- The format spec must cover native asset references, metadata and optional single-page PDF previews without requiring every asset to be converted into a new internal format.
- Research native-format libraries before selecting dependencies: record maintenance, licensing, Python binding availability and whether wheels include required native libraries. Prefer subscription-included research tools.
- For each MVP product, verify MCP, CLI and Rust-library capabilities separately against source and official documentation. Record unsupported operations; reference-product compatibility is a goal, not an established capability.
- The MVP covers the unified API, the `.mcruft` format, the native-format libraries, and the batch-1 products: VectorCraft, DeckCraft, PhotoCraft, PdfCraft and DesignCraft. Batch-2 products are out of scope until then.
- Every conversion has two variants: one that favours editability and one that favours visual fidelity.
- Define both conversion policies in the spec and report losses or unsupported routes explicitly; never imply a round trip preserves features without testing it.
- Each product's fully bundled wheel ships as its own package. Wheels must not download anything at runtime.
