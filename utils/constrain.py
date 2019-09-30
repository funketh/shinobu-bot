class ConstraintError(ValueError):
    pass


def constrain(condition, msg: str):
    if not condition:
        raise ConstraintError(msg)
