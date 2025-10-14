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
    Это сделано для предотвращения конфликтов с питомцами других пользователей на публичном стенде
    """
    return 100000 + int(time.time() * 1000) % 900000  # например: 123456


@pytest.fixture
def unique_order_id():
    """
    Это используется в тестах блока store, чтобы гарантировать, что каждому заказу присваивается уникальный номер
    """
    return 10000 + int(time.time() * 1000) % 90000  # например: 12345


@pytest.fixture
def unique_username():
    """
    Случайный набор букв добавляется, чтобы предотвратить пересечение логинов с аккаунтами других пользователей
    """
    letters = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))
    return f"user_{letters}"  # например: user_qwe


@pytest.fixture
def unique_user_id():
    """
    Это используется в тестах блока user, чтобы каждому пользователю присваивался уникальный числовой ID
    """
    return 10000 + int(time.time() * 1000) % 90000  # например: 12345


@pytest.fixture
def temp_image_file(tmp_path):
    path = tmp_path / "test_image.jpg"
    # заглушка (не настоящее фото, но API примет его)
    with open(path, "wb") as f:
        f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    return str(path)


@pytest.fixture
def pet_id(api_client, unique_pet_id, make_pet):
    """Готовый питомец для GET/UPDATE/DELETE."""
    make_pet(unique_pet_id, status="available")
    return unique_pet_id


@pytest.fixture
def make_pet(api_client):
    """Фабрика: создаёт питомца, дожидается доступности по GET и возвращает pet_id."""

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
        # Petstore возвращает 200 на создание; допускаем 201 как каноничный вариант
        assert resp.status_code in (200, 201), f"Не создали питомца: {resp.status_code}"
        # Дождаться консистентности чтения (GET /pet/{id} -> 200)
        resp_get = get_with_retry(api_client, pet_id, getter=api_client.get_pet)
        assert resp_get.status_code == 200, "Питомец недоступен после создания"
        return pet_id

    return _create


@pytest.fixture
def make_order(api_client):
    """Фабрика: создаёт заказ, дожидается доступности по GET и возвращает order_id. READ на публичном стенде может быть нестабилен."""

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
        assert resp.status_code in (200, 201), f"Не создали заказ: {resp.status_code}"
        # Дождаться консистентности чтения (GET /store/order/{id} -> 200)
        resp_get = get_with_retry(api_client, order_id, getter=api_client.get_order)
        assert resp_get.status_code == 200, "Заказ недоступен после создания"
        return order_id

    return _create


@pytest.fixture
def make_user(api_client):
    """Фабрика: создаёт пользователя, дожидается доступности по GET и возвращает username."""

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
        assert resp.status_code in (200, 201), f"Не создали пользователя: {resp.status_code}"
        # дождаться, что GET /user/{username} начал отдавать пользователя
        resp_get = get_with_retry(api_client, username, getter=api_client.get_user)
        assert resp_get.status_code == 200, "Пользователь недоступен после создания"
        return username

    return _create


@pytest.fixture
def cleanup(api_client):
    """
    Универсальная очистка: {"pet": [], "user": [], "order": []}
    В конце теста удаляем всё, что пользователь добавил в списки.
    """
    bag = {"pet": [], "user": [], "order": []}
    yield bag

    # pets
    for pet_id in bag["pet"]:
        try:
            api_client.delete_pet(pet_id)
        except Exception as e:
            logging.warning(f"Не удалось удалить питомца {pet_id}: {e}")

    # users
    for username in bag["user"]:
        try:
            api_client.delete_user(username)
        except Exception as e:
            logging.warning(f"Не удалось удалить пользователя {username}: {e}")

    # orders
    for order_id in bag["order"]:
        try:
            api_client.delete_order(order_id)
        except Exception as e:
            logging.warning(f"Не удалось удалить заказ {order_id}: {e}")


def get_with_retry(api_client, entity_id, getter=None, field=None, expected=None, expect_deleted=False, attempts=30,
                   delay=0.5):
    """
    Универсальный retry, выполняющий повторные проверки состояния ресурса через GET.
    Используется после POST/PUT/DELETE, чтобы дождаться нужного результата.

    :param getter: функция получения сущности (например, api_client.get_pet или api_client.get_order)
    :param expect_deleted: если True — ждём 404 (удаление)
    """
    getter = getter or api_client.get_pet  # дефолт: get_pet
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
    """Возвращает текущую дату и время в формате ISO 8601 (UTC)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def attach_json(data, name="payload"):
    """Вспомогательная функция для добавления JSON-данных в отчёт Allure"""
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
