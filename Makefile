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
DOCKER_COMPOSE=docker-compose --env-file=${ENV_FILE}

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
	if [ -z `docker-compose ps -q $$service` ] || [ -z `docker ps -q --no-trunc | grep $$(${DOCKER_COMPOSE} ps -q $$service)` ]; then \
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
	docker-compose build


up:
ifdef service
	${DOCKER_COMPOSE} up -d ${service} 2>&1
else
	${DOCKER_COMPOSE} up -d 2>&1
endif


down:
	@echo "🥫 Bringing down containers …"
	${DOCKER_COMPOSE} down
