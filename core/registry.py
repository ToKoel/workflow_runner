from typing import Callable, Type, Any


class Workflow:
    def __init__(self, name: str, description: str, steps: list[Callable], data_cls: Type[Any]):
        self.name = name
        self.description = description
        self.steps = steps
        self.data_cls = data_cls


class WorkflowRegistry:
    _workflows: dict[str, Workflow] = {}

    @classmethod
    def register(cls, name: str, description: str = "", data_cls: Type[Any] = None):
        def decorator(workflow_definition_func: Callable):
            steps_list = workflow_definition_func()

            if not isinstance(steps_list, list):
                raise TypeError(f"The decorated workflow function '{
                                workflow_definition_func.__name__}' must return a list of step functions.")
            cls._workflows[name] = Workflow(
                name, description, steps_list, data_cls=data_cls)

            return workflow_definition_func
        return decorator

    @classmethod
    def get_all(cls) -> dict[str, Workflow]:
        return cls._workflows
