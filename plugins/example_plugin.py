from core.registry import WorkflowRegistry
from core.context import WorkflowContext, WorkflowTable
import time
import logging

logger = logging.getLogger("workflows")


def step_one(ctx: WorkflowContext):
    api_key = ctx.settings.get("api_key", "default_key")
    ctx.data["processed_items"] = [f"Item {i}" for i in range(100)]
    logger.info("Started")
    time.sleep(2)
    logger.warning("step one finished")


def step_two(ctx: WorkflowContext):
    logger.error("step 2 error")
    time.sleep(2)
    logger.info("finished")
    items = ctx.data.get("processed_items", [])
    rows = [[i, "Success"] for i in items]
    ctx.output_table = WorkflowTable(
        columns=["Item Name", "Status"], rows=rows)


def failing_step(ctx: WorkflowContext):
    raise ValueError("error here")


@WorkflowRegistry.register(
    name="Process_Data",
    description="Fetches data and compiles a status report"
)
def process_data_workflow():
    return [step_one, step_two]


@WorkflowRegistry.register(
    name="Process_Data_2",
    description="Fetches data and compiles a status report"
)
def process_data_workflow2():
    return [step_one, failing_step, step_two]
