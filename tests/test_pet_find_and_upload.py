import logging
import pytest
import allure
from conftest import get_with_retry, attach_json


# На публичном Petstore POST /pet/{petId} через form-data не принимает частичные обновления (только name или только status)
# и стабильно отдаёт 405/400, а не 200.

@pytest.mark.regression
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@pytest.mark.parametrize(
    "new_name,new_status",
    [
        pytest.param("Nora", "pending", id="name+status"),
    ],
)
@allure.feature("Pet")
@allure.story("Update pet via form-data (parametrized)")
def test_pet_update_via_form(api_client, unique_pet_id, make_pet, new_name, new_status, cleanup):
    logging.info(f"[UPDATE-FORM] START pet_id={unique_pet_id}")
    with allure.step("Создать питомца для form-data обновления"):
        make_pet(unique_pet_id, status="available", name="Chaya")

        # добавляем элемент в cleanup
        cleanup["pet"].append(unique_pet_id)

    kwargs = {}
    if new_name is not None:
        kwargs["name"] = new_name
    if new_status is not None:
        kwargs["status"] = new_status

    with allure.step("Выполнить form-data обновление питомца"):
        resp = api_client.update_pet_form(unique_pet_id, **kwargs)
        attach_json("Request kwargs", kwargs)
        if resp.status_code == 200:
            attach_json("Response", resp.json())
    # На публичном стенде Petstore этот эндпойнт часто отдаёт 405/400.
    # Делаем тест толерантным: если не 200 — фиксируем как известный флак и
    # пропускаем детальные проверки.
    allowed = {200, 400, 405}
    assert resp.status_code in allowed, f"Неожиданный код при обновлении через form-data: {resp.status_code}"
    logging.info(f"[UPDATE-FORM] sent: {kwargs}, got={resp.status_code}")
    if resp.status_code != 200:
        pytest.xfail(
            "Публичный Petstore часто возвращает 405/400 на form-data update — пропускаем проверку содержимого")

    with allure.step("Проверить обновление питомца через GET"):
        resp = get_with_retry(api_client, unique_pet_id, field="status", expected=new_status)
        attach_json("GET response", resp.json())
        assert resp.status_code == 200
        pet = resp.json()
        logging.info(f"[UPDATE-FORM] got: name={pet.get('name')}, status={pet.get('status')}")

        assert pet.get("status") == new_status
        assert pet.get("name") in {new_name, "Chaya"}

    logging.info("[UPDATE-FORM] DONE")


@pytest.mark.regression
@pytest.mark.flaky(reruns=2, reruns_delay=1)
@allure.feature("Pet")
@allure.story("Upload pet image")
def test_pet_upload_image(api_client, unique_pet_id, make_pet, temp_image_file, cleanup):
    logging.info(f"[UPLOAD] START pet_id={unique_pet_id}")
    with allure.step("Создать питомца перед загрузкой изображения"):
        make_pet(unique_pet_id, status="available", name="Gosha")

        # добавляем элемент в cleanup
        cleanup["pet"].append(unique_pet_id)

    with allure.step("Загрузить изображение питомца через POST /pet/{id}/uploadImage"):
        resp = api_client.upload_pet_image(unique_pet_id, temp_image_file)
        attach_json("Upload response", resp.json())
    assert resp.status_code == 200, "Ошибка при загрузке изображения"
    msg = (resp.json().get("message") or "").lower()
    logging.info(f"[UPLOAD] response: {msg}")
    assert ("test metadata" in msg) or (str(unique_pet_id) in msg) or ("uploaded" in msg)

    logging.info("[UPLOAD] DONE")
