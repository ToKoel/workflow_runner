import logging
from textual.widgets import RichLog


class TextualRichLogHandler(logging.Handler):
    """Custom logging handler that safely pipes python logs into a Textual RichLog widget."""

    def __init__(self, rich_log_widget: RichLog, app_instance):
        super().__init__()
        self.widget = rich_log_widget
        self.app = app_instance

    def emit(self, record):
        try:
            msg = self.format(record)

            self.app.call_from_thread(self.widget.write, msg)
        except Exception:
            self.handleError(record)
