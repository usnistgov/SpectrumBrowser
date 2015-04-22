# Makefile for SpectrumBrowser

# NOTE: use sudo -E make install

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST=$(DESTDIR)/etc/nginx

CONF_SRC_GUNICORN=${REPO_HOME}/flask/gunicorn.conf
CONF_DEST_GUNICORN=$(DESTDIR)/etc/gunicorn.d/gunicorn.conf

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

update:
	git pull

install:
	@if [ -f /etc/debian_version ]; then \
		for f in ${NGINX_CONF_FILES}; do \
			if [ ! -f ${NGINX_SRC}/$$f ]; then \
			 	echo "Couldn't find ${NGINX_SRC}/$$f" >&2; \
			 	exit 1; \
			fi; \
			echo "Installing ${NGINX_DEST}/$$f ... "; \
			install -m 644 ${NGINX_SRC}/$$f ${NGINX_DEST}/$$f; \
		done; \
		if [ ! -f ${CONF_SRC_GUNICORN} ]; then \
			echo "Couldn't find ${CONF_SRC_GUNICORN}" >&2; \
			exit 1; \
		fi; \
		echo "Installing ${CONF_DEST_GUNICORN} ... "; \
		install -m 644 ${CONF_SRC_GUNICORN} ${CONF_DEST_GUNICORN}; \
	fi

	@if [ -f /etc/redhat-release ]; then \
		echo "Redhat support not yet implemented"; \
	fi

	@echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in ${CONF_DEST_GUNICORN}"
	@sed -i -r 's:(^SPECTRUM_BROWSER_HOME).*$$:\1 = "'${REPO_HOME}'":' ${CONF_DEST_GUNICORN}

uninstall:
	@if [ -f /etc/debian_version ]; then \
		for f in ${NGINX_CONF_FILES}; do \
			echo "rm -f ${NGINX_DEST}/$$f ... "; \
			rm -f ${NGINX_DEST}/$$f; \
		done; \
		echo "rm -f ${CONF_DEST_GUNICORN} ..."; \
		rm -f ${CONF_DEST_GUNICORN}; \
	fi

	@if [ -f /etc/redhat-release ]; then \
		echo "Redhat support not yet implemented"; \
	fi
