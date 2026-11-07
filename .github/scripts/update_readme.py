import html
import json
import os
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

USERNAME = "OxaC2000"
README = Path("README.md")
CALENDAR = Path("assets/contribution-calendar.svg")
STATS = Path("assets/github-stats.svg")
LANGS = Path("assets/top-langs.svg")

PURPLE = "#A78BFA"
COLORS = [
    "#24283B",
    "#40345F",
    "#60458D",
    "#8560BD",
    "#A78BFA",
]

LANG_COLORS = [
    "#A78BFA",
    "#7AA2F7",
    "#BB9AF7",
    "#7DCFFF",
    "#9D7CD8",
    "#2AC3DE",
    "#C0CAF5",
    "#787C99",
]

def fetch_json(url, token=None):
    headers = {
        "User-Agent": "OxaC2000-GitHub-Portfolio",
        "Accept": "application/vnd.github+json",
    }

    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, headers=headers)

    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def badge(label, value, color=PURPLE):
    def escape(text):
        text = str(text).replace("-", "--").replace("_", "__")
        return urllib.parse.quote(text, safe="")

    color = color.lstrip("#")

    url = (
        f"https://img.shields.io/badge/"
        f"{escape(label)}-{escape(value)}-{color}"
        f"?style=for-the-badge&labelColor=1A1B27"
    )

    alt = html.escape(f"{label}: {value}")

    return f'<img src="{url}" alt="{alt}" />'


def get_owned_repositories(token):
    url = (
        f"https://api.github.com/users/{USERNAME}/repos"
        "?type=owner&sort=pushed&direction=desc&per_page=100"
    )

    return fetch_json(url, token)


def get_repositories(token):
    repositories = get_owned_repositories(token)

    selected = [
        repo for repo in repositories
        if not repo["fork"]
        and not repo["archived"]
        and not repo["disabled"]
        and repo["name"].lower() != USERNAME.lower()
    ]

    selected.sort(
        key=lambda repo: repo.get("pushed_at") or "",
        reverse=True,
    )

    return selected[:6]


def build_project_cards(repositories):
    if not repositories:
        return (
            '<p align="center">\n'
            '  <i>New projects coming soon.</i>\n'
            '</p>'
        )

    cells = []

    for repo in repositories:
        name = html.escape(repo["name"])
        description = html.escape(
            repo.get("description") or "No description provided."
        )

        url = repo["html_url"]
        language = repo.get("language") or "Other"

        language_badge = badge("LANGUAGE", language)
        stars_badge = badge("STARS", repo["stargazers_count"])
        forks_badge = badge("FORKS", repo["forks_count"])

        view_badge = (
            f'<a href="{url}">'
            f'{badge("VIEW", "REPOSITORY")}'
            f'</a>'
        )

        cell = "\n".join([
            '<td width="33%" valign="top">',
            '  <h3>',
            f'    <a href="{url}">{name}</a>',
            '  </h3>',
            f'  <p>{description}</p>',
            f'  <p>{language_badge}</p>',
            f'  <p>{stars_badge} {forks_badge}</p>',
            f'  <p>{view_badge}</p>',
            '</td>',
        ])
        cells.append(cell)

    rows = []

    for index in range(0, len(cells), 3):
        row = cells[index:index + 3]

        while len(row) < 3:
            row.append('<td width="33%"></td>')

        rows.append("<tr>\n" + "\n".join(row) + "\n</tr>")

    return "<table>\n" + "\n".join(rows) + "\n</table>"


def update_readme(projects):
    content = README.read_text(encoding="utf-8")

    start_marker = "<!-- PROJECTS:START -->"
    end_marker = "<!-- PROJECTS:END -->"

    if start_marker not in content or end_marker not in content:
        raise RuntimeError("Project markers not found in README.md")

    start = content.index(start_marker) + len(start_marker)
    end = content.index(end_marker)

    updated = (
        content[:start]
        + "\n"
        + projects
        + "\n"
        + content[end:]
    )

    README.write_text(updated, encoding="utf-8")


def get_contributions():
    url = (
        f"https://github-contributions-api.jogruber.de/v4/"
        f"{USERNAME}?y=last"
    )

    data = fetch_json(url)
    contributions = data.get("contributions", [])

    if not contributions:
        raise RuntimeError("No contribution data returned.")

    return contributions


def build_calendar(contributions):
    # Align the first contribution with Sunday.
    first_date = date.fromisoformat(contributions[0]["date"])
    offset = (first_date.weekday() + 1) % 7

    days = [None] * offset + contributions

    while len(days) % 7:
        days.append(None)

    weeks = [
        days[index:index + 7]
        for index in range(0, len(days), 7)
    ]

    cell = 12
    gap = 4
    step = cell + gap

    left = 44
    top = 34
    bottom = 35

    width = left + len(weeks) * step + 16
    height = top + 7 * step + bottom

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" '
        f'rx="18" fill="#1A1B27"/>',
        '<g font-family="Arial, sans-serif">',
        '<text x="18" y="22" fill="#C0CAF5" '
        'font-size="12" font-weight="600">'
        'CONTRIBUTIONS · LAST 12 MONTHS</text>',
    ]

    weekday_labels = [
        (1, "Mon"),
        (3, "Wed"),
        (5, "Fri"),
    ]

    for day_index, label in weekday_labels:
        y = top + day_index * step + 10
        parts.append(
            f'<text x="8" y="{y}" fill="#787C99" '
            f'font-size="9">{label}</text>'
        )

    previous_month = None

    for column, week in enumerate(weeks):
        x = left + column * step

        for row, contribution in enumerate(week):
            if contribution is None:
                continue

            current_date = date.fromisoformat(
                contribution["date"]
            )

            if current_date.day <= 7:
                month = current_date.strftime("%b")

                if month != previous_month:
                    parts.append(
                        f'<text x="{x}" y="31" '
                        f'fill="#A78BFA" font-size="10">'
                        f'{month}</text>'
                    )
                    previous_month = month

            level = int(contribution.get("level", 0))
            level = max(0, min(level, 4))

            y = top + row * step

            parts.append(
                f'<rect x="{x}" y="{y}" '
                f'width="{cell}" height="{cell}" '
                f'rx="4" ry="4" '
                f'fill="{COLORS[level]}">'
                f'<title>{current_date}: '
                f'{contribution["count"]} contributions'
                f'</title></rect>'
            )

    legend_y = height - 13
    legend_x = width - 132

    parts.append(
        f'<text x="{legend_x - 32}" y="{legend_y + 10}" '
        'fill="#787C99" font-size="9">Less</text>'
    )

    for index, color in enumerate(COLORS):
        x = legend_x + index * 17
        parts.append(
            f'<rect x="{x}" y="{legend_y}" '
            f'width="11" height="11" rx="3" '
            f'fill="{color}"/>'
        )

    parts.append(
        f'<text x="{legend_x + 92}" y="{legend_y + 10}" '
        'fill="#787C99" font-size="9">More</text>'
    )

    parts.append("</g></svg>")

    return "\n".join(parts)


def get_user(token):
    return fetch_json(
        f"https://api.github.com/users/{USERNAME}", token
    )


def get_language_totals(repositories, token):
    totals = {}

    for repo in repositories:
        if repo["fork"] or repo["archived"] or repo["disabled"]:
            continue

        try:
            languages = fetch_json(repo["languages_url"], token)
        except Exception as error:
            print(f"Skipping languages of {repo['name']}: {error}")
            continue

        for language, size in languages.items():
            totals[language] = totals.get(language, 0) + size

    return totals


def current_streak(contributions):
    streak = 0

    for index, contribution in enumerate(reversed(contributions)):
        if int(contribution["count"]) > 0:
            streak += 1
        elif index == 0:
            # Today may not have any contribution yet.
            continue
        else:
            break

    return streak


def build_stats_svg(user, repositories, contributions):
    owned = [repo for repo in repositories if not repo["fork"]]

    stars = sum(repo["stargazers_count"] for repo in owned)
    forks = sum(repo["forks_count"] for repo in owned)
    total = sum(int(item["count"]) for item in contributions)
    streak = current_streak(contributions)

    rows = [
        ("Total stars", stars),
        ("Total forks", forks),
        ("Public repositories", user.get("public_repos", 0)),
        ("Followers", user.get("followers", 0)),
        ("Contributions (last 12 months)", total),
        ("Current streak", f"{streak} days"),
    ]

    width = 495
    height = 66 + len(rows) * 26 + 10

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" '
        f'height="{height - 1}" rx="12" fill="#1A1B27"/>',
        '<g font-family="Arial, sans-serif">',
        f'<text x="25" y="36" fill="#A78BFA" font-size="18" '
        f'font-weight="700">{html.escape(USERNAME)}\'s GitHub Stats</text>',
    ]

    for index, (label, value) in enumerate(rows):
        y = 66 + index * 26 + 14
        parts.append(
            f'<circle cx="31" cy="{y - 4}" r="4" fill="#A78BFA"/>'
        )
        parts.append(
            f'<text x="46" y="{y}" fill="#C0CAF5" '
            f'font-size="14">{html.escape(str(label))}:</text>'
        )
        parts.append(
            f'<text x="440" y="{y}" fill="#A78BFA" font-size="14" '
            f'font-weight="700" text-anchor="end">'
            f'{html.escape(str(value))}</text>'
        )

    parts.append("</g></svg>")

    return "\n".join(parts)


def build_languages_svg(totals):
    width = 495

    if not totals:
        height = 110
        return "\n".join([
            f'<svg xmlns="http://www.w3.org/2000/svg" '
            f'width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}">',
            f'<rect x="0.5" y="0.5" width="{width - 1}" '
            f'height="{height - 1}" rx="12" fill="#1A1B27"/>',
            '<g font-family="Arial, sans-serif">',
            '<text x="25" y="36" fill="#A78BFA" font-size="18" '
            'font-weight="700">Most Used Languages</text>',
            '<text x="25" y="72" fill="#787C99" font-size="14">'
            'No language data yet.</text>',
            '</g></svg>',
        ])

    grand_total = sum(totals.values())
    top = sorted(totals.items(), key=lambda item: -item[1])[:8]

    height = 66 + len(top) * 26 + 10

    bar_x = 150
    bar_width = 260

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        f'<rect x="0.5" y="0.5" width="{width - 1}" '
        f'height="{height - 1}" rx="12" fill="#1A1B27"/>',
        '<g font-family="Arial, sans-serif">',
        '<text x="25" y="36" fill="#A78BFA" font-size="18" '
        'font-weight="700">Most Used Languages</text>',
    ]

    for index, (language, size) in enumerate(top):
        percent = size / grand_total * 100
        color = LANG_COLORS[index % len(LANG_COLORS)]
        y = 66 + index * 26
        fill_width = max(6, round(bar_width * percent / 100))

        parts.append(
            f'<text x="25" y="{y + 13}" fill="#C0CAF5" '
            f'font-size="13">{html.escape(language)}</text>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 3}" width="{bar_width}" '
            f'height="10" rx="5" fill="#24283B"/>'
        )
        parts.append(
            f'<rect x="{bar_x}" y="{y + 3}" width="{fill_width}" '
            f'height="10" rx="5" fill="{color}"/>'
        )
        parts.append(
            f'<text x="470" y="{y + 13}" fill="#787C99" '
            f'font-size="12" text-anchor="end">{percent:.1f}%</text>'
        )

    parts.append("</g></svg>")

    return "\n".join(parts)


def main():
    token = os.environ.get("GITHUB_TOKEN")

    print("Fetching public repositories...")
    repositories = get_repositories(token)

    print(f"Found {len(repositories)} projects.")
    projects = build_project_cards(repositories)
    update_readme(projects)

    print("Generating contribution calendar...")
    contributions = get_contributions()

    CALENDAR.parent.mkdir(parents=True, exist_ok=True)
    CALENDAR.write_text(
        build_calendar(contributions),
        encoding="utf-8",
    )

    print("Generating statistics cards...")

    try:
        user = get_user(token)
        owned = get_owned_repositories(token)

        STATS.write_text(
            build_stats_svg(user, owned, contributions),
            encoding="utf-8",
        )

        languages = get_language_totals(owned, token)

        LANGS.write_text(
            build_languages_svg(languages),
            encoding="utf-8",
        )
    except Exception as error:
        print(f"Warning: could not generate statistics cards: {error}")

    print("Portfolio successfully updated.")


if __name__ == "__main__":
    main()
