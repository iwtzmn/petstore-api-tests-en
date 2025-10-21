import logging
import time
import random
import string
import pytest
import allure
import json
from datetime import datetime, timezone
from utils.api_client import PetStoreClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)


@pytest.fixture(scope="session")
def api_client():
    return PetStoreClient()


@pytest.fixture
def unique_pet_id():
    """
    This prevents conflicts with pets created by other users on the public environment.
    """
    return 100000 + int(time.time() * 1000) % 900000  # for example: 123456


@pytest.fixture
def unique_order_id():
    """
    Used in store tests to ensure each order gets a unique number.
    """
    return 10000 + int(time.time() * 1000) % 90000  # for example: 12345


@pytest.fixture
def unique_username():
    """
    A random suffix is added to avoid collisions with other users' accounts.
    """
    letters = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))
    return f"user_{letters}"  # for example: user_qwe


@pytest.fixture
def unique_user_id():
    """
    Used in user tests to ensure each user gets a unique numeric ID.
    """
    return 10000 + int(time.time() * 1000) % 90000  # for example: 12345


@pytest.fixture
def temp_image_file(tmp_path):
    path = tmp_path / "test_image.jpg"
    # stub (not a real photo, but the API will accept it)
    with open(path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    return str(path)


@pytest.fixture
def pet_id(api_client, unique_pet_id, make_pet):
    """Ready-made pet for GET/UPDATE/DELETE."""
    make_pet(unique_pet_id, status="available")
    return unique_pet_id


@pytest.fixture
def make_pet(api_client):
    """Creates a pet, waits until it is available via GET, and returns pet_id"""

    def _create(pet_id, status="available", name="Chupa"):
        payload = {
            "id": pet_id,
            "category": {"id": 1, "name": "cats"},
            "name": name,
            "photoUrls": ["https://example.com/cat.jpg"],
            "tags": [{"id": 1, "name": "cute"}],
            "status": status,
        }
        resp = api_client.add_pet(payload)
        # Petstore returns 200 on create; accept 201 as a canonical alternative
        assert resp.status_code in (200, 201), f"Failed to create pet: {resp.status_code}"
        # Wait for read consistency (GET /pet/{id} -> 200)
        resp_get = get_with_retry(api_client, pet_id, getter=api_client.get_pet)
        assert resp_get.status_code == 200, "Pet not available after creation"
        return pet_id

    return _create


@pytest.fixture
def make_order(api_client):
    """Creates an order, waits until it is available via GET, and returns order_id. READ on the public environment may be unstable"""

    def _create(order_id, pet_id, status="placed", complete=True, quantity=1):
        payload = {
            "id": order_id,
            "petId": pet_id,
            "quantity": quantity,
            "shipDate": _now_iso(),
            "status": status,
            "complete": complete,
        }
        resp = api_client.create_order(payload)
        assert resp.status_code in (200, 201), f"Failed to create order: {resp.status_code}"
        # Wait for read consistency (GET /store/order/{id} -> 200)
        resp_get = get_with_retry(api_client, order_id, getter=api_client.get_order)
        assert resp_get.status_code == 200, "Order not available after creation"
        return order_id

    return _create


@pytest.fixture
def make_user(api_client):
    """Creates a user, waits until it is available via GET, and returns username"""

    def _create(id: int, username: str, userStatus: int = 0):
        payload = {
            "id": id,
            "username": username,
            "firstName": "Test",
            "lastName": "User",
            "email": f"{username}@example.com",
            "password": "p@ssw0rd!",
            "phone": "+1000000000",
            "userStatus": userStatus,
        }
        resp = api_client.create_user(payload)
        assert resp.status_code in (200, 201), f"Failed to create user: {resp.status_code}"
        # wait until GET /user/{username} returns the user
        resp_get = get_with_retry(api_client, username, getter=api_client.get_user)
        assert resp_get.status_code == 200, "User not available after creation"
        return username

    return _create


@pytest.fixture
def cleanup(api_client):
    """
    Generic cleanup: {"pet": [], "user": [], "order": []}
    At the end of the test, delete everything the test added to these lists.
    """
    bag = {"pet": [], "user": [], "order": []}
    yield bag

    # pets
    for pet_id in bag["pet"]:
        try:
            api_client.delete_pet(pet_id)
        except Exception as e:
            logging.warning(f"Failed to delete pet {pet_id}: {e}")

    # users
    for username in bag["user"]:
        try:
            api_client.delete_user(username)
        except Exception as e:
            logging.warning(f"Failed to delete user {username}: {e}")

    # orders
    for order_id in bag["order"]:
        try:
            api_client.delete_order(order_id)
        except Exception as e:
            logging.warning(f"Failed to delete order {order_id}: {e}")


def get_with_retry(api_client, entity_id, getter=None, field=None, expected=None, expect_deleted=False, attempts=30,
                   delay=0.5):
    """
    Generic retry that repeatedly checks a resource state via GET.
    Used after POST/PUT/DELETE to wait for the desired result.

    :param getter: function to fetch the entity (e.g., api_client.get_pet or api_client.get_order)
    :param expect_deleted: if True — wait for 404 (deletion)
    """
    getter = getter or api_client.get_pet  # default: get_pet
    resp = None
    for _ in range(attempts):
        resp = getter(entity_id)

        if expect_deleted and resp.status_code == 404:
            return resp

        if resp.status_code == 200 and (field is None or resp.json().get(field) == expected):
            return resp

        time.sleep(delay)
    return resp


def _now_iso():
    """Returns the current date and time in ISO 8601 (UTC)"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def attach_json(data, name="payload"):
    """Helper function to attach JSON data to the Allure report"""
    if isinstance(name, str):
        name_str = name
    else:
        try:
            name_str = json.dumps(name, ensure_ascii=False)
        except Exception:
            name_str = str(name)
    try:
        allure.attach(
            json.dumps(data, ensure_ascii=False, indent=2),
            name=name_str,
            attachment_type=allure.attachment_type.JSON
        )
    except Exception:
        allure.attach(str(data), name=name_str, attachment_type=allure.attachment_type.TEXT)
