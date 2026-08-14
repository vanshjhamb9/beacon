.PHONY: compile lint test e2e security performance recovery ci

compile:
	python -m compileall apps packages tests -q

lint:
	ruff check apps packages tests
	black --check apps packages tests
	isort --check-only apps packages tests

test:
	pytest tests/production_validation tests/live_revenue_execution tests/sales_intelligence -q

e2e:
	pytest tests/e2e -q

security:
	pytest tests/security -q

performance:
	pytest tests/performance tests/*/test_*performance*.py -q

recovery:
	pytest tests/recovery -q

ci: compile lint test e2e security recovery
	@echo "CI quality gates passed"
