from importlib.util import spec_from_file_location, module_from_spec
from core.registry import WorkflowRegistry
from core.context import WorkflowContext, current_context
from core.settings import get_settings
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("workflow engine")


class WorkflowEngine:
    def __init__(self):
        self.settings = get_settings()

    def load_plugins(self, plugin_path: Path):
        if not plugin_path.exists():
            return

        for file in plugin_path.glob("*.py"):
            spec = spec_from_file_location(file.name, file)
            if spec and spec.loader:
                module = module_from_spec(spec)
                spec.loader.exec_module(module)

    def run_chain(self, workflow_names: list[str],
                  progress_callback=None) -> WorkflowContext:
        ctx = WorkflowContext()
        if progress_callback:
            ctx.update_progress = progress_callback

        token = current_context.set(ctx)

        try:

            total_workflows = len(workflow_names)

            for w_idx, name in enumerate(workflow_names):
                workflow = WorkflowRegistry.get_all().get(name)
                if not workflow:
                    raise ValueError(f"Workflow '{name}' not found.")

                ctx.data = workflow.data_cls()

                total_steps = len(workflow.steps)
                for s_idx, step in enumerate(workflow.steps):
                    overall_progress = ((w_idx / total_workflows) +
                                        (s_idx / total_steps) / total_workflows) * 100
                    ctx.update_progress(f"Running {workflow.name}: {
                                        step.__name__}", overall_progress)
                    try:
                        step()
                    except Exception as e:
                        logger.error(
                            f"Step {step.__name__} failed due to: {e}")
                        ctx.success = False
                        break

            ctx.update_progress(f"Finished {workflow.name}", 100.0)

        finally:
            current_context.reset(token)
        return ctx


if __name__ == "__main__":
    settings = {}
    engine = WorkflowEngine(settings)
    engine.load_plugins(Path.cwd() / "plugins")
