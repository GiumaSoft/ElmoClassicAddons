local _,A=...
_G.ElmoSpellTracker=A
_G.ClassicCooldownTracker=A -- compatibility for existing integrations
A.version="1.0.3"
A.DEFAULT_LIMIT=10
A.HARD_LIMIT=12

local function result(ok,...)
    if ok then return ... end
end
function A.Call(fn,...)
    if type(fn)=="function" then return result(pcall(fn,...)) end
end
function A.Secret(value)
    return type(issecretvalue)=="function" and issecretvalue(value)
end
function A.Number(value)
    if not A.Secret(value) and type(value)=="number" and value==value and value~=math.huge and value~=-math.huge then return value end
end
function A.Text(value)
    if not A.Secret(value) and type(value)=="string" then return value end
end
function A.Bool(value)
    if not A.Secret(value) and type(value)=="boolean" then return value end
end
function A.Now() return A.Number(A.Call(GetTime)) or 0 end
function A.Print(message)
    if DEFAULT_CHAT_FRAME then DEFAULT_CHAT_FRAME:AddMessage("|cffffd100ElmoSpellTracker:|r "..message) end
end
