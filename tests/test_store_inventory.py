import logging
import pytest
import allure
from conftest import attach_json


@allure.feature("Store")
@allure.story("Get store inventory")
@pytest.mark.smoke
@pytest.mark.regression
def test_store_inventory(api_client):
    """
    GET /store/inventory — returns a map {status -> quantity}
    """
    with allure.step("Execute GET /store/inventory request"):
        resp = api_client.get_inventory()
        assert resp.status_code == 200, "Inventory is not available"
        body = resp.json()
        attach_json("Inventory response", body)

    with allure.step("Check the structure and values of the inventory"):
        assert isinstance(body, dict), "Expected an object-dictionary"
        total = sum(body.values())
        logging.info(f"Total pets in inventory: {total}")
        for k, v in body.items():
            assert isinstance(k, str), "Keys must be strings"
            assert isinstance(v, int), f"Quantity for '{k}' must be int"
            assert v >= 0, f"Quantity for '{k}' must not be negative"

    with allure.step("Check correctness of known keys (available, pending, sold)"):
        for known in ("available", "pending", "sold"):
            if known in body:
                assert isinstance(body[known], int)
