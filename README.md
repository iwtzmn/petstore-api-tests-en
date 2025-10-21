# 🧪 PetStore API Tests

Automated testing of the public **Swagger PetStore** REST API using **PyTest**, **Requests**, and **Allure**.

---

## 🎯 Project Goals
- Validate CRUD operations for **User**, **Pet**, and **Store** entities.
- Demonstrate the use of fixtures, parametrization, and a lightweight API client wrapper.
- Set up **Allure** reporting and enable parallel test execution.

---

## ⚙️ Tech Stack
- **Python 3.11+**
- **PyTest**
- **Requests**
- **Allure-PyTest**
- **pytest-xdist** (parallel runs)
- **pytest-rerunfailures** (retry flaky tests)
- **Makefile** (common commands)

---

## 📁 Project Structure
```
PetStoreProject/
│
├── tests/                          # Test suite
│   ├── test_user_crud.py           # User CRUD
│   ├── test_store_order.py         # Store orders
│   ├── test_store_inventory.py     # Store inventory
│   ├── test_pet_crud.py            # Pet CRUD
│   └── test_pet_find_and_upload.py # Pet image upload & find
│
├── utils/
│   └── api_client.py               # API client wrapper
│
├── pytest.ini                      # PyTest configuration
├── conftest.py                     # Shared fixtures & helpers
├── requirements.txt                # Dependencies
├── Makefile                        # Make targets for local runs
├── .gitignore                      # Git ignore rules
└── README.md                       # Documentation
```

---

## ✅ Test Coverage

| Module | Scenarios | Case Types |
|---|---|---|
| **Pet** | create, read, update, delete, image upload | valid & invalid CRUD |
| **User** | create, read, update, delete, login/logout | valid & invalid data |
| **Store** | create order, delete order, check inventory | valid & invalid IDs |

**Total tests:** 27  
**Breakdown:**
- ✅ Valid scenarios — 17
- ⚠️ Invalid scenarios — 10

---

## 🧰 Test Diagnostics
Useful commands to verify that PyTest correctly discovers all tests and parametrized nodes.

### 🔹 List all collected test nodes
Save all collected nodes (including parametrized ones) to `now.txt`:
```bash
pytest --collect-only -q > now.txt
```

### 🔹 Per-file summary (how many tests per file)
```bash
awk -F'::' '{print $1}' now.txt | sort | uniq -c
```

### 🔹 Inspect tests inside a specific file
```bash
pytest tests/test_store_order.py --collect-only -q
```

---

## 🧩 Approaches Used

### 🔹 Fixtures
Used for:
- creating and cleaning up test users, pets, and orders;
- preparing data before test execution;
- repeated GET checks with waiting (`get_with_retry`);
- automatic resource cleanup after tests (`cleanup`).

### 🔹 Parametrize
Applied to:
- test different input combinations (e.g., `userStatus`, `petStatus`, `orderId`);
- validate APIs with valid and invalid parameters;
- reduce duplication while increasing coverage.

> 💡 This keeps the code **flexible, readable, and maintainable**—adding scenarios often means extending parameters instead of duplicating tests.

### 🔹 Smoke & Regression marks
- `@pytest.mark.smoke` — **critical flows** (API availability & core operations)
- `@pytest.mark.regression` — **deep stability checks** after changes

### 🔹 Flaky tests
To handle unstable responses from the public PetStore API:
```python
@pytest.mark.flaky(reruns=2, reruns_delay=1)
```
This ensures:
- up to **2 automatic reruns** with a 1‑second delay;
- more stable CI/CD pipelines despite transient issues;
- Allure keeps visibility with the “Flaky” label.

---

## 🚀 Local Setup & Run
> Requirements: **Python 3.11+**, **Allure CLI** installed

### 1️⃣ Go to the project root
Make sure you are where `pytest.ini`, `requirements.txt`, and `Makefile` are located.

### 2️⃣ Create a virtual environment
**macOS / Linux**
```bash
python3 -m venv .venv
source .venv/bin/activate
```
**Windows**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3️⃣ Install dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Run tests
```bash
pytest -v
```
Parallel execution:
```bash
pytest -v -n auto
```

### 5️⃣ Generate Allure report
```bash
pytest --alluredir=allure-results
allure serve allure-results
```
If `allure` is not found:
- macOS → `brew install allure`
- Windows → `choco install allure` or `scoop install allure`

---

## 📊 Reporting
After a test run, open the report:
```bash
allure serve allure-results
```
Allure provides an interactive report with:
- **Suites** — test suites by files
- **Behaviors** — grouping by features (`@allure.feature`, `@allure.story`)
- **Graphs / Timeline** — trends and execution time
- **Attachments** — JSON responses, logs, and status codes

Each run can start clean when using the Makefile target: **`make report`**.

---

## 🧠 Makefile Commands
- **`make smoke`** — run smoke tests (`MARK=smoke`) and open the report
- **`make regression`** — run regression tests (`MARK=regression`)
- **`make report`** — clean, run tests, generate Allure report, and open it
- **`make clean`** — remove `allure-results` and `allure-report`
- **`make open-report`** — open an already generated Allure report

---

## 👩‍💻 Author
**Irina Weitzman**  
QA Engineer | Python | API Automation Testing  
📫 GitHub: **iwtzmn**