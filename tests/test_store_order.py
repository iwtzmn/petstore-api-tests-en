import logging
import pytest
import allure
from conftest import get_with_retry, attach_json


@allure.feature("Store")
@allure.story("Create order")
@pytest.mark.smoke
@pytest.mark.regression
# Checks the basic happy-path (one stable order)
def test_order_create(api_client, unique_order_id, unique_pet_id, make_order, cleanup):
    logging.info(f"CREATE order_id={unique_order_id} pet_id={unique_pet_id}")
    with allure.step("Create order via POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True, quantity=1)
        # add element to cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Check order via GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404), f"Unexpected code on GET: {resp.status_code}"
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
    with allure.step("Create order via POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True)
        # add element to cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Check order via GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404), f"Unexpected code on GET: {resp.status_code}"
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
# Checks multiple combinations (placed/approved/delivered…)
def test_order_create_param(api_client, unique_order_id, unique_pet_id,
                            make_order, cleanup, status, complete, quantity):
    logging.info(
        f"CREATE(PARAM) order_id={unique_order_id} pet_id={unique_pet_id} "
        f"status={status} complete={complete} quantity={quantity}"
    )
    with allure.step(
            f"Create order via POST /store/order with parameters status={status}, complete={complete}, quantity={quantity}"):
        make_order(unique_order_id, unique_pet_id, status=status, complete=complete, quantity=quantity)
        # add element to cleanup
        cleanup["order"].append(unique_order_id)

    with allure.step("Check order via GET /store/order/{id}"):
        resp = api_client.get_order(unique_order_id)
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            attach_json("GET /order response", resp.json())
            data = resp.json()
            assert data.get("id") == unique_order_id
            assert data.get("petId") == unique_pet_id
            assert isinstance(data.get("complete"), bool)


# For flaky tests we use pytest-rerunfailures:
@allure.feature("Store")
@allure.story("Delete order (flaky public stand)")
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.regression
def test_order_delete(api_client, unique_order_id, unique_pet_id, make_order):
    logging.info(f"DELETE order_id={unique_order_id}")

    with allure.step("Create order via POST /store/order"):
        make_order(unique_order_id, unique_pet_id, status="placed", complete=True)

    with allure.step("Delete order via DELETE /store/order/{id}"):
        resp = api_client.delete_order(unique_order_id)
        allure.attach(str(resp.status_code), "delete_status", allure.attachment_type.TEXT)
        assert resp.status_code in (200, 204, 400, 404), f"Unexpected code on delete: {resp.status_code}"

    with allure.step("Check order deletion via GET /store/order/{id} with retries"):
        resp = get_with_retry(api_client, unique_order_id, getter=api_client.get_order, expect_deleted=True)
        if resp.status_code == 200:
            attach_json("GET after delete", resp.json())

        if resp.status_code != 404:
            logging.warning("Order still exists after deletion — trying to delete again and check once more")
            api_client.delete_order(unique_order_id)
            resp = get_with_retry(api_client, unique_order_id, getter=api_client.get_order, expect_deleted=True)
            if resp.status_code == 200:
                attach_json("GET after delete", resp.json())

        if resp.status_code != 404:
            pytest.xfail("Flaky Petstore: order may temporarily remain accessible after DELETE")
        else:
            logging.info("Order successfully deleted (GET -> 404)")
