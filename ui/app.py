import json
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, ListView, ListItem, Label, Input, ProgressBar, DataTable, RichLog, Static, ContentSwitcher
from textual.containers import Horizontal, Vertical, Grid
import time
import asyncio
from textual import work
from textual.reactive import reactive
import logging
from ui.richlog_handler import TextualRichLogHandler
from textual.binding import Binding
from textual.events import Key

from core.engine import WorkflowEngine
from core.registry import WorkflowRegistry
from core.settings import get_settings


class WorkflowInput(Input):
    def on_key(self, event: Key) -> None:
        if event.key == "escape":
            event.prevent_default()
            event.stop()
            self.screen.focus_next()


class WorkflowTUI(App):
    BINDINGS = [("escape", "quit", "Quit"),
                Binding("q", "quit", "Quit", show=True),
                Binding("1", "focus_box('wf_list')",
                        "Focus Workflows", show=False),
                Binding("2", "focus_box('settings')",
                        "Focus Settings", show=False),
                Binding("3", "focus_box('logs')",
                        "Focus Settings", show=False),
                Binding("4", "focus_box('results')",
                        "Focus Settings", show=False),
                Binding("[", "prev_tab", "Prev Tab"),
                Binding("]", "next_tab", "Next Tab"),
                ]
    CSS = """
    #outer_grid { grid-size: 2; grid-columns: 1fr 3fr; height: 1fr; }
    #settings_grid { grid-size: 1;
                     grid-columns: 1fr;
                     height: 1fr; 
                     }
    .box {
               border: solid round green;
               padding: 1;
               background: transparent;
        }
    .box:focus-within {
        border: solid round $accent;
        }

    #wf_list { margin-bottom: 1; }
    #timer-layout { height: auto; align: left middle; margin-bottom: 1; }
    #save_settings {
    width: 100%;
    margin-top: 1;
    height: 3;
    background: transparent;
    color: $success;
    border: solid $success;
    text-style: bold;
}

#save_settings:hover {
    background: $success 20%;
    color: #ffffff;
}

#save_settings:focus {
    border: double $accent;
}
    #elapsed-time { margin-left: 2; color: $accent; }
    #progress_container { align: left top; }
    #progress_bar { margin-left: 1; }
    #log_output { height: 30%; align: center top; margin-bottom: 1; scrollbar-size: 1 1;}
    #output_box { align: center top; }
    #result_table { height: 60%; align: center top; scrollbar-size: 1 1;}
    Input { margin-bottom: 1;}
    Footer { dock: bottom; width: 100%; }
    """
    is_running = reactive(False)

    def __init__(self, plugin_dir: str):
        super().__init__()
        self.plugin_dir = plugin_dir
        self.engine = WorkflowEngine()
        self.engine.load_plugins(Path(self.plugin_dir))
        self.tabs = ["tab-description", "tab-output"]
        self.current_tab_idx = 0

    def on_mount(self):
        wf_list = self.query_one("#wf_list", ListView)
        wf_list.border_title = "[1]-Workflows"
        settings = self.query_one("#settings", Vertical)
        settings.border_title = "[2]-Settings"
        table = self.query_one("#result_table", DataTable)
        table.border_title = "[4]-Results"

        log_window = self.query_one("#log_output", RichLog)
        log_window.border_title = "[3]-Logs"

        output_box = self.query_one("#output_box", Vertical)
        output_box.border_subtitle = "1 of 2"

        log_handler = TextualRichLogHandler(log_window, self)

        formatter = logging.Formatter(
            "[dim]%(asctime)s[/dim] | %(levelname)5s | [cyan]%(name)s[/cyan] - %(message)s",
            datefmt="%H:%M:%S"
        )
        log_handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(log_handler)

        logging.getLogger("textual").setLevel(logging.WARNING)

    def on_data_table_header_selected(self, event: DataTable.HeaderSelected) -> None:
        """Fires automatically when a user clicks on a column header."""
        table = event.data_table
        column_key = event.column_key

        data_rows = [table.get_row(row_key) for row_key in table.rows.keys()]
        column_index = list(table.columns.keys()).index(column_key)
        current_sort = getattr(table, "_last_sorted_col", None)

        if current_sort == (column_key, "asc"):
            data_rows.sort(key=lambda row: row[column_index], reverse=True)
            table._last_sorted_col = (column_key, "desc")
        else:
            data_rows.sort(key=lambda row: row[column_index])
            table._last_sorted_col = (column_key, "asc")

        table.clear(columns=False)
        table.add_rows(data_rows)

    def action_focus_box(self, location: str) -> None:
        match location:
            case "wf_list":
                self.query_one("#wf_list", ListView).focus()
                self.query_one("#main-content",
                               ContentSwitcher).current = "tab-description"
            case "settings":
                self.query_one("#project_dir", WorkflowInput).focus()
            case "logs":
                self.query_one("#log_output", RichLog).focus()
                self.query_one("#main-content",
                               ContentSwitcher).current = "tab-output"
            case "results":
                self.query_one("#result_table", DataTable).focus()
                self.query_one("#main-content",
                               ContentSwitcher).current = "tab-output"

    def save_settings(self):
        self.settings.project_dir = Path(
            self.query_one("#project_dir", Input).value)
        self.settings.output_dir = Path(
            self.query_one("#output_dir", Input).value)
        self.settings.ams_net_id = self.query_one(
            "#ams_net_id", Input).value
        self.settings.save_settings()
        self.notify("Settings Saved!")

    def compose(self) -> ComposeResult:
        return [
            Grid(
                Grid(
                    ListView(*[ListItem(Label(name), id=name)
                               for name in WorkflowRegistry.get_all().keys()], id="wf_list",
                             classes="box"),
                    Vertical(
                        Label("Project Directory:", id="project_dir_label"),
                        WorkflowInput(
                            value=f"{get_settings().project_dir}", id="project_dir"),
                        Label("Output Directory:"),
                        WorkflowInput(
                            value=f"{get_settings().output_dir}", id="output_dir"),
                        Label("Target Ams Net Id:"),
                        WorkflowInput(
                            value=get_settings().ams_net_id, id="ams_net_id"),
                        Button("Save Settings", variant="success",
                               id="save_settings"),
                        id="settings", classes="box"
                    ),
                    id="settings_grid"
                ),
                Vertical(
                    ContentSwitcher(
                        Vertical(
                            Vertical(
                                Label("Progress:", id="progress_label"),
                                Horizontal(
                                    ProgressBar(total=100, show_percentage=True, show_eta=False,
                                                id="progress_bar"),
                                    Label("00:00", id="elapsed-time"),
                                    id="timer-layout"
                                ),
                                id="progress_container"
                            ),
                            RichLog(id="log_output", highlight=True,
                                    markup=True, classes="box"),
                            DataTable(id="result_table", classes="box"),
                            id="tab-output"
                        ),
                        Vertical(
                            Static("Select a workflow to view details...",
                                   id="detail-body"),
                            id="tab-description"),
                        id="main-content", initial="tab-description"),
                    id="output_box", classes="box"
                ),
                id="outer_grid"
            ),
            Footer()]

    def update_tab_ui(self) -> None:
        active_id = self.tabs[self.current_tab_idx]
        self.query_one("#main-content", ContentSwitcher).current = active_id
        output_box = self.query_one("#output_box", Vertical)
        output_box.border_subtitle = f"{self.current_tab_idx+1} of 2"

    def action_next_tab(self) -> None:
        self.current_tab_idx = (self.current_tab_idx + 1) % len(self.tabs)
        self.update_tab_ui()

    def action_prev_tab(self) -> None:
        self.current_tab_idx = (self.current_tab_idx - 1) % len(self.tabs)
        self.update_tab_ui()

    @work(thread=True)
    async def continuous_timer_loop(self, start_time: float) -> None:
        time_label = self.query_one("#elapsed-time", Label)
        while self.is_running:
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            time_label.update(f"{minutes:02d}:{seconds:02d}")
            await asyncio.sleep(0.2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings":
            self.save_settings()

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        self.current_tab_idx = 0
        self.update_tab_ui()
        if event.item and event.item.id:
            workflows = WorkflowRegistry.get_all()
            workflow = workflows[event.item.id]

            steps_str = "\n".join(
                f" {i+1}. {step.__name__}" for i, step in enumerate(workflow.steps))
            formatted_details = (
                f"{workflow.description}\n\n"
                f"[bold cyan]Steps:[/]\n"
                f"{steps_str}"
            )
            self.query_one("#detail-body", Static).update(formatted_details)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_item = event.item
        if selected_item and not self.is_running:
            self.is_running = True

            self.continuous_timer_loop(time.time())
            self.run_workflow_async(selected_item.id)

    @work(thread=True)
    def run_workflow_async(self, workflow_name: str) -> None:
        p_bar = self.query_one("#progress_bar", ProgressBar)
        p_label = self.query_one("#progress_label", Label)
        table_widget = self.query_one("#result_table", DataTable)
        self.current_tab_idx = 1
        self.update_tab_ui()

        self.call_from_thread(table_widget.clear, columns=True)

        def progress_updater(status: str, percentage: float):
            p_label.update(status)
            self.call_from_thread(
                setattr, p_label, "renderable", f"Status: {status}")
            self.call_from_thread(setattr, p_bar, "progress", percentage)

        try:
            ctx = self.engine.run_chain(
                [workflow_name], progress_callback=progress_updater)
            if not ctx.success:
                p_label.update("[red]Workflow failed[/]")

            if ctx.output_table:
                self.call_from_thread(
                    setattr, table_widget, "zebra_stripes", True)
                self.call_from_thread(
                    setattr, table_widget, "cursor_type", "row")
                t = ctx.output_table
                self.call_from_thread(table_widget.add_columns, *t.columns)
                self.call_from_thread(table_widget.add_rows, t.rows)
                table_widget.focus()
        finally:
            self.call_from_thread(setattr, self, "is_running", False)
