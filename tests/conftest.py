import pytest

INTEGRATION_TESTS = {
    "test_get_top_news",
    "test_get_topic_news",
    "test_search",
    "test_search_with_dates",
    "test_search_with_date_range",
    "test_search_with_date_range_content",
    "test_search_with_relative_time",
    "test_search_with_relative_time_content",
    "test_async_search_with_time_parameters",
    "test_async_search_with_time_parameters_content",
    "test_sync_client_search",
    "test_sync_client_top_news",
    "test_max_results_validation",
    "test_batch_search",
    "test_batch_search_with_time_params",
    "test_async_batch_search",
    "test_async_batch_search_with_time_params",
    "test_async_batch_search_error_handling",
    "test_decode_url",
    "test_decode_urls",
    "test_decode_urls_concurrency",
}


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
        if item.name in INTEGRATION_TESTS:
            item.add_marker(pytest.mark.integration)
            item.add_marker(skip_integration)
