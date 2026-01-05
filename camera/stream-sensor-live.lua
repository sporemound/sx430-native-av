-- Host-side chdkptp live sensor streaming script for OBS Studio
-- Direct Sensor LiveView Stream | Zero SD Writes | Continuous Uptime
local ticks = require('ticktime')

local function note(s)
    local f = io.open('stream-status.txt', 'w')
    if f then f:write(s, '\n'); f:close() end
end

local function run()
    local p, s, id, rev = con:execwait('local b=get_buildinfo(); return b.platform,b.platsub,b.platformid,b.build_revision')
    assert(p=='sx430is' and s=='100b' and id==13013 and tostring(rev)=='6357', 'Camera identity mismatch')

    local r, v, m = con:execwait('return get_mode()')
    pcall(function() con:execwait('set_auto_off(0)') end)

    -- Switch camera to Shooting/Live Sensor mode (extends lens, starts live sensor DMA)
    if not r then
        note("SWITCHING_TO_SENSOR_MODE")
        con:execwait([[
            switch_mode_usb(true)
            sleep(100)
            pcall(call_func_ptr, 0xff05f154, 0x105f, 0)
            for i=1,35 do
                sleep(100)
                local r_s, v_s = get_mode()
                local pr = peek(0x3ac8, 4)
                local cc = peek(0x23cc, 4)
                if r_s and pr==2 and cc==1 then break end
            end
        ]])
    end

    sys.sleep(200)
    assert(con:live_is_api_compatible(), 'Live display API incompatible')
    note("CAMERA_CONNECTED")

    local vf = assert(io.open('stream_video.bin', 'ab'))
    local lv = con.live
    local frames_received = 0

    -- Reusable C image buffers for maximum performance
    local pimg = nil
    local lb = nil
    local hdr = nil
    local last_w, last_h = 0, 0

    while true do
        local ok, err = con:live_get_frame_pcall(1)
        if not ok then
            note('STREAM_ERROR: ' .. tostring(err))
            break
        end

        -- Extract native square-pixel RGB frame
        pimg = liveimg.get_viewport_pimg(pimg, lv._frame, true)
        if pimg then
            local w = pimg:width()
            local h = pimg:height()
            if w ~= last_w or h ~= last_h then
                hdr = string.format('P6\n%d %d\n255\n', w, h)
                last_w = w
                last_h = h
            end
            vf:write(hdr)
            lb = pimg:to_lbuf_packed_rgb(lb)
            lb:fwrite(vf)
            vf:flush()
            frames_received = frames_received + 1
            if frames_received % 10 == 0 then
                note(string.format('STAT_V,%d,%d', frames_received, w * h * 3))
            end
        end
        sys.sleep(0)
    end
    vf:close()
end

local ok, err = pcall(run)
if not ok then note('FATAL_STREAM_ERROR: ' .. tostring(err)) end
if con:is_connected() then pcall(function() con:disconnect() end) end
