# Makefile for SpectrumBrowser

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/flask
GUNICORN_CONF_FILE=gunicorn.conf
GUNICORN_PID_FILE=$(shell python -c "execfile(\"${GUNICORN_SRC_DIR}/${GUNICORN_CONF_FILE}\"); print pidfile")

MSOD_SRC_DIR=${REPO_HOME}
MSOD_CONF_FILE=MSODConfig.json
MSOD_DEST_DIR=$(DESTDIR)/etc/msod

LOG_DIRS=$(DESTDIR)/var/log/flask

.test-envvars:
	@echo "Testing environment variables"
	@echo "GWT_HOME='${GWT_HOME}'"
	@if [ -z ${GWT_HOME} ]; then \
		echo "Set environment variable GWT_HOME to location of gwt" >&2; \
		exit 1; \
	fi

all: .test-envvars
	ant

demo: .test-envvars
	ant demo

clean:
	ant clean

install:
	@for d in ${LOG_DIRS}; do \
		echo "mkdir -p $$d"; \
		mkdir -p $$d; \
	done

	@for f in ${NGINX_CONF_FILES}; do \
		if [ ! -f ${NGINX_SRC_DIR}/$$f ]; then \
			echo "Couldn't find ${NGINX_SRC_DIR}/$$f" >&2; \
			exit 1; \
		fi; \
		echo "install -D -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f"; \
		install -D -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f; \
	done

	@f=${MSOD_CONF_FILE}; \
	if [ ! -f ${MSOD_SRC_DIR}/$$f ]; then \
		echo "Couldn't find ${MSOD_SRC_DIR}/$$f" >&2; \
		exit 1; \
	fi; \
	echo "install -D -m 644 ${MSOD_SRC_DIR}/$$f ${MSOD_DEST_DIR}/$$f"; \
	install -D -m 644 ${MSOD_SRC_DIR}/$$f ${MSOD_DEST_DIR}/$$f

	@f=${MSOD_CONF_FILE}; \
	echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in ${MSOD_DEST_DIR}/$$f"; \
	sed -i -r 's:(^.*"SPECTRUM_BROWSER_HOME")[^,]*:\1\: "'${REPO_HOME}'":' ${MSOD_DEST_DIR}/$$f

#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi

uninstall:
	@echo "Removing empty log directories: "
	@echo ">>>>>"
	@for d in ${LOG_DIRS}; do \
		find $$d -empty -type d -delete -print; \
	done
	@echo "<<<<<"

	@echo "The following log directories are not empty, not removing: "
	@echo ">>>>>"
	@for d in ${LOG_DIRS}; do \
		find $$d ! -empty -type d -print; \
	done
	@echo "<<<<<"

	@for f in ${NGINX_CONF_FILES}; do \
		echo "rm -f ${NGINX_DEST_DIR}/$$f"; \
		rm -f ${NGINX_DEST_DIR}/$$f; \
	done

	@f=${MSOD_CONF_FILE}; \
	echo "rm -f ${MSOD_DEST_DIR}/$$f"; \
	rm -f ${MSOD_DEST_DIR}/$$f; \

#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi

start-workers:
	@if ps p $(shell cat ${GUNICORN_PID_FILE}) 1>/dev/null; then \
		echo "gunicorn already running"; \
	else \
		echo "Starting gunicorn..."; \
		gunicorn -c ${GUNICORN_SRC_DIR}/${GUNICORN_CONF_FILE} flaskr:app; \
		echo "$(shell cat ${GUNICORN_PID_FILE}) >> ${GUNICORN_PID_FILE}"; \
	fi

stop-workers:
	@if [ -f ${GUNICORN_PID_FILE} ] && ps p $(shell cat ${GUNICORN_PID_FILE}) 1>/dev/null; then \
		kill -9 $(shell cat ${GUNICORN_PID_FILE}); \
	fi

status:
	@echo -n "gunicorn: "
	@if [ ! -f ${GUNICORN_PID_FILE} ] || ! ps p $(shell cat ${GUNICORN_PID_FILE}) 1>/dev/null; then \
		echo -n "not "; \
	fi
	@echo "running"
