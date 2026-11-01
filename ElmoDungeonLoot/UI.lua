local _,CD=...
local U={lootRows={},questRows={}}
CD.UI=U
local W,H=1180,720
local WHITE="Interface\\Buttons\\WHITE8X8"
local MEDIA="Interface\\AddOns\\ElmoDungeonLoot\\Media\\skin\\"
local FONT="Interface\\AddOns\\ElmoDungeonLoot\\Fonts\\Cinzel.ttf"
local BODY=STANDARD_TEXT_FONT or "Fonts\\FRIZQT__.TTF"
local C={gold={1,.82,0},bronze={.47,.36,.14},ink={.94,.92,.86},ink2={.76,.76,.72},
    muted={.51,.51,.48},green={.40,.85,.43},red={1,.36,.32},amber={1,.70,.22},blue={.41,.69,1}}
U.colors=C

local function frame(kind,name,parent)
    return CreateFrame(kind,name,parent,BackdropTemplateMixin and "BackdropTemplate" or nil)
end
local function paint(f,bg,border,alpha)
    f:SetBackdrop({bgFile=WHITE,edgeFile=WHITE,edgeSize=1})
    f:SetBackdropColor(bg[1],bg[2],bg[3],alpha or 1)
    f:SetBackdropBorderColor(border[1],border[2],border[3],1)
end
local function text(parent,size,color,heading)
    local t=parent:CreateFontString(nil,"OVERLAY")
    t:SetFont(heading and FONT or BODY,size,"")
    t:SetTextColor(unpack(C[color or "ink"]))
    t:SetShadowColor(0,0,0,1);t:SetShadowOffset(1,-1)
    t:SetJustifyH("LEFT");t:SetJustifyV("TOP");t:SetWordWrap(true)
    return t
end
local function solid(parent,layer,color,alpha)
    local t=parent:CreateTexture(nil,layer)
    t:SetTexture(WHITE);t:SetVertexColor(unpack(color))
    if alpha then t:SetAlpha(alpha) end
    return t
end
local function line(parent,y,width,color)
    local t=solid(parent,"BORDER",color or C.bronze,.65)
    t:SetPoint("TOPLEFT",0,-y);t:SetSize(width,1)
    return t
end
local function button(parent,label,width)
    local b=frame("Button",nil,parent);b:SetSize(width,26)
    paint(b,{.105,.100,.092},C.bronze)
    b.label=text(b,12,"ink");b.label:SetPoint("LEFT",10,0);b.label:SetPoint("RIGHT",-8,0)
    b.label:SetJustifyV("MIDDLE");b.label:SetText(label)
    b.wash=solid(b,"HIGHLIGHT",C.gold,.13);b.wash:SetAllPoints()
    return b
end
local function height(t,width)
    t:SetWidth(width)
    return math.max(14,t:GetStringHeight() or 14)
end

-- Same dark page, leather corners and bronze trim as TalentsClassic; no dependency on it.
local function skin(f)
    local size,inset=52,15
    local page=f:CreateTexture(nil,"BACKGROUND",nil,-8)
    page:SetTexture(MEDIA.."page.png","REPEAT","REPEAT")
    page:SetPoint("TOPLEFT",inset,-inset);page:SetPoint("BOTTOMRIGHT",-inset,inset)
    local vignette=f:CreateTexture(nil,"BACKGROUND",nil,-7)
    vignette:SetTexture(MEDIA.."vignette.png");vignette:SetAllPoints(page)
    local corners={}
    for _,p in ipairs({{"tl","TOPLEFT"},{"tr","TOPRIGHT"},{"bl","BOTTOMLEFT"},{"br","BOTTOMRIGHT"}}) do
        local t=f:CreateTexture(nil,"BORDER")
        t:SetTexture(MEDIA.."cover-"..p[1]..".png");t:SetSize(size,size);t:SetPoint(p[2]);corners[p[1]]=t
    end
    for _,e in ipairs({{"top","tl","TOPRIGHT","tr","TOPLEFT"},{"bottom","bl","TOPRIGHT","br","TOPLEFT"},
        {"left","tl","BOTTOMLEFT","bl","TOPLEFT"},{"right","tr","BOTTOMLEFT","br","TOPLEFT"}}) do
        local t=f:CreateTexture(nil,"BORDER");t:SetTexture(MEDIA.."cover-"..e[1]..".png")
        if e[1]=="top" or e[1]=="bottom" then
            t:SetPoint("TOPLEFT",corners[e[2]],"TOPRIGHT");t:SetPoint("BOTTOMRIGHT",corners[e[4]],"BOTTOMLEFT")
        else
            t:SetPoint("TOPLEFT",corners[e[2]],"BOTTOMLEFT");t:SetPoint("BOTTOMRIGHT",corners[e[4]],"TOPRIGHT")
        end
    end
end

local function scroller(parent,width,tall)
    local sc=CreateFrame("ScrollFrame",nil,parent)
    sc:SetSize(width,tall)
    local child=CreateFrame("Frame",nil,sc);child:SetSize(width-16,tall)
    sc:SetScrollChild(child);sc.child=child;sc.contentWidth=width-16
    local slider=CreateFrame("Slider",nil,parent)
    slider:SetPoint("TOPLEFT",sc,"TOPRIGHT",-9,0);slider:SetSize(7,tall)
    slider:SetOrientation("VERTICAL");slider:SetMinMaxValues(0,0);slider:SetValueStep(1)
    slider:SetThumbTexture(WHITE)
    local thumb=slider:GetThumbTexture();thumb:SetSize(5,36);thumb:SetVertexColor(.78,.61,.10,.9)
    local track=solid(slider,"BACKGROUND",C.bronze,.22);track:SetAllPoints()
    sc.slider=slider
    function sc:Scroll(value)
        local max=math.max(0,self.child:GetHeight()-self:GetHeight())
        value=math.max(0,math.min(max,value))
        self:SetVerticalScroll(value)
        if math.abs((self.slider:GetValue() or 0)-value)>.1 then self.slider:SetValue(value) end
    end
    function sc:Finish(contentHeight,reset)
        self.child:SetHeight(math.max(self:GetHeight(),contentHeight))
        local max=math.max(0,contentHeight-self:GetHeight())
        self.slider:SetMinMaxValues(0,max);self.slider:SetShown(max>0)
        self:Scroll(reset and 0 or self:GetVerticalScroll())
    end
    slider:SetScript("OnValueChanged",function(_,value) sc:Scroll(value) end)
    sc:EnableMouseWheel(true)
    sc:SetScript("OnMouseWheel",function(_,delta) sc:Scroll(sc:GetVerticalScroll()-delta*46) end)
    sc:SetScript("OnVerticalScroll",function(_,value)
        if math.abs((slider:GetValue() or 0)-value)>.1 then slider:SetValue(value) end
    end)
    return sc
end

local function itemTooltip(row)
    if not row.item then return end
    GameTooltip:SetOwner(row,"ANCHOR_RIGHT")
    local ok=pcall(GameTooltip.SetHyperlink,GameTooltip,row.item.link or "item:"..row.item.id)
    if not ok or (GameTooltip.NumLines and GameTooltip:NumLines()==0) then
        GameTooltip:ClearLines();GameTooltip:AddLine(row.item.name,1,.82,0)
        GameTooltip:AddLine(CD.Items.FormatStats(row.item),1,1,1,true)
        GameTooltip:AddLine("The live item tooltip is loading.",.7,.7,.7,true)
    end
    GameTooltip:Show()
end

local function lootRow(index,sc)
    local row=U.lootRows[index]
    if row then return row end
    row=CreateFrame("Button",nil,sc.child);row:SetWidth(sc.contentWidth)
    row.bg=solid(row,"BACKGROUND",{.15,.14,.12},.32);row.bg:SetAllPoints()
    row.hl=solid(row,"HIGHLIGHT",C.gold,.07);row.hl:SetAllPoints()
    row.rule=line(row,0,sc.contentWidth,C.bronze)
    row.icon=row:CreateTexture(nil,"ARTWORK");row.icon:SetSize(24,24);row.icon:SetPoint("TOPLEFT",4,-8)
    row.title=text(row,12,"ink");row.title:SetPoint("TOPLEFT",36,-8);row.title:SetWidth(166)
    row.req=text(row,12,"ink2");row.req:SetPoint("TOPLEFT",211,-8);row.req:SetWidth(36)
    row.stats=text(row,11,"ink2");row.stats:SetPoint("TOPLEFT",253,-8);row.stats:SetWidth(282)
    row.use=text(row,11,"ink2");row.use:SetPoint("TOPLEFT",545,-8);row.use:SetWidth(91)
    row.heading=text(row,14,"gold",true);row.heading:SetPoint("TOPLEFT",4,-10);row.heading:SetWidth(sc.contentWidth-10)
    row:SetScript("OnEnter",itemTooltip)
    row:SetScript("OnLeave",function() GameTooltip:Hide() end)
    row:SetScript("OnClick",function(self)
        if self.item and IsModifiedClick and IsModifiedClick("CHATLINK") and ChatEdit_InsertLink then
            ChatEdit_InsertLink(self.item.link)
        end
    end)
    U.lootRows[index]=row
    return row
end

function U.RenderLoot(reset)
    if not U.frame then return end
    local sc=U.lootScroll
    local dungeon=CD.Catalog.dungeons[CD.db.lastDungeon]
    local filter,err=CD.Search.Parse(U.search and U.search:GetText() or "")
    local count,offset,drops,total,encounters=0,0,0,0,0
    local hint=(err or "AND between conditions · | for armor / slot alternatives · Click ? for all filters"):gsub("|","||")
    U.searchHint:SetText(hint)
    U.searchHint:SetTextColor(unpack(err and C.red or C.muted))
    local function header(group,shared)
        count=count+1;local row=lootRow(count,sc)
        row:ClearAllPoints();row:SetPoint("TOPLEFT",0,-offset);row:SetHeight(38);row.item=nil
        for _,f in ipairs({row.title,row.req,row.stats,row.use,row.icon}) do f:Hide() end
        local title=group.name
        if group.minLevel then
            title=title.." ("..group.minLevel..(group.maxLevel~=group.minLevel and "–"..group.maxLevel or "")..")"
        end
        if group.kind=="rare" then title=title.."  · Rare" end
        if #group.loot==0 then title=title.."  · No exclusive drops recorded" end
        if shared then title=title.."  · Shared drops" end
        row.heading:SetText(title);row.heading:Show();row.rule:Show();row.bg:Hide();row:Show()
        offset=offset+38
    end
    local function item(it)
        drops=drops+1;count=count+1
        local row=lootRow(count,sc);row.item=it
        row:ClearAllPoints();row:SetPoint("TOPLEFT",0,-offset)
        row.heading:Hide();row.rule:Hide();row.bg:SetShown(drops%2==0)
        for _,f in ipairs({row.title,row.req,row.stats,row.use,row.icon}) do f:Show() end
        local color=ITEM_QUALITY_COLORS and ITEM_QUALITY_COLORS[it.quality]
        row.title:SetText(it.name);row.title:SetTextColor(color and color.r or 1,color and color.g or 1,color and color.b or 1)
        row.icon:SetTexture(it.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
        row.req:SetText((it.level or 0)>0 and it.level or "—")
        row.req:SetTextColor(unpack((it.level or 0)>CD.Items.Character().level and C.red or C.ink2))
        row.stats:SetText(CD.Items.FormatStats(it))
        row.use:SetText(it.useReason);row.use:SetTextColor(unpack(it.usable==true and C.green or it.usable==false and C.red or C.muted))
        local h=math.max(40,height(row.title,166)+16,height(row.stats,282)+16,height(row.use,91)+16)
        row:SetHeight(h);row:Show();offset=offset+h
    end
    for _,section in ipairs({{dungeon.bosses,false},{dungeon.sharedLoot or {},true}}) do
        for _,group in ipairs(section[1]) do
            local matches={}
            for _,entry in ipairs(group.loot) do
                total=total+1
                if filter then
                    local it=CD.Items.Read(entry.id)
                    if CD.Search.Matches(it,filter) then matches[#matches+1]=it end
                end
            end
            if filter and (#matches>0 or not filter.active) then
                header(group,section[2]);encounters=encounters+1
                for _,it in ipairs(matches) do item(it) end
            end
        end
    end
    for i=count+1,#U.lootRows do U.lootRows[i]:Hide();U.lootRows[i].item=nil end
    sc:Finish(offset+8,reset)
    U.lootCount:SetText(drops.." / "..total.." drops · "..encounters.." groups")
    U.searchEmpty:SetText(err and "Fix the search expression above." or
        (total==0 and "No drop table recorded for this dungeon." or "No items match this search in the selected dungeon."))
    U.searchEmpty:SetShown(drops==0)
end

local function questRow(index,sc)
    local row=U.questRows[index]
    if row then return row end
    row=CreateFrame("Button",nil,sc.child);row:SetWidth(sc.contentWidth)
    row.bg=solid(row,"BACKGROUND",{.14,.13,.11},.4);row.bg:SetAllPoints()
    row.hl=solid(row,"HIGHLIGHT",C.gold,.06);row.hl:SetAllPoints()
    row.title=text(row,12,"gold");row.title:SetPoint("TOPLEFT",9,-10);row.title:SetWidth(sc.contentWidth-22)
    row.state=text(row,11,"ink2");row.state:SetWidth(sc.contentWidth-22)
    row.body=text(row,11,"ink2");row.body:SetWidth(sc.contentWidth-22)
    row.chain=text(row,11,"blue");row.chain:SetWidth(sc.contentWidth-22)
    row:SetScript("OnEnter",function(self)
        if not self.quest then return end
        GameTooltip:SetOwner(self,"ANCHOR_LEFT");GameTooltip:ClearLines()
        GameTooltip:AddLine(self.quest.name,1,.82,0)
        GameTooltip:AddLine("Quest #"..self.quest.id.." · Requires level "..self.quest.minLevel,.8,.8,.8,true)
        for _,giver in ipairs(self.quest.givers or {}) do
            GameTooltip:AddLine(giver.name,1,1,1,true)
            for _,loc in ipairs(giver.locations or {}) do
                GameTooltip:AddLine(CD.Quests.LocationText(loc),.76,.76,.72,true)
            end
        end
        if #(self.quest.skill or {})>0 then GameTooltip:AddLine("Profession skill #"..self.quest.skill[1].." · Rank "..self.quest.skill[2],1,.7,.2,true) end
        GameTooltip:AddLine("Click: expand previous steps · Shift-click: link in chat",.4,.7,1,true)
        GameTooltip:Show()
    end)
    row:SetScript("OnLeave",function() GameTooltip:Hide() end)
    row:SetScript("OnClick",function(self)
        if IsModifiedClick and IsModifiedClick("CHATLINK") and ChatEdit_InsertLink then
            ChatEdit_InsertLink(CD.Quests.Link(self.quest));return
        end
        U.expanded[self.quest.id]=not U.expanded[self.quest.id]
        U.RenderQuests()
    end)
    U.questRows[index]=row;return row
end

function U.RenderQuests(reset)
    if not U.frame then return end
    local sc=U.questScroll
    local dungeon=CD.Catalog.dungeons[CD.db.lastDungeon]
    local quests=CD.Quests.List(dungeon)
    local offset=0
    for index,quest in ipairs(quests) do
        local row=questRow(index,sc);row.quest=quest
        row:ClearAllPoints();row:SetPoint("TOPLEFT",0,-offset)
        local title="["..quest.level.."] "..quest.name
        row.title:SetText(title)
        local c=CD.Call(GetQuestDifficultyColor,quest.level) or {r=1,g=.82,b=0}
        row.title:SetTextColor(c.r,c.g,c.b)
        local y=height(row.title,sc.contentWidth-22)+15
        local status,color=CD.Quests.State(quest)
        row.state:ClearAllPoints();row.state:SetPoint("TOPLEFT",9,-y);row.state:SetText(status);row.state:SetTextColor(unpack(C[color] or C.ink2))
        y=y+height(row.state,sc.contentWidth-22)+7
        local body=table.concat(CD.Quests.GiverLines(quest),"\n")
        row.body:ClearAllPoints();row.body:SetPoint("TOPLEFT",9,-y);row.body:SetText(body)
        y=y+height(row.body,sc.contentWidth-22)+8
        local prerequisites=CD.Quests.Prerequisites(quest)
        row.chain:ClearAllPoints();row.chain:SetPoint("TOPLEFT",9,-y)
        if #prerequisites>0 then
            local lines={(U.expanded[quest.id] and "− " or "+ ")..#prerequisites.." previous steps · click to "..(U.expanded[quest.id] and "collapse" or "expand")}
            if U.expanded[quest.id] then
                for _,step in ipairs(prerequisites) do
                    local prefix=CD.Quests.Completed(step.quest.id) and "|cff66d96e[done]|r " or ""
                    lines[#lines+1]=string.rep("  ",step.depth)..step.relation..": "..prefix.."["..step.quest.level.."] "..step.quest.name.." (#"..step.quest.id..")"
                    for _,s in ipairs(CD.Quests.GiverLines(step.quest)) do lines[#lines+1]="    "..s end
                end
            else
                local first=prerequisites[1]
                lines[#lines+1]=first.relation..": "..first.quest.name
            end
            row.chain:SetText(table.concat(lines,"\n"));row.chain:Show()
            y=y+height(row.chain,sc.contentWidth-22)+9
        else row.chain:Hide() end
        row:SetHeight(y+4);row:Show();offset=offset+y+10
    end
    for i=#quests+1,#U.questRows do U.questRows[i]:Hide();U.questRows[i].quest=nil end
    U.emptyQuests:SetShown(#quests==0)
    U.questTitle:SetText("Dungeon quests · "..CD.Items.Character().faction)
    U.questCount:SetText(#quests.." for your character")
    sc:Finish(offset+4,reset)
end

function U.Render(reset)
    if not U.frame then return end
    local dungeon=CD.Catalog.dungeons[CD.db.lastDungeon]
    U.dropdown.label:SetText(dungeon.name)
    local levels=dungeon.levels
    U.description:SetText("Recommended "..table.concat(levels,"–").." · Minimum entry level "..
        (dungeon.minimumLevel or "not recorded"))
    local who=CD.Items.Character()
    U.character:SetText(who.faction.." · "..(who.className or who.class or "Character").." · Level "..who.level)
    U.RenderLoot(reset);U.RenderQuests(reset)
end

function U.Create()
    if U.frame then return end
    local f=frame("Frame","ElmoDungeonLootFrame",UIParent);U.frame=f
    f:SetSize(W,H);f:SetPoint("CENTER");f:SetFrameStrata("HIGH");f:SetClampedToScreen(true)
    f:SetMovable(true);f:EnableMouse(true)
    paint(f,{.025,.025,.025},C.bronze,.98);skin(f)
    local scale=math.min(1,(UIParent:GetWidth()-32)/W,(UIParent:GetHeight()-32)/H)
    f:SetScale(math.max(.4,scale))
    if CD.db.position then
        local p=CD.db.position
        if type(p.x)=="number" and type(p.y)=="number" then
            f:ClearAllPoints();f:SetPoint(p.point or "TOPLEFT",UIParent,p.relative or "TOPLEFT",p.x,p.y)
        end
    end
    U.expanded={}
    local drag=CreateFrame("Frame",nil,f);drag:SetPoint("TOPLEFT",20,-15);drag:SetSize(W-90,45)
    drag:EnableMouse(true);drag:RegisterForDrag("LeftButton")
    drag:SetScript("OnDragStart",function() f:StartMoving() end)
    drag:SetScript("OnDragStop",function()
        f:StopMovingOrSizing()
        local point,_,relative,x,y=f:GetPoint()
        CD.db.position={point=point,relative=relative,x=x,y=y}
    end)
    local title=text(f,20,"gold",true);title:SetPoint("TOPLEFT",28,-24);title:SetText("ElmoDungeonLoot")
    local subtitle=text(f,10,"muted");subtitle:SetPoint("LEFT",title,"RIGHT",14,0);subtitle:SetText("DUNGEON JOURNAL  ·  "..CD.version)
    U.character=text(f,11,"ink2");U.character:SetPoint("TOPRIGHT",-69,-30)
    local close=button(f,"X",27);close:SetPoint("TOPRIGHT",-23,-23)
    close.label:SetJustifyH("CENTER");close.label:ClearAllPoints();close.label:SetAllPoints()
    close:SetScript("OnClick",function() f:Hide() end)
    U.dropdown=button(f,"Select a dungeon",370);U.dropdown:SetPoint("TOPLEFT",28,-75);U.dropdown:SetHeight(32)
    local arrow=text(U.dropdown,14,"gold");arrow:SetPoint("RIGHT",-10,0);arrow:SetText("v")
    U.dropdown.label:SetPoint("RIGHT",-30,0)
    U.description=text(f,12,"ink2");U.description:SetPoint("LEFT",U.dropdown,"RIGHT",20,0)
    local refresh=button(f,"Refresh",80);refresh:SetPoint("TOPRIGHT",-28,-78)
    refresh:SetScript("OnClick",function() CD.Items.Reset();U.Render();CD.QueueItems() end)

    local menu=frame("Frame",nil,f);U.menu=menu
    menu:SetPoint("TOPLEFT",U.dropdown,"BOTTOMLEFT",0,-3);menu:SetSize(370,328)
    menu:SetFrameStrata("DIALOG");menu:SetFrameLevel(f:GetFrameLevel()+30)
    paint(menu,{.035,.033,.028},C.bronze)
    local menuScroll=scroller(menu,358,312);menuScroll:SetPoint("TOPLEFT",6,-7)
    U.options={}
    for index,id in ipairs(CD.Catalog.order) do
        local option=button(menuScroll.child,"",menuScroll.contentWidth);option:SetHeight(29)
        option:SetPoint("TOPLEFT",0,-(index-1)*30)
        local dungeon=CD.Catalog.dungeons[id]
        option.label:SetText(dungeon.name)
        option:SetScript("OnClick",function() menu:Hide();CD.SelectDungeon(id) end)
        option.dungeonID=id;U.options[index]=option
    end
    menuScroll:Finish(#CD.Catalog.order*30,true);menu:Hide()
    U.dropdown:SetScript("OnClick",function() menu:SetShown(not menu:IsShown()) end)

    local left=frame("Frame",nil,f);left:SetPoint("TOPLEFT",28,-124);left:SetSize(674,539)
    local right=frame("Frame",nil,f);right:SetPoint("TOPLEFT",left,"TOPRIGHT",14,0);right:SetSize(436,539)
    paint(left,{.035,.035,.033},{.29,.25,.16});paint(right,{.035,.035,.033},{.29,.25,.16})
    local lootTitle=text(left,15,"gold",true);lootTitle:SetPoint("TOPLEFT",13,-13);lootTitle:SetWidth(150);lootTitle:SetText("Boss loot")
    U.lootCount=text(left,10,"muted");U.lootCount:SetPoint("TOPRIGHT",-14,-18)
    local search=frame("EditBox",nil,left);U.search=search
    search:SetPoint("TOPLEFT",13,-42);search:SetSize(540,28)
    paint(search,{.025,.024,.021},C.bronze)
    search:SetFont(BODY,12,"");search:SetTextColor(unpack(C.ink))
    search:SetTextInsets(9,9,0,0);search:SetAutoFocus(false);search:SetMaxLetters(0)
    search:SetScript("OnEscapePressed",function(self) self:ClearFocus() end)
    search:SetScript("OnEnterPressed",function(self) self:ClearFocus() end)
    local placeholder=text(search,11,"muted");placeholder:SetPoint("LEFT",9,0)
    placeholder:SetText("Name, type, slot or stats: cloth||leather, head||chest, sta >= 5")
    search:SetScript("OnTextChanged",function(self)
        placeholder:SetShown(self:GetText()=="")
        if U.lootScroll then GameTooltip:Hide();U.RenderLoot(true) end
    end)
    search:SetText("")
    local clear=button(left,"Clear",58);U.clearSearch=clear;clear:SetPoint("TOPLEFT",562,-43)
    clear:SetScript("OnClick",function() search:SetText("");search:ClearFocus() end)
    local help=button(left,"?",26);help:SetPoint("TOPLEFT",631,-43)
    help:SetScript("OnEnter",function(self)
        GameTooltip:SetOwner(self,"ANCHOR_RIGHT");GameTooltip:ClearLines()
        GameTooltip:AddLine("Search item names and stats",1,.82,0)
        for _,s in ipairs(CD.Search.HelpLines()) do
            local literal=s:gsub("|","||")
            GameTooltip:AddLine(literal,.85,.85,.8,true)
        end
        GameTooltip:Show()
    end)
    help:SetScript("OnLeave",function() GameTooltip:Hide() end)
    U.searchHint=text(left,10,"muted");U.searchHint:SetPoint("TOPLEFT",13,-79);U.searchHint:SetWidth(644)
    for _,col in ipairs({{"Item",46},{"Req.",221},{"Stats",263},{"Usable",555}}) do
        local t=text(left,11,"ink2");t:SetPoint("TOPLEFT",col[2],-107);t:SetText(col[1])
    end
    local separator=line(left,126,648);separator:ClearAllPoints();separator:SetPoint("TOPLEFT",12,-126)
    U.lootScroll=scroller(left,650,398);U.lootScroll:SetPoint("TOPLEFT",10,-132)
    U.searchEmpty=text(U.lootScroll,12,"muted");U.searchEmpty:SetPoint("TOPLEFT",12,-16);U.searchEmpty:SetWidth(610)
    U.questTitle=text(right,14,"gold",true);U.questTitle:SetPoint("TOPLEFT",13,-13);U.questTitle:SetWidth(400)
    U.questCount=text(right,10,"muted");U.questCount:SetPoint("TOPLEFT",13,-37)
    local qline=line(right,62,410);qline:ClearAllPoints();qline:SetPoint("TOPLEFT",12,-62)
    U.questScroll=scroller(right,412,462);U.questScroll:SetPoint("TOPLEFT",10,-68)
    U.emptyQuests=text(U.questScroll,12,"muted");U.emptyQuests:SetPoint("TOPLEFT",10,-12)
    U.emptyQuests:SetWidth(370);U.emptyQuests:SetText("No dungeon quests recorded for your faction and class.")
    local foot=text(f,10,"muted");foot:SetPoint("BOTTOMLEFT",30,29)
    foot:SetText("Hover an item for its tooltip · Shift-click to link · Quest chains expand on click · Coordinates are map percentages")
    f:SetScript("OnHide",function() menu:Hide();search:ClearFocus();GameTooltip:Hide() end)
    tinsert(UISpecialFrames,"ElmoDungeonLootFrame")
    U.Render(true);f:Hide()
end

function U.Show()
    U.Create();U.Render();U.frame:Show()
end
