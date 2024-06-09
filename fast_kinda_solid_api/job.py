# from functools import wraps
# from typing import Callable

# from fastapi.dependencies.utils import get_dependant, solve_dependencies
# from prefect import Flow, task


# def flow(name: str):
#     def decorator(func: Callable):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             async def wrapped_func():
#                 return await _resolve_dependencies(func, *args, **kwargs)

#             return wrapped_func

#         with Flow(name) as flow:
#             task(wrapper)

#         return flow

#     return decorator


# class Job:
#     flow: Flow

#     def __init__(self) -> None:
#         pass


# async def _resolve_dependencies(func: Callable, *args, **kwargs):
#     dependant = get_dependant(path="", call=func)
#     solved_result = await solve_dependencies(request=None, dependant=dependant, body=None)
#     values = {**solved_result[0], **kwargs}
#     return func(*args, **values)


# __all__ = [
#     "Job",
#     "flow",
# ]
