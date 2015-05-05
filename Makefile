# Makefile for SpectrumBrowser

REPO_HOME:=$(shell git rev-parse --show-toplevel)

<<<<<<< HEAD
NGINX_SRC=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST=$(DESTDIR)/etc/nginx

CONF_SRC_GUNICORN=${REPO_HOME}/flask/gunicorn.conf
CONF_DEST_GUNICORN=$(DESTDIR)/etc/gunicorn.d/gunicorn.conf
=======
NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/flask
GUNICORN_CONF_FILE=gunicorn.conf
GUNICORN_DEST_DIR=$(DESTDIR)/etc/gunicorn.d
>>>>>>> b83ae564cb671b1355359a6c9f4b8edea06fa9af

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

<<<<<<< HEAD
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
=======
install:
	@for f in ${NGINX_CONF_FILES}; do \
		if [ ! -f ${NGINX_SRC_DIR}/$$f ]; then \
			echo "Couldn't find ${NGINX_SRC_DIR}/$$f" >&2; \
			exit 1; \
		fi; \
		echo "install -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f"; \
		install -m 644 ${NGINX_SRC_DIR}/$$f ${NGINX_DEST_DIR}/$$f; \
	done

	@f=${GUNICORN_CONF_FILE}; \
	if [ ! -f ${GUNICORN_SRC_DIR}/$$f ]; then \
		echo "Couldn't find ${GUNICORN_SRC_DIR}/$$f" >&2; \
		exit 1; \
	fi; \
	echo "install -m 644 ${GUNICORN_SRC_DIR}/$$f ${GUNICORN_DEST_DIR}/$$f"; \
	install -m 644 ${GUNICORN_SRC_DIR}/$$f ${GUNICORN_DEST_DIR}/$$f

	@f=${GUNICORN_CONF_FILE}; \
	echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in ${GUNICORN_DEST_DIR}/$$f"; \
	sed -i -r 's:(^SPECTRUM_BROWSER_HOME).*$$:\1 = "'${REPO_HOME}'":' ${GUNICORN_DEST_DIR}/$$f
>>>>>>> b83ae564cb671b1355359a6c9f4b8edea06fa9af


#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi

	@echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in ${CONF_DEST_GUNICORN}"
	@sed -i -r 's:(^SPECTRUM_BROWSER_HOME).*$$:\1 = "'${REPO_HOME}'":' ${CONF_DEST_GUNICORN}

uninstall:
<<<<<<< HEAD
	@if [ -f /etc/debian_version ]; then \
		for f in ${NGINX_CONF_FILES}; do \
			echo "rm -f ${NGINX_DEST}/$$f ... "; \
			rm -f ${NGINX_DEST}/$$f; \
		done; \
		echo "rm -f ${CONF_DEST_GUNICORN} ..."; \
		rm -f ${CONF_DEST_GUNICORN}; \
	fi
=======
	@for f in ${NGINX_CONF_FILES}; do \
		echo "rm -f ${NGINX_DEST_DIR}/$$f"; \
		rm -f ${NGINX_DEST_DIR}/$$f; \
	done

	@f=${GUNICORN_CONF_FILE}; \
	echo "rm -f ${GUNICORN_DEST_DIR}/$$f"; \
	rm -f ${GUNICORN_DEST_DIR}/$$f; \
>>>>>>> b83ae564cb671b1355359a6c9f4b8edea06fa9af

#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi
