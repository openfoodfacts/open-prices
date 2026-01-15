#!/usr/bin/make

ifneq (,$(wildcard ./.env))
    -include .env
    -include .envrc
    export
endif

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
DOCKER_COMPOSE=docker compose --env-file=${ENV_FILE}
DOCKER_COMPOSE_TEST=COMPOSE_PROJECT_NAME=open_prices_test COMMON_NET_NAME=po_test docker compose --env-file=${ENV_FILE}

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
	echo ${ENV_FILE}

livecheck:
	@echo "🥫 livecheck services…" ; \
	exit_code=0; \
	services=`${DOCKER_COMPOSE} config  --services | tr '\n' ' '`; \
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
	${DOCKER_COMPOSE} logs -f api update-listener scheduler


#------------#
# Quality    #
#------------#
toml-check:
	${DOCKER_COMPOSE} run --rm --no-deps api poetry run toml-sort --check pyproject.toml

toml-lint:
	${DOCKER_COMPOSE} run --rm --no-deps api poetry run toml-sort --in-place pyproject.toml

mypy:
	${DOCKER_COMPOSE} run --rm --no-deps api mypy .

docs:
	@echo "🥫 Generationg doc…"
	${DOCKER_COMPOSE} run --rm --no-deps api ./build_mkdocs.sh

checks: toml-check mypy docs

tests: django-tests

django-tests:
	@echo "🥫 Running tests …"
	# change project name to run in isolation
	# Override Q2_SYNC to make sure that async tasks are run synchronously during tests
	# See https://github.com/openfoodfacts/open-prices/issues/962
	${DOCKER_COMPOSE_TEST} run -e 'Q2_SYNC=True' --rm api poetry run python3 manage.py test -v 2


django-tests-single: guard-args
	@echo "🥫 Running specific tests …"
	${DOCKER_COMPOSE_TEST} run -e 'Q2_SYNC=True' --rm api poetry run python3 manage.py test -v 2 ${args}

#------------#
# Production #
#------------#

# Create all external volumes needed for production. Using external volumes is useful to prevent data loss (as they are not deleted when performing docker down -v)
create_external_volumes:
	@echo "🥫 Creating external volumes (production only) …"
	docker volume create open_prices_postgres-data
	docker volume create open_prices_images
	docker volume create open_prices_data-dump

create_external_networks:
	@echo "🥫 Creating external networks if needed … (dev only)"
	( docker network create ${COMMON_NET_NAME} || true )
# for tests
	( docker network create po_test || true )

cp-static-files:
	@echo "🥫 Copying static files from api container to the host …"
	docker cp open_prices-api-1:/opt/open-prices/static www/

migrate-db:
	@echo "🥫 Migrating database …"
	${DOCKER_COMPOSE} run --rm --no-deps api python3 manage.py migrate

cli: guard-args
	${DOCKER_COMPOSE} run --rm --no-deps api python3 manage.py ${args}


makemigrations:
	${DOCKER_COMPOSE} run --rm --no-deps api python3 manage.py makemigrations ${args}

#---------#
# Cleanup #
#---------#
prune:
	@echo "🥫 Pruning unused Docker artifacts (save space) …"
	docker system prune -af

prune_cache:
	@echo "🥫 Pruning Docker builder cache …"
	docker builder prune -f
