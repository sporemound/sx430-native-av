-- Host-side chdkptp Lua module; sends only CHDK getter scripts to camera.
-- SPDX-License-Identifier: GPL-2.0-or-later
local M = {}
function M.run(count, wait_ms)
    assert(type(count) == 'number' and count >= 1 and count <= 10000 and count % 1 == 0)
    assert(type(wait_ms) == 'number' and wait_ms >= 0 and wait_ms <= 10000)
    assert(con:is_connected(), 'connect using PTP/IP first')
    local platform, sub, id = con:execwait(
        'local b=get_buildinfo(); return b.platform,b.platsub,b.platformid')
    assert(platform == 'sx430is' and sub == '100b' and id == 13013,
        'CHDK build identity mismatch; stop')
    local identity = assert(io.open('identity.txt', 'w'))
    identity:write(platform, '\n', sub, '\n', tostring(id),
        '\nCHDK build identity only; Canon ROM version still requires verification.\n')
    identity:close()
    assert(con:live_is_api_compatible(), 'live-view API unavailable')
    local timing = assert(io.open('timing.csv', 'w'))
    timing:write('index,begin_us,end_us,bytes\n')
    local function now()
        local sec, usec = sys.gettimeofday()
        return sec * 1000000 + usec
    end
    local function telemetry(label)
        local tick, bat, ccd, optical, mv = con:execwait(
            'return get_tick_count(),get_temperature(0),get_temperature(1),get_temperature(2),get_vbatt()')
        local file = assert(io.open('telemetry.txt', 'a'))
        file:write(label, ' tick_ms=', tostring(tick),
            ' battery_C=', tostring(bat), ' sensor_C=', tostring(ccd),
            ' optical_C=', tostring(optical), ' battery_mV=', tostring(mv), '\n')
        file:close()
    end
    local success, err = xpcall(function()
        telemetry('before')
        con:live_dump_start('baseline.lvdump')
        for i=1,count do
            local t0 = now()
            con:live_get_frame(1) -- viewport only; no movie data
            local t1 = now()
            assert(t1 >= t0, 'host clock moved backwards')
            con:live_dump_frame()
            timing:write(string.format('%d,%.0f,%.0f,%d\n', i,t0,t1,con.live._frame:len()))
            timing:flush()
            if i < count then sys.sleep(wait_ms) end
        end
        telemetry('after')
    end, debug.traceback)
    if con.live and con.live.dump_fh then con:live_dump_end() end
    timing:close()
    if not success then error(err) end
    print('SX430_BASELINE_COMPLETE; VIEWPORT ONLY; NO AUDIO')
end
return M
