import json
import os
from textual.app import App, ComposeResult
from textual.widgets import Header, Footer, Button, ListView, ListItem, Label, Input, ProgressBar, DataTable, RichLog
from textual.containers import Horizontal, Vertical, Grid
import time
import asyncio
from textual import work
from textual.reactive import reactive
import logging
from ui.richlog_handler import TextualRichLogHandler
from textual.binding import Binding

from core.engine import WorkflowEngine
from core.registry import WorkflowRegistry

SETTINGS_FILE = "settings.json"


class WorkflowTUI(App):
    BINDINGS = [("escape", "quit", "Quit"), Binding(
        "q", "quit", "Quit", show=True)]
    CSS = """
    Grid { grid-size: 2; grid-columns: 1fr 2fr; height: 1fr; }
    .box { border: solid green; padding: 1; margin: 1; height: 100%; }
    #timer-layout { height: auto; align: center middle; margin-bottom: 1; }
    #save_settings { margin-bottom: 1; }
    #elapsed-time { margin-left: 2; color: $accent; }
    #progress-container { align: center top; }
    #log_output { height: 30%; align: center top; margin-bottom: 1; }
    #output_box { align: center top; }
    #result_table { height: 60%; align: center top; }
    Input { margin-bottom: 1;}
    Footer { dock: bottom; width: 100%; }
    """
    is_running = reactive(False)

    def __init__(self, plugin_dir: str):
        super().__init__()
        self.plugin_dir = plugin_dir
        self.settings = self.load_settings()
        self.engine = WorkflowEngine(self.settings)
        self.engine.load_plugins(self.plugin_dir)

    def on_mount(self):
        log_window = self.query_one("#log_output", RichLog)

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

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r") as f:
                settings = json.load(f)
                if "project_dir" not in settings.keys():
                    settings["project_dir"] = ""
                if "output_dir" not in settings.keys():
                    settings["output_dir"] = ""
                if "ams_net_id" not in settings.keys():
                    settings["ams_net_id"] = ""
                return settings
        return {"project_dir": "", "output_dir": "./output", "ams_net_id": ""}

    def save_settings(self):
        self.settings["project_dir"] = self.query_one(
            "#project_dir", Input).value
        self.settings["ams_net_id"] = self.query_one(
            "#ams_net_id", Input).value
        self.settings["output_dir"] = self.query_one(
            "#output_dir", Input).value
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self.settings, f, indent=4)
        self.notify("Settings Saved!")

    def compose(self) -> ComposeResult:
        yield Header()
        yield Grid(
            Vertical(
                Label("--- Global Settings ---"),
                Label("Project Directory:"),
                Input(value=self.settings["project_dir"], id="project_dir"),
                Label("Output Directory:"),
                Input(value=self.settings["output_dir"], id="output_dir"),
                Label("Target Ams Net Id:"),
                Input(value=self.settings["ams_net_id"], id="ams_net_id"),
                Button("Save Settings", variant="success", id="save_settings"),
                Label("--- Available Workflows ---"),
                ListView(*[ListItem(Label(name), id=name)
                           for name in WorkflowRegistry.get_all().keys()], id="wf_list"),
                Button("Run Selected", variant="primary", id="run_wf"),
                classes="box"
            ),
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
                        markup=True),
                DataTable(id="result_table"),
                classes="box",
                id="output_box"
            )
        )
        yield Footer()

    @work(exclusive=True, thread=True)
    async def continuous_timer_loop(self, start_time: float) -> None:
        """Runs directly on the main async event loop, forcing visual updates."""
        time_label = self.query_one("#elapsed-time", Label)
        while self.is_running:
            elapsed = int(time.time() - start_time)
            minutes, seconds = divmod(elapsed, 60)
            time_label.update(f"{minutes:02d}:{seconds:02d}")
            await asyncio.sleep(0.2)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save_settings":
            self.save_settings()
        elif event.button.id == "run_wf":
            list_view = self.query_one("#wf_list", ListView)
            selected_item = list_view.highlighted_child

            if selected_item:
                self.is_running = True
                self.run_workflow_async(selected_item.id)
                self.continuous_timer_loop(time.time())

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        selected_item = event.item
        if selected_item and not self.is_running:
            self.is_running = True

            self.continuous_timer_loop(time.time())
            self.run_workflow_async(selected_item.id)

    @work(exclusive=True, thread=True)
    def run_workflow_async(self, workflow_name: str) -> None:
        p_bar = self.query_one("#progress_bar", ProgressBar)
        p_label = self.query_one("#progress_label", Label)
        table_widget = self.query_one("#result_table", DataTable)

        self.call_from_thread(table_widget.clear, columns=True)

        def progress_updater(status: str, percentage: float):
            p_label.update(status)
            self.call_from_thread(
                setattr, p_label, "renderable", f"Status: {status}")
            self.call_from_thread(setattr, p_bar, "progress", percentage)

        try:
            ctx = self.engine.run_chain(
                [workflow_name], progress_callback=progress_updater)

            if ctx.output_table:
                self.call_from_thread(
                    setattr, table_widget, "zebra_stripes", True)
                self.call_from_thread(
                    setattr, table_widget, "cursor_type", "row")
                t = ctx.output_table
                self.call_from_thread(table_widget.add_columns, *t.columns)
                self.call_from_thread(table_widget.add_rows, t.rows)
        finally:
            self.call_from_thread(setattr, self, "is_running", False)
