"""Clean, slim terminal rendering, built on rich."""

from __future__ import annotations

from contextlib import contextmanager

from habu.discovery import DetectionResult
from habu.models import CheckResult, Exercise, Project, Verdict

try:
    from rich.console import Console

except ImportError as exc:
    raise SystemExit(
        "Habu needs the 'rich' package for its terminal UI.\n"
        "Install it with: pip install rich"
    ) from exc

console = Console(highlight=False)

_VERDICT_GLYPH = {
    Verdict.PASS: ("✓", "green"),
    Verdict.FAIL: ("✗", "red"),
    Verdict.SKIP: ("–", "yellow"),
    Verdict.ERROR: ("!", "bold red"),
}


def print_header(project: Project, detection: DetectionResult | None, submission_root: str) -> None:

    console.print()
    console.print(f"[bold]{project.name}[/bold] [dim]({project.id})[/dim] — {project.tagline}")
    console.print(f"[dim]{submission_root}[/dim]")

    if detection is not None and detection.project is not None:
        pct = round(detection.score * 100)
        console.print(
            f"[dim]detected via {len(detection.matched)}/{detection.total} known files matched ({pct}%)[/dim]"
        )

    console.rule(style="dim")


def print_exercise_header(exercise: Exercise) -> None:

    console.print(f"\n[bold cyan]{exercise.id}[/bold cyan] · {exercise.title}")


def print_check_result(check_name: str, result: CheckResult) -> None:

    glyph, style = _VERDICT_GLYPH[result.verdict]
    console.print(f"  [{style}]{glyph}[/{style}] {check_name} [dim]—[/dim] {result.message}")

    if result.detail and result.verdict in (Verdict.FAIL, Verdict.ERROR):
        for line in result.detail.strip("\n").splitlines():
            console.print(f"      [dim]{line}[/dim]")


def print_missing_files(exercise: Exercise, missing: list[str]) -> None:

    console.print(f"  [yellow]–[/yellow] missing files: {', '.join(missing)} [dim](exercise skipped)[/dim]")


@contextmanager
def spinner(message: str):

    with console.status(f"[dim]{message}[/dim]", spinner="dots"):
        yield


def print_summary(counts: dict[Verdict, int], exercise_counts: tuple[int, int]) -> None:

    passed_ex, total_ex = exercise_counts
    console.rule(style="dim")

    parts = []
    if counts.get(Verdict.PASS):
        parts.append(f"[green]{counts[Verdict.PASS]} passed[/green]")

    if counts.get(Verdict.FAIL):
        parts.append(f"[red]{counts[Verdict.FAIL]} failed[/red]")

    if counts.get(Verdict.ERROR):
        parts.append(f"[bold red]{counts[Verdict.ERROR]} errored[/bold red]")

    if counts.get(Verdict.SKIP):
        parts.append(f"[yellow]{counts[Verdict.SKIP]} skipped[/yellow]")

    summary = " · ".join(parts) if parts else "no checks ran"
    console.print(f"{summary}")

    console.print(f"[bold]{passed_ex}/{total_ex}[/bold] exercises fully passing")

    if counts.get(Verdict.FAIL) or counts.get(Verdict.ERROR):
        console.print("[bold red]Submission: FAIL[/bold red]")
    else:
        console.print("[bold green]Submission: PASS[/bold green]")

    console.print()


def print_error(message: str) -> None:

    console.print(f"[bold red]error:[/bold red] {message}")


def print_project_list(projects: list[Project]) -> None:

    console.print("[bold]Known projects:[/bold]")
    for p in projects:
        console.print(f"  [cyan]{p.id}[/cyan]  {p.name} — [dim]{p.tagline}[/dim]")
