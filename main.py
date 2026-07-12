import argparse
import os
import json
from rich.progress import Progress, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
from rich.console import Console
from ui.app import WorkflowTUI
from core.engine import WorkflowEngine
from core.settings import get_settings
from core.context import WorkflowContext


def main():
    parser = argparse.ArgumentParser(
        description="Workflow Runner Automation App")
    parser.add_init = False
    parser.add_argument("--ui", action="store_true",
                        help="Launch the Textual TUI interface")
    parser.add_argument(
        "--run", nargs="+", help="List of workflow names to run in chain sequentially")
    parser.add_argument("--plugins", default="./plugins",
                        help="Directory where plugins are located")

    args = parser.parse_args()

    if args.ui:
        app = WorkflowTUI(plugin_dir=args.plugins)
        app.run()
    elif args.run:
        console = Console()

        settings = get_settings()
        engine = WorkflowEngine(settings)
        engine.load_plugins(args.plugins)

        console.print(
            f"[bold green]Executing workflow chain[/]: {", ".join(args.run)}\n")
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=40),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task_id = progress.add_task("[cyan]Initializing...", total=100)

            def cli_progress_callback(status: str, percentage: float):
                progress.update(
                    task_id,
                    description=f"[yellow]{status:<35}[/]",
                    completed=percentage
                )
            ctx = WorkflowContext()

            ctx = engine.run_chain(
                args.run, progress_callback=cli_progress_callback, ctx=ctx)

        if ctx.output_table:
            from rich.table import Table

            console.print(
                "\n[bold list]--- Workflow Output Table ---[/bold list]")
            rich_table = Table(show_header=True, header_style="bold magenta")

            for col in ctx.output_table.columns:
                rich_table.add_column(col)

            for row in ctx.output_table.rows:
                rich_table.add_row(*[str(item) for item in row])

            console.print(rich_table)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
