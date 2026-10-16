"""hcskills CLI — install, update, list, memory, and guard commands."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import click

from hcskills import __version__
from hcskills.guard import scan_paths

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"

# Team-tier pack: hcskills update pulls team skills from this private repo.
TEAM_SKILLS_REPO = "blacktj/hc-data-skills-pro"
TEAM_SKILLS_REPO_URL = f"https://github.com/{TEAM_SKILLS_REPO}.git"

TIER_MAP: dict[str, str] = {
    "834-file-check": "team",
    "fhir-mapping": "team",
    "hl7v2-parse": "free",
    "deid-pass": "team",
    "phi-column-scan": "free",
    "member-match": "team",
    "dbt-healthcare-conventions": "team",
    "roster-reconcile": "team",
    "code-set-lookup": "team",
    "pipeline-runbook": "free",
}


def _check_license(tier: str) -> bool:
    """Check whether the current license allows a given tier.

    TODO: Implement real license-key validation against a key server.
    For v0.1 all tiers are unlocked. When gating is added, read a key from
    ~/.hcskills/license or HCSKILLS_LICENSE_KEY env var and verify it.
    """
    if tier == "free":
        return True
    # STUB: team tier is unlocked during preview
    return True


def _resolve_target(target: str) -> Path:
    targets = {
        "cursor": Path(".cursor/skills/hc-data-skills"),
        "claude": Path(".claude/skills/hc-data-skills"),
    }
    return targets[target]


def _copy_skills(skills_root: Path, dest: Path) -> tuple[int, int]:
    """Copy licensed skills from skills_root into dest. Returns (installed, skipped)."""
    installed = 0
    skipped = 0
    for slug, tier in sorted(TIER_MAP.items()):
        if not _check_license(tier):
            click.echo(f"  SKIP  {slug} (requires {tier} license)")
            skipped += 1
            continue
        src = skills_root / slug
        if not src.exists():
            click.echo(f"  WARN  {slug} source not found at {src}")
            continue
        skill_dest = dest / slug
        if skill_dest.exists():
            shutil.rmtree(skill_dest)
        shutil.copytree(src, skill_dest, ignore=shutil.ignore_patterns("fixtures", "__pycache__"))
        click.echo(f"  OK    {slug} ({tier})")
        installed += 1
    return installed, skipped


def _try_clone_skills(repo: str) -> Path | None:
    """Shallow-clone repo and return its skills/ directory, or None on failure."""
    import subprocess
    import tempfile

    dest = Path(tempfile.mkdtemp(prefix="hcskills-update-")) / "repo"
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo, str(dest)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    skills = dest / "skills"
    return skills if skills.is_dir() else None


def _skills_source_for_update(repo: str) -> Path:
    """Resolve team skills from blacktj/hc-data-skills-pro, with local fallback."""
    fetched = _try_clone_skills(repo)
    if fetched is not None:
        return fetched
    if SKILLS_DIR.is_dir():
        click.echo(f"  WARN  using local skills at {SKILLS_DIR} (could not fetch {repo})")
        return SKILLS_DIR
    raise click.ClickException(
        f"Could not fetch team skills from {repo} and no local skills/ found."
    )


@click.group()
@click.version_option(__version__, prog_name="hcskills")
def cli() -> None:
    """hc-data-skills — agent skills for healthcare data engineering."""


@cli.command()
@click.option(
    "--target",
    type=click.Choice(["cursor", "claude"]),
    default="cursor",
    help="Where to install skills (default: cursor).",
)
def install(target: str) -> None:
    """Copy skills into the current repo's skills directory."""
    dest = _resolve_target(target)
    installed, skipped = _copy_skills(SKILLS_DIR, dest)
    click.echo(f"\nInstalled {installed} skills to {dest}/ (skipped {skipped})")


@cli.command()
@click.option(
    "--target",
    type=click.Choice(["cursor", "claude"]),
    default="cursor",
    help="Where skills are installed (default: cursor).",
)
@click.option(
    "--repo",
    default=TEAM_SKILLS_REPO_URL,
    show_default=True,
    help="Git repo to pull Team skills from.",
)
def update(target: str, repo: str) -> None:
    """Pull latest Team skills from blacktj/hc-data-skills-pro and re-install."""
    click.echo(f"Updating team skills from {TEAM_SKILLS_REPO} ({repo})")
    skills_root = _skills_source_for_update(repo)
    dest = _resolve_target(target)
    installed, skipped = _copy_skills(skills_root, dest)
    click.echo(
        f"\nUpdated {installed} skills in {dest}/ from {TEAM_SKILLS_REPO} (skipped {skipped})"
    )


@cli.command(name="list")
def list_skills() -> None:
    """List available skills and their tiers."""
    click.echo(f"{'Skill':<30} {'Tier':<8}")
    click.echo("-" * 38)
    for slug, tier in sorted(TIER_MAP.items()):
        licensed = "✓" if _check_license(tier) else "✗"
        click.echo(f"{slug:<30} {tier:<8} {licensed}")


@cli.group()
def memory() -> None:
    """Manage the local memory/ folder."""


@memory.command(name="init")
def memory_init() -> None:
    """Create a memory/ folder template in the current repo."""
    base = Path("memory")
    templates: dict[str, str] = {
        "decisions/README.md": (
            "# Decisions\n\n"
            "Record data-engineering decisions here.\n"
            "Format: one Markdown file per decision, named `YYYY-MM-DD-<slug>.md`.\n"
        ),
        "column-glossary/README.md": (
            "# Column Glossary\n\n"
            "Map source columns to canonical names.\n"
            "Use CSV or Markdown tables. One file per source system.\n"
        ),
        "gotchas/README.md": (
            "# Gotchas\n\n"
            "Document known data quality issues, vendor quirks, and edge cases.\n"
        ),
    }
    created = 0
    for rel_path, content in templates.items():
        fp = base / rel_path
        if fp.exists():
            click.echo(f"  EXISTS  {fp}")
            continue
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        click.echo(f"  CREATE  {fp}")
        created += 1
    click.echo(f"\nMemory folder ready at {base}/ ({created} files created)")


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("--staged", is_flag=True, help="Scan git staged files instead of explicit paths.")
def guard(paths: tuple[str, ...], staged: bool) -> None:
    """Scan files for PHI patterns and block if found."""
    import subprocess

    file_list: list[Path] = []
    if staged:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True,
            text=True,
        )
        file_list = [Path(f) for f in result.stdout.strip().splitlines() if f]
    else:
        file_list = [Path(p) for p in paths]

    if not file_list:
        click.echo("No files to scan.")
        sys.exit(0)

    findings = scan_paths(file_list)
    if findings:
        click.echo("🚨 PHI DETECTED — commit blocked\n")
        for finding in findings:
            click.echo(f"  {finding['file']}:{finding['line']}")
            click.echo(f"    Pattern: {finding['pattern_name']}")
            click.echo(f"    Match:   {finding['match']}")
            click.echo()
        click.echo(
            "Remove or redact the flagged content before committing.\n"
            "If this is a false positive, add a # phi-safe comment on that line."
        )
        sys.exit(1)
    else:
        click.echo(f"✓ No PHI patterns found in {len(file_list)} file(s).")
        sys.exit(0)
