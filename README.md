# Dynamica Lab website

Source of the [Dynamica Research Lab](https://dynamicalab.github.io) website, built with [Quarto](https://quarto.org/).

The pages are not written by hand: `create-pages.py` reads the YAML files in `data/` and generates the Quarto pages (`home.qmd`, `news.qmd`, `team.qmd`, `pubs.qmd` and one `<id>.qmd` per member with a personal page), which Quarto then renders to HTML in `docs/`. The generated `.qmd` files and `docs/` are git-ignored, so **to change the site, edit the files in `data/`** (or `create-pages.py` for the layout), never the `.qmd` files.


## Building the site locally

Requirements: [uv](https://docs.astral.sh/uv/) and [Quarto](https://quarto.org/docs/get-started/) (Quarto is not a Python package and must be installed separately). PDFs are stored with [Git LFS](https://git-lfs.com/), so run `git lfs install` before cloning.

1. Install Python and the dependencies (Python version taken from `.python-version`):
   ```sh
   uv sync
   ```
2. Install the Quarto extensions (icons), only needed once:
   ```sh
   quarto add quarto-ext/fontawesome --no-prompt
   quarto add schochastics/academicons --no-prompt
   ```
3. Generate the `.qmd` pages from `data/`:
   ```sh
   uv run python create-pages.py
   ```
4. Render and browse the site, with live reload while editing:
   ```sh
   quarto preview
   ```
   This serves the site at a local URL.

Re-run step 3 every time a file in `data/` changes: `quarto preview` does not re-run `create-pages.py` by itself.


## Deployment

Every push to `main` triggers `.github/workflows/publish.yml`, which runs steps 1–3 above on GitHub Actions, renders the site and publishes `docs/` to GitHub Pages. It can also be started manually from the Actions tab (`workflow_dispatch`). Nothing needs to be built or committed locally to deploy.


## Repository layout

| Path | Content |
|---|---|
| `create-pages.py` | Generates the `.qmd` pages from `data/`. Constants at the top control role ordering, icons, labels, etc. |
| `data/team.yml` | Members and alumni, their positions and theses. |
| `data/pubs.yml` | Journal articles, proceedings, other writings and presentations. |
| `data/news.yml` | News items. |
| `data/home-about-us.md`, `data/home-group-picture.md` | Markdown blocks inserted in the home page. |
| `images/members/` | Member pictures (`default.png` is used when none is given). |
| `pdf/` | PDFs of papers and theses (Git LFS). |
| `cv/`, `slides/`, `posters/` | Files linked from member cards and publication entries. |
| `assets/js/` | Scripts used by the pages (e.g. truncation of news excerpts on the home page). |
| `custom.scss` | Site styles (on top of the `simplex` Bootswatch theme). |
| `_quarto.yml` | Quarto configuration: navbar, theme, output directory. |


## Editing the content

Each of `data/team.yml`, `data/pubs.yml` and `data/news.yml` starts with a commented example showing the supported fields; use them as the reference (copying an example is the easiest way to add an entry). The main rules are summarized below.

### Team (`data/team.yml`)

Each member has an `id` (`lastname-firstname`, used everywhere else to refer to them), a `name` and a list of `positions`, each with a `role`, a `start` year and an `end` year (no `end` means the position is still held).

- `role` must be one of the roles listed in `ROLE_ORDER` in `create-pages.py` (`Group leader`, `Honorary member`, `Postdoctoral fellow`, `PhD student`, `MSc student`, `Intern`), otherwise `create-pages.py` stops with a `KeyError`. The exception is `BSc student`, which is only used for the education section of personal pages and should be flagged `outside-of-dynamica: true` (see below).
- Current members are shown as cards, ordered by role. Members with `alumnus: true` are listed under *Alumni*, most recent departures first; `nowat` or `movedto` adds their current whereabouts.
- Optional fields: `picture` (file in `images/members/`), `email` (shown only for some roles, see `ROLE_WITH_EMAIL`), and `links` with any of `website`, `ul`, `orcid`, `gscholar`, `github`, `twitter`, `cv` (file in `cv/`).
- A `PhD student` or `MSc student` position can carry a `thesis` (`title`, `doi`, `pdf`, and `tableau-d-honneur: true` for theses added to the Board of Honor). Theses appear in the *Theses* section of the Publications page; their year is the position's `end` year.
- A position can list its supervisors under `supervisor` and its cosupervisors under `cosupervisor`. Both are lists of entries with a `name` (a member id or a plain name) and, for people who are not members of Dynamica, an optional `university` (defaults to `SUPERVISOR_UNIVERSITY_DEFAULT`, i.e. U. Laval). On personal pages, they are shown under the corresponding education entry as "Supervised by A, B and C (University)", supervisors first.

### Publications and presentations (`data/pubs.yml`)

Each entry has a `type`, a `title`, `authors` and a `year`. Authors are given either as a member `id` (highlighted as a lab member) or as a plain name (collaborator).

- Types shown under *Journal Articles & Writings*: `article` (`journal`, `volume`, `pages`), `conference-proceeding`, `book-chapter`, `other-writing` (`reference`).
- Types shown under *Presentations*: `invited-presentation`, `oral-presentation`, `poster-presentation` (`conference`, `location`). `presenters` lists who presented; it defaults to the first author.
- Optional links: `doi` (plus `open-access: true`), `pdf` (file in `pdf/`), `fulltext`, `arxiv`, `biorxiv`, `medrxiv`, `slides` (file in `slides/`), `poster` (file in `posters/`).
- Optional extras: `keywords` (list of tags) and `highlights` (list of short distinctions, shown with a star).
- Theses are not listed in `pubs.yml`: they are taken from the positions in `team.yml` (see above).

### News (`data/news.yml`)

Each item has a `date` (`YYYY-MM-DD`) and a `text` (Markdown). `members` lists the ids of the members involved, so the item also appears on their personal pages. `draft: true` hides an item everywhere. The home page shows the 10 most recent items (`NUMBER_NEWS_ITEMS`); the News page shows all of them, grouped by year.

### Personal pages

Setting `personal-page: true` on a member generates a CV-style page (`<id>.html`), linked from their name on the team page. It shows their `bio` (free text), education (degrees, theses and internships), publications, presentations and news.

Work done outside Dynamica can be added to a personal page without appearing on the lab's pages: any position, `pubs.yml` entry or `news.yml` item can be flagged `outside-of-dynamica: true`. It is then hidden from the home, news, team and publications pages and shown only on the personal pages of the members it belongs to (positions and publications get a "Not completed as a member of Dynamica" badge). Publications and presentations always go in `pubs.yml`, never in `team.yml`.
