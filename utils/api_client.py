import os
import requests
from dotenv import load_dotenv

# Loading variables from .env
load_dotenv()

BASE_URL = os.getenv("BASE_URL")


class PetStoreClient:

    def __init__(self):
        if not BASE_URL:
            raise ValueError("BASE_URL not found in file .env")
        self.base_url = BASE_URL

    # --- PET ---

    def get_pet(self, pet_id):
        return requests.get(f"{self.base_url}/pet/{pet_id}")

    def add_pet(self, pet_data):
        return requests.post(f"{self.base_url}/pet/", json=pet_data)

    def update_pet(self, pet_data):
        return requests.put(f"{self.base_url}/pet/", json=pet_data)

    def delete_pet(self, pet_id):
        return requests.delete(f"{self.base_url}/pet/{pet_id}")

    def find_by_status(self, status):
        return requests.get(f"{self.base_url}/pet/findByStatus", params={"status": status})

    def update_pet_form(self, pet_id, name=None, status=None):
        """Update pet via form-data (application/x-www-form-urlencoded)"""
        data = {}
        if name:
            data["name"] = name
        if status:
            data["status"] = status
        return requests.post(f"{self.base_url}/pet/{pet_id}", data=data)

    def upload_pet_image(self, pet_id, file_path):
        """Upload pet image (multipart/form-data)"""
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "image/jpeg")}
            return requests.post(f"{self.base_url}/pet/{pet_id}/uploadImage", files=files)

    # --- STORE ---

    def create_order(self, order_data):
        return requests.post(f"{self.base_url}/store/order", json=order_data)

    def get_order(self, order_id):
        return requests.get(f"{self.base_url}/store/order/{order_id}")

    def delete_order(self, order_id):
        return requests.delete(f"{self.base_url}/store/order/{order_id}")

    def get_inventory(self):
        return requests.get(f"{self.base_url}/store/inventory")

    # --- USER ---

    def create_user(self, user_data):
        return requests.post(f"{self.base_url}/user", json=user_data)

    def create_users_with_list(self, users_list):
        return requests.post(f"{self.base_url}/user/createWithList", json=users_list)

    def get_user(self, username):
        return requests.get(f"{self.base_url}/user/{username}")

    def update_user(self, username, user_data):
        return requests.put(f"{self.base_url}/user/{username}", json=user_data)

    def delete_user(self, username):
        return requests.delete(f"{self.base_url}/user/{username}")

    def login_user(self, username, password):
        params = {"username": username, "password": password}
        return requests.get(f"{self.base_url}/user/login", params=params)

    def logout_user(self):
        return requests.get(f"{self.base_url}/user/logout")
