-- Optional host-only tests run under chdkptp's Lua runtime, without a camera.
-- Set SX430_PROJECT_ROOT to the repository; run in a fresh scratch directory.
local root=assert(os.getenv('SX430_PROJECT_ROOT'),'Set SX430_PROJECT_ROOT')
local function baseline_case(wrong)
    local frame_count,ended,queries,t=0,false,0,0
    con={live={_frame={len=function() return 124 end}}}
    function con:is_connected() return true end
    function con:execwait(code)
        queries=queries+1
        if queries==1 then return wrong and 'other' or 'sx430is','100b',13013 end
        return 100,20,21,22,3900
    end
    function con:live_is_api_compatible() return true end
    function con:live_dump_start() self.live.dump_fh=true end -- nil is success
    function con:live_get_frame(flags) assert(flags==1) end
    function con:live_dump_frame() frame_count=frame_count+1 end
    function con:live_dump_end() ended=true;self.live.dump_fh=nil end
    sys={gettimeofday=function() t=t+100;return 0,t end,sleep=function() end}
    local ok=pcall(function() dofile(root..'/camera/baseline.lua').run(2,0) end)
    assert(ok~=wrong)
    if wrong then assert(frame_count==0 and queries==1) else assert(frame_count==2 and ended and queries==3) end
end
baseline_case(false);baseline_case(true)
print('PASS baseline r1528 nil-success APIs and identity rejection')

local fixture='host-candidate-fixture.lua'
local f=assert(io.open(fixture,'w'));f:write('return "fixture"');f:close()
local runner=dofile(root..'/camera/experimental/run-mode.lua')
for _,kind in ipairs({'success','guard','incomplete','identity'}) do
    local output='host-candidate-result-'..kind..'.csv'
    os.remove(output)
    local calls,closed=0,false
    con={}
    function con:is_connected() return not closed end
    function con:disconnect() closed=true end
    function con:execwait(code,opts)
        calls=calls+1
        if calls==1 then return kind=='identity' and 'other' or 'sx430is','100b',13013 end
        assert(opts.timeout==20000 and code:find('local sx430_ptpip_test=true',1,true))
        if kind=='guard' then return 'BEGIN\nERROR,refused\nDONE\n' end
        if kind=='incomplete' then return 'BEGIN\n' end
        return 'BEGIN\nRESULT,STABLE_RECORD_OBSERVED\nDONE\n'
    end
    local ok=pcall(function() runner.run(fixture,output) end)
    assert(closed and ok==(kind=='success'))
    local saved=io.open(output,'r')
    assert((saved~=nil)==(kind=='success' or kind=='guard'))
    if saved then saved:close() end
    print('PASS experimental host '..kind)
end
print('PUBLIC_HOST_TESTS_PASSED')
