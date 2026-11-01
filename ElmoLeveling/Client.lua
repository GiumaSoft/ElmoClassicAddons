local _, A = ...
if not A.flavor then
    local interface = type(GetBuildInfo) == "function" and select(4, GetBuildInfo()) or 11509
    A.flavor = interface == 16001 and "forever" or "classic"
end
