from hashlib import sha1
from itertools import groupby
from pathlib import Path
from typing import Any
from copy import deepcopy

# --- Constants -----------------------

SHORTENED_AUTHORS = "..."

PICTURE_DEFAULT = "default.png"
PICTURE_PREFIX = "images/members/"

EMAIL_ICON = "{{< fa envelope >}}"
EMAIL_PREFIX = "mailto:"

ORCID_ICON = "{{< ai orcid >}}"
ORCID_PREFIX = "https://orcid.org/"

GITHUB_ICON = "{{< fa brands github >}}"
GITHUB_PREFIX = "https://github.com/"

WEBSITE_ICON = "{{< fa globe >}}"

GSCHOLAR_ICON = "{{< ai google-scholar >}}"
GSCHOLAR_PREFIX = "https://scholar.google.com/citations?user="

TWITTER_ICON = "{{< fa brands x-twitter >}}"
TWITTER_PREFIX = "https://x.com/"

CV_ICON = "{{< ai cv >}}"
CV_PREFIX = "cv/"

THESIS_ICON = "{{< fa book >}}"
THESIS_PREFIX = "thesess/"

OPEN_ACCESS_ICON = "{{< ai open-access color=#DD8452 size=lg >}}"

DOI_PREFIX = "https://doi.org/"

PDF_PREFIX = "pdf/"
POSTER_PREFIX = "posters/"
SLIDES_PREFIX = "slides/"

ARXIV_PREFIX = "https://arxiv.org/abs/"

UNIVERSITY_DEFAULT = "Université Laval"

# Shorter default used for the university of supervisors who are not members
# of Dynamica, shown in parentheses after their name on personal pages.
SUPERVISOR_UNIVERSITY_DEFAULT = "U. Laval"

DEGREE_DEFAULT = "Physics"

TABLEAU_HONNEUR = "Thesis added to the Board of Honor, the highest distinction at Université Laval."

NUMBER_NEWS_ITEMS = int(10)

# WARNING: Anyone whose current role is not in ROLE_ORDER will not appear.
ROLE_ORDER = [
    "Group leader",
    "Honorary member",
    "Postdoctoral fellow",
    "PhD student",
    "MSc student",
    "Intern",
]

# A personal CV-style page (id.qmd -> id.html) is generated for any member
# whose team.yml entry sets this flag to true.
PERSONAL_PAGE_KEY = "personal-page"

# Positions counted as "Education" entries on a personal page, mapped to the
# short degree label used there.
EDUCATION_ROLE_LABELS = {
    "PhD student": "PhD",
    "MSc student": "MSc",
    "BSc student": "BSc",
}

# Roles whose thesis (if any) feeds the "Theses" pseudo-type on the main
# Publications page and the thesis entry on a personal page.
ROLE_TO_THESIS_TYPE = {
    "PhD student": "phd-thesis",
    "MSc student": "msc-thesis",
}

# Any position, publication/presentation (data/pubs.yml) or news item
# (data/news.yml) can be flagged outside-of-dynamica: true. Such entries are
# excluded from every site-wide page (team.qmd, pubs.qmd, home.qmd, news.qmd)
# and shown only on the personal page of the member(s) they belong to.
OUTSIDE_OF_DYNAMICA_LABEL = "Not completed as a member of Dynamica"

# Prefix of the line listing the supervisors and cosupervisors of a position on
# a personal page. Supervisors who are not members of Dynamica (i.e. given by
# name rather than by id) are followed by their university, which defaults to
# SUPERVISOR_UNIVERSITY_DEFAULT.
SUPERVISORS_LABEL = "Supervised by"

ROLE_WITH_EMAIL = [
    "Group leader",
    "Honorary member",
    "Postdoctoral fellow",
    "PhD student",
    "MSc student",
]

PUB_TYPES = {
    "publication": "Journal Articles & Writings",
    "presentation": "Presentations",
    "thesis": "Theses",
}

PUB_WITH_YEAR = [
    "publication",
    "presentation",
    "thesis",
]

# The individual publication types grouped together under the combined
# "publication" pseudo-type used for the "Journal Articles & Writings" section.
PUBLICATION_TYPES = [
    "article",
    "conference-proceeding",
    "book-chapter",
    "other-writing",
]

# The individual presentation types grouped together under the combined
# "presentation" pseudo-type used for the "Presentations" section.
PRESENTATION_TYPES = [
    "invited-presentation",
    "oral-presentation",
    "poster-presentation",
]

# The individual thesis types grouped together under the combined "thesis"
# pseudo-type used for the "Theses" section. Order matters: within a given
# year, PhD theses are listed before MSc theses.
THESIS_TYPES = [
    "phd-thesis",
    "msc-thesis",
]

# Tag folded into the first line of the details of each presentation and
# thesis entry (as plain text, comma-separated). Not used for the "Journal
# Articles & Writings" group (article, conference-proceeding, book-chapter,
# other-writing) — those entries show no tag.
ENTRY_TAGS = {
    "invited-presentation": "Invited presentation",
    "oral-presentation": "Contributed presentation",
    "poster-presentation": "Poster presentation",
    "phd-thesis": "PhD thesis",
    "msc-thesis": "MSc thesis",
}


# --- Headers ----------------------------------------------------------------


HEADER_HOME_PAGE = """---
pagetitle: "Home"
format:
  html:
    page-layout: article
    grid:
      sidebar-width: 0px
      body-width: 950px
      margin-width: 0px
      gutter-width: 0.5em
aliases:
    - index.html
---

::: {style="display: flex; align-items: center; gap: 1rem;"}
![](images/logos/dynamica-bleu.svg){width="75px"}

[Dynamica Research Lab]{ .home-title }\\
[UNIVERSITÉ LAVAL, QUÉBEC, CANADA]{ .home-subtitle}
:::
[Understanding the structure and the dynamics of complex systems.]{ .home-subsubtitle}
"""

HEADER_NEWS_PAGE = """---
pagetitle: "News"
format:
  html:
    page-layout: article
    grid:
      sidebar-width: 0px
      body-width: 950px
      margin-width: 0px
      gutter-width: 0.5em
---
"""

HEADER_TEAM_PAGE = """---
pagetitle: "Team"
format:
  html:
    page-layout: article
    grid:
      sidebar-width: 0px
      body-width: 950px
      margin-width: 0px
      gutter-width: 0.5em
---
"""

HEADER_PUBS_PAGE = """---
pagetitle: "Publications"
format:
  html:
    page-layout: article
    toc: true
    toc-title: "Publications"
    toc-depth: 2
    grid:
      sidebar-width: 0px
      body-width: 700px
      margin-width: 250px
      gutter-width: 0.5em
---
"""

HEADER_MEMBER_PAGE = """---
pagetitle: "{name}"
format:
  html:
    page-layout: article
    toc: false
    grid:
      sidebar-width: 0px
      body-width: 800px
      margin-width: 150px
      gutter-width: 0.5em
---
"""


# --- Helpers ----------------------------------------------------------------


ROLE_RANK = {role: i for i, role in enumerate(ROLE_ORDER)}


def generate_news_item_slug(item: dict) -> str:
    """Stable anchor id ('YYYY-MM-DD-<hash>') for a news item, used to link the
    home-page excerpt to the full item on news.qmd."""
    date_str = item["date"].strftime("%Y-%m-%d") if hasattr(item["date"], "strftime") else str(item["date"])
    # slug the content so the slug is stable across rebuilds but changes if the item's text changes
    content = date_str + " ".join(item.get("members", "")) + item.get("text", "")
    digest = sha1(content.encode("utf-8")).hexdigest()[:6]
    return f"{date_str}-{digest}"


# def generate_pub_slug(item: dict) -> str:
#     """Stable anchor id ('pub-<hash>') for a publication, derived from its
#     title, DOI and PDF."""
#     content = item.get("title", "") + item.get("doi", "") + item.get("pdf", "")
#     digest = sha1(content.encode("utf-8")).hexdigest()[:6]
#     return f"pub-{digest}"


def get_dynamica_positions(member: dict[str, Any]) -> list[dict[str, Any]]:
    """A member's positions actually held within Dynamica. Positions flagged
    outside-of-dynamica (e.g. a degree earned elsewhere) are excluded from
    every site-wide page and only ever considered on that member's own
    personal page."""
    return [pos for pos in member.get("positions", []) if not pos.get("outside-of-dynamica")]


def get_latest_role(member: dict[str, Any]) -> str:
    """Role tied to a position with no 'end' (i.e. still active), else the role of the most recently ended position."""
    positions = get_dynamica_positions(member)
    for pos in positions:
        if "end" not in pos:
            return pos["role"]
    return max(positions, key=lambda p: p["end"])["role"]


def get_member_icon_links(member: dict[str, Any]) -> str:
    """Icon row used on member cards (includes email)."""
    parts = []
    if "email" in member:
        if get_latest_role(member) in ROLE_WITH_EMAIL:
            parts.append(f"[{EMAIL_ICON}]({EMAIL_PREFIX}{member['email']}){{ .member-icon }}")

    links = member.get("links") or {}
    if "ul" in links:
        parts.append(f"[UL]({links['ul']}){{ .member-icon .icon-text }}")
    if "website" in links:
        parts.append(f"[{WEBSITE_ICON}]({links['website']}){{ .member-icon }}")
    if "orcid" in links:
        parts.append(f"[{ORCID_ICON}]({ORCID_PREFIX}{links['orcid']}){{ .member-icon }}")
    if "gscholar" in links:
        parts.append(f"[{GSCHOLAR_ICON}]({GSCHOLAR_PREFIX}{links['gscholar']}){{ .member-icon }}")
    if "cv" in links:
        parts.append(f"[{CV_ICON}]({CV_PREFIX}{links['cv']}){{ .member-icon }}")
    if "github" in links:
        parts.append(f"[{GITHUB_ICON}]({GITHUB_PREFIX}{links['github']}){{ .member-icon }}")
    if "twitter" in links:
        parts.append(f"[{TWITTER_ICON}]({TWITTER_PREFIX}{links['twitter']}){{ .member-icon }}")
    return "".join(parts)


def get_alumni_icon_links(member: dict[str, Any]) -> str:
    """Icon row used on the alumni list (no email, space-separated)."""
    links = member.get("links") or {}
    parts = []
    if "website" in links:
        parts.append(f" [{WEBSITE_ICON}]({links['website']})")
    if "orcid" in links:
        parts.append(f" [{ORCID_ICON}]({ORCID_PREFIX}{links['orcid']})")
    if "gscholar" in links:
        parts.append(f" [{GSCHOLAR_ICON}]({GSCHOLAR_PREFIX}{links['gscholar']})")
    return "".join(parts)


def get_alumni_position_chain(member: dict[str, Any]) -> str:
    """'Role A [thesis] → Role B → ...' ordered by end date, ascending."""
    positions = sorted(get_dynamica_positions(member), key=lambda p: p["end"])
    links = []
    for pos in positions:
        label = pos["role"]
        if pos.get("thesis"):
            pub_type = ROLE_TO_THESIS_TYPE.get(pos["role"], pos["role"])
            slug = f"{member["id"]}-{pub_type}"
            label += f" [{THESIS_ICON}](pubs.qmd#{slug})"
            # if pos["thesis"].get("doi"):
            #     label += f" [{THESIS_ICON}]({DOI_PREFIX}{pos["thesis"]["doi"]})"
            # elif pos["thesis"].get("pdf"):
            #     label += f" [{THESIS_ICON}]({THESIS_PREFIX}{pos["thesis"]["pdf"]})"
        links.append(label)
    links = list(dict.fromkeys(links))
    return " \u2192 ".join(links)


def get_pub_title(pub: dict[str, Any]) -> str:
    """Publication title as a styled span, carrying the entry's id (if any) as
    its anchor."""
    pubID = pub.get("id", "")
    return f"[{pub.get("title", "title is missing...")}]{{{pubID} .pub-title }}"


def get_pub_authors(pub: dict[str, Any],
                    id2name: dict[str, str],
                    id2page: dict[str, bool]) -> str:
    """Authors line, with Dynamica members (ids found in id2name) styled
    differently from collaborators and presenters highlighted. For a
    presentation with no 'presenters', the first author is taken as the
    presenter."""

    presenters = pub.get("presenters") or []
    if pub.get("type") in PRESENTATION_TYPES and not presenters:
        presenters = [pub["authors"][0]]

    authors = []

    num_authors = len(pub["authors"])
    # Arbitrary rules to the cut number of authors shown
    shorten = num_authors > 8
    display_dots = True
    for i, author_id in enumerate(pub["authors"]):
        is_member = author_id in id2name
        if shorten:
            if not is_member and 1 < i < num_authors-1:
                if display_dots:
                    authors.append(SHORTENED_AUTHORS)
                display_dots = False
                continue
            display_dots = True

        has_personal_page = id2page.get(author_id)
        authors.append(
            "[{author_name}]{link}{{ {tag1} {tag2} {tag3} }}"\
            .format(
                author_name=id2name.get(author_id, author_id),
                link=f"({author_id}.html)" if has_personal_page else "",
                tag1=".pub-author-member" if author_id in id2name else ".pub-author-collaborator",
                tag2=".pub-author-page" if has_personal_page else ".pub-author-nopage",
                tag3=".author-presenter" if author_id in presenters else "",
            )
        )

    if num_authors == 1:
        return f"[{authors[0]}]{{ .pub-authors }}"
    else:
        last_separator = ", " if authors[-2] == SHORTENED_AUTHORS else " and"
        return f"[{', '.join(authors[:-1])}{last_separator} {authors[-1]}]{{ .pub-authors }}"


def get_journal_reference(pub: dict[str, Any]) -> str:
    """'Journal volume, pages (year)' line for an article; empty if no journal
    is given (e.g. a preprint)."""
    journal_reference = []
    if pub.get("journal"):  # journal details omitted if preprint
        journal_reference.append(f"{pub['journal']}")
        if pub.get("volume"):
            journal_reference.append(f"{pub['volume']},")
        if pub.get("pages"):
            journal_reference.append(f"{pub['pages']}")
        if pub.get("year"):
            journal_reference.append(f"({pub['year']})")
    if not journal_reference:
        return ""
    return "[" + " ".join(journal_reference) + f"]{{ .pub-details }}"


def get_conference_details(pub: dict[str, Any]) -> list[str]:
    """Up to two detail lines for a presentation or conference proceeding:
    '<tag>, <conference>' then '<location>, <year>'."""
    conference_details = []
    first_line = []
    tag = ENTRY_TAGS.get(pub.get("type")) # pyright: ignore[reportArgumentType]
    if tag:
        first_line.append(tag)
    if pub.get("conference"):
        first_line.append(f"{pub['conference']}")
    if first_line:
        conference_details.append("[" + ", ".join(first_line) + f"]{{ .pub-details }}")
    second_line = []
    if pub.get("location"):
        second_line.append(f"{pub['location']},")
    if pub.get("year"):
        second_line.append(f"{pub['year']}")
    if second_line:
        conference_details.append("[" + " ".join(second_line) + f"]{{ .pub-details }}")
    return conference_details


def get_thesis_details(pub: dict[str, Any]) -> str:
    """'<tag>, <university> (<year>)' detail line for a thesis."""
    parts = []
    tag = ENTRY_TAGS.get(pub.get("type")) # pyright: ignore[reportArgumentType]
    if tag:
        parts.append(tag)
    parts.append(f"{pub["university"]} ({pub["year"]})")
    return "[" + ", ".join(parts) + f"]{{ .pub-details }}"


def get_pub_body_details(pub: dict[str, Any]) -> list[str]:
    """Detail lines (reference, conference, thesis university, etc.) shown
    below the authors line, dispatched on the publication's actual type."""
    pub_type = pub.get("type")

    if pub_type == "article":
        reference = get_journal_reference(pub)
        return [reference] if reference else []

    if pub_type in ["conference-proceeding", *PRESENTATION_TYPES]:
        return get_conference_details(pub)

    if pub_type == "other-writing":
        if pub.get("reference"):
            return [f"[{pub['reference']}]{{ .pub-details }}"]
        return []

    if pub_type == "book-chapter":
        return []

    if pub_type in THESIS_TYPES:
        return [get_thesis_details(pub)]

    return []


def get_pub_links(pub: dict[str, Any]) -> str:
    """'doi | pdf | arXiv | ...' row of the links available for an entry, with
    an open-access icon next to the DOI when applicable."""
    links = []
    if pub.get("doi"):
        doi = f"[doi]({DOI_PREFIX}{pub['doi']}){{ .pub-link }}"
        if pub.get("open-access"):
            doi += f" {OPEN_ACCESS_ICON}"
        links.append(doi)
    if pub.get("pdf"):
        links.append(f"[pdf]({PDF_PREFIX}{pub['pdf']}){{ .pub-link }}")
    if pub.get("fulltext"):
        links.append(f"[full text]({pub['fulltext']}){{ .pub-link }}")
    if pub.get("arxiv"):
        links.append(f"[arXiv]({ARXIV_PREFIX}{pub['arxiv']}){{ .pub-link }}")
    if pub.get("biorxiv"):
        links.append(f"[bioRxiv]({DOI_PREFIX}{pub['biorxiv']}){{ .pub-link }}")
    if pub.get("medrxiv"):
        links.append(f"[medRxiv]({DOI_PREFIX}{pub['medrxiv']}){{ .pub-link }}")
    if pub.get("slides"):
        links.append(f"<a class='pub-link' target='_blank' href='{SLIDES_PREFIX}{pub['slides']}'>slides<a>")
    if pub.get("poster"):
        links.append(f"<a class='pub-link' target='_blank' href='{POSTER_PREFIX}{pub['poster']}'>poster<a>")
    return " | ".join(links)


def get_pub_keywords(keywords: list[str]) -> str:
    """Keywords shown as a row of styled tags; empty if there are none."""
    if not keywords:
        return ""
    inner = " ".join(f"[{kw}]{{.pub-keyword}}" for kw in keywords)
    return f"[{inner}]{{.pub-keywords}}"


def get_pub_highlights(pub: dict[str, Any]) -> list[str]:
    """Starred highlight lines for an entry: its 'highlights' list, plus the
    Board of Honor distinction for theses flagged tableau-d-honneur."""

    items = []
    if pub.get("type") in ["phd-thesis", "msc-thesis"]:
        if pub.get("tableau-d-honneur"):
            items.append(f"[\u2605 {TABLEAU_HONNEUR}]{{ .pub-highlight }}")
    if pub.get("highlights"):
        for highlight in pub.get("highlights"): # pyright: ignore[reportOptionalIterable]
            items.append(f"[\u2605 {highlight}]{{ .pub-highlight }}")
    return items


def get_outside_badge(item: dict[str, Any]) -> str:
    """Marker shown on a personal page for entries flagged as not done as a member of Dynamica."""
    if not item.get("outside-of-dynamica"):
        return ""
    return f"[{OUTSIDE_OF_DYNAMICA_LABEL}]{{ .pub-outside-badge }}"


def get_position_supervisors(pos: dict[str, Any]) -> list[dict[str, Any]]:
    """Supervisors then cosupervisors of a position, each as a dict with a
    'name' (member id or plain name) and an optional 'university'."""
    return [*(pos.get("supervisor") or []), *(pos.get("cosupervisor") or [])]


def get_supervisors_line(supervisors: list[dict[str, Any]], id2name: dict[str, str]) -> str:
    """'Supervised by A, B and C (University)' line shown under an education
    entry on a personal page. Member ids are replaced by names; supervisors who
    are not members are followed by their university. Empty if there are no
    supervisors."""
    if not supervisors:
        return ""
    names = []
    for sup in supervisors:
        if sup["name"] in id2name:
            names.append(id2name[sup["name"]])
        else:
            names.append(f"{sup['name']} ({sup.get('university', SUPERVISOR_UNIVERSITY_DEFAULT)})")
    if len(names) == 1:
        listed = names[0]
    else:
        listed = f"{', '.join(names[:-1])} and {names[-1]}"
    return f"[{SUPERVISORS_LABEL} {listed}]{{ .education-supervisors }}"


def get_member_education_entries(member: dict[str, Any]) -> list[dict[str, Any]]:
    """Education entries for a personal page, derived from ALL of the member's
    positions (student roles), including ones flagged outside-of-dynamica
    (e.g. a degree obtained before joining Dynamica). Internships are nested
    as sub-entries under the BSc entry, if there is one."""
    entries = []
    internships = []
    for pos in member.get("positions", []):
        role = pos.get("role")
        if role == "Intern":
            internships.append(pos)
            continue
        if role not in EDUCATION_ROLE_LABELS:
            continue
        thesis_type = ROLE_TO_THESIS_TYPE.get(role)
        entries.append({
            "role": role,
            "label": f"{EDUCATION_ROLE_LABELS[role]} in {pos.get("degree", DEGREE_DEFAULT)}",
            "institution": pos.get("university", UNIVERSITY_DEFAULT),
            "start": pos.get("start"),
            "end": pos.get("end"),
            "thesis": pos.get("thesis"),
            "thesis-anchor": f"#{member["id"]}-{thesis_type}" if thesis_type else None,
            "supervisors": get_position_supervisors(pos),
            "outside-of-dynamica": pos.get("outside-of-dynamica", False),
            "sub-entries": [],
        })

    bsc_entry = next((e for e in entries if e["role"] == "BSc student"), None)
    if bsc_entry:
        for pos in internships:
            bsc_entry["sub-entries"].append({
                "label": "Internship",
                "institution": pos.get("university"),
                "start": pos.get("start"),
                "end": pos.get("end"),
                "supervisors": get_position_supervisors(pos),
                "outside-of-dynamica": pos.get("outside-of-dynamica", False),
            })
        bsc_entry["sub-entries"].sort(key=lambda e: (e.get("end") or e.get("start") or 0, e.get("start") or 0), reverse=True)

    entries.sort(key=lambda e: (e.get("end") or e.get("start") or 0, e.get("start") or 0), reverse=True)
    return entries


def get_member_own_theses(member: dict[str, Any]) -> list[dict[str, Any]]:
    """All of a member's own theses, drawn from ALL of their positions
    (including ones flagged outside-of-dynamica). For use on a personal page
    only — the main Publications page draws theses from _collect_thesis_items
    instead, which excludes outside-of-dynamica positions."""
    items = []
    for pos in member.get("positions", []):
        thesis_type = ROLE_TO_THESIS_TYPE.get(pos.get("role"))
        if not thesis_type:
            continue
        entry = _build_thesis_entry(member, pos, thesis_type)
        if entry:
            items.append(entry)
    return items


def get_member_publications(member: dict[str, Any],
                            pubs: list[dict[str, Any]],
                            team: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A member's journal articles & writings and theses, combined. Includes
    data/pubs.yml entries flagged outside-of-dynamica, which are hidden from
    pubs.qmd."""
    member_id = member["id"]
    items = [pub for pub in pubs if pub.get("type") in PUBLICATION_TYPES and member_id in pub.get("authors", [])]
    items.extend(get_member_own_theses(member))
    items.sort(key=lambda p: p.get("year", 0), reverse=True)
    return items


def get_member_presentations(member: dict[str, Any],
                             pubs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """A member's presentations, including data/pubs.yml entries flagged
    outside-of-dynamica, which are hidden from pubs.qmd."""
    member_id = member["id"]
    items = [
        pub for pub in pubs
        if pub.get("type") in PRESENTATION_TYPES
        and (member_id in pub.get("authors", []) or member_id in pub.get("presenters", []))
    ]
    items.sort(key=lambda p: p.get("year", 0), reverse=True)
    return items


def build_pub_entry(pub: dict[str, Any], id2name: dict[str, str], id2page: dict[str, bool]) -> str:
    """A single publication/presentation entry, formatted the same way as on
    the main Publications page, with an added badge for entries flagged as
    not done as a member of Dynamica."""
    title = get_pub_title(pub)
    entry = [get_pub_authors(pub, id2name, id2page)]
    entry.extend(get_pub_body_details(pub))
    entry.append(get_pub_links(pub))
    if pub.get("keywords"):
        entry.append(get_pub_keywords(pub.get("keywords"))) # pyright: ignore[reportArgumentType]
    entry.extend(get_pub_highlights(pub))
    entry.append(get_outside_badge(pub))
    entry = [part for part in entry if part]
    content = f'::: {{ .pub-content }}\n' + "\n\n".join(entry) + '\n:::\n'
    return f'::: {{ .pub-entry }}\n' + "\n\n".join([title, content]) + '\n:::\n'


def _build_thesis_entry(person: dict[str, Any], pos: dict[str, Any], thesis_type: str) -> dict[str, Any] | None:
    """Publication-like dict built from the thesis attached to a position, so it
    can be rendered like any other entry (its year is the position's end year).
    None if the position has no thesis."""
    thesis = pos.get("thesis")
    if not thesis:
        return None
    entry = dict(thesis)  # copy to avoid mutating source
    entry["type"] = thesis_type
    entry["id"] = f"#{person.get("id")}-{thesis_type}"
    entry["authors"] = [person.get("id")] # pyright: ignore[reportArgumentType]
    entry["presenters"] = [person.get("presenters")] # pyright: ignore[reportArgumentType]
    entry["year"] = pos.get("end")
    entry["university"] = pos.get("university", UNIVERSITY_DEFAULT)
    if pos.get("outside-of-dynamica"):
        entry["outside-of-dynamica"] = True
    return entry


def _collect_thesis_items(thesis_type: str, team: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Theses for the main Publications page. Positions flagged
    outside-of-dynamica are excluded — such theses only ever appear on the
    owning member's personal page, via get_member_own_theses."""
    position = thesis_type.replace("phd-thesis", "PhD student")\
                          .replace("msc-thesis", "MSc student")
    items = []
    for person in team:
        for pos in get_dynamica_positions(person):
            if pos.get("role", "").strip().lower() == position.strip().lower():
                entry = _build_thesis_entry(person, pos, thesis_type)
                if entry:
                    items.append(entry)
    return items


def get_pubs_by_year(pub_type: str,
                     pubs: list[dict[str, Any]],
                     team: list[dict[str, Any]]) -> dict:
    """Entries of a given type for the main Publications page, grouped by year
    as {year: [entries]}. pub_type is either a PUB_TYPES pseudo-type or an
    individual type. Entries flagged outside-of-dynamica are excluded."""

    if pub_type == "thesis":

        # PhD theses are listed before MSc theses within a given year.
        thesis_rank = {t: i for i, t in enumerate(THESIS_TYPES)}
        items = [item for t in THESIS_TYPES for item in _collect_thesis_items(t, team)]
        items_by_year = sorted(items, key=lambda p: (p["year"], thesis_rank[p["type"]]))  # groupby requires the input sorted by the grouping key first
        return {year: list(pubs) for year, pubs in groupby(items_by_year, key=lambda p: p["year"])}

    elif pub_type in THESIS_TYPES:

        items = _collect_thesis_items(pub_type, team)
        items_by_year = sorted(items, key=lambda p: p["year"])  # groupby requires the input sorted by the grouping key first
        return {year: list(pubs) for year, pubs in groupby(items_by_year, key=lambda p: p["year"])}

    elif pub_type == "presentation":

        items = [pub for pub in pubs if pub.get("type") in PRESENTATION_TYPES and not pub.get("outside-of-dynamica")]
        items_by_year = sorted(items, key=lambda p: p["year"])  # groupby requires the input sorted by the grouping key first
        return {year: list(pubs) for year, pubs in groupby(items_by_year, key=lambda p: p["year"])}

    elif pub_type == "publication":

        items = [pub for pub in pubs if pub.get("type") in PUBLICATION_TYPES and not pub.get("outside-of-dynamica")]
        items_by_year = sorted(items, key=lambda p: p["year"])  # groupby requires the input sorted by the grouping key first
        return {year: list(pubs) for year, pubs in groupby(items_by_year, key=lambda p: p["year"])}

    else:

        items = [pub for pub in pubs if pub.get("type") == pub_type and not pub.get("outside-of-dynamica")]
        items_by_year = sorted(items, key=lambda p: p["year"])  # groupby requires the input sorted by the grouping key first
        return {year: list(pubs) for year, pubs in groupby(items_by_year, key=lambda p: p["year"])}


def get_news_by_year(news: list[dict[str, Any]]) -> dict:
    """Published news items (no drafts, nothing flagged outside-of-dynamica)
    grouped by year as {year: [items]}, newest first."""
    news_items = [n for n in news if not n.get("draft", False) and not n.get("outside-of-dynamica", False)]
    news_items = sorted(news_items, key=lambda p: p["date"], reverse=True) # groupby requires the input sorted by the grouping key first
    return {year: list(pubs) for year, pubs in groupby(news_items, key=lambda p: p["date"].year)}


def get_news_item_home(item: dict) -> str:
    """Short news excerpt for the home page, with a [more] link to the full item
    on news.qmd."""
    slug = generate_news_item_slug(item)

    parts = [
        f'::: {{#news-{slug} .home-news-item }}',
        '',
        '::: { .home-news-excerpt }',
        f'[{item["date"]}]{{ .news-date }} \u2014 {item.get("text", "")}',
        ':::',
        '',
        '::: { .home-news-more-details }',
        f'[[more]](/news.qmd#news-{slug})',
        ':::',
        '',
        ':::',
        '',
    ]
    return "\n".join(parts) + "\n"


def get_news_item_full(item: dict) -> str:
    """Full news item, as shown on news.qmd and on personal pages, anchored so
    that home-page excerpts can link to it."""
    slug = generate_news_item_slug(item)

    parts = [
        '',
        f'::: {{#news-{slug} .news-item }}',
        '',
        '::: { .news-body }',
        f'[{item["date"]}]{{ .news-date }} \u2014 {item.get("text", "")}',
        ':::',
        '',
        ':::',
    ]
    return "\n".join(parts) + "\n"


def get_recent_news(news: list[dict[str, Any]], n: int = 10) -> list[dict]:
    """The n most recent published news items (no drafts, nothing flagged
    outside-of-dynamica), newest first."""
    news_items = [item for item in news if not item.get("draft", False) and not item.get("outside-of-dynamica", False)]
    if len(news_items) < n:
        n = len(news_items)
    return sorted(news_items, key=lambda p: p["date"], reverse=True)[:n]


def get_member_news(member: dict[str, Any], news: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """News items a member is tagged in (via the item's 'members' list), newest first."""
    member_id = member["id"]
    items = [item for item in news if not item.get("draft", False) and member_id in item.get("members", [])]
    return sorted(items, key=lambda item: item["date"], reverse=True)





# --- Section builders ---------------------------------------------------

def build_current_members_section(items: list[dict[str, Any]]) -> str:
    """'Current Members' grid of member cards (picture, name, role, icon links),
    ordered by ROLE_ORDER then by id. Names link to personal pages when they
    exist."""

    # Gets a list of current members
    current = [m for m in items if not m.get("alumnus", False)]

    # Sorts following ROLE_ORDER. Within a same role, sorts in alphabetical order
    role_rank = {role: i for i, role in enumerate(ROLE_ORDER)}
    entries = [{"member": member, "role": get_latest_role(member), "id": member["id"]} for member in current]
    entries.sort(key=lambda e: (role_rank[e["role"]], e["id"]))

    lines = ["# Current Members", ":::: {.grid}"]
    for entry in entries:
        member = entry["member"]
        role = get_latest_role(member)
        picture = member.get("picture", PICTURE_DEFAULT)
        lines.append("")
        lines.append("::: {.g-col-6 .g-col-sm-4 .g-col-md-3 .g-col-lg-3 .member-card}")

        if member.get(PERSONAL_PAGE_KEY):
            url = f"{member['id']}.html"
            lines.append("::: {.member-clickable-handle}")
            lines.append(f"<a href='{url}'>")
        lines.append(f"![]({PICTURE_PREFIX}{picture}){{.rounded-circle height=120}}")
        lines.append(f"[{member['name']}]{{ .member-name }}")
        if member.get(PERSONAL_PAGE_KEY):
            lines.append("</a>")
            lines.append(":::")

        lines.append(f"{role}")
        lines.append(get_member_icon_links(member))
        lines.append(":::")

    lines.append("")
    lines.append("::::")
    return "\n\n".join(lines)


def build_alumni_section(items: list[dict[str, Any]]) -> str:
    """'Alumni' list, one line per alumnus: name, links, chain of roles held,
    years at Dynamica and current whereabouts. Most recent departures first."""

    # Gets a list of alumni.
    alumni = [m for m in items if m.get("alumnus")]

    # Sorts in reverse order of graduation year. Within a same graduation year, sorts following ROLE_ORDER
    entries = [{"member": member, "role": get_latest_role(member), "max_end": max(p["end"] for p in get_dynamica_positions(member))} for member in alumni]
    entries.sort(key=lambda e: (-e["max_end"], ROLE_RANK[e["role"]]))

    lines = ["# Alumni"]
    for entry in entries:
        member = entry["member"]
        max_end = entry["max_end"]
        min_start = min(p["start"] for p in get_dynamica_positions(member))

        name = f"[{member['name']}]({member['id']}.html)" if member.get(PERSONAL_PAGE_KEY) else member["name"]
        line = f"{name}{get_alumni_icon_links(member)} | "
        line += f"{get_alumni_position_chain(member)} | "
        if min_start == max_end:
            line += f"{min_start}"
        else:
            line += f"{min_start}\u2013{max_end}"

        if "nowat" in member:
            line += f" | Now {member['nowat']}"
        elif "movedto" in member:
            line += f" | Moved to {member['movedto']}"

        lines.append("")
        lines.append(line)

    return "\n".join(lines)


def build_member_page_header(member: dict[str, Any]) -> str:
    """Top of a personal page: picture, name, current role and icon links."""

    picture = member.get("picture", PICTURE_DEFAULT)
    role = get_latest_role(member)

    lines = [
        "::: { .member-page-header }",
        "",
        f"![]({PICTURE_PREFIX}{picture}){{ .member-page-picture }}",
        "",
        "::: { .member-page-headtext }",
        "",
        f"# {member['name']}",
        "",
        f"[{role}]{{ .member-page-role }}",
        "",
        get_member_icon_links(member),
        "",
        ":::",
        "",
        ":::",
    ]
    return "\n".join(lines)


def build_biography_section(member: dict[str, Any], id2name: dict[str, str], id2page) -> str:
    """'Biography' section of a personal page, from the member's 'bio' field;
    empty if there is none."""
    bio = member.get("bio")
    if not bio:
        return ""
    biography =  "\n\n".join(["## Biography", bio.strip()])
    for id, name in id2name.items():
        content = f"[{name}]({id}.html)" if id2page.get(id) else name
        biography = biography.replace(id, content)
    return biography


def format_date_range(start: int | None, end: int | None) -> str:
    """'start–end', or 'start' if both are equal, or 'start–present' if there is
    no end."""
    if end is None:
        return f"{start}–present"
    if start == end:
        return f"{start}"
    return f"{start}–{end}"


def build_education_section(member: dict[str, Any], id2name: dict[str, str]) -> str:
    """'Education' section of a personal page: one line per degree (with a link
    to its thesis, its supervisors and an outside-of-dynamica badge if needed),
    internships nested under the BSc."""

    entries = get_member_education_entries(member)
    if not entries:
        return ""

    lines = ["## Education"]
    for entry in entries:
        line = f"[{entry['label']}]{{ .member-page-education-entry }}, {entry['institution']} ({format_date_range(entry.get("start"), entry.get("end"))})"
        if entry.get("thesis"):
            line += f" — [{entry['thesis']['title']}]({entry['thesis-anchor']}){{ .pub-link }}"
        if entry["role"] != "BSc student":  # redundant to flag a BSc as not done at Dynamica
            badge = get_outside_badge(entry)
            if badge:
                line += f" {badge}"
        supervisors = get_supervisors_line(entry.get("supervisors", []), id2name)
        if supervisors:
            line += f" {supervisors}"

        lines.append("")
        lines.append(line)

        sub_entries = entry.get("sub-entries", [])
        if sub_entries:
            lines.append("")
            lines.append("::: { .education-sub-entries }")
            for sub in sub_entries:
                sub_line = sub["label"]
                if sub.get("institution"):
                    sub_line += f", {sub['institution']}"
                sub_line += f" ({format_date_range(sub.get("start"), sub.get("end"))})"
                badge = get_outside_badge(sub)
                if badge:
                    sub_line += f" {badge}"
                supervisors = get_supervisors_line(sub.get("supervisors", []), id2name)
                if supervisors:
                    sub_line += f" {supervisors}"
                lines.append(f"- {sub_line}")
            lines.append(":::")

    return "\n".join(lines)


def build_member_publications_section(member: dict[str, Any],
                                      pubs: list[dict[str, Any]],
                                      team: list[dict[str, Any]],
                                      id2name: dict[str, str],
                                      id2page: dict[str, bool]) -> str:
    """'Publications' section of a personal page; empty if the member has
    none."""

    items = get_member_publications(member, pubs, team)
    if not items:
        return ""

    lines = ["## Publications", ""]
    lines.extend(build_pub_entry(pub, id2name, id2page) for pub in items)
    return "\n".join(lines)


def build_member_presentations_section(member: dict[str, Any],
                                       pubs: list[dict[str, Any]],
                                       id2name: dict[str, str],
                                       id2page: dict[str, bool]) -> str:
    """'Presentations' section of a personal page; empty if the member has
    none."""

    items = get_member_presentations(member, pubs)
    if not items:
        return ""

    lines = ["## Presentations", ""]
    lines.extend(build_pub_entry(pub, id2name, id2page) for pub in items)
    return "\n".join(lines)


def build_member_news_section(member: dict[str, Any], news: list[dict[str, Any]]) -> str:
    """'News' section of a personal page, listing the items the member is tagged
    in; empty if there are none."""

    items = get_member_news(member, news)
    if not items:
        return ""

    lines = ["## News", ""]
    lines.extend(get_news_item_full(item) for item in items)
    return "\n".join(lines)





# --- Entry point --------------------------------------------------------

def create_home_page(news: list[dict[str, Any]]) -> None:
    """Generates home.qmd: the about-us text and group picture (from
    data/home-*.md), followed by the most recent news excerpts."""

    lines = [HEADER_HOME_PAGE]

    lines.append("")

    lines.append("::: { .home-about-us }")
    lines.append(Path("data/home-about-us.md").read_text(encoding="utf-8"))
    lines.append(":::")
    lines.append("")

    lines.append("::: { .home-group-picture }")
    lines.append(Path("data/home-group-picture.md").read_text(encoding="utf-8"))
    lines.append(":::")
    lines.append("")

    lines.append("::: { .home-news }")
    lines.append("### News and recent activities")
    lines.append("")

    recent_news = get_recent_news(news, n=NUMBER_NEWS_ITEMS)

    for news_item in recent_news:
        # line = []
        # line.append(f"**{news_item["date"].strftime('%Y.%m.%d')}**")
        # line.append("\u2014")
        # line.append(news_item["text"])
        # lines.append(" ".join(line))
        # lines.append("")
        lines.append(get_news_item_home(news_item))

    lines.append(":::")

    lines.append("")
    lines.append('```{=html}')
    lines.append('<script src="/assets/js/news-truncation.js"></script>')
    lines.append('```')

    content = "\n".join(lines).rstrip() + "\n"
    Path("home.qmd").write_text(content, encoding="utf-8")


def create_news_page(news: list[dict[str, Any]]) -> None:
    """Generates news.qmd: all published news items, grouped by year, newest
    first."""

    lines = [HEADER_NEWS_PAGE]

    lines.append("# News")

    years = get_news_by_year(news)

    for year in sorted(years, reverse=True):
        lines.append(f"## {year}")
        lines.append("")
        for news_item in years[year]:
            # line = []
            # line.append(f"**{news_item["date"].strftime('%Y.%m.%d')}**")
            # line.append("\u2014")
            # line.append(news_item["text"])
            # lines.append(" ".join(line))
            # lines.append("")
            lines.append(get_news_item_full(news_item))

    content = "\n".join(lines).rstrip() + "\n"
    Path("news.qmd").write_text(content, encoding="utf-8")



def create_team_page(team: list[dict[str, Any]]) -> None:
    """Generates team.qmd: the current members grid followed by the alumni
    list."""
    content = "\n\n".join([
        HEADER_TEAM_PAGE,
        build_current_members_section(team),
        build_alumni_section(team),
    ]) + "\n"
    Path("team.qmd").write_text(content, encoding="utf-8")



def create_pubs_page(pubs: list[dict[str, Any]],
                     team: list[dict[str, Any]]) -> None:
    """Generates pubs.qmd: one section per PUB_TYPES entry, each grouped by
    year, newest first."""

    lines = [HEADER_PUBS_PAGE]

    lines.append("# Publications")

    id2name = {member["id"]: member["name"] for member in team}
    id2page = {member["id"]: member.get("personal-page", False) for member in team}

    for pub_type in PUB_TYPES:

        years = get_pubs_by_year(pub_type, pubs, team)
        if not years:
            continue

        lines.append(f"## {PUB_TYPES[pub_type]}")
        lines.append("")

        for year in sorted(years, reverse=True):

            if pub_type in PUB_WITH_YEAR:
                lines.append(f"### {year}")
                lines.append("")

            for pub in years[year]:
                title = get_pub_title(pub)
                entry = []
                entry.append(get_pub_authors(pub, id2name, id2page))
                entry.extend(get_pub_body_details(pub))

                entry.append(get_pub_links(pub))
                if pub.get("keywords"):
                    entry.append(get_pub_keywords(pub.get("keywords")))
                entry.extend(get_pub_highlights(pub))

                content = f'::: {{ .pub-content }}\n' + "\n\n".join(entry) + '\n:::\n'
                lines.append(f'::: {{ .pub-entry }}\n' + "\n\n".join([title, content]) + '\n:::\n')

    content = "\n".join(lines).rstrip() + "\n"
    Path("pubs.qmd").write_text(content, encoding="utf-8")


def create_member_pages(team: list[dict[str, Any]],
                        pubs: list[dict[str, Any]],
                        news: list[dict[str, Any]]) -> None:
    """One CV-style page per member whose team.yml entry sets personal-page: true."""

    id2name = {member["id"]: member["name"] for member in team}
    id2page = {member["id"]: member.get("personal-page", False) for member in team}

    for member in team:
        if not member.get(PERSONAL_PAGE_KEY):
            continue
        # Do not self-reference personal page
        id2page_no_self = deepcopy(id2page)
        id2page_no_self[member['id']] = False

        sections = [
            HEADER_MEMBER_PAGE.format(name=member["name"]),
            build_member_page_header(member),
            build_biography_section(member, id2name, id2page_no_self),
            build_education_section(member, id2name),
            build_member_publications_section(member, pubs, team, id2name, id2page_no_self),
            build_member_presentations_section(member, pubs, id2name, id2page_no_self),
            build_member_news_section(member, news),
        ]
        sections = [section for section in sections if section]

        content = "\n\n".join(sections).rstrip() + "\n"
        Path(f"{member['id']}.qmd").write_text(content, encoding="utf-8")





if __name__ == "__main__":
    import yaml

    news = yaml.safe_load(Path("data/news.yml").read_text())
    pubs = yaml.safe_load(Path("data/pubs.yml").read_text())
    team = yaml.safe_load(Path("data/team.yml").read_text())

    create_home_page(news)
    create_news_page(news)
    create_team_page(team)
    create_pubs_page(pubs, team)
    create_member_pages(team, pubs, news)
