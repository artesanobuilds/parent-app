# MVP — Most Valuable Parent

The MVP parenting app in one repository: SwiftUI iOS, FastAPI backend, React parent dashboard, and admin CMS. Research, design, planning, and project-history documents are included alongside the implementation.

## Repository layout

- [`mvp/`](mvp/) — iOS application and Xcode project.
- [`mvp-backend/`](mvp-backend/) — FastAPI/LangGraph/DuckDB backend, with [setup instructions](mvp-backend/README.md).
- [`mvp-backend/parent-dashboard/`](mvp-backend/parent-dashboard/) — React parent-facing web app.
- [`mvp-backend/cms/`](mvp-backend/cms/) — React admin CMS.
- [`docs/`](docs/) — architecture, research, design, roadmaps, and project history.
- [`docs/GTM/research/2026-08-parent-planning-behavior/`](docs/GTM/research/2026-08-parent-planning-behavior/) — parent-planning research, sources, data, and findings.
- [`spec/`](spec/) — product and design specifications.
- [`pitch/`](pitch/) — presentation materials and supporting narrative.
- [`setup/`](setup/) — integration and service setup guides.
- [`tests/`](tests/) — cross-surface and natural-language test harnesses.

Read [the project context](docs/parent-app-context.md) for the implementation history, then [the latest research addendum](docs/GTM/2026-09-27-artist-led-research-addendum.md) for the current exploration. Older documents describe the state at their publication dates; their statements about having no GitHub remote are historical. No new product direction is implied by publishing this repository.

## Local development

Use Python 3.13+ for the backend:

```sh
cd mvp-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env
# Configure your own development credentials in .env.
uvicorn app.server:app --reload --port 8904
```

Run the dashboard separately:

```sh
cd mvp-backend/parent-dashboard
npm ci
npm run dev
```

The CMS has its own `package.json` and can be started with `npm ci` and `npm run dev` from `mvp-backend/cms/`. For iOS, open `mvp/MVP.xcodeproj`, configure your own signing team, and use `ServerConfiguration` to select your development backend.

## Data and credentials

This is a source-code and documentation repository, not a production backup. It includes the editorial article/category seeds. Family profiles, conversations, community snapshots, databases, credentials, local environment files, machine settings, and generated benchmark results are excluded from both the published tree and its retained history. Supply your own development secrets; do not commit them.

The original local development workspace is separate and remains unchanged. Historical commits were filtered for sharing, so their IDs differ from that original workspace while retained author/date information remains available. Clone this repository for collaboration rather than pushing the unfiltered original history into it.

Production deployment is a separate operation and requires explicit authorization. Publishing this repository does not deploy the app.
