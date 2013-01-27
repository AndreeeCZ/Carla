#!/usr/bin/make -f
# Makefile for Carla #
# ---------------------- #
# Created by falkTX
#

PREFIX  = /usr/local
DESTDIR =

SED_PREFIX = $(shell echo $(PREFIX) | sed "s/\//\\\\\\\\\//g")

LINK  = ln -s
PYUIC = pyuic4
PYRCC = pyrcc4 -py3


all: CPP RES UI WIDGETS


# ------------------------------------------------------------------------------------------------------------------------------------------------------

CPP: discovery

discovery:
	$(MAKE) -C source/discovery

# ------------------------------------------------------------------------------------------------------------------------------------------------------

RES = source/resources_rc.py

RES: $(RES)

source/resources_rc.py: resources/resources.qrc
	$(PYRCC) $< -o $@

# ------------------------------------------------------------------------------------------------------------------------------------------------------

UIs = source/ui_carla.py source/ui_carla_control.py\
	source/ui_carla_about.py source/ui_carla_database.py source/ui_carla_edit.py source/ui_carla_parameter.py source/ui_carla_plugin.py source/ui_carla_refresh.py \
	source/ui_inputdialog_value.py

UI: $(UIs)

source/ui_%.py: resources/ui/%.ui
	$(PYUIC) $< -o $@

# ------------------------------------------------------------------------------------------------------------------------------------------------------

WIDGETS = source/digitalpeakmeter.py source/ledbutton.py source/paramspinbox.py source/pixmapdial.py source/pixmapkeyboard.py

WIDGETS: $(WIDGETS)

source/%.py: source/widgets/%.py
	$(LINK) widgets/$*.py $@

# ------------------------------------------------------------------------------------------------------------------------------------------------------

debug:
	$(MAKE) DEBUG=true

# doxygen:
# 	$(MAKE) doxygen -C source/backend

# ------------------------------------------------------------------------------------------------------------------------------------------------------

posix32:
	$(MAKE) -C source/bridge posix32
	$(MAKE) -C source/discovery posix32

posix64:
	$(MAKE) -C source/bridge posix64
	$(MAKE) -C source/discovery posix64

win32:
	$(MAKE) -C source/bridge win32
	$(MAKE) -C source/discovery win32

win64:
	$(MAKE) -C source/bridge win64
	$(MAKE) -C source/discovery win64

wine32:
	$(MAKE) -C source/jackbridge wine32
	$(LINK) source/libs/jackbridge/libcarla-jackbridge-win32.dll.so source/bridge/libcarla-jackbridge-win32.dll

wine64:
	$(MAKE) -C source/jackbridge wine64
	$(LINK) source/libs/jackbridge/libcarla-jackbridge-win64.dll.so source/bridge/libcarla-jackbridge-win64.dll

# ------------------------------------------------------------------------------------------------------------------------------------------------------

clean:
	$(MAKE) clean -C source/discovery
	rm -f $(RES)
	rm -f $(UIs)
	rm -f $(WIDGETS)
	rm -f *~ source/*~ source/*.pyc
# 	rm -rf source/*/doxygen

install:
	# Create directories
	install -d $(DESTDIR)$(PREFIX)/bin/
	install -d $(DESTDIR)$(PREFIX)/lib/carla/
	install -d $(DESTDIR)$(PREFIX)/share/applications/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
	install -d $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
	install -d $(DESTDIR)$(PREFIX)/share/carla/

	# Install script files and binaries
	install -m 755 \
		data/carla \
		data/carla-control \
		data/carla-standalone \
		$(DESTDIR)$(PREFIX)/bin/

	# Install desktop files
	install -m 644 data/*.desktop $(DESTDIR)$(PREFIX)/share/applications/

	# Install icons, 16x16
	install -m 644 resources/16x16/carla.png               $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/
	install -m 644 resources/16x16/carla-control.png       $(DESTDIR)$(PREFIX)/share/icons/hicolor/16x16/apps/

	# Install icons, 48x48
	install -m 644 resources/48x48/carla.png               $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/
	install -m 644 resources/48x48/carla-control.png       $(DESTDIR)$(PREFIX)/share/icons/hicolor/48x48/apps/

	# Install icons, 128x128
	install -m 644 resources/128x128/carla.png             $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/
	install -m 644 resources/128x128/carla-control.png     $(DESTDIR)$(PREFIX)/share/icons/hicolor/128x128/apps/

	# Install icons, 256x256
	install -m 644 resources/256x256/carla.png             $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/
	install -m 644 resources/256x256/carla-control.png     $(DESTDIR)$(PREFIX)/share/icons/hicolor/256x256/apps/

	# Install icons, scalable
	install -m 644 resources/scalable/carla.svg            $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/
	install -m 644 resources/scalable/carla-control.svg    $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/

	# Install main code
	install -m 755 source/*.py $(DESTDIR)$(PREFIX)/share/carla/

	install -m 755 \
		source/backend/*.so \
		source/bridge/carla-bridge-* \
		source/discovery/carla-discovery-* \
		$(DESTDIR)$(PREFIX)/lib/cadence/

	# Adjust PREFIX value in script files
	sed -i "s/X-PREFIX-X/$(SED_PREFIX)/" \
		$(DESTDIR)$(PREFIX)/bin/carla \
		$(DESTDIR)$(PREFIX)/bin/carla-control \
		$(DESTDIR)$(PREFIX)/bin/carla-standalone \

uninstall:
	rm -f $(DESTDIR)$(PREFIX)/bin/carla*
	rm -f $(DESTDIR)$(PREFIX)/share/applications/carla.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/applications/carla-control.desktop
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/carla.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/*/apps/carla-control.png
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/carla.svg
	rm -f $(DESTDIR)$(PREFIX)/share/icons/hicolor/scalable/apps/carla-control.svg
	rm -rf $(DESTDIR)$(PREFIX)/lib/carla/
	rm -rf $(DESTDIR)$(PREFIX)/share/carla/