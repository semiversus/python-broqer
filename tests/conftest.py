import async_solipsism
import pytest


@pytest.fixture(autouse=True)
def event_loop_policy():
    return async_solipsism.EventLoopPolicy()