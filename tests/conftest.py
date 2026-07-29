import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="run tests that make live network calls",
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--run-integration"):
        return

    skip_integration = pytest.mark.skip(reason="use --run-integration to run")
    for item in items:
        if item.get_closest_marker("integration"):
            item.add_marker(skip_integration)
