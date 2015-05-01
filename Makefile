# Makefile for SpectrumBrowser

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/flask
GUNICORN_CONF_FILE=gunicorn.conf
GUNICORN_DEST_DIR=$(DESTDIR)/etc/gunicorn.d

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
	@if [ -f /etc/debian_version ]; then \
		for f in ${NGINX_CONF_FILES}; do \
			if [ ! -f ${NGINX_SRC_DIR}/$$f ]; then \
			 	echo "Couldn't find ${NGINX_SRC_DIR}/$$f" >&2; \
			 	exit 1; \
			fi; \
			echo "Installing ${NGINX_DEST_DIR}/$$f ... "; \
			install -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f; \
		done; \
		f=${GUNICORN_CONF_FILE}; \
		if [ ! -f ${GUNICORN_SRC_DIR}/$$f ]; then \
			echo "Couldn't find ${GUNICORN_SRC_DIR}/$$f" >&2; \
			exit 1; \
		fi; \
		echo "Installing ${GUNICORN_DEST_DIR}/$$f"; \
		install -m 644 ${GUNICORN_SRC_DIR}/$$f ${GUNICORN_DEST_DIR}/$$f; \
	fi

	@if [ -f /etc/redhat-release ]; then \
		echo "Redhat support not yet implemented"; \
	fi

	@f=${GUNICORN_CONF_FILE}; \
	echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in ${GUNICORN_DEST_DIR}/$$f"; \
	sed -i -r 's:(^SPECTRUM_BROWSER_HOME).*$$:\1 = "'${REPO_HOME}'":' ${GUNICORN_DEST_DIR}/$$f

uninstall:
	@if [ -f /etc/debian_version ]; then \
		for f in ${NGINX_CONF_FILES}; do \
			echo "rm -f ${NGINX_DEST_DIR}/$$f ... "; \
			rm -f ${NGINX_DEST_DIR}/$$f; \
		done; \
		f=${GUNICORN_CONF_FILE}; \
		echo "rm -f ${GUNICORN_DEST_DIR}/$$f ..."; \
		rm -f ${GUNICORN_DEST_DIR}/$$f; \
	fi

	@if [ -f /etc/redhat-release ]; then \
		echo "Redhat support not yet implemented"; \
	fi
