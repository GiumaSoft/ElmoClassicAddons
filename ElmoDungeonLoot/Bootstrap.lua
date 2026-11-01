local _, CD = ...
_G.ElmoDungeonLoot = CD
CD.version = "2.2.0"

function CD.IsSecret(value)
    return type(issecretvalue) == "function" and issecretvalue(value)
end

function CD.Number(value)
    if CD.IsSecret(value) or type(value) ~= "number" then return nil end
    if value ~= value or value == math.huge or value == -math.huge then return nil end
    return value
end

function CD.Text(value)
    if CD.IsSecret(value) or type(value) ~= "string" then return nil end
    return value
end

function CD.Table(value)
    if not CD.IsSecret(value) and type(value) == "table" then return value end
end

function CD.Bool(value)
    if not CD.IsSecret(value) and type(value) == "boolean" then return value end
end

local function checked(ok, ...)
    if ok then return ... end
end
function CD.Call(fn, ...)
    if type(fn) == "function" then return checked(pcall(fn, ...)) end
end

function CD.Print(message)
    if DEFAULT_CHAT_FRAME then
        DEFAULT_CHAT_FRAME:AddMessage("|cff65dca5ElmoDungeonLoot:|r " .. message)
    end
end

function CD.Now()
    return CD.Number(CD.Call(GetTime)) or 0
end

function CD.Copy(source)
    local result = {}
    for k, v in pairs(source or {}) do result[k] = v end
    return result
end
