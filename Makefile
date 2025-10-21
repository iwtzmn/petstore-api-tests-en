SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# ==== Parameters with defaults ====
ALLURE_RESULTS ?= allure-results
ALLURE_REPORT  ?= allure-report
PYTEST         ?= pytest
EXIT_CODE_FILE ?= .pytest_exit_code

# Options that can be passed to make:
#   MARK=smoke / regression / "smoke or regression"
#   WORKERS=auto (or a number)
#   PYTEST_ARGS="... any additional arguments ..."
#
# Examples:
#   make report
#   make smoke
#   make regression
#   make report MARK="smoke or regression"
#   make report WORKERS=auto
#   make report PYTEST_ARGS="-k user -x"

define RUN_PYTEST
	@echo "[pytest] running with MARK='$(MARK)' WORKERS='$(WORKERS)' PYTEST_ARGS='$(PYTEST_ARGS)'"
	@exit_code=0; \
	$(PYTEST) -v \
	  $(if $(MARK),-m '$(MARK)',) \
	  $(if $(WORKERS),-n $(WORKERS),) \
	  $(PYTEST_ARGS) \
	  --alluredir=$(ALLURE_RESULTS) || exit_code=$$?; \
	echo "[pytest] exit code: $$exit_code"; \
	echo $$exit_code > $(EXIT_CODE_FILE)
endef

.PHONY: help clean results report smoke regression open-report

help:
	@echo "Targets:"
	@echo "  make report            - clean + pytest + allure open"
	@echo "  make smoke             - report with MARK=smoke + allure open"
	@echo "  make regression        - report with MARK=regression + allure open"
	@echo "  make clean             - remove allure-results and allure-report"
	@echo "  make open-report       - only open the already generated report"
	@echo ""
	@echo "Parameters: MARK=..., WORKERS=..., PYTEST_ARGS=..."
	@echo "Examples:   make report MARK='smoke or regression' WORKERS=auto"

clean:
	@rm -rf $(ALLURE_RESULTS) $(ALLURE_REPORT) $(EXIT_CODE_FILE) now.txt

results: clean
	@echo "[make] collecting results into $(ALLURE_RESULTS)"
	$(RUN_PYTEST)

report: results
	@echo "[allure] generate report → $(ALLURE_REPORT) from $(ALLURE_RESULTS)"
	allure generate --clean -o $(ALLURE_REPORT) $(ALLURE_RESULTS) || true
	@echo "[allure] open report"
	- allure open $(ALLURE_REPORT) >/dev/null 2>&1 &
	@exit_code=$$(cat $(EXIT_CODE_FILE) 2>/dev/null || echo 0); echo "[make] returning pytest exit $$exit_code"; exit $$exit_code

smoke:
	@$(MAKE) report MARK=smoke

regression:
	@$(MAKE) report MARK=regression

open-report:
	@echo "[allure] open existing report → $(ALLURE_REPORT)"
	allure open $(ALLURE_REPORT)