# Makefile for SpectrumBrowser

# NOTE: use sudo -E make install

REPO_HOME:=$(shell git rev-parse --show-toplevel)
SB=${SPECTRUM_BROWSER_HOME}
GWT=${GWT_HOME}

CONF_SRC_NGINX=${SB}/nginx/nginx.conf
CONF_DEST_NGINX=$(DESTDIR)/etc/nginx/conf.d/nginx.conf

CONF_SRC_GUNICORN=${SB}/flask/gunicorn.conf
CONF_DEST_GUNICORN=$(DESTDIR)/etc/gunicorn.d/gunicorn.conf

.test-envvars:
	@echo "Testing environment variable"
	@if [ -z ${SB} ] || [ ${SB} != ${REPO_HOME} ]; then \
		echo "Set environment variable SPECTRUM_BROWSER_HOME to ${REPO_HOME}" >&2; \
		exit 1; \
	fi

	@if [ -z ${GWT} ]; then \
		echo "Set environment variable GWT_HOME to location of gwt" >&2; \
		exit 1; \
	fi

all: .test-envvars
	ant

demo: .test-envvars
	ant demo

clean:
	ant clean

install: .test-envvars
	@if [ -f /etc/debian_version ]; then \
		if [ ! -f ${CONF_SRC_NGINX} ]; then \
			echo "Couldn't find ${CONF_SRC_NGINX}" >&2; \
			exit 1; \
		fi; \
		echo "Installing ${CONF_DEST_NGINX} ... "; \
		install -m 644 ${CONF_SRC_NGINX} ${CONF_DEST_NGINX}; \
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

uninstall:
	@if [ -f /etc/debian_version ]; then \
		echo "rm -f ${CONF_DEST_NGINX} ..."; \
		rm -f ${CONF_DEST_NGINX}; \
		echo "rm -f ${CONF_DEST_GUNICORN} ..."; \
		rm -f ${CONF_DEST_GUNICORN}; \
	fi

	@if [ -f /etc/redhat-release ]; then \
		echo "Redhat support not yet implemented"; \
	fi
