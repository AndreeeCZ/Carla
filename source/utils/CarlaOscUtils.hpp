/*
 * Carla OSC utils
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

#ifndef __CARLA_OSC_UTILS_HPP__
#define __CARLA_OSC_UTILS_HPP__

#include "CarlaUtils.hpp"

#include <cstdint>
#include <lo/lo.h>

// -------------------------------------------------

struct CarlaOscData {
    const char* path;
    lo_address source;
    lo_address target;

    CarlaOscData()
        : path(nullptr),
          source(nullptr),
          target(nullptr) {}

    ~CarlaOscData()
    {
        free();
    }

    void free()
    {
        if (path != nullptr)
        {
            delete[] path;
            path = nullptr;
        }

        if (source != nullptr)
        {
            lo_address_free(source);
            source = nullptr;
        }

        if (target != nullptr)
        {
            lo_address_free(target);
            target = nullptr;
        }
    }
};

// -------------------------------------------------

static inline
void osc_send_configure(const CarlaOscData* const oscData, const char* const key, const char* const value)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(key != nullptr);
    CARLA_ASSERT(value != nullptr);
    carla_debug("osc_send_configure(path:\"%s\", \"%s\", \"%s\")", oscData->path, key, value);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && key != nullptr && value != nullptr)
    {
        char targetPath[strlen(oscData->path)+11];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/configure");
        lo_send(oscData->target, targetPath, "ss", key, value);
    }
}

static inline
void osc_send_control(const CarlaOscData* const oscData, const int32_t index, const float value)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(index != -1); // -1 == PARAMETER_NULL
    carla_debug("osc_send_control(path:\"%s\", %i, %f)", oscData->path, index, value);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && index != -1)
    {
        char targetPath[strlen(oscData->path)+9];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/control");
        lo_send(oscData->target, targetPath, "if", index, value);
    }
}

static inline
void osc_send_program(const CarlaOscData* const oscData, const int32_t index)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(index >= 0);
    carla_debug("osc_send_program(path:\"%s\", %i)", oscData->path, index);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && index >= 0)
    {
        char targetPath[strlen(oscData->path)+9];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/program");
        lo_send(oscData->target, targetPath, "i", index);
    }
}

static inline
void osc_send_program(const CarlaOscData* const oscData, const int32_t bank, const int32_t program)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(program >= 0);
    CARLA_ASSERT(bank >= 0);
    carla_debug("osc_send_program(path:\"%s\", %i, %i)", oscData->path, bank, program);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && bank >= 0 && program >= 0)
    {
        char targetPath[strlen(oscData->path)+9];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/program");
        lo_send(oscData->target, targetPath, "ii", bank, program);
    }
}

static inline
void osc_send_midi_program(const CarlaOscData* const oscData, const int32_t index)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(index >= 0);
    carla_debug("osc_send_midi_program(path:\"%s\", %i)", oscData->path, index);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && index >= 0)
    {
        char targetPath[strlen(oscData->path)+14];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/midi_program");
        lo_send(oscData->target, targetPath, "i", index);
    }
}

static inline
void osc_send_midi_program(const CarlaOscData* const oscData, const int32_t bank, const int32_t program)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(program >= 0);
    CARLA_ASSERT(bank >= 0);
    carla_debug("osc_send_midi_program(path:\"%s\", %i, %i)", oscData->path, bank, program);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && bank >= 0 && program >= 0)
    {
        char targetPath[strlen(oscData->path)+14];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/midi_program");
        lo_send(oscData->target, targetPath, "ii", bank, program);
    }
}

static inline
void osc_send_midi(const CarlaOscData* const oscData, const uint8_t buf[4])
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(buf[0] == 0);
    CARLA_ASSERT(buf[1] != 0);
    carla_debug("osc_send_midi(path:\"%s\", 0x%X, %03u, %03u)", oscData->path, buf[1], buf[2], buf[3]);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && buf[0] == 0 && buf[1] != 0)
    {
        char targetPath[strlen(oscData->path)+6];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/midi");
        lo_send(oscData->target, targetPath, "m", buf);
    }
}

static inline
void osc_send_sample_rate(const CarlaOscData* const oscData, const float sampleRate)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(sampleRate > 0.0f);
    carla_debug("osc_send_sample_rate(path:\"%s\", %f)", oscData->path, sampleRate);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && sampleRate > 0.0f)
    {
        char targetPath[strlen(oscData->path)+13];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/sample-rate");
        lo_send(oscData->target, targetPath, "f", sampleRate);
    }
}

#ifdef BUILD_BRIDGE
static inline
void osc_send_update(const CarlaOscData* const oscData, const char* const url)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(url != nullptr);
    carla_debug("osc_send_update(path:\"%s\", \"%s\")", oscData->path, url);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && url != nullptr)
    {
        char targetPath[strlen(oscData->path)+8];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/update");
        lo_send(oscData->target, targetPath, "s", url);
    }
}

static inline
void osc_send_exiting(const CarlaOscData* const oscData)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    carla_debug("osc_send_exiting(path:\"%s\")", oscData->path);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr)
    {
        char targetPath[strlen(oscData->path)+9];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/exiting");
        lo_send(oscData->target, targetPath, "");
    }
}
#endif

static inline
void osc_send_show(const CarlaOscData* const oscData)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    carla_debug("osc_send_show(path:\"%s\")", oscData->path);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr)
    {
        char targetPath[strlen(oscData->path)+6];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/show");
        lo_send(oscData->target, targetPath, "");
    }
}

static inline
void osc_send_hide(const CarlaOscData* const oscData)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    carla_debug("osc_send_hide(path:\"%s\")", oscData->path);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr)
    {
        char targetPath[strlen(oscData->path)+6];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/hide");
        lo_send(oscData->target, targetPath, "");
    }
}

static inline
void osc_send_quit(const CarlaOscData* const oscData)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    carla_debug("osc_send_quit(path:\"%s\")", oscData->path);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr)
    {
        char targetPath[strlen(oscData->path)+6];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/quit");
        lo_send(oscData->target, targetPath, "");
    }
}

// -------------------------------------------------

#ifdef BUILD_BRIDGE_PLUGIN
static inline
void osc_send_bridge_update(const CarlaOscData* const oscData, const char* const url)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(url != nullptr);
    carla_debug("osc_send_bridge_update(path:\"%s\", \"%s\")", oscData->path, url);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && url != nullptr)
    {
        char targetPath[strlen(oscData->path)+15];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/bridge_update");
        lo_send(oscData->target, targetPath, "s", url);
    }
}

static inline
void osc_send_bridge_error(const CarlaOscData* const oscData, const char* const error)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(error != nullptr);
    carla_debug("osc_send_bridge_error(path:\"%s\", \"%s\")", oscData->path, error);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && error != nullptr)
    {
        char targetPath[strlen(oscData->path)+14];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/bridge_error");
        lo_send(oscData->target, targetPath, "s", error);
    }
}
#endif

#if defined(BRIDGE_LV2) || defined(WANT_LV2)
static inline
void osc_send_lv2_transfer_atom(const CarlaOscData* const oscData, const int32_t portIndex, const char* const typeStr, const char* const atomBuf)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(portIndex >= 0);
    CARLA_ASSERT(typeStr != nullptr);
    CARLA_ASSERT(atomBuf != nullptr);
    carla_debug("osc_send_lv2_transfer_atom(path:\"%s\", %i, \"%s\", <atomBuf:%p>)", oscData->path, portIndex, typeStr, atomBuf);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && portIndex >= 0 && typeStr != nullptr && atomBuf != nullptr)
    {
        char targetPath[strlen(oscData->path)+19];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/lv2_atom_transfer");
        lo_send(oscData->target, targetPath, "iss", portIndex, typeStr, atomBuf);
    }
}

static inline
void osc_send_lv2_transfer_event(const CarlaOscData* const oscData, const int32_t portIndex, const char* const typeStr, const char* const atomBuf)
{
    CARLA_ASSERT(oscData != nullptr && oscData->path != nullptr);
    CARLA_ASSERT(portIndex >= 0);
    CARLA_ASSERT(typeStr != nullptr);
    CARLA_ASSERT(atomBuf != nullptr);
    carla_debug("osc_send_lv2_transfer_event(path:\"%s\", %i, \"%s\", <atomBuf:%p>)", oscData->path, portIndex, typeStr, atomBuf);

    if (oscData != nullptr && oscData->path != nullptr && oscData->target != nullptr && portIndex >= 0 && typeStr != nullptr && atomBuf != nullptr)
    {
        char targetPath[strlen(oscData->path)+20];
        strcpy(targetPath, oscData->path);
        strcat(targetPath, "/lv2_event_transfer");
        lo_send(oscData->target, targetPath, "iss", portIndex, typeStr, atomBuf);
    }
}
#endif

// -------------------------------------------------

#endif // __CARLA_OSC_UTILS_HPP__