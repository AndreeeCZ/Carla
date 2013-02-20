﻿/*
 * Carla JACK Engine
 * Copyright (C) 2012-2013 Filipe Coelho <falktx@falktx.com>
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

#ifdef WANT_JACK

#include "CarlaEngineInternal.hpp"
#include "CarlaBackendUtils.hpp"
#include "CarlaMIDI.h"

#include "jackbridge/jackbridge.h"

#include <cmath>

CARLA_BACKEND_START_NAMESPACE

#if 0
} // Fix editor indentation
#endif

// -------------------------------------------------------------------
// Helpers, defined in CarlaPlugin.cpp

extern CarlaEngine* CarlaPluginGetEngine(CarlaPlugin* const plugin);
extern CarlaEngineAudioPort* CarlaPluginGetAudioInPort(CarlaPlugin* const plugin, uint32_t index);
extern CarlaEngineAudioPort* CarlaPluginGetAudioOutPort(CarlaPlugin* const plugin, uint32_t index);

// -------------------------------------------------------------------------------------------------------------------
// Carla Engine JACK-Audio port

class CarlaEngineJackAudioPort : public CarlaEngineAudioPort
{
public:
    CarlaEngineJackAudioPort(const bool isInput, const ProcessMode processMode, jack_client_t* const client, jack_port_t* const port)
        : CarlaEngineAudioPort(isInput, processMode),
          kClient(client),
          kPort(port)
    {
        qDebug("CarlaEngineJackAudioPort::CarlaEngineJackAudioPort(%s, %s, %p, %p)", bool2str(isInput), ProcessMode2Str(processMode), client, port);

        if (processMode == PROCESS_MODE_SINGLE_CLIENT || processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            CARLA_ASSERT(client != nullptr && port != nullptr);
        }
        else
        {
            CARLA_ASSERT(client == nullptr && port == nullptr);
        }
    }

    ~CarlaEngineJackAudioPort()
    {
        qDebug("CarlaEngineJackAudioPort::~CarlaEngineJackAudioPort()");

        if (kClient != nullptr && kPort != nullptr)
            jackbridge_port_unregister(kClient, kPort);
    }

    void initBuffer(CarlaEngine* const engine)
    {
        CARLA_ASSERT(engine != nullptr);

        if (engine == nullptr)
        {
            fBuffer = nullptr;
            return;
        }

        if (kPort == nullptr)
            return CarlaEngineAudioPort::initBuffer(engine);

        fBuffer = (float*)jackbridge_port_get_buffer(kPort, engine->getBufferSize());

        if (! kIsInput)
           carla_zeroFloat(fBuffer, engine->getBufferSize());
    }

private:
    jack_client_t* const kClient;
    jack_port_t*   const kPort;

    friend class CarlaEngineJack;

    CARLA_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CarlaEngineJackAudioPort)
};

// -------------------------------------------------------------------------------------------------------------------
// Carla Engine JACK-Event port

static const EngineEvent kFallbackJackEngineEvent;

class CarlaEngineJackEventPort : public CarlaEngineEventPort
{
public:
    CarlaEngineJackEventPort(const bool isInput, const ProcessMode processMode, jack_client_t* const client, jack_port_t* const port)
        : CarlaEngineEventPort(isInput, processMode),
          kClient(client),
          kPort(port),
          fJackBuffer(nullptr)
    {
        qDebug("CarlaEngineJackEventPort::CarlaEngineJackEventPort(%s, %s, %p, %p)", bool2str(isInput), ProcessMode2Str(processMode), client, port);

        if (processMode == PROCESS_MODE_SINGLE_CLIENT || processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            CARLA_ASSERT(client != nullptr && port != nullptr);
        }
        else
        {
            CARLA_ASSERT(client == nullptr && port == nullptr);
        }
    }

    ~CarlaEngineJackEventPort()
    {
        qDebug("CarlaEngineJackEventPort::~CarlaEngineJackEventPort()");

        if (kClient != nullptr && kPort != nullptr)
            jackbridge_port_unregister(kClient, kPort);
    }

    void initBuffer(CarlaEngine* const engine)
    {
        CARLA_ASSERT(engine != nullptr);

        if (engine == nullptr)
        {
            fJackBuffer = nullptr;
            return;
        }

        if (kPort == nullptr)
            return CarlaEngineEventPort::initBuffer(engine);

        fJackBuffer = jackbridge_port_get_buffer(kPort, engine->getBufferSize());

        if (! kIsInput)
            jackbridge_midi_clear_buffer(fJackBuffer);
    }

    uint32_t getEventCount()
    {
        if (kPort == nullptr)
            return CarlaEngineEventPort::getEventCount();

        CARLA_ASSERT(kIsInput);
        CARLA_ASSERT(fJackBuffer != nullptr);

        if (! kIsInput)
            return 0;
        if (fJackBuffer == nullptr)
            return 0;

        return jackbridge_midi_get_event_count(fJackBuffer);
    }

    const EngineEvent& getEvent(const uint32_t index)
    {
        if (kPort == nullptr)
            return CarlaEngineEventPort::getEvent(index);

        CARLA_ASSERT(kIsInput);
        CARLA_ASSERT(fJackBuffer != nullptr);

        if (! kIsInput)
            return kFallbackJackEngineEvent;
        if (fJackBuffer == nullptr)
            return kFallbackJackEngineEvent;

        jack_midi_event_t jackEvent;

        if (jackbridge_midi_event_get(&jackEvent, fJackBuffer, index) != 0 || jackEvent.size > 3)
            return kFallbackJackEngineEvent;

        fRetEvent.clear();

        const uint8_t midiStatus  = MIDI_GET_STATUS_FROM_DATA(jackEvent.buffer);
        const uint8_t midiChannel = MIDI_GET_CHANNEL_FROM_DATA(jackEvent.buffer);

        fRetEvent.time    = jackEvent.time;
        fRetEvent.channel = midiChannel;

        if (MIDI_IS_STATUS_CONTROL_CHANGE(midiStatus))
        {
            const uint8_t midiControl = jackEvent.buffer[1];
            fRetEvent.type            = kEngineEventTypeControl;

            if (MIDI_IS_CONTROL_BANK_SELECT(midiControl))
            {
                const uint8_t midiBank = jackEvent.buffer[2];

                fRetEvent.ctrl.type  = kEngineControlEventTypeMidiBank;
                fRetEvent.ctrl.param = midiBank;
                fRetEvent.ctrl.value = 0.0;
            }
            else if (midiControl == MIDI_CONTROL_ALL_SOUND_OFF)
            {
                fRetEvent.ctrl.type  = kEngineControlEventTypeAllSoundOff;
                fRetEvent.ctrl.param = 0;
                fRetEvent.ctrl.value = 0.0;
            }
            else if (midiControl == MIDI_CONTROL_ALL_NOTES_OFF)
            {
                fRetEvent.ctrl.type  = kEngineControlEventTypeAllNotesOff;
                fRetEvent.ctrl.param = 0;
                fRetEvent.ctrl.value = 0.0;
            }
            else
            {
                const uint8_t midiValue = jackEvent.buffer[2];

                fRetEvent.ctrl.type  = kEngineControlEventTypeParameter;
                fRetEvent.ctrl.param = midiControl;
                fRetEvent.ctrl.value = double(midiValue)/127.0;
            }
        }
        else if (MIDI_IS_STATUS_PROGRAM_CHANGE(midiStatus))
        {
            const uint8_t midiProgram = jackEvent.buffer[1];
            fRetEvent.type            = kEngineEventTypeControl;

            fRetEvent.ctrl.type  = kEngineControlEventTypeMidiProgram;
            fRetEvent.ctrl.param = midiProgram;
            fRetEvent.ctrl.value = 0.0;
        }
        else
        {
            fRetEvent.type = kEngineEventTypeMidi;

            fRetEvent.midi.data[0] = midiStatus;
            fRetEvent.midi.data[1] = jackEvent.buffer[1];
            fRetEvent.midi.data[2] = jackEvent.buffer[2];
            fRetEvent.midi.size    = static_cast<uint8_t>(jackEvent.size);
        }

        return fRetEvent;
    }

    void writeControlEvent(const uint32_t time, const uint8_t channel, const EngineControlEventType type, const uint16_t param, const double value)
    {
        if (kPort == nullptr)
            return CarlaEngineEventPort::writeControlEvent(time, channel, type, param, value);

        CARLA_ASSERT(! kIsInput);
        CARLA_ASSERT(fJackBuffer != nullptr);
        CARLA_ASSERT(type != kEngineControlEventTypeNull);
        CARLA_ASSERT(channel < MAX_MIDI_CHANNELS);
        CARLA_ASSERT(param < MAX_MIDI_VALUE);
        CARLA_SAFE_ASSERT(value >= 0.0 && value <= 1.0);

        if (kIsInput)
            return;
        if (fJackBuffer == nullptr)
            return;
        if (type == kEngineControlEventTypeNull)
            return;
        if (channel >= MAX_MIDI_CHANNELS)
            return;
        if (param >= MAX_MIDI_VALUE)
            return;
        if (type == kEngineControlEventTypeParameter)
        {
            CARLA_ASSERT(! MIDI_IS_CONTROL_BANK_SELECT(param));
        }

        const double fixedValue = carla_fixValue<double>(0.0, 1.0, value);

        uint8_t data[3] = { 0 };
        uint8_t size    = 0;

        switch (type)
        {
        case kEngineControlEventTypeNull:
            break;
        case kEngineControlEventTypeParameter:
            data[0] = MIDI_STATUS_CONTROL_CHANGE + channel;
            data[1] = static_cast<uint8_t>(param);
            data[2] = uint8_t(fixedValue * 127.0);
            size    = 3;
            break;
        case kEngineControlEventTypeMidiBank:
            data[0] = MIDI_STATUS_CONTROL_CHANGE + channel;
            data[1] = MIDI_CONTROL_BANK_SELECT;
            data[2] = static_cast<uint8_t>(param);
            size    = 3;
            break;
        case kEngineControlEventTypeMidiProgram:
            data[0] = MIDI_STATUS_PROGRAM_CHANGE + channel;
            data[1] = static_cast<uint8_t>(param);
            size    = 2;
            break;
        case kEngineControlEventTypeAllSoundOff:
            data[0] = MIDI_STATUS_CONTROL_CHANGE + channel;
            data[1] = MIDI_CONTROL_ALL_SOUND_OFF;
            size    = 2;
            break;
        case kEngineControlEventTypeAllNotesOff:
            data[0] = MIDI_STATUS_CONTROL_CHANGE + channel;
            data[1] = MIDI_CONTROL_ALL_NOTES_OFF;
            size    = 2;
            break;
        }

        if (size > 0)
            jackbridge_midi_event_write(fJackBuffer, time, data, size);
    }

    void writeMidiEvent(const uint32_t time, const uint8_t channel, const uint8_t port, const uint8_t* const data, const uint8_t size)
    {
        if (kPort == nullptr)
            return CarlaEngineEventPort::writeMidiEvent(time, channel, port, data, size);

        CARLA_ASSERT(! kIsInput);
        CARLA_ASSERT(fJackBuffer != nullptr);
        CARLA_ASSERT(channel < MAX_MIDI_CHANNELS);
        CARLA_ASSERT(data != nullptr);
        CARLA_ASSERT(size > 0);

        if (kIsInput)
            return;
        if (fJackBuffer == nullptr)
            return;
        if (channel >= MAX_MIDI_CHANNELS)
            return;
        if (data == nullptr)
            return;
        if (size == 0)
            return;

        uint8_t jdata[size];
        std::memcpy(jdata, data, sizeof(uint8_t)*size);

        jdata[0] = data[0] + channel;

        jackbridge_midi_event_write(fJackBuffer, time, jdata, size);
    }

private:
    jack_client_t* const kClient;
    jack_port_t*   const kPort;

    void*       fJackBuffer;
    EngineEvent fRetEvent;

    CARLA_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CarlaEngineJackEventPort)
};

// -------------------------------------------------------------------------------------------------------------------
// Jack Engine client

class CarlaEngineJackClient : public CarlaEngineClient
{
public:
    CarlaEngineJackClient(const EngineType engineType, const ProcessMode processMode, jack_client_t* const client)
        : CarlaEngineClient(engineType, processMode),
          kClient(client),
          kUseClient(processMode == PROCESS_MODE_SINGLE_CLIENT || processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
    {
        qDebug("CarlaEngineJackClient::CarlaEngineJackClient(%s, %s, %p)", EngineType2Str(engineType), ProcessMode2Str(processMode), client);

        if (kUseClient)
        {
            CARLA_ASSERT(kClient != nullptr);
        }
        else
        {
            CARLA_ASSERT(kClient == nullptr);
        }
    }

    ~CarlaEngineJackClient()
    {
        qDebug("CarlaEngineClient::~CarlaEngineClient()");

        if (kProcessMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            if (kClient)
                jackbridge_client_close(kClient);
        }
    }

    void activate()
    {
        qDebug("CarlaEngineJackClient::activate()");

        if (kProcessMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            CARLA_ASSERT(kClient && ! fActive);

            if (kClient && ! fActive)
                jackbridge_activate(kClient);
        }

        CarlaEngineClient::activate();
    }

    void deactivate()
    {
        qDebug("CarlaEngineJackClient::deactivate()");

        if (kProcessMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            CARLA_ASSERT(kClient && fActive);

            if (kClient && fActive)
                jackbridge_deactivate(kClient);
        }

        CarlaEngineClient::deactivate();
    }

    bool isOk() const
    {
        qDebug("CarlaEngineJackClient::isOk()");

        if (kUseClient)
            return bool(kClient);

        return CarlaEngineClient::isOk();
    }

    void setLatency(const uint32_t samples)
    {
        CarlaEngineClient::setLatency(samples);

        if (kUseClient)
            jackbridge_recompute_total_latencies(kClient);
    }

    const CarlaEnginePort* addPort(const EnginePortType portType, const char* const name, const bool isInput)
    {
        qDebug("CarlaEngineJackClient::addPort(%s, \"%s\", %s)", EnginePortType2Str(portType), name, bool2str(isInput));

        jack_port_t* port = nullptr;

        // Create JACK port first, if needed
        if (kUseClient)
        {
            switch (portType)
            {
            case kEnginePortTypeNull:
                break;
            case kEnginePortTypeAudio:
                port = jackbridge_port_register(kClient, name, JACK_DEFAULT_AUDIO_TYPE, isInput ? JackPortIsInput : JackPortIsOutput, 0);
                break;
            case kEnginePortTypeEvent:
                port = jackbridge_port_register(kClient, name, JACK_DEFAULT_MIDI_TYPE, isInput ? JackPortIsInput : JackPortIsOutput, 0);
                break;
            }
        }

        // Create Engine port
        switch (portType)
        {
        case kEnginePortTypeNull:
            break;
        case kEnginePortTypeAudio:
            return new CarlaEngineJackAudioPort(isInput, kProcessMode, kClient, port);
        case kEnginePortTypeEvent:
            return new CarlaEngineJackEventPort(isInput, kProcessMode, kClient, port);
        }

        carla_stderr("CarlaEngineJackClient::addPort(%s, \"%s\", %s) - invalid type", EnginePortType2Str(portType), name, bool2str(isInput));
        return nullptr;
    }

private:
    jack_client_t* const kClient;
    const bool           kUseClient;

    CARLA_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CarlaEngineJackClient)
};

// -------------------------------------------------------------------------------------------------------------------
// Jack Engine

class CarlaEngineJack : public CarlaEngine
{
public:
    CarlaEngineJack()
        : CarlaEngine(),
#ifdef BUILD_BRIDGE
          fHasQuit(false),
#else
          fClient(nullptr),
          fTransportState(JackTransportStopped),
          fRackPorts{nullptr},
#endif
          fFreewheel(false)
    {
        qDebug("CarlaEngineJack::CarlaEngineJack()");

#ifdef BUILD_BRIDGE
        fOptions.processMode = PROCESS_MODE_MULTIPLE_CLIENTS;
#endif

        carla_zeroStruct<jack_position_t>(fTransportPos);
    }

    ~CarlaEngineJack()
    {
        qDebug("CarlaEngineJack::~CarlaEngineJack()");
        CARLA_ASSERT(fClient == nullptr);
    }

    // -------------------------------------------------------------------
    // Maximum values

    unsigned int maxClientNameSize()
    {
        if (fOptions.processMode == PROCESS_MODE_SINGLE_CLIENT || fOptions.processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
            return static_cast<unsigned int>(jackbridge_client_name_size());

        return CarlaEngine::maxClientNameSize();
    }

    unsigned int maxPortNameSize()
    {
        if (fOptions.processMode == PROCESS_MODE_SINGLE_CLIENT || fOptions.processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
            return static_cast<unsigned int>(jackbridge_port_name_size());

        return CarlaEngine::maxPortNameSize();
    }

    // -------------------------------------------------------------------
    // Virtual, per-engine type calls

    bool init(const char* const clientName)
    {
        qDebug("CarlaEngineJack::init(\"%s\")", clientName);

        fFreewheel      = false;
        fTransportState = JackTransportStopped;

        carla_zeroStruct<jack_position_t>(fTransportPos);

#ifndef BUILD_BRIDGE
        fClient = jackbridge_client_open(clientName, JackNullOption, nullptr);

        if (fClient != nullptr)
        {
            fBufferSize = jackbridge_get_buffer_size(fClient);
            fSampleRate = jackbridge_get_sample_rate(fClient);

            jackbridge_set_buffer_size_callback(fClient, carla_jack_bufsize_callback, this);
            jackbridge_set_sample_rate_callback(fClient, carla_jack_srate_callback, this);
            jackbridge_set_freewheel_callback(fClient, carla_jack_freewheel_callback, this);
            jackbridge_set_process_callback(fClient, carla_jack_process_callback, this);
            jackbridge_set_latency_callback(fClient, carla_jack_latency_callback, this);
            jackbridge_on_shutdown(fClient, carla_jack_shutdown_callback, this);

            if (fOptions.processMode == PROCESS_MODE_CONTINUOUS_RACK)
            {
                fRackPorts[rackPortAudioIn1]  = jackbridge_port_register(fClient, "audio-in1",  JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0);
                fRackPorts[rackPortAudioIn2]  = jackbridge_port_register(fClient, "audio-in2",  JACK_DEFAULT_AUDIO_TYPE, JackPortIsInput, 0);
                fRackPorts[rackPortAudioOut1] = jackbridge_port_register(fClient, "audio-out1", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0);
                fRackPorts[rackPortAudioOut2] = jackbridge_port_register(fClient, "audio-out2", JACK_DEFAULT_AUDIO_TYPE, JackPortIsOutput, 0);
                fRackPorts[rackPortEventIn]   = jackbridge_port_register(fClient, "events-in",  JACK_DEFAULT_MIDI_TYPE, JackPortIsInput, 0);
                fRackPorts[rackPortEventOut]  = jackbridge_port_register(fClient, "events-out", JACK_DEFAULT_MIDI_TYPE, JackPortIsOutput, 0);
            }

            if (jackbridge_activate(fClient) == 0)
            {
                const char* const jackClientName = jackbridge_get_client_name(fClient);

                return CarlaEngine::init(jackClientName);
            }
            else
            {
                setLastError("Failed to activate the JACK client");
                jackbridge_client_close(fClient);
                fClient = nullptr;
            }
        }
        else
            setLastError("Failed to create new JACK client");

        return false;
#else
        if (fBufferSize == 0 || fSampleRate == 0.0)
        {
            // open temp client to get initial buffer-size and sample-rate values
            if (jack_client_t* tmpClient = jackbridge_client_open(clientName, JackNullOption, nullptr))
            {
                fBufferSize = jackbridge_get_buffer_size(tmpClient);
                fSampleRate = jackbridge_get_sample_rate(tmpClient);

                jackbridge_client_close(tmpClient);
            }
        }

        return CarlaEngine::init(clientName);
#endif
    }

    bool close()
    {
        qDebug("CarlaEngineJack::close()");
        CarlaEngine::close();

#ifdef BUILD_BRIDGE
        fClient  = nullptr;
        fHasQuit = true;
        return true;
#else
        if (jackbridge_deactivate(fClient) == 0)
        {
            if (fOptions.processMode == PROCESS_MODE_CONTINUOUS_RACK)
            {
                jackbridge_port_unregister(fClient, fRackPorts[rackPortAudioIn1]);
                jackbridge_port_unregister(fClient, fRackPorts[rackPortAudioIn2]);
                jackbridge_port_unregister(fClient, fRackPorts[rackPortAudioOut1]);
                jackbridge_port_unregister(fClient, fRackPorts[rackPortAudioOut2]);
                jackbridge_port_unregister(fClient, fRackPorts[rackPortEventIn]);
                jackbridge_port_unregister(fClient, fRackPorts[rackPortEventOut]);
            }

            if (jackbridge_client_close(fClient) == 0)
            {
                fClient = nullptr;
                return true;
            }
            else
                setLastError("Failed to close the JACK client");
        }
        else
            setLastError("Failed to deactivate the JACK client");

        fClient = nullptr;
#endif
        return false;
    }

    bool isRunning() const
    {
#ifdef BUILD_BRIDGE
        return (fClient != nullptr || ! fHasQuit);
#else
        return (fClient != nullptr);
#endif
    }

    bool isOffline() const
    {
        return fFreewheel;
    }

    EngineType type() const
    {
        return kEngineTypeJack;
    }

    CarlaEngineClient* addClient(CarlaPlugin* const plugin)
    {
        jack_client_t* client = nullptr;

#ifdef BUILD_BRIDGE
        client = fClient = jackbridge_client_open(plugin->name(), JackNullOption, nullptr);

        fBufferSize = jackbridge_get_buffer_size(client);
        fSampleRate = jackbridge_get_sample_rate(client);

        jackbridge_set_buffer_size_callback(client, carla_jack_bufsize_callback, this);
        jackbridge_set_sample_rate_callback(client, carla_jack_srate_callback, this);
        jackbridge_set_freewheel_callback(client, carla_jack_freewheel_callback, this);
        jackbridge_set_process_callback(client, carla_jack_process_callback, this);
        jackbridge_set_latency_callback(client, carla_jack_latency_callback, this);
        jackbridge_on_shutdown(client, carla_jack_shutdown_callback, this);
#else
        if (fOptions.processMode == PROCESS_MODE_SINGLE_CLIENT)
        {
            client = fClient;
        }
        else if (fOptions.processMode == PROCESS_MODE_MULTIPLE_CLIENTS)
        {
            client = jackbridge_client_open(plugin->name(), JackNullOption, nullptr);
            jackbridge_set_process_callback(client, carla_jack_process_callback_plugin, plugin);
            jackbridge_set_latency_callback(client, carla_jack_latency_callback_plugin, plugin);
        }
#endif

        return new CarlaEngineJackClient(kEngineTypeJack, fOptions.processMode, client);
    }

    // -------------------------------------

protected:
    void handleJackBufferSizeCallback(const uint32_t newBufferSize)
    {
        if (fBufferSize != newBufferSize)
        {
            fBufferSize = newBufferSize;

            bufferSizeChanged(newBufferSize);
        }
    }

    void handleJackSampleRateCallback(const double newSampleRate)
    {
        if (fSampleRate != newSampleRate)
        {
            fSampleRate = newSampleRate;

            sampleRateChanged(newSampleRate);
        }
    }

    void handleJackFreewheelCallback(const bool isFreewheel)
    {
        fFreewheel = isFreewheel;
    }

    void handleJackProcessCallback(const uint32_t nframes)
    {
#ifndef BUILD_BRIDGE
        if (kData->curPluginCount == 0)
            return proccessPendingEvents();
#endif

        fTransportPos.unique_1 = fTransportPos.unique_2 + 1; // invalidate

        fTransportState = jackbridge_transport_query(fClient, &fTransportPos);

        fTimeInfo.playing = (fTransportState == JackTransportRolling);

        if (fTransportPos.unique_1 == fTransportPos.unique_2)
        {
            fTimeInfo.frame = fTransportPos.frame;
            fTimeInfo.time  = fTransportPos.usecs;

            if (fTransportPos.valid & JackPositionBBT)
            {
                fTimeInfo.valid              = EngineTimeInfo::ValidBBT;
                fTimeInfo.bbt.bar            = fTransportPos.bar;
                fTimeInfo.bbt.beat           = fTransportPos.beat;
                fTimeInfo.bbt.tick           = fTransportPos.tick;
                fTimeInfo.bbt.barStartTick   = fTransportPos.bar_start_tick;
                fTimeInfo.bbt.beatsPerBar    = fTransportPos.beats_per_bar;
                fTimeInfo.bbt.beatType       = fTransportPos.beat_type;
                fTimeInfo.bbt.ticksPerBeat   = fTransportPos.ticks_per_beat;
                fTimeInfo.bbt.beatsPerMinute = fTransportPos.beats_per_minute;
            }
            else
                fTimeInfo.valid = 0x0;
        }
        else
        {
            fTimeInfo.frame = 0;
            fTimeInfo.valid = 0x0;
        }

#ifdef BUILD_BRIDGE
        CarlaPlugin* const plugin = getPluginUnchecked(0);

        if (plugin && plugin->enabled())
        {
            plugin->initBuffers();
            processPlugin(plugin, nframes);
        }
#else
        if (fOptions.processMode == PROCESS_MODE_SINGLE_CLIENT)
        {
            for (unsigned int i=0; i < kData->curPluginCount; i++)
            {
                CarlaPlugin* const plugin = getPluginUnchecked(i);

                if (plugin && plugin->enabled())
                {
                    plugin->initBuffers();
                    processPlugin(plugin, nframes);
                }
            }
        }
        else if (fOptions.processMode == PROCESS_MODE_CONTINUOUS_RACK)
        {
            // get buffers from jack
            float* const audioIn1  = (float*)jackbridge_port_get_buffer(fRackPorts[rackPortAudioIn1], nframes);
            float* const audioIn2  = (float*)jackbridge_port_get_buffer(fRackPorts[rackPortAudioIn2], nframes);
            float* const audioOut1 = (float*)jackbridge_port_get_buffer(fRackPorts[rackPortAudioOut1], nframes);
            float* const audioOut2 = (float*)jackbridge_port_get_buffer(fRackPorts[rackPortAudioOut2], nframes);
            void* const  eventIn   = jackbridge_port_get_buffer(fRackPorts[rackPortEventIn],  nframes);
            void* const  eventOut  = jackbridge_port_get_buffer(fRackPorts[rackPortEventOut], nframes);

            // assert buffers
            CARLA_ASSERT(audioIn1 != nullptr);
            CARLA_ASSERT(audioIn2 != nullptr);
            CARLA_ASSERT(audioOut1 != nullptr);
            CARLA_ASSERT(audioOut2 != nullptr);
            CARLA_ASSERT(eventIn != nullptr);
            CARLA_ASSERT(eventOut != nullptr);

            // create audio buffers
            float* inBuf[2]  = { audioIn1, audioIn2 };
            float* outBuf[2] = { audioOut1, audioOut2 };

#if 0
            // initialize control input
            memset(rackControlEventsIn, 0, sizeof(CarlaEngineControlEvent)*MAX_CONTROL_EVENTS);
            {
                jack_midi_event_t jackEvent;
                const uint32_t jackEventCount = jackbridge_midi_get_event_count(controlIn);

                uint32_t carlaEventIndex = 0;

                for (uint32_t jackEventIndex=0; jackEventIndex < jackEventCount; jackEventIndex++)
                {
                    if (jackbridge_midi_event_get(&jackEvent, controlIn, jackEventIndex) != 0)
                        continue;

                    CarlaEngineControlEvent* const carlaEvent = &rackControlEventsIn[carlaEventIndex++];

                    const uint8_t midiStatus  = jackEvent.buffer[0];
                    const uint8_t midiChannel = midiStatus & 0x0F;

                    carlaEvent->time    = jackEvent.time;
                    carlaEvent->channel = midiChannel;

                    if (MIDI_IS_STATUS_CONTROL_CHANGE(midiStatus))
                    {
                        const uint8_t midiControl = jackEvent.buffer[1];

                        if (MIDI_IS_CONTROL_BANK_SELECT(midiControl))
                        {
                            const uint8_t midiBank = jackEvent.buffer[2];
                            carlaEvent->type  = CarlaEngineMidiBankChangeEvent;
                            carlaEvent->value = midiBank;
                        }
                        else if (midiControl == MIDI_CONTROL_ALL_SOUND_OFF)
                        {
                            carlaEvent->type = CarlaEngineAllSoundOffEvent;
                        }
                        else if (midiControl == MIDI_CONTROL_ALL_NOTES_OFF)
                        {
                            carlaEvent->type = CarlaEngineAllNotesOffEvent;
                        }
                        else
                        {
                            const uint8_t midiValue = jackEvent.buffer[2];
                            carlaEvent->type      = CarlaEngineParameterChangeEvent;
                            carlaEvent->parameter = midiControl;
                            carlaEvent->value     = double(midiValue)/127;
                        }
                    }
                    else if (MIDI_IS_STATUS_PROGRAM_CHANGE(midiStatus))
                    {
                        const uint8_t midiProgram = jackEvent.buffer[1];
                        carlaEvent->type  = CarlaEngineMidiProgramChangeEvent;
                        carlaEvent->value = midiProgram;
                    }
                }
            }

            // initialize midi input
            memset(rackMidiEventsIn, 0, sizeof(CarlaEngineMidiEvent)*MAX_MIDI_EVENTS);
            {
                uint32_t i = 0, j = 0;
                jack_midi_event_t jackEvent;

                while (jackbridge_midi_event_get(&jackEvent, midiIn, j++) == 0)
                {
                    if (i == MAX_MIDI_EVENTS)
                        break;

                    if (jackEvent.size < 4)
                    {
                        rackMidiEventsIn[i].time = jackEvent.time;
                        rackMidiEventsIn[i].size = jackEvent.size;
                        memcpy(rackMidiEventsIn[i].data, jackEvent.buffer, jackEvent.size);
                        i += 1;
                    }
                }
            }
#endif

            // process rack
            processRack(inBuf, outBuf, nframes);

#if 0
            // output control
            {
                jackbridge_midi_clear_buffer(controlOut);

                for (unsigned short i=0; i < MAX_CONTROL_EVENTS; i++)
                {
                    CarlaEngineControlEvent* const event = &rackControlEventsOut[i];

                    if (event->type == CarlaEngineParameterChangeEvent && MIDI_IS_CONTROL_BANK_SELECT(event->parameter))
                        event->type = CarlaEngineMidiBankChangeEvent;

                    uint8_t data[4] = { 0 };

                    switch (event->type)
                    {
                    case CarlaEngineNullEvent:
                        break;
                    case CarlaEngineParameterChangeEvent:
                        data[0] = MIDI_STATUS_CONTROL_CHANGE + event->channel;
                        data[1] = event->parameter;
                        data[2] = event->value * 127;
                        jackbridge_midi_event_write(controlOut, event->time, data, 3);
                        break;
                    case CarlaEngineMidiBankChangeEvent:
                        data[0] = MIDI_STATUS_CONTROL_CHANGE + event->channel;
                        data[1] = MIDI_CONTROL_BANK_SELECT;
                        data[2] = event->value;
                        jackbridge_midi_event_write(controlOut, event->time, data, 3);
                        break;
                    case CarlaEngineMidiProgramChangeEvent:
                        data[0] = MIDI_STATUS_PROGRAM_CHANGE + event->channel;
                        data[1] = event->value;
                        jackbridge_midi_event_write(controlOut, event->time, data, 2);
                        break;
                    case CarlaEngineAllSoundOffEvent:
                        data[0] = MIDI_STATUS_CONTROL_CHANGE + event->channel;
                        data[1] = MIDI_CONTROL_ALL_SOUND_OFF;
                        jackbridge_midi_event_write(controlOut, event->time, data, 2);
                        break;
                    case CarlaEngineAllNotesOffEvent:
                        data[0] = MIDI_STATUS_CONTROL_CHANGE + event->channel;
                        data[1] = MIDI_CONTROL_ALL_NOTES_OFF;
                        jackbridge_midi_event_write(controlOut, event->time, data, 2);
                        break;
                    }
                }
            }

            // output midi
            {
                jackbridge_midi_clear_buffer(midiOut);

                for (unsigned short i=0; i < MAX_MIDI_EVENTS; i++)
                {
                    if (rackMidiEventsOut[i].size == 0)
                        break;

                    jackbridge_midi_event_write(midiOut, rackMidiEventsOut[i].time, rackMidiEventsOut[i].data, rackMidiEventsOut[i].size);
                }
            }
#endif
        }
#endif // ! BUILD_BRIDGE

        proccessPendingEvents();
    }

    void handleJackLatencyCallback(const jack_latency_callback_mode_t mode)
    {
        if (fOptions.processMode != PROCESS_MODE_SINGLE_CLIENT)
            return;

        for (unsigned int i=0; i < kData->curPluginCount; i++)
        {
            CarlaPlugin* const plugin = getPluginUnchecked(i);

            if (plugin && plugin->enabled())
                latencyPlugin(plugin, mode);
        }
    }

    void handleJackShutdownCallback()
    {
        for (unsigned int i=0; i < kData->curPluginCount; i++)
        {
            //CarlaPlugin* const plugin = getPluginUnchecked(i);

            //if (plugin)
            //    plugin->x_client = nullptr;
        }

        fClient = nullptr;
        callback(CALLBACK_QUIT, 0, 0, 0, 0.0f, nullptr);
    }

    // -------------------------------------

private:
    jack_client_t*         fClient;
    jack_position_t        fTransportPos;
    jack_transport_state_t fTransportState;

    // -------------------------------------

#ifdef BUILD_BRIDGE
    bool fHasQuit;
#else
    enum RackPorts {
        rackPortAudioIn1  = 0,
        rackPortAudioIn2  = 1,
        rackPortAudioOut1 = 2,
        rackPortAudioOut2 = 3,
        rackPortEventIn   = 4,
        rackPortEventOut  = 5,
        rackPortCount     = 8
    };

    jack_port_t* fRackPorts[rackPortCount];
#endif

    bool fFreewheel;

    // -------------------------------------

    void processPlugin(CarlaPlugin* const plugin, const uint32_t nframes)
    {
        const uint32_t inCount  = plugin->audioInCount();
        const uint32_t outCount = plugin->audioOutCount();

        float* inBuffer[inCount];
        float* outBuffer[outCount];

        float inPeaks[inCount];
        float outPeaks[outCount];

        if (inCount > 0)
            carla_zeroFloat(inPeaks, inCount);
        if (outCount > 0)
            carla_zeroFloat(outPeaks, outCount);

        for (uint32_t i=0; i < inCount; i++)
        {
            CarlaEngineAudioPort* const port = CarlaPluginGetAudioInPort(plugin, i);
            inBuffer[i] = port->getBuffer();
        }

        for (uint32_t i=0; i < outCount; i++)
        {
            CarlaEngineAudioPort* const port = CarlaPluginGetAudioOutPort(plugin, i);
            outBuffer[i] = port->getBuffer();
        }

        for (uint32_t i=0; i < inCount; i++)
        {
            for (uint32_t j=0; j < nframes; j++)
            {
                const float absV = std::fabs(inBuffer[i][j]);

                if (absV > inPeaks[i])
                    inPeaks[i] = absV;
            }
        }

        plugin->process(inBuffer, outBuffer, nframes);

        for (uint32_t i=0; i < outCount; i++)
        {
            for (uint32_t j=0; j < nframes; j++)
            {
                const float absV = std::fabs(outBuffer[i][j]);

                if (absV > outPeaks[i])
                    outPeaks[i] = absV;
            }
        }

        setPeaks(plugin->id(), inPeaks, outPeaks);
    }

    void latencyPlugin(CarlaPlugin* const plugin, jack_latency_callback_mode_t mode)
    {
        const uint32_t inCount  = plugin->audioInCount();
        const uint32_t outCount = plugin->audioOutCount();

        jack_latency_range_t range;
        uint32_t pluginLatency = plugin->latency();

        if (pluginLatency == 0)
            return;

        if (mode == JackCaptureLatency)
        {
            for (uint32_t i=0; i < inCount; i++)
            {
                uint aOutI = (i >= outCount) ? outCount : i;
                jack_port_t* const portIn  = ((CarlaEngineJackAudioPort*)CarlaPluginGetAudioInPort(plugin, i))->kPort;
                jack_port_t* const portOut = ((CarlaEngineJackAudioPort*)CarlaPluginGetAudioOutPort(plugin, aOutI))->kPort;

                jackbridge_port_get_latency_range(portIn, mode, &range);
                range.min += pluginLatency;
                range.max += pluginLatency;
                jackbridge_port_set_latency_range(portOut, mode, &range);
            }
        }
        else
        {
            for (uint32_t i=0; i < outCount; i++)
            {
                uint aInI = (i >= inCount) ? inCount : i;
                jack_port_t* const portIn  = ((CarlaEngineJackAudioPort*)CarlaPluginGetAudioInPort(plugin, aInI))->kPort;
                jack_port_t* const portOut = ((CarlaEngineJackAudioPort*)CarlaPluginGetAudioOutPort(plugin, i))->kPort;

                jackbridge_port_get_latency_range(portOut, mode, &range);
                range.min += pluginLatency;
                range.max += pluginLatency;
                jackbridge_port_set_latency_range(portIn, mode, &range);
            }
        }
    }

    // -------------------------------------

    #define handlePtr ((CarlaEngineJack*)arg)

    static int carla_jack_srate_callback(jack_nframes_t newSampleRate, void* arg)
    {
        handlePtr->handleJackSampleRateCallback(newSampleRate);
        return 0;
    }

    static int carla_jack_bufsize_callback(jack_nframes_t newBufferSize, void* arg)
    {
        handlePtr->handleJackBufferSizeCallback(newBufferSize);
        return 0;
    }

    static void carla_jack_freewheel_callback(int starting, void* arg)
    {
        handlePtr->handleJackFreewheelCallback(bool(starting));
    }

    static int carla_jack_process_callback(jack_nframes_t nframes, void* arg)
    {
        handlePtr->handleJackProcessCallback(nframes);
        return 0;
    }

    static void carla_jack_latency_callback(jack_latency_callback_mode_t mode, void* arg)
    {
        handlePtr->handleJackLatencyCallback(mode);
    }

    static void carla_jack_shutdown_callback(void* arg)
    {
        handlePtr->handleJackShutdownCallback();
    }

    #undef handlePtr

    // -------------------------------------

#ifndef BUILD_BRIDGE
    static int carla_jack_process_callback_plugin(jack_nframes_t nframes, void* arg)
    {
        CarlaPlugin* const plugin = (CarlaPlugin*)arg;

        if (plugin != nullptr && plugin->enabled())
        {
            CarlaEngineJack* const engine = (CarlaEngineJack*)CarlaPluginGetEngine(plugin);

            plugin->initBuffers();
            engine->processPlugin(plugin, nframes);
        }

        return 0;
    }

    static void carla_jack_latency_callback_plugin(jack_latency_callback_mode_t mode, void* arg)
    {
        CarlaPlugin* const plugin = (CarlaPlugin*)arg;

        if (plugin != nullptr && plugin->enabled())
        {
            CarlaEngineJack* const engine = (CarlaEngineJack*)CarlaPluginGetEngine(plugin);

            engine->latencyPlugin(plugin, mode);
        }
    }
#endif

    CARLA_DECLARE_NON_COPYABLE_WITH_LEAK_DETECTOR(CarlaEngineJack)
};

// -----------------------------------------

CarlaEngine* CarlaEngine::newJack()
{
    return new CarlaEngineJack();
}

// -----------------------------------------

CARLA_BACKEND_END_NAMESPACE

#endif // CARLA_ENGINE_JACK