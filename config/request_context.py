from contextvars import ContextVar, Token

# When a request comes in, we run the middleware here and establish
# an ID for the request. Then we essentially run it in a try, finally
# block for accepting the response. No matter how the response processing
# ends, we return to the previous state afterwards with our token.

# This is designed for nested context changes. Currently we only move
# from None to Request to None, but in nested context changes the token
# reset will be more important.


# _request_id is a ContextVar storing either a string or none.
# If a _request_id has not been set in the current context, set
# it to None.
_request_id: ContextVar[str | None] = ContextVar(
    "request_id",
    default=None,
)


def get_request_id() -> str | None:
    return _request_id.get()


# The returned token maintains the previous state, which the caller
# keeps so it can revert to that state.
def set_request_id(
    request_id: str,
) -> Token[str | None]:
    return _request_id.set(request_id)


# Here the request id can be reset with the token from above.
def reset_request_id(
    token: Token[str | None],
) -> None:
    _request_id.reset(token)
