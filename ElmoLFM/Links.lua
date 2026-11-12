local _, A = ...
local L = {}
A.Links = L
local edit, wrapped = nil, setmetatable({}, {__mode = "k"})

function L.Insert(text)
    text = A.Text(text)
    if not edit or not edit:IsShown() or not edit:HasFocus() or not text or text == "" then return false end
    if #edit:GetText() + #text > 255 then
        A.Status("The quest link would exceed 255 bytes. Shorten the whisper first.", true)
        return true
    end
    edit:Insert(text)
    return true
end

-- Questie's tracker checks for a native chat window before linking. Its own
-- reusable rows can route this click to our focused editor without changing
-- Blizzard's chat-window getters or the normal untrack action.
function L.AttachQuestie()
    if not QuestieLoader or type(QuestieLoader.ImportModule) ~= "function" then return end
    local pool = A.Call(QuestieLoader.ImportModule, QuestieLoader, "TrackerLinePool")
    local data = A.Call(QuestieLoader.ImportModule, QuestieLoader, "TrackerData")
    if not pool or type(pool.GetLine) ~= "function" or not data or type(data.GetQuestLink) ~= "function" then return end
    local function attach(line)
        local original = line:GetScript("OnClick")
        if type(original) ~= "function" or original == wrapped[line] then return end
        local callback = function(self, button, ...)
            if button == "LeftButton" and self.Quest and IsModifiedClick("CHATLINK") and
                L.Insert(A.Call(data.GetQuestLink, self.Quest)) then return end
            return original(self, button, ...)
        end
        wrapped[line] = callback
        line:SetScript("OnClick", callback)
    end
    for index = 1, 1000 do
        local line = pool.GetLine(index)
        if not line then break end
        if not line.elmoLFMChatHook and type(line.SetOnClick) == "function" then
            hooksecurefunc(line, "SetOnClick", attach)
            line.elmoLFMChatHook = true
        end
        attach(line)
    end
end

function L.Register(editor)
    if edit then return end
    edit = editor
    if ChatFrameUtil and type(ChatFrameUtil.InsertLink) == "function" then
        hooksecurefunc(ChatFrameUtil, "InsertLink", L.Insert)
    elseif type(ChatEdit_InsertLink) == "function" then
        hooksecurefunc("ChatEdit_InsertLink", L.Insert)
    end
    edit:HookScript("OnEditFocusGained", L.AttachQuestie)
end
