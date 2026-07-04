import json
from typing import Any

class WorkflowTable:
    def __init__(self, columns: list[str], rows: list[list[Any]]):
        self.columns = columns
        self.rows = rows

class WorkflowContext:
    def __init__(self, global_settings: dict[str, Any]):
        self.settings = global_settings
        self.data: dict[str, Any] = {}
        self.output_table: Optional[Workflowtable] = None

    def update_progress(self, step_name: str, percentage: float):
        pass

