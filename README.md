# benquinteros.com — Zola Resume & Portfolio

Minimal personal site built with Zola and deployed to GitHub Pages.

## Stack

- Zola static site generator
- GitHub Pages hosting
- GitHub Actions deployment (`main` -> `gh-pages`)
- Data-driven resume from `data/resume.toml`

## Project Structure

- `content/` markdown pages
- `templates/` Tera templates
- `data/resume.toml` source of truth for resume content
- `static/` static assets and `CNAME`
- `themes/BelResume/` vendored upstream theme source
- `.github/workflows/deploy.yml` deployment workflow

## Local Development

1. Install Zola: https://www.getzola.org/documentation/getting-started/installation/
2. Run locally:

```bash
zola serve
```

3. Build production output:

```bash
zola build
```

Generated files are output to `public/` (ignored by git).

## Theme Management

- Upstream theme: `https://github.com/cx48/BelResume` (MIT)
- Current approach: vendored copy in `themes/BelResume` for reproducible CI builds
- Zola best practice (Context7 docs): either vendored theme folder **or** git submodule are valid
- If updating manually, replace `themes/BelResume` from upstream and run `zola check`
- If switching to submodule later:

```bash
git submodule add https://github.com/cx48/BelResume themes/BelResume
git submodule update --init --recursive
```

## Resume Update Workflow (PDF -> TOML)

1. Upload your latest resume PDF to Copilot.
2. Ask Copilot to return content in this repository's `data/resume.toml` schema.
3. Replace/update `data/resume.toml`.
4. Run `zola serve` and verify `/resume/`.
5. Commit and push to `main`.

## Deployment

- Workflow: `.github/workflows/deploy.yml`
- Trigger: push to `main`
- Action builds and deploys `public/` to `gh-pages`
- Custom domain is preserved via `static/CNAME`

## Domain

- `base_url` in `config.toml` is set to `https://benquinteros.com`
- `static/CNAME` contains `benquinteros.com`