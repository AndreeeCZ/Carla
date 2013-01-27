/*
 * Carla Plugin
 * Copyright (C) 2011-2013 Filipe Coelho <falktx@falktx.com>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * For a full copy of the GNU General Public License see the GPL.txt file
 */

#ifndef __CARLA_PLUGIN_INTERNAL_HPP__
#define __CARLA_PLUGIN_INTERNAL_HPP__

#include "carla_plugin.hpp"
#include "carla_plugin_thread.hpp"

#include "carla_engine.hpp"

#ifdef BUILD_BRIDGE
# include "carla_bridge_osc.hpp"
#else
# include "carla_osc_utils.hpp"
#endif

#include "rt_list.hpp"

#define CARLA_DECLARE_NON_COPY_STRUCT(structName) \
    structName(const structName&) = delete;

#define CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(structName) \
    CARLA_DECLARE_NON_COPY_STRUCT(structName) \
    CARLA_LEAK_DETECTOR(structName)

#define CARLA_PROCESS_CONTINUE_CHECK if (! fData->enabled) { fData->engine->callback(CALLBACK_DEBUG, fData->id, 0, 0, 0.0, nullptr); return; }

CARLA_BACKEND_START_NAMESPACE

// -----------------------------------------------------------------------

struct PluginAudioPort {
    uint32_t rindex;
    CarlaEngineAudioPort* port;

    PluginAudioPort()
        : rindex(0),
          port(nullptr) {}

    ~PluginAudioPort()
    {
        CARLA_ASSERT(port == nullptr);
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginAudioPort)
};

struct PluginAudioData {
    uint32_t count;
    PluginAudioPort* ports;

    PluginAudioData()
        : count(0),
          ports(nullptr) {}

    ~PluginAudioData()
    {
        CARLA_ASSERT(ports == nullptr);
    }

    void createNew(const size_t count)
    {
        CARLA_ASSERT(ports == nullptr);

        if (ports == nullptr)
            ports = new PluginAudioPort[count];
    }

    void free()
    {
        CARLA_ASSERT(ports != nullptr);

        if (ports != nullptr)
        {
            delete[] ports;
            ports = nullptr;
        }
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginAudioData)
};

// -----------------------------------------------------------------------

struct PluginEventData {
    CarlaEngineEventPort* portIn;
    CarlaEngineEventPort* portOut;

    PluginEventData()
        : portIn(nullptr),
          portOut(nullptr) {}

    ~PluginEventData()
    {
        CARLA_ASSERT(portIn == nullptr);
        CARLA_ASSERT(portOut == nullptr);
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginEventData)
};

// -----------------------------------------------------------------------

struct PluginParameterData {
    uint32_t count;
    ParameterData*   data;
    ParameterRanges* ranges;

    PluginParameterData()
        : count(0),
          data(nullptr),
          ranges(nullptr) {}

    ~PluginParameterData()
    {
        CARLA_ASSERT(data == nullptr);
        CARLA_ASSERT(ranges == nullptr);
    }

    void createNew(const size_t count)
    {
        CARLA_ASSERT(data == nullptr);
        CARLA_ASSERT(ranges == nullptr);

        if (data == nullptr)
            data = new ParameterData[count];

        if (ranges == nullptr)
            ranges = new ParameterRanges[count];
    }

    void free()
    {
        CARLA_ASSERT(data != nullptr);
        CARLA_ASSERT(ranges != nullptr);

        if (data != nullptr)
        {
            delete[] data;
            data = nullptr;
        }

        if (ranges != nullptr)
        {
            delete[] ranges;
            ranges = nullptr;
        }
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginParameterData)
};

// -----------------------------------------------------------------------

typedef const char* ProgramName;

struct PluginProgramData {
    uint32_t count;
    int32_t  current;
    ProgramName* names;

    PluginProgramData()
        : count(0),
          current(-1),
          names(nullptr) {}

    ~PluginProgramData()
    {
        CARLA_ASSERT(names == nullptr);
    }

    void createNew(const size_t count)
    {
        CARLA_ASSERT(names == nullptr);

        if (names == nullptr)
            names = new ProgramName[count];
    }

    void free()
    {
        CARLA_ASSERT(names != nullptr);

        if (names != nullptr)
        {
            delete[] names;
            names = nullptr;
        }
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginProgramData)
};

struct PluginMidiProgramData {
    uint32_t count;
    int32_t  current;
    MidiProgramData* data;

    PluginMidiProgramData()
        : count(0),
          current(-1),
          data(nullptr) {}

    ~PluginMidiProgramData()
    {
        CARLA_ASSERT(data == nullptr);
    }

    void createNew(const size_t count)
    {
        CARLA_ASSERT(data == nullptr);

        if (data == nullptr)
            data = new MidiProgramData[count];
    }

    void free()
    {
        CARLA_ASSERT(data != nullptr);

        if (data != nullptr)
        {
            delete[] data;
            data = nullptr;
        }
    }

    const MidiProgramData& getCurrent()
    {
        return data[current];
    }

    CARLA_DECLARE_NON_COPY_STRUCT_WITH_LEAK_DETECTOR(PluginMidiProgramData)
};

// -----------------------------------------------------------------------

struct PluginPostRtEvent {
    PluginPostRtEventType type;
    int32_t value1;
    int32_t value2;
    double  value3;

    PluginPostRtEvent()
        : type(kPluginPostRtEventNull),
          value1(-1),
          value2(-1),
          value3(0.0) {}

    CARLA_DECLARE_NON_COPY_STRUCT(PluginPostRtEvent)
};

// -----------------------------------------------------------------------

struct ExternalMidiNote {
    int8_t  channel; // invalid = -1
    uint8_t note;
    uint8_t velo;

    ExternalMidiNote()
        : channel(-1),
          note(0),
          velo(0) {}

    CARLA_DECLARE_NON_COPY_STRUCT(ExternalMidiNote)
};

// -----------------------------------------------------------------------

const unsigned int PLUGIN_OPTION2_HAS_MIDI_IN  = 0x1;
const unsigned int PLUGIN_OPTION2_HAS_MIDI_OUT = 0x2;

struct CarlaPluginProtectedData {
    unsigned short id;

    CarlaEngine* const engine;
    CarlaEngineClient* client;

    unsigned int hints;
    unsigned int options;
    unsigned int options2;

    bool active;
    bool activeBefore;
    bool enabled;

    void* lib;
    const char* name;
    const char* filename;

    // misc
    int8_t   ctrlInChannel;
    uint32_t latency;
    float**  latencyBuffers;

    // data
    PluginAudioData       audioIn;
    PluginAudioData       audioOut;
    PluginEventData       event;
    PluginParameterData   param;
    PluginProgramData     prog;
    PluginMidiProgramData midiprog;
    NonRtList<CustomData> custom;

    struct ExternalNotes {
        CarlaMutex mutex;
        RtList<ExternalMidiNote> data;

        ExternalNotes()
            : data(32, 512) {}
    } extNotes;

    struct PostRtEvents {
        CarlaMutex mutex;
        RtList<PluginPostRtEvent> data;

        PostRtEvents()
            : data(152, 512) {}

        void append(const PluginPostRtEvent& event)
        {
            data.append(event);
        }

    } postRtEvents;

    struct PostProc {
        double dryWet;
        double volume;
        double balanceLeft;
        double balanceRight;
        double panning;

        PostProc()
            : dryWet(1.0),
              volume(1.0),
              balanceLeft(-1.0),
              balanceRight(1.0),
              panning(0.0) {}
    } postProc;

    struct OSC {
        CarlaOscData data;
        CarlaPluginThread* thread;

        OSC()
            : thread(nullptr) {}
    } osc;

    CarlaPluginProtectedData(CarlaEngine* const engine_, const unsigned short id_)
        : id(id_),
          engine(engine_),
          client(nullptr),
          hints(0x0),
          options(0x0),
          options2(0x0),
          active(false),
          activeBefore(false),
          enabled(false),
          lib(nullptr),
          name(nullptr),
          filename(nullptr),
          ctrlInChannel(-1),
          latency(0),
          latencyBuffers(nullptr) {}

    CarlaPluginProtectedData() = delete;

    CARLA_LEAK_DETECTOR(CarlaPluginProtectedData)
};

// -----------------------------------------------------------------------

CARLA_BACKEND_END_NAMESPACE

#endif // __CARLA_PLUGIN_INTERNAL_HPP__

// common includes
//#include <cmath>
//#include <vector>
//#include <QtCore/QMutex>
//#include <QtGui/QMainWindow>

//#ifdef Q_WS_X11
//# include <QtGui/QX11EmbedContainer>
//typedef QX11EmbedContainer GuiContainer;
//#else
//# include <QtGui/QWidget>
//typedef QWidget GuiContainer;
//#endif


#if 0
// -------------------------------------------------------------------
// Extra

ExternalMidiNote extMidiNotes[MAX_MIDI_EVENTS];

// -------------------------------------------------------------------
// Utilities

static double fixParameterValue(double& value, const ParameterRanges& ranges)
{
    if (value < ranges.min)
        value = ranges.min;
    else if (value > ranges.max)
        value = ranges.max;
    return value;
}

static float fixParameterValue(float& value, const ParameterRanges& ranges)
{
    if (value < ranges.min)
        value = ranges.min;
    else if (value > ranges.max)
        value = ranges.max;
    return value;
}

friend class CarlaEngine; // FIXME
friend class CarlaEngineJack;
#endif

#if 0

// -------------------------------------------------------------------

/*!
 * \class ScopedDisabler
 *
 * \brief Carla plugin scoped disabler
 *
 * This is a handy class that temporarily disables a plugin during a function scope.\n
 * It should be used when the plugin needs reload or state change, something like this:
 * \code
 * {
 *      const CarlaPlugin::ScopedDisabler m(plugin);
 *      plugin->setChunkData(data);
 * }
 * \endcode
 */
class ScopedDisabler
{
public:
    /*!
     * Disable plugin \a plugin if \a disable is true.
     * The plugin is re-enabled in the deconstructor of this class if \a disable is true.
     *
     * \param plugin The plugin to disable
     * \param disable Wherever to disable the plugin or not, true by default
     */
    ScopedDisabler(CarlaPlugin* const plugin, const bool disable = true)
        : m_plugin(plugin),
          m_disable(disable)
    {
        if (m_disable)
        {
            m_plugin->engineProcessLock();
            m_plugin->setEnabled(false);
            m_plugin->engineProcessUnlock();
        }
    }

    ~ScopedDisabler()
    {
        if (m_disable)
        {
            m_plugin->engineProcessLock();
            m_plugin->setEnabled(true);
            m_plugin->engineProcessUnlock();
        }
    }

private:
    CarlaPlugin* const m_plugin;
    const bool m_disable;
};

/*!
 * \class CarlaPluginGUI
 *
 * \brief Carla Backend gui plugin class
 *
 * \see CarlaPlugin
 */
class CarlaPluginGUI : public QMainWindow
{
public:
    /*!
     * \class Callback
     *
     * \brief Carla plugin GUI callback
     */
    class Callback
    {
    public:
        virtual ~Callback() {}
        virtual void guiClosedCallback() = 0;
    };

    // -------------------------------------------------------------------
    // Constructor and destructor

    /*!
     * TODO
     */
    CarlaPluginGUI(QWidget* const parent, Callback* const callback);

    /*!
     * TODO
     */
    ~CarlaPluginGUI();

    // -------------------------------------------------------------------
    // Get data

    /*!
     * TODO
     */
    GuiContainer* getContainer() const;

    /*!
     * TODO
     */
    WId getWinId() const;

    // -------------------------------------------------------------------
    // Set data

    /*!
     * TODO
     */
    void setNewSize(const int width, const int height);

    /*!
     * TODO
     */
    void setResizable(const bool resizable);

    /*!
     * TODO
     */
    void setTitle(const char* const title);

    /*!
     * TODO
     */
    void setVisible(const bool yesNo);

    // -------------------------------------------------------------------

private:
    Callback* const m_callback;
    GuiContainer*   m_container;

    QByteArray m_geometry;
    bool m_resizable;

    void hideEvent(QHideEvent* const event);
    void closeEvent(QCloseEvent* const event);
};
#endif