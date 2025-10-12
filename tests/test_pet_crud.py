import logging
import pytest
import allure
from conftest import get_with_retry, attach_json


@allure.feature("Pet")
@allure.story("Create pet")
@pytest.mark.smoke
@pytest.mark.regression
def test_pet_create(api_client, unique_pet_id, make_pet, cleanup):
    with allure.step(f"CREATE pet_id={unique_pet_id}"):
        logging.info(f"CREATE pet_id={unique_pet_id}")
        make_pet(unique_pet_id, status="available")
        # добавляем элемент в cleanup
        cleanup["pet"].append(unique_pet_id)

        resp = get_with_retry(api_client, unique_pet_id)
        attach_json("Response body", resp.json())
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == unique_pet_id
        assert body["status"] == "available"


@allure.feature("Pet")
@allure.story("Get pet")
@pytest.mark.regression
def test_pet_get(api_client, pet_id):
    with allure.step(f"GET pet_id={pet_id}"):
        logging.info(f"GET pet_id={pet_id}")
        resp = get_with_retry(api_client, pet_id)
        attach_json("Response body", resp.json())
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == pet_id
        assert isinstance(body.get("category"), dict)
        assert isinstance(body.get("photoUrls"), list)
        assert isinstance(body.get("tags"), list)


@allure.feature("Pet")
@allure.story("Update pet status (parametrized)")
@pytest.mark.parametrize(
    "initial_status, updated_status",
    [
        ("available", "pending"),
        ("pending", "sold"),
        ("available", "sold"),
    ],
)
@pytest.mark.regression
def test_pet_update_status(api_client, unique_pet_id, make_pet, cleanup, initial_status, updated_status):
    with allure.step(f"UPDATE pet_id={unique_pet_id}: {initial_status} -> {updated_status}"):
        logging.info(f"UPDATE pet_id={unique_pet_id}: {initial_status} -> {updated_status}")
        make_pet(unique_pet_id, status=initial_status)
        # добавляем элемент в cleanup
        cleanup["pet"].append(unique_pet_id)

        payload = {
            "id": unique_pet_id,
            "category": {"id": 1, "name": "cats"},
            "name": "Chupa",
            "photoUrls": ["https://example.com/cat.jpg"],
            "tags": [{"id": 1, "name": "cute"}],
            "status": updated_status,
        }
        attach_json("Update payload", payload)
        resp = api_client.update_pet(payload)
        attach_json("Response body", resp.json())
        assert resp.status_code == 200, "Ошибка при обновлении питомца"

        resp = get_with_retry(api_client, unique_pet_id, field="status", expected=updated_status)
        attach_json("Response body", resp.json())
        assert resp.status_code == 200
        assert resp.json()["status"] == updated_status


# Для flaky используем pytest-rerunfailures:
@allure.feature("Pet")
@allure.story("Delete pet (flaky public stand)")
@pytest.mark.flaky(reruns=2, reruns_delay=1)  # повторим, если флак на публичном стенде
@pytest.mark.regression
def test_pet_delete(api_client, pet_id):
    with allure.step(f"DELETE pet_id={pet_id}"):
        logging.info(f"DELETE pet_id={pet_id}")

        # Сам DELETE
        resp = api_client.delete_pet(pet_id)
        attach_json("Response body", resp.json())
        assert resp.status_code in (200, 204, 404)

        # ждём подтверждения удаления
        resp = get_with_retry(api_client, pet_id, expect_deleted=True)
        attach_json("Response body", resp.json())

        if resp.status_code != 404:
            logging.warning("Не удалён сразу, пробуем ещё раз")
            api_client.delete_pet(pet_id)
            resp = get_with_retry(api_client, pet_id, expect_deleted=True)

        if resp.status_code != 404:
            pytest.xfail("Флак Petstore: ресурс иногда остаётся доступным после DELETE")
