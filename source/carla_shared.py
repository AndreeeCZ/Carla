#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Common Carla code
# Copyright (C) 2011-2013 Filipe Coelho <falktx@falktx.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For a full copy of the GNU General Public License see the COPYING file

# ------------------------------------------------------------------------------------------------------------
# Imports (Global)

import os
import platform
import sys
from codecs import open as codecopen
from copy import deepcopy
#from decimal import Decimal
from PyQt4.QtCore import pyqtSlot, qWarning, SIGNAL, SLOT
#pyqtSlot, qFatal, Qt, QSettings, QTimer
from PyQt4.QtGui import QDialog, QWidget
#from PyQt4.QtGui import QColor, QCursor, QFontMetrics, QFrame, QGraphicsScene, QInputDialog, QLinearGradient, QMenu, QPainter, QPainterPath, QVBoxLayout
#from PyQt4.QtXml import QDomDocument

# ------------------------------------------------------------------------------------------------------------
# Imports (Custom)

import ui_carla_about
#import ui_carla_edit
import ui_carla_parameter
#import ui_carla_plugin

# ------------------------------------------------------------------------------------------------------------
# Try Import Signal

try:
    from signal import signal, SIGINT, SIGTERM, SIGUSR1, SIGUSR2
    haveSignal = True
except:
    haveSignal = False

# ------------------------------------------------------------------------------------------------------------
# Set Platform

if sys.platform == "darwin":
    from PyQt4.QtGui import qt_mac_set_menubar_icons
    qt_mac_set_menubar_icons(False)
    HAIKU   = False
    LINUX   = False
    MACOS   = True
    WINDOWS = False
elif "haiku" in sys.platform:
    HAIKU   = True
    LINUX   = False
    MACOS   = False
    WINDOWS = False
elif "linux" in sys.platform:
    HAIKU   = False
    LINUX   = True
    MACOS   = False
    WINDOWS = False
elif sys.platform in ("win32", "win64", "cygwin"):
    WINDIR  = os.getenv("WINDIR")
    HAIKU   = False
    LINUX   = False
    MACOS   = False
    WINDOWS = True
else:
    HAIKU   = False
    LINUX   = False
    MACOS   = False
    WINDOWS = False

# ------------------------------------------------------------------------------------------------------------
# Set Version

VERSION = "0.5.0"

# ------------------------------------------------------------------------------------------------------------
# Set TMP

TMP = os.getenv("TMP")

if TMP is None:
    if WINDOWS:
        qWarning("TMP variable not set")
        TMP = os.path.join(WINDIR, "temp")
    else:
        TMP = "/tmp"

# ------------------------------------------------------------------------------------------------------------
# Set HOME

HOME = os.getenv("HOME")

if HOME is None:
    HOME = os.path.expanduser("~")

    if LINUX or MACOS:
        qWarning("HOME variable not set")

if not os.path.exists(HOME):
    qWarning("HOME does not exist")
    HOME = TMP

# ------------------------------------------------------------------------------------------------------------
# Set PATH

PATH = os.getenv("PATH")

if PATH is None:
    qWarning("PATH variable not set")

    if MACOS:
        PATH = ("/opt/local/bin", "/usr/local/bin", "/usr/bin", "/bin")
    elif WINDOWS:
        PATH = (os.path.join(WINDIR, "system32"), WINDIR)
    else:
        PATH = ("/usr/local/bin", "/usr/bin", "/bin")

else:
    PATH = PATH.split(os.pathsep)

# ------------------------------------------------------------------------------------------------------------
# 64bit check

kIs64bit = bool(platform.architecture()[0] == "64bit" and sys.maxsize > 2**32)

# ------------------------------------------------------------------------------------------------------------
# Convert a ctypes c_char_p into a python string

def cString(value):
    if not value:
        return ""
    if isinstance(value, str):
        return value
    return value.decode("utf-8", errors="ignore")

# ------------------------------------------------------------------------------------------------------------
# Check if a value is a number (float support)

def isNumber(value):
    try:
        float(value)
        return True
    except:
        return False

# ------------------------------------------------------------------------------------------------------------
# Unicode open

def uopen(filename, mode="r"):
    return codecopen(filename, encoding="utf-8", mode=mode)

# ------------------------------------------------------------------------------------------------
# Backend defines

MAX_DEFAULT_PLUGINS    = 99
MAX_RACK_PLUGINS       = 16
MAX_PATCHBAY_PLUGINS   = 999
MAX_DEFAULT_PARAMETERS = 200

# Plugin Hints
PLUGIN_IS_BRIDGE          = 0x001
PLUGIN_IS_RTSAFE          = 0x002
PLUGIN_IS_SYNTH           = 0x004
PLUGIN_HAS_GUI            = 0x010
PLUGIN_USES_CHUNKS        = 0x020
PLUGIN_USES_SINGLE_THREAD = 0x040
PLUGIN_CAN_DRYWET         = 0x100
PLUGIN_CAN_VOLUME         = 0x200
PLUGIN_CAN_BALANCE        = 0x400
PLUGIN_CAN_FORCE_STEREO   = 0x800

# Parameter Hints
PARAMETER_IS_BOOLEAN       = 0x01
PARAMETER_IS_INTEGER       = 0x02
PARAMETER_IS_LOGARITHMIC   = 0x04
PARAMETER_IS_ENABLED       = 0x08
PARAMETER_IS_AUTOMABLE     = 0x10
PARAMETER_USES_SAMPLERATE  = 0x20
PARAMETER_USES_SCALEPOINTS = 0x40
PARAMETER_USES_CUSTOM_TEXT = 0x80

# FIXME
# Custom Data types
CUSTOM_DATA_INVALID = None
CUSTOM_DATA_CHUNK   = "http://kxstudio.sf.net/ns/carla/chunk"
CUSTOM_DATA_STRING  = "http://kxstudio.sf.net/ns/carla/string"

# Binary Type
BINARY_NONE    = 0
BINARY_POSIX32 = 1
BINARY_POSIX64 = 2
BINARY_WIN32   = 3
BINARY_WIN64   = 4
BINARY_OTHER   = 5

# Plugin Type
PLUGIN_NONE     = 0
PLUGIN_INTERNAL = 1
PLUGIN_LADSPA   = 2
PLUGIN_DSSI     = 3
PLUGIN_LV2      = 4
PLUGIN_VST      = 5
PLUGIN_GIG      = 6
PLUGIN_SF2      = 7
PLUGIN_SFZ      = 8

# Plugin Category
PLUGIN_CATEGORY_NONE      = 0
PLUGIN_CATEGORY_SYNTH     = 1
PLUGIN_CATEGORY_DELAY     = 2 # also Reverb
PLUGIN_CATEGORY_EQ        = 3
PLUGIN_CATEGORY_FILTER    = 4
PLUGIN_CATEGORY_DYNAMICS  = 5 # Amplifier, Compressor, Gate
PLUGIN_CATEGORY_MODULATOR = 6 # Chorus, Flanger, Phaser
PLUGIN_CATEGORY_UTILITY   = 7 # Analyzer, Converter, Mixer
PLUGIN_CATEGORY_OTHER     = 8 # used to check if a plugin has a category

# Parameter Type
PARAMETER_UNKNOWN       = 0
PARAMETER_INPUT         = 1
PARAMETER_OUTPUT        = 2
PARAMETER_LATENCY       = 3
PARAMETER_SAMPLE_RATE   = 4
PARAMETER_LV2_FREEWHEEL = 5
PARAMETER_LV2_TIME      = 6

# Internal Parameters Index
PARAMETER_NULL          = -1
PARAMETER_ACTIVE        = -2
PARAMETER_DRYWET        = -3
PARAMETER_VOLUME        = -4
PARAMETER_BALANCE_LEFT  = -5
PARAMETER_BALANCE_RIGHT = -6
PARAMETER_PANNING       = -7

# Options Type
OPTION_PROCESS_NAME            = 0
OPTION_PROCESS_MODE            = 1
OPTION_PROCESS_HIGH_PRECISION  = 2
OPTION_FORCE_STEREO            = 3
OPTION_PREFER_PLUGIN_BRIDGES   = 4
OPTION_PREFER_UI_BRIDGES       = 5
OPTION_USE_DSSI_VST_CHUNKS     = 6
OPTION_MAX_PARAMETERS          = 7
OPTION_OSC_UI_TIMEOUT          = 8
OPTION_PREFERRED_BUFFER_SIZE   = 9
OPTION_PREFERRED_SAMPLE_RATE   = 10
OPTION_PATH_BRIDGE_NATIVE      = 11
OPTION_PATH_BRIDGE_POSIX32     = 12
OPTION_PATH_BRIDGE_POSIX64     = 13
OPTION_PATH_BRIDGE_WIN32       = 14
OPTION_PATH_BRIDGE_WIN64       = 15
OPTION_PATH_BRIDGE_LV2_GTK2    = 16
OPTION_PATH_BRIDGE_LV2_GTK3    = 17
OPTION_PATH_BRIDGE_LV2_QT4     = 18
OPTION_PATH_BRIDGE_LV2_QT5     = 19
OPTION_PATH_BRIDGE_LV2_COCOA   = 20
OPTION_PATH_BRIDGE_LV2_WINDOWS = 21
OPTION_PATH_BRIDGE_LV2_X11     = 22
OPTION_PATH_BRIDGE_VST_COCOA   = 23
OPTION_PATH_BRIDGE_VST_HWND    = 24
OPTION_PATH_BRIDGE_VST_X11     = 25

# Callback Type
CALLBACK_DEBUG                          = 0
CALLBACK_PARAMETER_VALUE_CHANGED        = 1
CALLBACK_PARAMETER_MIDI_CHANNEL_CHANGED = 2
CALLBACK_PARAMETER_MIDI_CC_CHANGED = 3
CALLBACK_PROGRAM_CHANGED      = 4
CALLBACK_MIDI_PROGRAM_CHANGED = 5
CALLBACK_NOTE_ON              = 6
CALLBACK_NOTE_OFF             = 7
CALLBACK_SHOW_GUI             = 8
CALLBACK_UPDATE               = 9
CALLBACK_RELOAD_INFO          = 10
CALLBACK_RELOAD_PARAMETERS    = 11
CALLBACK_RELOAD_PROGRAMS      = 12
CALLBACK_RELOAD_ALL           = 13
CALLBACK_NSM_ANNOUNCE         = 14
CALLBACK_NSM_OPEN1            = 15
CALLBACK_NSM_OPEN2            = 16
CALLBACK_NSM_SAVE             = 17
CALLBACK_ERROR                = 18
CALLBACK_QUIT                 = 19

# Process Mode Type
PROCESS_MODE_SINGLE_CLIENT    = 0
PROCESS_MODE_MULTIPLE_CLIENTS = 1
PROCESS_MODE_CONTINUOUS_RACK  = 2
PROCESS_MODE_PATCHBAY         = 3

# Set BINARY_NATIVE
if HAIKU or LINUX or MACOS:
    BINARY_NATIVE = BINARY_POSIX64 if kIs64bit else BINARY_POSIX32
elif WINDOWS:
    BINARY_NATIVE = BINARY_WIN64 if kIs64bit else BINARY_WIN32
else:
    BINARY_NATIVE = BINARY_OTHER

# ------------------------------------------------------------------------------------------------------------
# Carla Host object

class CarlaHostObject(object):
    __slots__ = [
        'host',
        'gui',
        'isControl',
        'processMode',
        'maxParameters'
    ]

Carla = CarlaHostObject()
Carla.host = None
Carla.gui  = None
Carla.isControl = False
Carla.processMode   = PROCESS_MODE_CONTINUOUS_RACK
Carla.maxParameters = MAX_RACK_PLUGINS

# ------------------------------------------------------------------------------------------------------------
# Carla GUI stuff

ICON_STATE_NULL = 0
ICON_STATE_WAIT = 1
ICON_STATE_OFF  = 2
ICON_STATE_ON   = 3

PALETTE_COLOR_NONE   = 0
PALETTE_COLOR_WHITE  = 1
PALETTE_COLOR_RED    = 2
PALETTE_COLOR_GREEN  = 3
PALETTE_COLOR_BLUE   = 4
PALETTE_COLOR_YELLOW = 5
PALETTE_COLOR_ORANGE = 6
PALETTE_COLOR_BROWN  = 7
PALETTE_COLOR_PINK   = 8

CarlaStateParameter = {
    'index': 0,
    'name': "",
    'symbol': "",
    'value': 0.0,
    'midiChannel': 1,
    'midiCC': -1
}

CarlaStateCustomData = {
    'type': CUSTOM_DATA_INVALID,
    'key': "",
    'value': ""
}

CarlaSaveState = {
    'type': "",
    'name': "",
    'label': "",
    'binary': "",
    'uniqueId': 0,
    'active': False,
    'dryWet': 1.0,
    'volume': 1.0,
    'balanceLeft': -1.0,
    'balanceRight': 1.0,
    'pannning': 0.0,
    'parameterList': [],
    'currentProgramIndex': -1,
    'currentProgramName': "",
    'currentMidiBank': -1,
    'currentMidiProgram': -1,
    'customDataList': [],
    'chunk': None
}

# ------------------------------------------------------------------------------------------------------------
# Static MIDI CC list

MIDI_CC_LIST = (
    #"0x00 Bank Select",
    "0x01 Modulation",
    "0x02 Breath",
    "0x03 (Undefined)",
    "0x04 Foot",
    "0x05 Portamento",
    #"0x06 (Data Entry MSB)",
    "0x07 Volume",
    "0x08 Balance",
    "0x09 (Undefined)",
    "0x0A Pan",
    "0x0B Expression",
    "0x0C FX Control 1",
    "0x0D FX Control 2",
    "0x0E (Undefined)",
    "0x0F (Undefined)",
    "0x10 General Purpose 1",
    "0x11 General Purpose 2",
    "0x12 General Purpose 3",
    "0x13 General Purpose 4",
    "0x14 (Undefined)",
    "0x15 (Undefined)",
    "0x16 (Undefined)",
    "0x17 (Undefined)",
    "0x18 (Undefined)",
    "0x19 (Undefined)",
    "0x1A (Undefined)",
    "0x1B (Undefined)",
    "0x1C (Undefined)",
    "0x1D (Undefined)",
    "0x1E (Undefined)",
    "0x1F (Undefined)",
    #"0x20 *Bank Select",
    #"0x21 *Modulation",
    #"0x22 *Breath",
    #"0x23 *(Undefined)",
    #"0x24 *Foot",
    #"0x25 *Portamento",
    #"0x26 *(Data Entry MSB)",
    #"0x27 *Volume",
    #"0x28 *Balance",
    #"0x29 *(Undefined)",
    #"0x2A *Pan",
    #"0x2B *Expression",
    #"0x2C *FX *Control 1",
    #"0x2D *FX *Control 2",
    #"0x2E *(Undefined)",
    #"0x2F *(Undefined)",
    #"0x30 *General Purpose 1",
    #"0x31 *General Purpose 2",
    #"0x32 *General Purpose 3",
    #"0x33 *General Purpose 4",
    #"0x34 *(Undefined)",
    #"0x35 *(Undefined)",
    #"0x36 *(Undefined)",
    #"0x37 *(Undefined)",
    #"0x38 *(Undefined)",
    #"0x39 *(Undefined)",
    #"0x3A *(Undefined)",
    #"0x3B *(Undefined)",
    #"0x3C *(Undefined)",
    #"0x3D *(Undefined)",
    #"0x3E *(Undefined)",
    #"0x3F *(Undefined)",
    #"0x40 Damper On/Off", # <63 off, >64 on
    #"0x41 Portamento On/Off", # <63 off, >64 on
    #"0x42 Sostenuto On/Off", # <63 off, >64 on
    #"0x43 Soft Pedal On/Off", # <63 off, >64 on
    #"0x44 Legato Footswitch", # <63 Normal, >64 Legato
    #"0x45 Hold 2", # <63 off, >64 on
    "0x46 Control 1 [Variation]",
    "0x47 Control 2 [Timbre]",
    "0x48 Control 3 [Release]",
    "0x49 Control 4 [Attack]",
    "0x4A Control 5 [Brightness]",
    "0x4B Control 6 [Decay]",
    "0x4C Control 7 [Vib Rate]",
    "0x4D Control 8 [Vib Depth]",
    "0x4E Control 9 [Vib Delay]",
    "0x4F Control 10 [Undefined]",
    "0x50 General Purpose 5",
    "0x51 General Purpose 6",
    "0x52 General Purpose 7",
    "0x53 General Purpose 8",
    "0x54 Portamento Control",
    "0x5B FX 1 Depth [Reverb]",
    "0x5C FX 2 Depth [Tremolo]",
    "0x5D FX 3 Depth [Chorus]",
    "0x5E FX 4 Depth [Detune]",
    "0x5F FX 5 Depth [Phaser]"
  )

# ------------------------------------------------------------------------------------------------------------
# Carla XML helpers

def getSaveStateDictFromXML(xmlNode):
    saveState = deepcopy(CarlaSaveState)

    node = xmlNode.firstChild()

    while not node.isNull():
        # ------------------------------------------------------
        # Info

        if node.toElement().tagName() == "Info":
            xmlInfo = node.toElement().firstChild()

            while not xmlInfo.isNull():
                tag  = xmlInfo.toElement().tagName()
                text = xmlInfo.toElement().text().strip()

                if tag == "Type":
                    saveState["type"] = text
                elif tag == "Name":
                    saveState["name"] = xmlSafeString(text, False)
                elif tag in ("Label", "URI"):
                    saveState["label"] = xmlSafeString(text, False)
                elif tag == "Binary":
                    saveState["binary"] = xmlSafeString(text, False)
                elif tag == "UniqueID":
                    if text.isdigit(): saveState["uniqueId"] = int(text)

                xmlInfo = xmlInfo.nextSibling()

        # ------------------------------------------------------
        # Data

        elif node.toElement().tagName() == "Data":
            xmlData = node.toElement().firstChild()

            while not xmlData.isNull():
                tag  = xmlData.toElement().tagName()
                text = xmlData.toElement().text().strip()

                # ----------------------------------------------
                # Internal Data

                if tag == "Active":
                    saveState['active'] = bool(text == "Yes")
                elif tag == "DryWet":
                    if isNumber(text): saveState["dryWet"] = float(text)
                elif tag == "Volume":
                    if isNumber(text): saveState["volume"] = float(text)
                elif tag == "Balance-Left":
                    if isNumber(text): saveState["balanceLeft"] = float(text)
                elif tag == "Balance-Right":
                    if isNumber(text): saveState["balanceRight"] = float(text)
                elif tag == "Panning":
                    if isNumber(text): saveState["pannning"] = float(text)

                # ----------------------------------------------
                # Program (current)

                elif tag == "CurrentProgramIndex":
                    if text.isdigit(): saveState["currentProgramIndex"] = int(text)
                elif tag == "CurrentProgramName":
                    saveState["currentProgramName"] = xmlSafeString(text, False)

                # ----------------------------------------------
                # Midi Program (current)

                elif tag == "CurrentMidiBank":
                    if text.isdigit(): saveState["currentMidiBank"] = int(text)
                elif tag == "CurrentMidiProgram":
                    if text.isdigit(): saveState["currentMidiProgram"] = int(text)

                # ----------------------------------------------
                # Parameters

                elif tag == "Parameter":
                    stateParameter = deepcopy(CarlaStateParameter)

                    xmlSubData = xmlData.toElement().firstChild()

                    while not xmlSubData.isNull():
                        pTag  = xmlSubData.toElement().tagName()
                        pText = xmlSubData.toElement().text().strip()

                        if pTag == "Index":
                            if pText.isdigit(): stateParameter["index"] = int(pText)
                        elif pTag == "Name":
                            stateParameter["name"] = xmlSafeString(pText, False)
                        elif pTag == "Symbol":
                            stateParameter["symbol"] = xmlSafeString(pText, False)
                        elif pTag == "Value":
                            if isNumber(pText): stateParameter["value"] = float(pText)
                        elif pTag == "MidiChannel":
                            if pText.isdigit(): stateParameter["midiChannel"] = int(pText)
                        elif pTag == "MidiCC":
                            if pText.isdigit(): stateParameter["midiCC"] = int(pText)

                        xmlSubData = xmlSubData.nextSibling()

                    saveState["parameterList"].append(stateParameter)

                # ----------------------------------------------
                # Custom Data

                elif tag == "CustomData":
                    stateCustomData = deepcopy(CarlaStateCustomData)

                    xmlSubData = xmlData.toElement().firstChild()

                    while not xmlSubData.isNull():
                        cTag  = xmlSubData.toElement().tagName()
                        cText = xmlSubData.toElement().text().strip()

                        if cTag == "Type":
                            stateCustomData["type"] = xmlSafeString(cText, False)
                        elif cTag == "Key":
                            stateCustomData["key"] = xmlSafeString(cText, False)
                        elif cTag == "Value":
                            stateCustomData["value"] = xmlSafeString(cText, False)

                        xmlSubData = xmlSubData.nextSibling()

                    saveState["customDataList"].append(stateCustomData)

                # ----------------------------------------------
                # Chunk

                elif tag == "Chunk":
                    saveState["chunk"] = xmlSafeString(text, False)

                # ----------------------------------------------

                xmlData = xmlData.nextSibling()

        # ------------------------------------------------------

        node = node.nextSibling()

    return saveState

def xmlSafeString(string, toXml):
    if toXml:
        return string.replace("&", "&amp;").replace("<","&lt;").replace(">","&gt;").replace("'","&apos;").replace("\"","&quot;")
    else:
        return string.replace("&amp;", "&").replace("&lt;","<").replace("&gt;",">").replace("&apos;","'").replace("&quot;","\"")

# ------------------------------------------------------------------------------------------------------------
# Carla About dialog

class CarlaAboutW(QDialog):
    def __init__(self, parent):
        QDialog.__init__(self, parent)
        self.ui = ui_carla_about.Ui_CarlaAboutW()
        self.ui.setupUi(self)

        if Carla.isControl:
            extraInfo = " - <b>%s</b>" % self.tr("OSC Bridge Version")
        else:
            extraInfo = ""

        self.ui.l_about.setText(self.tr(""
                                     "<br>Version %s"
                                     "<br>Carla is a Multi-Plugin Host for JACK%s.<br>"
                                     "<br>Copyright (C) 2011-2013 falkTX<br>"
                                     "" % (VERSION, extraInfo)))

        if Carla.isControl:
            self.ui.l_extended.hide()
            self.ui.tabWidget.removeTab(1)
            self.ui.tabWidget.removeTab(1)

        else:
            self.ui.l_extended.setText(cString(Carla.host.get_extended_license_text()))
            self.ui.le_osc_url.setText(cString(Carla.host.get_host_osc_url()) if Carla.host.is_engine_running() else self.tr("(Engine not running)"))

            self.ui.l_osc_cmds.setText(
                                    " /set_active                 <i-value>\n"
                                    " /set_drywet                 <f-value>\n"
                                    " /set_volume                 <f-value>\n"
                                    " /set_balance_left           <f-value>\n"
                                    " /set_balance_right          <f-value>\n"
                                    " /set_panning                <f-value>\n"
                                    " /set_parameter_value        <i-index> <f-value>\n"
                                    " /set_parameter_midi_cc      <i-index> <i-cc>\n"
                                    " /set_parameter_midi_channel <i-index> <i-channel>\n"
                                    " /set_program                <i-index>\n"
                                    " /set_midi_program           <i-index>\n"
                                    " /note_on                    <i-note> <i-velo>\n"
                                    " /note_off                   <i-note>\n"
                                  )

            self.ui.l_example.setText("/Carla/2/set_parameter_value 5 1.0")
            self.ui.l_example_help.setText("<i>(as in this example, \"2\" is the plugin number and \"5\" the parameter)</i>")

            self.ui.l_ladspa.setText(self.tr("Everything! (Including LRDF)"))
            self.ui.l_dssi.setText(self.tr("Everything! (Including CustomData/Chunks)"))
            self.ui.l_lv2.setText(self.tr("About 95&#37; complete (using custom extensions).<br/>"
                                      "Implemented Feature/Extensions:"
                                      "<ul>"
                                      "<li>http://lv2plug.in/ns/ext/atom</li>"
                                      "<li>http://lv2plug.in/ns/ext/buf-size</li>"
                                      "<li>http://lv2plug.in/ns/ext/data-access</li>"
                                      #"<li>http://lv2plug.in/ns/ext/dynmanifest</li>"
                                      "<li>http://lv2plug.in/ns/ext/event</li>"
                                      "<li>http://lv2plug.in/ns/ext/instance-access</li>"
                                      "<li>http://lv2plug.in/ns/ext/log</li>"
                                      "<li>http://lv2plug.in/ns/ext/midi</li>"
                                      "<li>http://lv2plug.in/ns/ext/options</li>"
                                      #"<li>http://lv2plug.in/ns/ext/parameters</li>"
                                      "<li>http://lv2plug.in/ns/ext/patch</li>"
                                      #"<li>http://lv2plug.in/ns/ext/port-groups</li>"
                                      "<li>http://lv2plug.in/ns/ext/port-props</li>"
                                      #"<li>http://lv2plug.in/ns/ext/presets</li>"
                                      "<li>http://lv2plug.in/ns/ext/state</li>"
                                      "<li>http://lv2plug.in/ns/ext/time</li>"
                                      "<li>http://lv2plug.in/ns/ext/uri-map</li>"
                                      "<li>http://lv2plug.in/ns/ext/urid</li>"
                                      "<li>http://lv2plug.in/ns/ext/worker</li>"
                                      "<li>http://lv2plug.in/ns/extensions/ui</li>"
                                      "<li>http://lv2plug.in/ns/extensions/units</li>"
                                      "<li>http://kxstudio.sf.net/ns/lv2ext/external-ui</li>"
                                      "<li>http://kxstudio.sf.net/ns/lv2ext/programs</li>"
                                      "<li>http://kxstudio.sf.net/ns/lv2ext/rtmempool</li>"
                                      "<li>http://ll-plugins.nongnu.org/lv2/ext/midimap</li>"
                                      "<li>http://ll-plugins.nongnu.org/lv2/ext/miditype</li>"
                                      "</ul>"))
            self.ui.l_vst.setText(self.tr("<p>About 85&#37; complete (missing vst bank/presets and some minor stuff)</p>"))

    def done(self, r):
        QDialog.done(self, r)
        self.close()

# ------------------------------------------------------------------------------------------------------------
# Plugin Parameter

class PluginParameter(QWidget):
    def __init__(self, parent, pInfo, pluginId, tabIndex):
        QWidget.__init__(self, parent)
        self.ui = ui_carla_parameter.Ui_PluginParameter()
        self.ui.setupUi(self)

        pType  = pInfo['type']
        pHints = pInfo['hints']

        self.m_midiCC      = -1
        self.m_midiChannel = 1
        self.m_pluginId    = pluginId
        self.m_parameterId = pInfo['index']
        self.m_tabIndex    = tabIndex

        self.ui.label.setText(pInfo['name'])

        for MIDI_CC in MIDI_CC_LIST:
            self.ui.combo.addItem(MIDI_CC)

        if pType == PARAMETER_INPUT:
            self.ui.widget.set_minimum(pInfo['minimum'])
            self.ui.widget.set_maximum(pInfo['maximum'])
            self.ui.widget.set_default(pInfo['default'])
            self.ui.widget.set_value(pInfo['current'], False)
            self.ui.widget.set_label(pInfo['unit'])
            self.ui.widget.set_step(pInfo['step'])
            self.ui.widget.set_step_small(pInfo['stepSmall'])
            self.ui.widget.set_step_large(pInfo['stepLarge'])
            self.ui.widget.set_scalepoints(pInfo['scalepoints'], bool(pHints & PARAMETER_USES_SCALEPOINTS))

            if not pHints & PARAMETER_IS_ENABLED:
                self.ui.widget.set_read_only(True)
                self.ui.combo.setEnabled(False)
                self.ui.sb_channel.setEnabled(False)

            elif not pHints & PARAMETER_IS_AUTOMABLE:
                self.ui.combo.setEnabled(False)
                self.ui.sb_channel.setEnabled(False)

        elif pType == PARAMETER_OUTPUT:
            self.ui.widget.set_minimum(pInfo['minimum'])
            self.ui.widget.set_maximum(pInfo['maximum'])
            self.ui.widget.set_value(pInfo['current'], False)
            self.ui.widget.set_label(pInfo['unit'])
            self.ui.widget.set_read_only(True)

            if not pHints & PARAMETER_IS_AUTOMABLE:
                self.ui.combo.setEnabled(False)
                self.ui.sb_channel.setEnabled(False)

        else:
            self.ui.widget.setVisible(False)
            self.ui.combo.setVisible(False)
            self.ui.sb_channel.setVisible(False)

        self.set_parameter_midi_cc(pInfo['midiCC'])
        self.set_parameter_midi_channel(pInfo['midiChannel'])

        self.connect(self.ui.widget, SIGNAL("valueChanged(double)"), SLOT("slot_valueChanged(double)"))
        self.connect(self.ui.sb_channel, SIGNAL("valueChanged(int)"), SLOT("slot_midiChannelChanged(int)"))
        self.connect(self.ui.combo, SIGNAL("currentIndexChanged(int)"), SLOT("slot_midiCcChanged(int)"))

        #if force_parameters_style:
        #self.widget.force_plastique_style()

        if pHints & PARAMETER_USES_CUSTOM_TEXT:
            self.ui.widget.set_text_call(self.textCallBack)

        self.ui.widget.updateAll()

    def setDefaultValue(self, value):
        self.ui.widget.set_default(value)

    def set_parameter_value(self, value, send=True):
        self.ui.widget.set_value(value, send)

    def set_parameter_midi_cc(self, cc):
        self.m_midiCC = cc
        self.set_MIDI_CC_in_ComboBox(cc)

    def set_parameter_midi_channel(self, channel):
        self.m_midiChannel = channel+1
        self.ui.sb_channel.setValue(channel+1)

    def set_MIDI_CC_in_ComboBox(self, cc):
        for i in range(len(MIDI_CC_LIST)):
            ccText = MIDI_CC_LIST[i].split(" ")[0]
            if int(ccText, 16) == cc:
                ccIndex = i
                break
        else:
            ccIndex = -1

        self.ui.combo.setCurrentIndex(ccIndex+1)

    def tabIndex(self):
        return self.m_tabIndex

    def textCallBack(self):
        return cString(Carla.host.get_parameter_text(self.m_pluginId, self.m_parameterId))

    @pyqtSlot(float)
    def slot_valueChanged(self, value):
        self.emit(SIGNAL("valueChanged(int, double)"), self.m_parameterId, value)

    @pyqtSlot(int)
    def slot_midiCcChanged(self, ccIndex):
        if ccIndex <= 0:
            cc = -1
        else:
            ccText = MIDI_CC_LIST[ccIndex - 1].split(" ")[0]
            cc = int(ccText, 16)

        if self.m_midiCC != cc:
            self.emit(SIGNAL("midiCcChanged(int, int)"), self.m_parameterId, cc)

        self.m_midiCC = cc

    @pyqtSlot(int)
    def slot_midiChannelChanged(self, channel):
        if self.m_midiChannel != channel:
            self.emit(SIGNAL("midiChannelChanged(int, int)"), self.m_parameterId, channel)

        self.m_midiChannel = channel

# ------------------------------------------------------------------------------------------------------------
# TESTING

from PyQt4.QtGui import QApplication

Carla.isControl = True

ptest = {
    'index': 0,
    'name': "",
    'symbol': "",
    'current': 0.1,
    'default': 0.3,
    'minimum': 0.0,
    'maximum': 1.0,
    'midiChannel': 1,
    'midiCC': -1,
    'type': PARAMETER_INPUT,
    'hints': PARAMETER_IS_ENABLED | PARAMETER_IS_AUTOMABLE,
    'scalepoints': [],
    'step': 0.01,
    'stepSmall': 0.001,
    'stepLarge': 0.1,
    'unit': "un",
}

app  = QApplication(sys.argv)
gui1 = CarlaAboutW(None)
gui2 = PluginParameter(None, ptest, 0, 0)
gui1.show()
gui2.show()
app.exec_()