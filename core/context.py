from typing import Any, Optional, TypeVar, Type
from core.settings import get_settings
from contextvars import ContextVar

current_context: ContextVar["WorkflowContext"] = ContextVar("current_context")

T = TypeVar('T')


class WorkflowTable:
    def __init__(self, columns: list[str], rows: list[list[Any]]):
        self.columns = columns
        self.rows = rows


class WorkflowContext:
    def __init__(self, data: T = None):
        self.settings = get_settings()
        self.data: T = data
        self.output_table: Optional[WorkflowTable] = None
        self.success: bool = True

    def update_progress(self, step_name: str, percentage: float):
        pass


def get_data(data_type: Type[T]) -> T:
    ctx = current_context.get()
    return ctx.data


def get_ctx() -> WorkflowContext:
    try:
        return current_context.get()
    except LookupError:
        raise RuntimeError("No active workflow context found")
