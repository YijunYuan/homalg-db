UV := uv run --project tools --locked --all-extras

.PHONY: setup test validate-fast validate site data fixture-site check-fixture-site gen-roots governance literature

setup:
	uv sync --project tools --locked --all-extras
	npm ci --prefix site

test:
	$(UV) python tools/scripts/audit_security.py
	$(UV) ruff check tools
	$(UV) ruff format --check tools/homalg tools/tests
	$(UV) pytest tools/tests
	npm ci --prefix site
	npm run generate-types --prefix site -- --check
	npm run format:check --prefix site
	npm run lint --prefix site
	npm test --prefix site
	$(MAKE) check-fixture-site

validate-fast:
	$(UV) homalg validate --fast

validate:
	$(UV) homalg validate
	HOMALG_LEAN_TESTS=1 $(UV) pytest tools/tests/test_lean_smoke.py tools/tests/test_leanexport.py

site:
	npm ci --prefix site
	npm run build --prefix site

data:
	npm ci --prefix site
	$(UV) homalg gen-roots
	$(UV) homalg extract
	$(UV) homalg export-lean --all
	$(UV) homalg index
	$(UV) homalg site-data --check-budgets

fixture-site:
	$(UV) homalg index --docs Fixture2000,Fixture2001 --commit fixture --repo-url https://github.com/example/homalg-db --out build/fixture-index.json
	$(UV) homalg site-data --from build/fixture-index.json --out site/fixtures/data

check-fixture-site:
	$(UV) python tools/scripts/check_fixture_site.py

gen-roots:
	$(UV) homalg gen-roots

governance:
	python3 tools/scripts/governance.py $(GOVERNANCE_ARGS)

literature:
	$(UV) homalg literature sync
