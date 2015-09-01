# Makefile for SpectrumBrowser
# You can override REPO_HOME using make REPO_HOME=...

REPO_HOME:=$(shell git rev-parse --show-toplevel)

NGINX_SRC_DIR=${REPO_HOME}/nginx
NGINX_CONF_FILES=nginx.conf cacert.pem privkey.pem mime.types
NGINX_DEST_DIR=$(DESTDIR)/etc/nginx

GUNICORN_SRC_DIR=${REPO_HOME}/services/spectrumbrowser

SERVICES_SRC_DIR=${REPO_HOME}/services

MSOD_SRC_DIR=${REPO_HOME}

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

	mkdir -p /var/log/flask
	chown spectrumbrowser /var/log/flask
	install -m 644 ${GUNICORN_SRC_DIR}/gunicorn.conf /etc/gunicorn.conf
	install -m 644 ${SERVICES_SRC_DIR}/spectrumbrowser/spectrumbrowser-defaults $(DESTDIR)/etc/default/spectrumbrowser
	install -m 755 ${SERVICES_SRC_DIR}/spectrumbrowser/spectrumbrowser-init $(DESTDIR)/etc/init.d/spectrumbrowser

	install -m 755 ${SERVICES_SRC_DIR}/streaming/StreamingServer.py $(DESTDIR)/usr/bin/streaming
	install -m 755 ${SERVICES_SRC_DIR}/streaming/streaming-init $(DESTDIR)/etc/init.d/streaming

	install -m 755 ${SERVICES_SRC_DIR}/occupancy/OccupancyAlert.py $(DESTDIR)/usr/bin/occupancy
	install -m 755 ${SERVICES_SRC_DIR}/occupancy/occupancy-init $(DESTDIR)/etc/init.d/occupancy

	install -m 755 ${SERVICES_SRC_DIR}/webmonitor/ResourceStreamingServer.py $(DESTDIR)/usr/bin/monitoring
	install -m 755 ${SERVICES_SRC_DIR}/webmonitor/monitoring-init $(DESTDIR)/etc/init.d/monitoring

	install -m 755 ${SERVICES_SRC_DIR}/admin/Admin.py $(DESTDIR)/usr/bin/admin
	install -m 755 ${SERVICES_SRC_DIR}/admin/admin-init $(DESTDIR)/etc/init.d/admin

	install -m 755 ${SERVICES_SRC_DIR}/federation/federation-bin $(DESTDIR)/usr/bin/federation
	install -m 755 ${SERVICES_SRC_DIR}/federation/federation-init $(DESTDIR)/etc/init.d/federation

	install -m 755 ${SERVICES_SRC_DIR}/spectrumdb/spectrumdb-bin $(DESTDIR)/usr/bin/spectrumdb
	install -m 755 ${SERVICES_SRC_DIR}/spectrumdb/spectrumdb-init $(DESTDIR)/etc/init.d/spectrumdb

	install -D -m 644 ${MSOD_SRC_DIR}/MSODConfig.json $(DESTDIR)/etc/msod/MSODConfig.json
	install -m 755 ${SERVICES_SRC_DIR}/msod-init $(DESTDIR)/etc/init.d/msod

	@d=$(DESTDIR)/etc/msod; \
	f=MSODConfig.json; \
	echo "Hardcoding SPECTRUM_BROWSER_HOME as ${REPO_HOME} in $$d/$$f"; \
	sed -i -r 's:(^.*"SPECTRUM_BROWSER_HOME")[^,]*:\1\: "'${REPO_HOME}'":' $$d/$$f

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
	rm -f $(DESTDIR)/etc/init.d/spectrumbrowser
	rm -f $(DESTDIR)/etc/default/spectrumbrowser

	rm -f $(DESTDIR)/usr/bin/streaming
	rm -f $(DESTDIR)/etc/init.d/streaming

	rm -f $(DESTDIR)/usr/bin/occupancy
	rm -f $(DESTDIR)/etc/init.d/occupancy

	rm -f $(DESTDIR)/usr/bin/monitoring
	rm -f $(DESTDIR)/etc/init.d/monitoring

	rm -f $(DESTDIR)/usr/bin/federation
	rm -f $(DESTDIR)/etc/init.d/federation

	rm -f $(DESTDIR)/usr/bin/spectrumdb
	rm -f $(DESTDIR)/etc/init.d/spectrumdb

	rm -f $(DESTDIR)/usr/bin/admin
	rm -f $(DESTDIR)/etc/init.d/admin

	rm -f $(DESTDIR)/usr/bin/spectrumdb
	rm -f $(DESTDIR)/etc/init.d/spectrumdb

	rm -f $(DESTDIR)/etc/msod/MSODConfig.json
	rm -f $(DESTDIR)/etc/init.d/msod

#       We can use this block to do any distro-specific stuff
# 	@if [ -f /etc/debian_version ]; then \
# 		echo "Detected Debian-based distribution"
# 	fi
# 
# 	@if [ -f /etc/redhat-release ]; then \
# 		echo "Detected Redhat-based distribution"
# 	fi
