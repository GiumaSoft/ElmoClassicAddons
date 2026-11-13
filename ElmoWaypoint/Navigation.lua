local _, A = ...
local function xy(vector)
    if A.Private(vector) or type(vector) ~= "table" and type(vector) ~= "userdata" then return end
    local x, y = A.Call(function() return vector:GetXY() end)
    return A.Number(x), A.Number(y)
end
local function world(map, position)
    local continent, vector = A.Call(C_Map and C_Map.GetWorldPosFromMapPos, map, position)
    local north, west = xy(vector)
    return A.Number(continent), north, west
end
function A.PlayerPosition()
    local here = A.Number(A.Call(C_Map and C_Map.GetBestMapForUnit, "player"))
    if not here or here <= 0 or here % 1 ~= 0 then return end
    local position = A.Call(C_Map and C_Map.GetPlayerMapPosition, here, "player")
    local px, py = xy(position)
    if not px or not py or px < 0 or px > 1 or py < 0 or py > 1 then return end
    return {mapID = here, x = px, y = py, vector = position}
end
function A.Navigation(point, position)
    if not position then return {status = "Position unavailable"} end
    local destination = A.Call(CreateVector2D, point.x, point.y)
    if not destination then return {status = "Position unavailable"} end
    local hereContinent, north, west = world(position.mapID, position.vector)
    local thereContinent, targetNorth, targetWest = world(point.mapID, destination)
    if not hereContinent or not thereContinent or not north or not west or not targetNorth or not targetWest then
        return {status = "Position unavailable"}
    end
    if hereContinent ~= thereContinent then return {status = "Different continent"} end
    local dn, dw = targetNorth - north, targetWest - west
    local distance = A.Number(math.sqrt(dn * dn + dw * dw))
    if not distance then return {status = "Position unavailable"} end
    if distance <= 8 then return {angle = 0, distance = distance, arrived = true} end
    local facing = A.Number(A.Call(GetPlayerFacing))
    if not facing then return {status = "Facing unavailable", distance = distance} end
    -- Native world x points north, y points west. Facing uses north=0 with
    -- positive angles toward west. Subtract the player's facing, then normalize.
    local angle = (math.atan2(dw, dn) - facing + math.pi) % (2 * math.pi) - math.pi
    return {angle = angle, distance = distance}
end
