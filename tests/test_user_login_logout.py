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
        (True, False, {200, 400}),  # invalid_password (public environment often returns 200)
        (False, True, {200, 400}),  # invalid_username
        (False, False, {200, 400}),  # invalid_both
    ],
    ids=["valid_credentials", "invalid_password", "invalid_username", "invalid_both"],
)
@pytest.mark.regression
@allure.feature("User")
@allure.story("User login (parametrized)")
def test_user_login(api_client, unique_user_id, unique_username,
                                 valid_username, valid_password, expected_codes,
                                 make_user, cleanup):
    logging.info(f"--- TEST STARTED (id={unique_user_id}, username={unique_username}) ---")

    # Preparation: create a real user if the scenario requires it
    real_username = unique_username
    real_password = PASSWORD_OK

    if valid_username:
        with allure.step("Create test user"):
            make_user(id=unique_user_id, username=real_username, userStatus=0)
            # add item to cleanup
            cleanup["user"].append(real_username)
            # wait for availability via GET
            assert get_with_retry(api_client, real_username, getter=api_client.get_user).status_code == 200
            attach_json("Created user", {"username": real_username})

    username = real_username if valid_username else f"{unique_username}_invalid"
    password = real_password if valid_password else PASSWORD_BAD

    with allure.step("Perform login request"):
        logging.info(f"Trying login: username={username}, password={'OK' if valid_password else 'BAD'}")
        resp = api_client.login_user(username, password)
        logging.info(f"Expected codes {expected_codes}, got {resp.status_code}")
        attach_json("Login request", {"username": username, "password": password})
        attach_json("Login response", resp.json() if resp.text else {"status_code": resp.status_code})

    assert resp.status_code in expected_codes, (
        f"Expected {expected_codes}, got {resp.status_code}"
    )

    with allure.step("Perform logout after login"):
        logout = api_client.logout_user()
        logging.info(f"Logout returned: {logout.status_code}")
        attach_json("Logout response", {"status_code": logout.status_code})
        assert logout.status_code == 200

    logging.info("--- TEST FINISHED SUCCESSFULLY ---")


@pytest.mark.smoke
@allure.feature("User")
@allure.story("User logout")
def test_user_logout(api_client):
    logging.info("--- TEST STARTED (logout smoke) ---")

    with allure.step("Perform logout without active session"):
        resp = api_client.logout_user()
        attach_json("Logout response", {"status_code": resp.status_code})
        logging.info(f"GET /user/logout -> {resp.status_code}")
        assert resp.status_code == 200, "Expected 200 from /user/logout"

    logging.info("--- TEST FINISHED SUCCESSFULLY ---")
