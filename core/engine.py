import os
import glob
import importlib.util
from core.registry import WorkflowRegistry, Workflow
from core.context import WorkflowContext

class WorkflowEngine:
    def __init__(self, settings: dict):
        self.settings = settings

    def load_plugins(self, plugin_dir:str):
        if not os.path.exists(plugin_dir):
            return

        for filepath in glob.glob(os.path.join(plugin_dir, "*.py")):
            module_name = os.path.splitext(os.path.basename(filepath))[0]
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

    def run_chain(self, workflow_names: list[str], progress_callback=None) -> WorkflowContext:
        ctx = WorkflowContext(self.settings)
        if progress_callback:
            ctx.update_progress = progress_callback

        total_workflows= len(workflow_names)

        for w_idx, name in enumerate(workflow_names):
            workflow = WorkflowRegistry.get_all().get(name)
            if not workflow:
                raise ValueError(f"Workflow '{name}' not found.")

            total_steps = len(workflow.steps)
            for s_idx, step in enumerate(workflow.steps):
                overall_progress = ((w_idx / total_workflows) +
                                    (s_idx / total_steps) / total_workflows) * 100
                ctx.update_progress(f"Running {workflow.name}: {step.__name__}", overall_progress)
                step(ctx)

        ctx.update_progress("Finished", 100.0)
        return ctx

