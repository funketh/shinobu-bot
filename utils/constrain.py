from api.expected_errors import ExpectedCommandError


class ConstraintError(ExpectedCommandError):
    pass


def constrain(condition, msg: str):
    if not condition:
        raise ConstraintError(msg)
