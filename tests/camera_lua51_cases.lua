-- Lua 5.1 camera scheduler simulation; firmware and I/O are mocked.
local source=assert(candidate_source)
local fingerprint={}
for a,v in source:gmatch('{(0x%x+),(0x%x+)},') do fingerprint[tonumber(a)]=tonumber(v) end
local function run_case(name,opt)
    local tick,r,pr,cc,flag,pending=0,false,3,2,1,0
    if opt.initial_wait or opt.initial_stuck then cc=9 end
    local request,native,changes,rom_reads=nil,0,0,0
    sx430_ptpip_test=not opt.direct_sd
    function get_buildinfo() return {platform=opt.wrong_camera and 'other' or 'sx430is',platsub='100b',platformid=13013,build_revision=opt.wrong_build and '6307' or '6357'} end
    function get_config_value(id) assert(id==1999);return opt.disabled and 0 or 1 end
    function get_mode() return r,false,r and 257 or 513 end
    function get_tick_count() return tick end
    function get_vbatt() return opt.low_battery and 3300 or 3900 end
    function peek(addr,size)
        assert(size==4)
        if fingerprint[addr] then
            assert(changes==0,'ROM verification occurred after mode change')
            rom_reads=rom_reads+1
            return fingerprint[addr]+((opt.corrupt_rom and addr==0xff05f154) and 1 or 0)
        end
        local w={[0x3ac8]=pr,[0x23cc]=cc,[0x2410]=flag,[0x2414]=pending,[0x28d4]=0,[0x25848]=544,[0x3d34]=0}
        assert(w[addr]~=nil,'Unexpected memory read');return w[addr]
    end
    function sleep(ms)
        tick=tick+ms
        if opt.initial_wait and not request and cc==9 and tick>=1000 then cc=2 end
        if request and tick-request>=1200 then
            if flag==0 and not opt.reversed then r=true;pr=2;cc=1 else r=false;pr=3;cc=2 end
        end
        coroutine.yield()
    end
    function switch_mode_usb(value)
        assert(rom_reads==381,'All firmware words must match before mode change')
        changes=changes+1
        if value then
            assert(not r and cc==2);request=tick;pr=opt.state8 and 1 or 3;cc=opt.guard_refused and 15 or (opt.state8 and 8 or 12)
        else assert(pr==2 and cc==1,'Redundant return-to-playback');request=nil;r=false;pr=3;cc=2;flag=1 end
    end
    function call_func_ptr(addr,event,arg)
        assert(addr==0xff05f154 and event==0x105f and arg==0)
        assert(request and tick-request==100 and flag==1 and ((pr==3 and cc==12) or (pr==1 and cc==8)))
        native=native+1;assert(native==1,'Repeated native call')
        if opt.native_error then error('simulated native API error') end
        if not opt.ignored then flag=0;pending=1 end
        return 12345 -- Deliberately not a success code.
    end
    local closed=false
    io.open=function(path,mode)
        assert(path=='A/WFNATIVE.CSV' and mode=='a')
        return {write=function() end,flush=function() end,close=function() closed=true end}
    end
    local co=coroutine.create(assert(loadstring(source)))
    local ok,result
    local resumes=0
    repeat
        ok,result=coroutine.resume(co)
        resumes=resumes+1;assert(resumes<200,'Scheduler did not finish')
    until not ok or coroutine.status(co)=='dead'
    if not opt.direct_sd and not opt.wrong_camera and not opt.wrong_build and not opt.disabled and not opt.corrupt_rom then assert(closed) end
    local before=opt.direct_sd or opt.wrong_camera or opt.wrong_build or opt.disabled or opt.corrupt_rom
    if before then assert(not ok and changes==0 and native==0)
    else
        assert(ok,result)
        assert(result:match('DONE\n$'))
        for row in result:gmatch('[^\n]+') do
            if row:match('^initial,') or row:match('^observe,') or row:match('^wait_initial_playback,') then
                local _,commas=row:gsub(',','')
                assert(commas==12,'Snapshot must have exactly 13 columns')
                assert(not row:find('Memory read failed',1,true),'assert message leaked into CSV')
            end
        end
        local guarded=opt.low_battery or opt.guard_refused or opt.initial_stuck
        assert(native==(guarded and 0 or 1))
        if guarded or opt.ignored or opt.native_error then
            assert(result:find('\nERROR,',1,true))
        elseif opt.reversed then assert(result:find('RESULT,NO_STABLE_RECORD',1,true))
        else assert(result:find('RESULT,STABLE_RECORD_OBSERVED',1,true)) end
        assert(not r,'Cleanup left simulated camera in shooting')
        assert(changes==((opt.low_battery or opt.initial_stuck) and 0 or ((opt.guard_refused or opt.ignored or opt.native_error or opt.reversed) and 1 or 2)))
        assert(tick<=10000,'Test exceeded short-session budget')
    end
    print('PASS '..name)
end
run_case('successful change and normal cleanup',{})
run_case('state 8 transition and normal cleanup',{state8=true})
run_case('pairing playback initialization settles',{initial_wait=true})
run_case('playback initialization never settles',{initial_stuck=true})
run_case('firmware reverses after handler',{reversed=true})
run_case('handler result missing',{ignored=true})
run_case('native API throws',{native_error=true})
run_case('transition guard refuses',{guard_refused=true})
run_case('low battery stops before request',{low_battery=true})
run_case('native calls disabled',{disabled=true})
run_case('wrong camera rejected',{wrong_camera=true})
run_case('different CHDK build rejected',{wrong_build=true})
run_case('changed ROM word rejected',{corrupt_rom=true})
run_case('direct SD launch refused',{direct_sd=true})
print('NATIVE_MODE_SIMULATION_PASSED')
