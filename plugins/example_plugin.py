from core.registry import WorkflowRegistry
from core.context import WorkflowTable, get_ctx, get_data
import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("workflows")


@dataclass
class ProcessData:
    processed_items: list = field(default_factory=list)


def step_one():
    data = get_data(ProcessData)
    ctx = get_ctx()
    logger.info(ctx.settings)
    data.processed_items = [f"Item {i}" for i in range(100)]
    logger.info("Started")
    time.sleep(2)
    logger.warning("step one finished")


def step_two():
    ctx = get_ctx()
    data = get_data(ProcessData)
    logger.error("step 2 error")
    time.sleep(2)
    logger.info("finished")
    items = data.processed_items
    rows = [[i, "Success"] for i in items]
    ctx.output_table = WorkflowTable(
        columns=["Item Name", "Status"], rows=rows)


def failing_step():
    raise ValueError("error here")


@WorkflowRegistry.register(
    name="Process_Data",
    description="Fetches data and compiles a status report",
    data_cls=ProcessData
)
def process_data_workflow():
    return [step_one, step_two]


@WorkflowRegistry.register(
    name="Process_Data_2",
    description="Fetches data and compiles a status report"
)
def process_data_workflow2():
    return [step_one, failing_step, step_two]
