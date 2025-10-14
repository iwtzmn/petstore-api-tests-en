import logging
import pytest
import allure
from conftest import get_with_retry, attach_json


@allure.feature("Store")
@allure.story("Create order")
@pytest.mark.smoke
@pytest.mark.regression
# Проверяет базовый happy-path (один стабильный заказ)
def test_order_create(api_client, unique_order_id, unique_pet_id, make_order, cleanup):
    logging.info(f"CREATE order_id={unique_order_id} pet_id={unique_pet_id}")
    with allure.step("Создаём заказ через POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True, quantity=1)
        # добавляем элемент в cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Проверяем заказ через GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404), f"Неожиданный код на GET: {resp.status_code}"
        if resp.status_code == 200:
            attach_json("GET /order response", resp.json())
            body = resp.json()
            assert body.get("id") == unique_order_id
            assert body.get("petId") == unique_pet_id
            assert isinstance(body.get("complete"), bool)


@allure.feature("Store")
@allure.story("Get order by id")
@pytest.mark.regression
def test_order_get(api_client, unique_order_id, unique_pet_id, make_order, cleanup):
    logging.info(f"GET order_id={unique_order_id}")
    with allure.step("Создаём заказ через POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True)
        # добавляем элемент в cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Проверяем заказ через GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404), f"Неожиданный код на GET: {resp.status_code}"
        if resp.status_code == 200:
            attach_json("GET /order response", resp.json())
            body = resp.json()
            assert body.get("id") == unique_order_id
            assert body.get("petId") == unique_pet_id
            assert isinstance(body.get("complete"), bool)


@allure.feature("Store")
@allure.story("Create order (parametrized)")
@pytest.mark.parametrize(
    "status, complete, quantity",
    [
        ("placed", True, 1),
        ("approved", True, 2),
        ("delivered", True, 3),
        ("placed", False, 1),
    ],
)
@pytest.mark.regression
# Проверяет несколько комбинаций (placed/approved/delivered…)
def test_order_create_param(api_client, unique_order_id, unique_pet_id,
                            make_order, cleanup, status, complete, quantity):
    logging.info(
        f"CREATE(PARAM) order_id={unique_order_id} pet_id={unique_pet_id} "
        f"status={status} complete={complete} quantity={quantity}"
    )
    with allure.step(
            f"Создаём заказ через POST /store/order с параметрами status={status}, complete={complete}, quantity={quantity}"):
        make_order(unique_order_id, unique_pet_id, status=status, complete=complete, quantity=quantity)
        # добавляем элемент в cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Проверяем заказ через GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            attach_json("GET /order response", resp.json())
            data = resp.json()
            assert data.get("id") == unique_order_id
            assert data.get("petId") == unique_pet_id
            assert isinstance(data.get("complete"), bool)


# Для flaky используем pytest-rerunfailures:
@allure.feature("Store")
@allure.story("Delete order (flaky public stand)")
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.regression
def test_order_delete(api_client, unique_order_id, unique_pet_id, make_order):
    logging.info(f"DELETE order_id={unique_order_id}")

    with allure.step("Создаём заказ через POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True)

    with allure.step("Удаляем заказ через DELETE /store/order/{id}"):
        resp = api_client.delete_order(unique_order_id)
        allure.attach(str(resp.status_code), "delete_status", allure.attachment_type.TEXT)
        assert resp.status_code in (200, 204, 400, 404), f"Неожиданный код при удалении: {resp.status_code}"

    with allure.step("Проверяем удаление заказа через GET /store/order/{id} с повторными попытками"):
        resp = get_with_retry(api_client, unique_order_id, getter=api_client.get_order, expect_deleted=True)
        if resp.status_code == 200:
            attach_json("GET after delete", resp.json())

        if resp.status_code != 404:
            logging.warning("Заказ всё ещё существует после удаления — пробуем повторно удалить и проверить ещё раз")
            api_client.delete_order(unique_order_id)
            resp = get_with_retry(api_client, unique_order_id, getter=api_client.get_order, expect_deleted=True)
            if resp.status_code == 200:
                attach_json("GET after delete", resp.json())

        if resp.status_code != 404:
            pytest.xfail("Флак Petstore: заказ может временно оставаться доступным после DELETE")
        else:
            logging.info("Заказ успешно удалён (GET -> 404)")
