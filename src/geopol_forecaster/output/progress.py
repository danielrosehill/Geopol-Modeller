#!/usr/bin/env python3

"""Rich CLI progress reporting for Geopol Forecaster simulations."""

import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class SimulationProgress:
    """Rich-based progress reporting for CLI simulation runs.

    Provides formatted phase headers, move/player tracking, spinners
    between LLM calls, and elapsed time display. Pauses Rich output
    during LLM streaming to avoid garbled terminal output.
    """

    def __init__(self, console=None, total_moves=3, total_players=2):
        self.console = console or Console()
        self.total_moves = total_moves
        self.total_players = total_players
        self._start_time = time.monotonic()
        self._phase_start = None
        self._current_phase = None
        self._current_move = 0
        self._current_player = 0
        self._status = None

    def _elapsed(self):
        return time.monotonic() - self._start_time

    def _fmt_time(self, seconds):
        m, s = divmod(int(seconds), 60)
        if m > 0:
            return f"{m}m{s:02d}s"
        return f"{s}s"

    def _status_line(self):
        parts = []
        if self._current_phase:
            parts.append(self._current_phase)
        if self._current_phase == "SIMULATION" and self._current_move > 0:
            parts.append(f"Move {self._current_move}/{self.total_moves}")
        parts.append(f"Elapsed: {self._fmt_time(self._elapsed())}")
        return " | ".join(parts)

    def start_phase(self, phase):
        """Display a phase header (PLANNING, SIMULATION, ASSESSMENT)."""
        self._stop_status()
        self._current_phase = phase
        self._phase_start = time.monotonic()

        self.console.print()
        self.console.rule(f"[bold cyan]{phase}[/]", style="cyan")
        self.console.print()

    def start_move(self, move_num):
        """Mark the start of a simulation move."""
        self._stop_status()
        self._current_move = move_num
        self._current_player = 0

        table = Table.grid(padding=(0, 2))
        table.add_row(
            f"[bold]Move {move_num}/{self.total_moves}[/]",
            f"[dim]{self._fmt_time(self._elapsed())} elapsed[/]",
        )
        self.console.print(Panel(table, style="blue", expand=False))

    def start_player(self, player_name):
        """Mark a player's turn starting."""
        self._stop_status()
        self._current_player += 1
        self.console.print(
            f"\n[bold green]>>> {player_name}[/] "
            f"[dim](player {self._current_player}/{self.total_players})[/]\n"
        )

    def start_adjudication(self):
        """Mark adjudication phase of a move."""
        self._stop_status()
        self.console.print(f"\n[bold yellow]>>> Narrator (adjudication)[/]\n")

    def start_assessment(self, question):
        """Mark an assessment question."""
        self._stop_status()
        self.console.print(f"\n[bold magenta]--- {question}[/]\n")

    def checkpoint_saved(self, path):
        """Report a checkpoint was saved."""
        self.console.print(f"[dim]  checkpoint saved: {path}[/]")

    def update(self, message):
        """Show a status spinner with a message."""
        self._stop_status()
        self._status = self.console.status(
            f"[dim]{message}[/] [dim]({self._fmt_time(self._elapsed())})[/]"
        )
        self._status.start()

    def pause(self):
        """Pause Rich output before LLM streaming begins."""
        self._stop_status()

    def resume(self):
        """Resume Rich output after LLM streaming ends."""
        pass

    def end_phase(self):
        """End the current phase."""
        self._stop_status()
        if self._phase_start:
            phase_elapsed = time.monotonic() - self._phase_start
            self.console.print(
                f"\n[dim]{self._current_phase} completed in "
                f"{self._fmt_time(phase_elapsed)}[/]"
            )

    def finish(self):
        """Print final summary."""
        self._stop_status()
        total = self._elapsed()
        self.console.print()
        self.console.rule("[bold green]COMPLETE[/]", style="green")
        self.console.print(
            f"[bold]Total elapsed: {self._fmt_time(total)}[/]", justify="center"
        )
        self.console.print()

    def _stop_status(self):
        if self._status:
            self._status.stop()
            self._status = None


class NullProgress:
    """No-op progress reporter for --no-rich or non-TTY output.

    Falls back to the original bare print() behavior.
    """

    def __init__(self, total_moves=3, total_players=2):
        self.total_moves = total_moves
        self.total_players = total_players

    def start_phase(self, phase):
        print(f"\n{'=' * 40}")
        print(f"  {phase}")
        print(f"{'=' * 40}\n")

    def start_move(self, move_num):
        print(f"\n--- Move {move_num}/{self.total_moves} ---\n")

    def start_player(self, player_name):
        print(f"\n### {player_name}\n")

    def start_adjudication(self):
        print("\n### Result\n")

    def start_assessment(self, question):
        print(f"\n--- {question}\n")

    def checkpoint_saved(self, path):
        print(f"  [checkpoint saved: {path}]")

    def update(self, message):
        print(f"  {message}")

    def pause(self):
        pass

    def resume(self):
        pass

    def end_phase(self):
        pass

    def finish(self):
        pass
