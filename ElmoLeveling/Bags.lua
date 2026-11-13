local _, A = ...
local B = {dirty = true, requested = {}, pendingIDs = {}}
A.Bags = B

local function request(id)
    if not A.IsNumber(id) or id < 1 or id % 1 ~= 0 then return end
    B.pendingIDs[id] = true
    local load = C_Item and C_Item.RequestLoadItemDataByID
    if type(load) ~= "function" then return end
    local now = GetTime()
    if B.requested[id] and now - B.requested[id] < 5 then return end
    B.requested[id] = now
    load(id)
end

local function price(info)
    if info.hasNoValue then return 0 end
    local get = C_Item and C_Item.GetItemInfo or GetItemInfo
    local link = info.hyperlink
    if type(get) == "function" and type(link) == "string" and link ~= "" then
        local name, _, _, _, _, _, _, _, _, _, sellPrice = get(link)
        if name and A.IsNumber(sellPrice) and sellPrice % 1 == 0 then return sellPrice end
    end
    request(info.itemID)
end

function B.Scan()
    local state = {value = 0, stacks = 0, items = 0, pending = 0, free = 0, freeKnown = true,
        contents = {}, counts = {}}
    B.pendingIDs = {}
    local container = C_Container
    if not container or type(container.GetContainerNumSlots) ~= "function" or
        type(container.GetContainerItemInfo) ~= "function" then state.pending = 1; state.freeKnown = false
    else
        -- Era backpack and the four equipped bags only, including ammo bags.
        for bag = 0, 4 do
            local slots = container.GetContainerNumSlots(bag)
            if not A.IsNumber(slots) or slots % 1 ~= 0 or (bag == 0 and slots == 0) then
                state.pending = state.pending + 1
                state.freeKnown = false
            else
                if slots > 0 then
                    local free, family = A.Call(container.GetContainerNumFreeSlots, bag)
                    if A.IsNumber(free) and free % 1 == 0 and free <= slots and A.IsNumber(family) and family % 1 == 0 then
                        -- A free arrow/ammo/herb slot cannot hold ordinary loot.
                        if family == 0 then state.free = state.free + free end
                    else state.freeKnown = false end
                end
                for slot = 1, slots do
                    local info = container.GetContainerItemInfo(bag, slot)
                    if not A.IsSecret(info) and type(info) == "table" then
                        state.stacks = state.stacks + 1
                        if A.IsNumber(info.stackCount) and info.stackCount > 0 and info.stackCount % 1 == 0 then
                            state.items = state.items + info.stackCount
                            local unitPrice = price(info)
                            if A.IsNumber(info.itemID) and info.itemID > 0 then
                                local id = info.itemID
                                state.counts[id] = (state.counts[id] or 0) + info.stackCount
                                state.contents[bag .. ":" .. slot] = {id = id, count = info.stackCount,
                                    price = unitPrice, junk = not A.IsSecret(info.quality) and info.quality == 0}
                            end
                            if unitPrice then state.value = state.value + unitPrice * info.stackCount
                            else state.pending = state.pending + 1 end
                        else state.pending = state.pending + 1; request(info.itemID) end
                    elseif type(container.GetContainerItemID) == "function" then
                        local id = container.GetContainerItemID(bag, slot)
                        if id then state.pending = state.pending + 1; request(id) end
                    end
                end
            end
        end
    end
    if state.pending == 0 and A.db.bagBaseline == nil then A.db.bagBaseline = state.value end
    B.state, B.dirty = state, false
end

function B.Update()
    if B.dirty or (B.state and B.state.pending > 0) then B.Scan() end
end

function B.Reset()
    A.db.bagBaseline = nil
    B.Scan()
end

function B.ItemLoaded(id)
    if B.pendingIDs[id] then B.dirty = true end
end

function B.Change()
    if B.state and B.state.pending == 0 and A.db.bagBaseline ~= nil then
        return B.state.value - A.db.bagBaseline
    end
end

-- Sale receipts are tracked separately from the current carried-item value.
do
    local S = {pending = {}, hooked = {}}
    A.Sales = S

    local function copper(value)
        return A.IsNumber(value) and value % 1 == 0 and value or nil
    end
    local function buyback()
        local count = copper(A.Call(GetNumBuybackItems))
        if not count or count > 12 then return end
        local rows = {}
        for i = 1, count do
            local name, _, price, quantity = A.Call(GetBuybackItemInfo, i)
            name, price, quantity = A.Text(name), copper(price), copper(quantity)
            local link = A.Text(A.Call(GetBuybackItemLink, i))
            if not name or not price or not quantity or quantity < 1 then return end
            local id = link and link:match("item:(%d+)") or name
            rows[i] = {key = id .. ":" .. quantity .. ":" .. price, price = price, count = quantity,
                id = link and tonumber(link:match("item:(%d+)")) or nil}
        end
        return rows
    end

    -- Buyback rows are oldest first. Match retained rows in order, so purchases,
    -- eviction of old rows, and repeated MERCHANT_UPDATE events are not sales.
    local function added(old, new)
        local lengths = {[0] = {}}
        for j = 0, #new do lengths[0][j] = 0 end
        for i = 1, #old do
            lengths[i] = {[0] = 0}
            for j = 1, #new do
                lengths[i][j] = old[i].key == new[j].key and lengths[i - 1][j - 1] + 1 or
                    math.max(lengths[i - 1][j], lengths[i][j - 1])
            end
        end
        local i, j, value, fresh = #old, #new, 0, {}
        while j > 0 do
            if i > 0 and old[i].key == new[j].key then i, j = i - 1, j - 1
            elseif i > 0 and lengths[i - 1][j] >= lengths[i][j - 1] then i = i - 1
            else value = value + new[j].price; fresh[#fresh + 1] = new[j]; j = j - 1 end
        end
        return value, fresh
    end

    function S.Init()
        A.db.vendorSales = copper(A.db.vendorSales) or 0
        A.db.vendorSalesPartial = A.db.vendorSalesPartial == true
        S.Hook()
    end

    function S.Request(bag, slot)
        if not S.open or not A.Bags.state then return end
        if not A.IsNumber(bag) or not A.IsNumber(slot) then return end
        local key = tostring(bag) .. ":" .. tostring(slot)
        local item = A.Bags.state.contents[key]
        if item and copper(item.price) then
            S.pending[key] = S.pending[key] or {id = item.id, count = item.count, lost = 0,
                price = item.price, untilTime = GetTime() + 10}
        elseif A.Bags.state.pending > 0 then
            A.db.vendorSalesPartial = true
        end
    end

    function S.Hook()
        if type(hooksecurefunc) ~= "function" then return end
        local function hook(owner, key, callback)
            local identity = tostring(owner) .. ":" .. key
            if S.hooked[identity] or not owner or type(owner[key]) ~= "function" then return end
            local ok = pcall(hooksecurefunc, owner, key, callback)
            if ok then S.hooked[identity] = true end
        end
        -- Read-only post-hooks: never replace or invoke an item-use/sale function.
        hook(C_Container, "UseContainerItem", S.Request)
        hook(_G, "UseContainerItem", S.Request)
        hook(C_Container, "PickupContainerItem", function(bag, slot) S.cursorBag, S.cursorSlot = bag, slot end)
        hook(_G, "PickupContainerItem", function(bag, slot) S.cursorBag, S.cursorSlot = bag, slot end)
        hook(_G, "SellCursorItem", function() S.Request(S.cursorBag, S.cursorSlot); S.cursorBag, S.cursorSlot = nil, nil end)
        hook(C_MerchantFrame, "SellAllJunkItems", function()
            if not S.open or not A.Bags.state then return end
            for key, item in pairs(A.Bags.state.contents) do
                if item.junk then local bag, slot = key:match("^(%-?%d+):(%d+)$"); S.Request(tonumber(bag), tonumber(slot)) end
            end
        end)
    end

    function S.Open()
        S.open, S.pending, S.credits, S.cursorBag, S.cursorSlot = true, {}, 0, nil, nil
        A.Bags.Scan()
        S.rows, S.money, S.counts = buyback(), copper(A.Call(GetMoney)), A.Bags.state.counts
        if not S.rows then A.db.vendorSalesPartial = true end
    end

    function S.Update()
        for key, item in pairs(S.pending) do
            if item.untilTime < GetTime() then
                if item.lost > 0 then A.db.vendorSalesPartial = true end
                S.pending[key] = nil
            end
        end
        if not S.open and not next(S.pending) then return end
        local rows, money, bags = buyback(), copper(A.Call(GetMoney)), A.Bags.state
        if not rows or not bags then A.db.vendorSalesPartial = true; return end
        if not S.rows then S.rows, S.money, S.counts = rows, money, bags.counts; return end
        local value, fresh = added(S.rows, rows)
        -- A full buyback list can look identical after another identical sale, or
        -- retain only 12 rows from a bulk sale. Corroborate observed sale requests
        -- with removed bag quantities and actual received money in those cases.
        local removed = {}
        if bags.pending == 0 then
            for id, count in pairs(S.counts or {}) do removed[id] = math.max(0, count - (bags.counts[id] or 0)) end
        end
        if next(S.pending) and money and S.money then S.credits = (S.credits or 0) + math.max(0, money - S.money) end
        for _, item in pairs(S.pending) do
            local lost = math.min(item.count - item.lost, removed[item.id] or 0)
            item.lost = item.lost + lost
            removed[item.id] = (removed[item.id] or 0) - lost
        end
        -- A visible receipt settles the corresponding request even if the bag
        -- update arrives later. It must never be credited again on PLAYER_MONEY.
        for _, row in ipairs(fresh) do
            local count = row.count
            for _, item in pairs(S.pending) do
                if row.id == item.id then
                    local settled = math.min(count, item.count)
                    item.count, item.lost = item.count - settled, math.max(0, item.lost - settled)
                    count = count - settled
                end
            end
        end
        S.credits = math.max(0, (S.credits or 0) - value)
        local pendingValue = 0
        for _, item in pairs(S.pending) do pendingValue = pendingValue + item.lost * item.price end
        local overflow = #rows == 12 and #fresh > 0
        local corroborated = S.credits == pendingValue and (#rows == 12 or not S.open)
        if pendingValue > 0 and (corroborated or overflow) then
            value = value + pendingValue
            S.credits = math.max(0, S.credits - pendingValue)
            for _, item in pairs(S.pending) do item.count, item.lost = item.count - item.lost, 0 end
        end
        for key, item in pairs(S.pending) do
            if item.count == 0 then S.pending[key] = nil end
        end
        if not next(S.pending) then S.credits = 0 end
        A.db.vendorSales = A.db.vendorSales + value
        S.rows, S.money = rows, money or S.money
        if bags.pending == 0 then S.counts = bags.counts end
    end

    function S.Close()
        S.Update(); S.open = false
    end

    function S.Reset()
        A.db.vendorSales, A.db.vendorSalesPartial = 0, nil
        S.pending, S.credits = {}, 0
        if S.open then S.Open() end
    end
end
