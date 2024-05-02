MOUNT_POINT ?= /mnt
DOCKER_LOCAL_DATA ?= /srv/off/docker_data
ENV_FILE ?= .env
# for dev we need to align user uid with the one in the container
# this is handled through build args
UID ?= $(shell id -u)
export USER_UID:=${UID}
# prefer to use docker buildkit
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
# we need COMPOSE_PROJECT_NAME for some commands
# take it form env, or from env file
COMPOSE_PROJECT_NAME ?= $(shell grep COMPOSE_PROJECT_NAME ${ENV_FILE} | cut -d '=' -f 2)
DOCKER_COMPOSE=docker compose --env-file=${ENV_FILE}
DOCKER_COMPOSE_TEST=COMPOSE_PROJECT_NAME=${COMPOSE_PROJECT_NAME}_test docker compose --env-file=${ENV_FILE}

# avoid target corresponding to file names, to depends on them
.PHONY: *

#-----------#
# Utilities #
#-----------#

guard-%: # guard clause for targets that require an environment variable (usually used as an argument)
	@ if [ "${${*}}" = "" ]; then \
   		echo "Environment variable '$*' is mandatory"; \
   		echo use "make ${MAKECMDGOALS} $*=you-args"; \
   		exit 1; \
	fi;

#------------#
# Production #
#------------#

test:
	echo ${ENV_FILE} ${COMPOSE_PROJECT_NAME}

livecheck:
	@echo "🥫 livecheck services…" ; \
	exit_code=0; \
	services=`${DOCKER_COMPOSE} config  --service | tr '\n' ' '`; \
	for service in $$services; do \
	if [ -z `docker compose ps -q $$service` ] || [ -z `docker ps -q --no-trunc | grep $$(${DOCKER_COMPOSE} ps -q $$service)` ]; then \
		echo "$$service: DOWN"; \
		exit_code=1; \
	else \
		echo "$$service: UP"; \
	fi \
	done; \
	[ $$exit_code -eq 0 ] && echo "Success !"; \
	exit $$exit_code;


build:
	@echo "🥫 building docker (for dev)"
	${DOCKER_COMPOSE} build


up:
ifdef service
	${DOCKER_COMPOSE} up -d ${service} 2>&1
else
	${DOCKER_COMPOSE} up -d 2>&1
endif


down:
	@echo "🥫 Bringing down containers …"
	${DOCKER_COMPOSE} down


hdown:
	@echo "🥫 Bringing down containers and associated volumes …"
	${DOCKER_COMPOSE} down -v


# pull images from image repository
pull:
	${DOCKER_COMPOSE} pull

restart:
	@echo "🥫 Restarting containers …"
	${DOCKER_COMPOSE} restart

status:
	@echo "🥫 Getting container status …"
	${DOCKER_COMPOSE} ps

log:
	@echo "🥫 Reading logs (docker compose) …"
	${DOCKER_COMPOSE} logs -f api


#------------#
# Quality    #
#------------#
toml-check:
	${DOCKER_COMPOSE} run --rm --no-deps api poetry run toml-sort --check pyproject.toml

toml-lint:
	${DOCKER_COMPOSE} run --rm --no-deps api poetry run toml-sort --in-place pyproject.toml

flake8:
	${DOCKER_COMPOSE} run --rm --no-deps api flake8

black-check:
	${DOCKER_COMPOSE} run --rm --no-deps api black --check .

black:
	${DOCKER_COMPOSE} run --rm --no-deps api black .

mypy:
	${DOCKER_COMPOSE} run --rm --no-deps api mypy .

isort-check:
	${DOCKER_COMPOSE} run --rm --no-deps api isort --check .

isort:
	${DOCKER_COMPOSE} run --rm --no-deps api isort .

docs:
	@echo "🥫 Generationg doc…"
	${DOCKER_COMPOSE} run --rm --no-deps api ./build_mkdocs.sh

checks: toml-check flake8 black-check mypy isort-check docs


tests: unit-tests integration-tests

unit-tests:
	@echo "🥫 Running tests …"
	# change project name to run in isolation
	${DOCKER_COMPOSE_TEST} run --rm api poetry run pytest tests/unit

integration-tests:
	@echo "🥫 Running integration tests …"
	# change project name to run in isolation
	${DOCKER_COMPOSE_TEST} run --rm api poetry run pytest tests/integration
	( ${DOCKER_COMPOSE_TEST} down -v || true )


#------------#
# Production #
#------------#

# Create all external volumes needed for production. Using external volumes is useful to prevent data loss (as they are not deleted when performing docker down -v)
create_external_volumes:
	@echo "🥫 Creating external volumes (production only) …"
	docker volume create open_prices_postgres-data


migrate-db:
	@echo "🥫 Migrating database …"
	${DOCKER_COMPOSE} run --rm --no-deps api poetry run alembic upgrade head

add-db-revision: guard-message
	${DOCKER_COMPOSE} run --rm --no-deps api alembic revision --autogenerate -m "${message}"

#---------#
# Cleanup #
#---------#
prune:
	@echo "🥫 Pruning unused Docker artifacts (save space) …"
	docker system prune -af

prune_cache:
	@echo "🥫 Pruning Docker builder cache …"
	docker builder prune -f
