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


@WorkflowRegistry.register(
    name="Process_Data",
    description="Fetches data and compiles a status report"
)
def process_data_workflow():
    return [step_one, step_two]
