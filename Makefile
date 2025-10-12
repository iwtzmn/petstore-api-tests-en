SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# ==== Параметры с дефолтами ====
ALLURE_RESULTS ?= allure-results
ALLURE_REPORT  ?= allure-report
PYTEST         ?= pytest

# Опции, которые можно передавать в make:
#   MARK=smoke / regression / "smoke or regression"
#   WORKERS=auto (или число)
#   PYTEST_ARGS="... любые доп. аргументы ..."
#
# Примеры:
#   make report
#   make smoke
#   make regression
#   make report MARK="smoke or regression"
#   make report WORKERS=auto
#   make report PYTEST_ARGS="-k user -x"

define RUN_PYTEST
	@echo "[pytest] running with MARK='$(MARK)' WORKERS='$(WORKERS)' PYTEST_ARGS='$(PYTEST_ARGS)'"
	$(PYTEST) -v \
	  $(if $(MARK),-m '$(MARK)',) \
	  $(if $(WORKERS),-n $(WORKERS),) \
	  $(PYTEST_ARGS) \
	  --alluredir=$(ALLURE_RESULTS)
endef

.PHONY: help clean results report smoke regression open-report

help:
	@echo "Targets:"
	@echo "  make report            - clean + pytest + allure open"
	@echo "  make smoke             - report с MARK=smoke"
	@echo "  make regression        - report с MARK=regression"
	@echo "  make clean             - удалить allure-results и allure-report"
	@echo "  make open-report       - только открыть уже сгенерированный отчёт"
	@echo ""
	@echo "Параметры: MARK=..., WORKERS=..., PYTEST_ARGS=..."
	@echo "Примеры:   make report MARK='smoke or regression' WORKERS=auto"

clean:
	@rm -rf $(ALLURE_RESULTS) $(ALLURE_REPORT)

results: clean
	@echo "[make] collecting results into $(ALLURE_RESULTS)"
	$(RUN_PYTEST)

report: results
	@echo "[allure] generate report → $(ALLURE_REPORT) from $(ALLURE_RESULTS)"
	allure generate --clean -o $(ALLURE_REPORT) $(ALLURE_RESULTS)
	@echo "[allure] open report"
	allure open $(ALLURE_REPORT)

smoke:
	@$(MAKE) report MARK=smoke

regression:
	@$(MAKE) report MARK=regression

open-report:
	@echo "[allure] open existing report → $(ALLURE_REPORT)"
	allure open $(ALLURE_REPORT)