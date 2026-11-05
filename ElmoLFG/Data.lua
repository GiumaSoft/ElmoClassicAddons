local _, A = ...

-- Era entry requirements, not Dungeon Finder ranges or Cataclysm MapDifficulty.
-- Direct Era observations: Bren0man, https://www.wowhead.com/classic/pt/guide/classic-dungeons-overview#comments
-- In particular SFK/BFD = 10, Gnomeregan/RFK = 15, SM = 20.
-- Recommended ranges describe a normal group; they never restrict selection.
A.dungeons = {
    { id = "rfc", name = "Ragefire Chasm", min = 8, low = 13, high = 18, aliases = { "rfc", "ragefire" }, note = "Entrance in Orgrimmar, Horde territory." },
    { id = "dm", name = "The Deadmines", min = 10, low = 18, high = 23, aliases = { "deadmines", "vc", "dm" }, note = "Entrance in Westfall." },
    { id = "wc", name = "Wailing Caverns", min = 10, low = 17, high = 25, aliases = { "wc", "wailing" }, note = "Entrance in the Barrens." },
    { id = "sfk", name = "Shadowfang Keep", min = 10, low = 22, high = 30, aliases = { "sfk", "shadowfang" } },
    { id = "bfd", name = "Blackfathom Deeps", min = 10, low = 24, high = 32, aliases = { "bfd", "blackfathom" } },
    { id = "stocks", name = "The Stockade", min = 15, low = 22, high = 30, aliases = { "stocks", "stockades", "stockade" }, note = "Entrance in Stormwind, Alliance territory." },
    { id = "gnomer", name = "Gnomeregan", min = 15, low = 29, high = 38, aliases = { "gnomer", "gnomeregan" } },
    { id = "rfk", name = "Razorfen Kraul", min = 15, low = 30, high = 40, aliases = { "rfk", "razorfen kraul" } },
    { id = "smgy", name = "Scarlet Monastery - Graveyard", min = 20, low = 28, high = 38, aliases = { "sm", "sm gy", "sm graveyard", "scarlet monastery" } },
    { id = "smlib", name = "Scarlet Monastery - Library", min = 20, low = 29, high = 39, aliases = { "sm", "sm lib", "sm library", "scarlet monastery" } },
    { id = "smarm", name = "Scarlet Monastery - Armory", min = 20, low = 32, high = 42, aliases = { "sm", "sm arm", "sm armory", "scarlet monastery" }, note = "Door: Scarlet Key or another way for your group to open it." },
    { id = "smcath", name = "Scarlet Monastery - Cathedral", min = 20, low = 35, high = 45, aliases = { "sm", "sm cath", "sm cathedral", "scarlet monastery" }, note = "Door: Scarlet Key or another way for your group to open it." },
    { id = "rfd", name = "Razorfen Downs", min = 25, low = 40, high = 50, aliases = { "rfd", "razorfen downs" } },
    { id = "ulda", name = "Uldaman", min = 30, low = 42, high = 52, aliases = { "ulda", "uldaman" } },
    { id = "mara", name = "Maraudon", min = 30, low = 46, high = 55, aliases = { "mara", "maraudon" } },
    { id = "zf", name = "Zul'Farrak", min = 35, low = 44, high = 54, aliases = { "zf", "zul farrak", "zulfarrak" } },
    { id = "st", name = "Sunken Temple", min = 35, low = 50, high = 60, aliases = { "st", "sunken temple", "atal hakkar" } },
    { id = "brd", name = "Blackrock Depths", min = 40, low = 52, high = 60, aliases = { "brd", "blackrock depths" }, note = "Some routes require the Shadowforge Key or another way for your group to open the doors." },
    { id = "lbrs", name = "Lower Blackrock Spire", min = 45, low = 55, high = 60, aliases = { "lbrs", "lower blackrock" } },
    { id = "ubrs", name = "Upper Blackrock Spire", min = 45, low = 58, high = 60, aliases = { "ubrs", "upper blackrock" }, note = "Up to 10 players. A group member must open the door with the Seal of Ascension." },
    { id = "dme", name = "Dire Maul - East", min = 45, low = 55, high = 60, aliases = { "dire maul", "dme", "dm e", "dm east" } },
    { id = "dmw", name = "Dire Maul - West", min = 45, low = 58, high = 60, aliases = { "dire maul", "dmw", "dm w", "dm west" }, note = "Door: Crescent Key or another way for your group to open it." },
    { id = "dmn", name = "Dire Maul - North", min = 45, low = 58, high = 60, aliases = { "dire maul", "dmn", "dm n", "dm north", "dm tribute", "dmt" }, note = "Door: Crescent Key or another way for your group to open it." },
    { id = "scholo", name = "Scholomance", min = 45, low = 58, high = 60, aliases = { "scholo", "scholomance" }, note = "Door: Skeleton Key or another way for your group to open it." },
    { id = "stratlive", name = "Stratholme - Living", min = 45, low = 58, high = 60, aliases = { "strat", "stratholme", "strat live", "strat living" } },
    { id = "stratud", name = "Stratholme - Undead", min = 45, low = 58, high = 60, aliases = { "strat", "stratholme", "strat ud", "strat undead", "strat dead" }, note = "Service entrance: a group member needs the Key to the City. Also accessible from the Living side." },
}
