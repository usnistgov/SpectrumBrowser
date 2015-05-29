# Makefile for SpectrumBrowser

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/flask

MSOD_SRC_DIR=${REPO_HOME}
MSOD_CONF_FILE=MSODConfig.json
MSOD_DEST_DIR=$(DESTDIR)/etc/msod

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
	@for f in ${NGINX_CONF_FILES}; do \
		if [ ! -f ${NGINX_SRC_DIR}/$$f ]; then \
			echo "Couldn't find ${NGINX_SRC_DIR}/$$f" >&2; \
			exit 1; \
		fi; \
		echo "install -D -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f"; \
		install -D -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f; \
	done

	install -m 644 ${GUNICORN_SRC_DIR}/gunicorn.conf /etc/gunicorn.conf
	install -m 644 ${GUNICORN_SRC_DIR}/gunicorn-defaults $(DESTDIR)/etc/default/gunicorn
	install -m 755 ${GUNICORN_SRC_DIR}/gunicorn-init $(DESTDIR)/etc/init.d/gunicorn

	install -m 755 ${GUNICORN_SRC_DIR}/streaming-bin $(DESTDIR)/usr/bin/streaming
	install -m 755 ${GUNICORN_SRC_DIR}/streaming-init $(DESTDIR)/etc/init.d/streaming

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
	@for f in ${NGINX_CONF_FILES}; do \
		echo "rm -f ${NGINX_DEST_DIR}/$$f"; \
		rm -f ${NGINX_DEST_DIR}/$$f; \
	done

	rm -f $(DESTDIR)/etc/gunicorn.conf
	rm -f $(DESTDIR)/etc/init.d/gunicorn
	rm -f $(DESTDIR)/etc/default/gunicorn

	rm -f $(DESTDIR)/usr/bin/streaming
	rm -f $(DESTDIR)/etc/init.d/streaming

	rm -f ${MSOD_DEST_DIR}/${MSOD_CONF_FILE}

#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi
