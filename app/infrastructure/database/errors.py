from sqlalchemy.exc import DBAPIError

_TRANSIENT_SQLSTATES = frozenset(("40001", "40P01"))


def get_sqlstate(exc: DBAPIError) -> str | None:
    sqlstate = getattr(exc.orig, "sqlstate", None)
    if isinstance(sqlstate, str):
        return sqlstate

    return None


def is_transient(exc: DBAPIError) -> bool:
    sqlstate = get_sqlstate(exc)
    return sqlstate in _TRANSIENT_SQLSTATES
