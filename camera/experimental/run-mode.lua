-- SPDX-License-Identifier: GPL-2.0-or-later
-- Host-side chdkptp r1528; paths and connection supplied by the operator.
local M={}
function M.run(candidate_path,output_path)
    assert(type(candidate_path)=='string' and type(output_path)=='string','Supply input and output paths')
    assert(con:is_connected(),'Connect with PTP/IP first')
    local existing=io.open(output_path,'r')
    if existing then existing:close();error('Choose a fresh output filename') end
    local function run()
        local input=assert(io.open(candidate_path,'r'))
        local code=input:read('*a');input:close()
        local p,s,id=con:execwait('local b=get_buildinfo(); return b.platform,b.platsub,b.platformid')
        assert(p=='sx430is' and s=='100b' and id==13013,'Wrong camera')
        local result=con:execwait('local sx430_ptpip_test=true\n'..code,{timeout=20000})
        assert(type(result)=='string' and result:match('DONE\n$'),'Incomplete result; preserve card log')
        local out=assert(io.open(output_path,'w'));out:write(result);out:close()
        assert(not result:find('\nERROR,',1,true),'Candidate stopped; review saved result')
        print(result:match('RESULT,([^\n]+)') or 'No acceptance result')
    end
    local ok,err=pcall(run)
    if con:is_connected() then pcall(function() con:disconnect() end) end
    if not ok then error(err) end
end
return M
