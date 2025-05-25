def evolve(func):
    """Decorator for the function to be evolved.
    Will not influence the function itself.
    For example:

    ```python
    import funch

    @funch.evolve
    def func_to_evolve(...):
        ...
    ```

    WARNING: Only one function can be decorated with this decorator.
    """
    return func


def run(func):
    """Decorator for the function to be run.
    Will not influence the function itself.

    ```python
    import funch

    @funch.run
    def func_to_run1(...):
        ...

    @funch.run
    def func_to_run2(...):
        ...
    ```
    """
    return func


def validate(func):
    """Decorator for the function to be validated.
    Do not take anything as input.
    Raise Error when test failed
    """
    return func


def score(tag: str):
    """Decorator for the function output to be scored.
    It takes as input the output of the function marked with `@funch.run(tag)`,
    and returns a float number as the score.

    You can choose not to decorate any function with this decorator if output is already the scored.
    """

    def decorator(func):
        return func

    return decorator
