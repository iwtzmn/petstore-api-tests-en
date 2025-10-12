import logging
import pytest
import allure
from conftest import get_with_retry, attach_json

PASSWORD_OK = "p@ssw0rd!"
PASSWORD_BAD = "wrong_pass!"


@pytest.mark.parametrize(
    "valid_username, valid_password, expected_codes",
    [
        (True, True, {200}),  # valid_credentials
        (True, False, {200, 400}),  # invalid_password (публичный стенд часто даёт 200)
        (False, True, {200, 400}),  # invalid_username
        (False, False, {200, 400}),  # invalid_both
    ],
    ids=["valid_credentials", "invalid_password", "invalid_username", "invalid_both"],
)
@pytest.mark.regression
@allure.feature("User")
@allure.story("User login (parametrized)")
def test_user_login_parametrized(api_client, unique_user_id, unique_username,
                                 valid_username, valid_password, expected_codes,
                                 make_user, cleanup):
    logging.info(f"--- ТЕСТ НАЧАТ (id={unique_user_id}, username={unique_username}) ---")

    # Подготовка: создаём реального пользователя, если сценарий того требует
    real_username = unique_username
    real_password = PASSWORD_OK

    if valid_username:
        with allure.step("Создание тестового пользователя"):
            make_user(id=unique_user_id, username=real_username, userStatus=0)
            # добавляем элемент в cleanup
            cleanup["user"].append(real_username)
            # дождаться доступности по GET
            assert get_with_retry(api_client, real_username, getter=api_client.get_user).status_code == 200
            attach_json("Created user", {"username": real_username})

    username = real_username if valid_username else f"{unique_username}_invalid"
    password = real_password if valid_password else PASSWORD_BAD

    with allure.step("Выполнить login запрос"):
        logging.info(f"Пробуем логин: username={username}, password={'OK' if valid_password else 'BAD'}")
        resp = api_client.login_user(username, password)
        logging.info(f"Ожидали коды {expected_codes}, получили {resp.status_code}")
        attach_json("Login request", {"username": username, "password": password})
        attach_json("Login response", resp.json() if resp.text else {"status_code": resp.status_code})

    assert resp.status_code in expected_codes, (
        f"Ожидали {expected_codes}, получили {resp.status_code}"
    )

    with allure.step("Выполнить logout после login"):
        logout = api_client.logout_user()
        logging.info(f"Logout вернул: {logout.status_code}")
        attach_json("Logout response", {"status_code": logout.status_code})
        assert logout.status_code == 200

    logging.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЁН ---")


@pytest.mark.smoke
@allure.feature("User")
@allure.story("User logout (smoke)")
def test_user_logout(api_client):
    logging.info("--- ТЕСТ НАЧАТ (logout smoke) ---")

    with allure.step("Выполнить logout без активной сессии"):
        resp = api_client.logout_user()
        attach_json("Logout response", {"status_code": resp.status_code})
        logging.info(f"GET /user/logout -> {resp.status_code}")
        assert resp.status_code == 200, "Ожидали 200 от /user/logout"

    logging.info("--- ТЕСТ УСПЕШНО ЗАВЕРШЁН ---")
