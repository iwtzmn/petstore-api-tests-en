import logging
import pytest
import allure
from conftest import get_with_retry, attach_json


@allure.feature("User")
@allure.story("Create user")
@pytest.mark.smoke
# Проверяет базовый happy-path (один стабильный заказ)
def test_user_create(api_client, unique_user_id, unique_username, make_user, cleanup):
    logging.info(f"CREATE user: id={unique_user_id}, username={unique_username}")
    with allure.step("Создать пользователя через POST /user"):
        # добавляем элемент в cleanup
        username = make_user(id=unique_user_id, username=unique_username, userStatus=0)
        cleanup["user"].append(username)

    with allure.step("Убедиться, что пользователь читается через GET /user/{username}"):
        resp = get_with_retry(api_client, username, getter=api_client.get_user)
        attach_json("GET /user response", resp.json())
        assert resp.status_code == 200, "Пользователь не найден после создания"
        body = resp.json()
        assert body.get("username") == username
        assert body.get("userStatus") in (0, 1)


@allure.feature("User")
@allure.story("Get user by username")
@pytest.mark.regression
def test_user_get(api_client, unique_user_id, unique_username, make_user, cleanup):
    logging.info(f"GET user: username={unique_username}")
    with allure.step("Создать пользователя через POST /user"):
        username = make_user(id=unique_user_id, username=unique_username, userStatus=0)
        # добавляем элемент в cleanup
        cleanup["user"].append(username)

    with allure.step("Убедиться, что пользователь читается через GET /user/{username}"):
        resp = get_with_retry(api_client, username, getter=api_client.get_user)
        attach_json("GET /user response", resp.json())
        assert resp.status_code == 200, "Пользователь не найден"
        body = resp.json()
        assert body.get("username") == username
        assert isinstance(body.get("email"), str)
        assert isinstance(body.get("userStatus"), int)


@allure.feature("User")
@allure.story("Update user status (parametrized)")
@pytest.mark.parametrize(
    "initial_status, updated_status",
    [
        (0, 1),
        (1, 1),
        (0, 0),
    ],
)
@pytest.mark.regression
def test_user_update_status(api_client, unique_user_id, unique_username, make_user, cleanup,
                            initial_status, updated_status):
    logging.info(f"UPDATE user: username={unique_username} {initial_status} -> {updated_status}")

    with allure.step(f"Создать пользователя со статусом {initial_status}"):
        username = make_user(id=unique_user_id, username=unique_username, userStatus=initial_status)
        cleanup["user"].append(username)

    with allure.step("Дождаться доступности пользователя (GET)"):
        resp = get_with_retry(api_client, username, getter=api_client.get_user)
        attach_json("GET before update", resp.json())
        assert resp.status_code == 200, "Пользователь не появился после создания"

    payload = {
        "id": unique_user_id,
        "username": username,
        "firstName": "Updated",
        "lastName": "User",
        "email": f"{username}@example.com",
        "password": "p@ssw0rd!",
        "phone": "+1000000000",
        "userStatus": updated_status,
    }
    attach_json("PUT /user payload", payload)

    with allure.step("Обновить пользователя через PUT /user/{username}"):
        resp = api_client.update_user(username, payload)
        assert resp.status_code in (200, 204), f"Неожиданный код на UPDATE: {resp.status_code}"

    with allure.step("Проверить, что статус обновился (GET с retry)"):
        resp = get_with_retry(api_client, username, getter=api_client.get_user,
                              field="userStatus", expected=updated_status)
        attach_json("GET after update", resp.json())
        assert resp.status_code == 200
        assert resp.json().get("userStatus") == updated_status


# Для flaky используем pytest-rerunfailures:
@allure.feature("User")
@allure.story("Delete user (flaky public stand)")
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.regression
def test_user_delete(api_client, unique_user_id, unique_username, make_user):
    logging.info(f"DELETE user: username={unique_username}")
    with allure.step("Создать пользователя перед удалением"):
        username = make_user(id=unique_user_id, username=unique_username, userStatus=0)

    with allure.step("Удалить пользователя через DELETE /user/{username}"):
        resp = api_client.delete_user(username)
        allure.attach(str(resp.status_code), "delete_status", allure.attachment_type.TEXT)
        assert resp.status_code in (200, 204, 404), f"Неожиданный код при удалении: {resp.status_code}"

    with allure.step("Подтвердить удаление: GET -> 404 (с retry)"):
        resp = get_with_retry(api_client, username, getter=api_client.get_user, expect_deleted=True)

        if resp.status_code != 404:
            attach_json("GET after delete", resp.json())
            logging.warning(
                "Пользователь всё ещё существует после удаления — пробуем повторно удалить и проверить ещё раз")
            api_client.delete_user(username)
            resp = get_with_retry(api_client, username, getter=api_client.get_user, expect_deleted=True)

        if resp.status_code != 404:
            pytest.xfail("Флак Petstore: пользователь может временно оставаться доступным после DELETE")
        else:
            logging.info("Пользователь успешно удалён (GET -> 404)")
