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
    GET /store/inventory — возвращает мапу {status -> quantity}
    """
    with allure.step("Выполнить запрос GET /store/inventory"):
        resp = api_client.get_inventory()
        assert resp.status_code == 200, "Инвентарь недоступен"
        body = resp.json()
        attach_json("Inventory response", body)

    with allure.step("Проверить структуру и значения инвентаря"):
        assert isinstance(body, dict), "Ожидали объект-словарь"
        total = sum(body.values())
        logging.info(f"Всего питомцев в инвентаре: {total}")
        for k, v in body.items():
            assert isinstance(k, str), "Ключи должны быть строками"
            assert isinstance(v, int), f"Количество для '{k}' должно быть int"
            assert v >= 0, f"Количество для '{k}' не должно быть отрицательным"

    with allure.step("Проверить корректность известных ключей (available, pending, sold)"):
        for known in ("available", "pending", "sold"):
            if known in body:
                assert isinstance(body[known], int)
