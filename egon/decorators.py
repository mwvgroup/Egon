import inspect
from functools import wraps
from typing import Any, Callable, Collection, Generator

from . import connectors, nodes

GeneratorFunction = Callable[[], Generator]


def _create_single_arg_function(func: callable) -> callable:
    """Restructure a function to accept its arguments a single tuple

    Args:
        func: The function to wrap

    Returns:
        A wrapped copy of ``func``
    """

    # If the function already takes a single argument, there is nothing to do
    if len(inspect.getfullargspec(func).args) == 1:
        return func

    @wraps(func)
    def wrapped(args: Collection) -> Any:
        """A wrapped version of ``func`` that only takes a single argument"""

        return func(*args)

    return wrapped


def as_source() -> Callable[[GeneratorFunction], nodes.Source]:
    """Decorator for wrapping a callable as a pipeline ``Source`` object

    Returns:
        A wrapper for casting a function as a callable ``Source`` object
    """

    def wrapper(func: GeneratorFunction) -> nodes.Source:
        """Creates a class implementation of the given function"""

        class WrappedSource(nodes.Source):
            output = connectors.Output()
            __call__ = func

            def action(self) -> None:
                for x in func():
                    self.output.put(x)

        return WrappedSource()

    return wrapper


def as_target() -> Callable[[callable], nodes.Target]:
    """Decorator for wrapping a callable as a pipeline ``Target`` object

    Returns:
        A wrapper for casting a function as a callable ``Target`` object
    """

    def wrapper(func: callable) -> nodes.Target:
        """Creates a class implementation of the given function"""

        simplified_func = _create_single_arg_function(func)

        class WrappedTarget(nodes.Target):
            input = connectors.Input()
            __call__ = func

            def action(self) -> None:
                while self.expecting_inputs():
                    data = self.input.get()
                    simplified_func(data)

        return WrappedTarget()

    return wrapper


def as_inline() -> Callable[[callable], nodes.Inline]:
    """Decorator for wrapping a callable as a pipeline ``Inline`` object

    Returns:
        A wrapper for casting a function as a callable ``Inline`` object
    """

    def wrapper(func: callable) -> nodes.Inline:
        """Creates a class implementation of the given function"""

        simplified_func = _create_single_arg_function(func)

        class WrappedInline(nodes.Inline):
            input = connectors.Input()
            output = connectors.Output()
            __call__ = func

            def action(self) -> None:
                while self.expecting_inputs():
                    in_data = self.input.get()
                    out_data = simplified_func(in_data)
                    self.output.put(out_data)

        return WrappedInline()

    return wrapper