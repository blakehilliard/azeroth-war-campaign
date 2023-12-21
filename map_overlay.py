import enum
import typing
import dataclasses

from PIL import Image, ImageDraw

#TODO: put C,S,P,Z in data, not in string


class FactionEnum(enum.StrEnum):
    ALLIANCE = "Alliance"
    HORDE = "Horde"


class ContinentEnum(enum.StrEnum):
    KALIMDOR = "Kalimdor"
    EASTERN_KINGDOMS = "Eastern Kingdoms"


class ZoneEnum(enum.StrEnum):
    ASHENVALE = "Ashenvale"
    BARRENS = "Barrens"
    DARKSHORE = "Darkshore"
    STONETALON_MOUNTAINS = "Stonetalon Mountains"


@dataclasses.dataclass
class Continent:
    continent: ContinentEnum
    high_res_map: str
    low_res_map: str

    def get_name(self):
        return self.continent.value


@dataclasses.dataclass
class Zone:
    zone: ZoneEnum
    continent: Continent
    # These are the furthest point, in pixels, of the zone on its continent map
    west_edge: int 
    north_edge: int
    east_edge: int
    south_edge: int

    def get_name(self):
        return self.zone.value


@dataclasses.dataclass
class Territory:
    name: str
    zone: ZoneEnum
    coords: typing.Sequence[tuple[int, int]]


@dataclasses.dataclass
class Guild:
    name: str
    initials: str
    faction: FactionEnum
    controlled: typing.Sequence[str] # territory names

    def controls(self, territory_name: str) -> bool:
        return territory_name in self.controlled


def get_fill_color_of_territory(
    territory: Territory,
    guilds: typing.Sequence[Guild],
) -> str:

    for guild in guilds:
        if guild.controls(territory.name):
            if guild.faction == FactionEnum.HORDE:
                return "red"
            else:
                return "blue"
    return "grey"


def get_controlling_guild_of_territory(
    territory: Territory,
    guilds: typing.Sequence[Guild],
) -> Guild:
    for guild in guilds:
        if guild.controls(territory.name):
            return guild
    return None

def get_centroid(coords: typing.Sequence[tuple[int, int]]) -> tuple[int, int]:
    return (
        sum([n[0] for n in coords]) / len(coords),
        sum([n[1] for n in coords]) / len(coords),
    )


def make_zone_map(
    continent_image: Image,
    zone: Zone,
) -> Image:

    img = continent_image.crop((zone.west_edge, zone.north_edge, zone.east_edge, zone.south_edge))
    dest_path = zone.get_name() + ".jpg"
    img.save(dest_path, optimize=True)
    return img


def make_continent_map(
    continent: Continent,
    zones: typing.Sequence[Zone],
    all_territories: typing.Sequence[Territory],
    guilds: typing.Sequence[Guild],
) -> Image:

    Image.open(continent.high_res_map).save(continent.low_res_map, optimize=True, quality=10)

    continent_territories = []
    for territory in all_territories:
        zone = next(z for z in zones if z.zone == territory.zone)
        if zone.continent == continent:
            continent_territories.append(territory)

    img = generate_overlayed_map(continent.low_res_map, continent_territories, guilds)
    dest_path = continent.get_name() + ".jpg"
    img.save(dest_path, optimize=True)
    return img


def generate_overlayed_map(
    unedited_map_path: str,
    territories: typing.Sequence[Territory],
    guilds: typing.Sequence[Guild],
) -> Image:

    unedited_map_img = Image.open(unedited_map_path)

    # Blend in semi-transparent territory colors
    territory_overlay_img = unedited_map_img.copy()
    draw = ImageDraw.Draw(territory_overlay_img)
    for territory in territories:
        fill = get_fill_color_of_territory(territory, guilds)
        #draw.polygon(territory.coords, fill=fill, outline="black", width=5)
        draw.polygon(territory.coords, fill=fill)
    img = Image.blend(unedited_map_img, territory_overlay_img, 0.3)

    # Add text on top
    draw = ImageDraw.Draw(img)
    for territory in territories:
        draw.polygon(territory.coords, outline="black", width=4)
        text = territory.name
        guild = get_controlling_guild_of_territory(territory, guilds)
        if guild is not None:
            text += "\n<" + guild.initials + ">"
        centroid = get_centroid(territory.coords)
        #draw.text(centroid, text, align="center", anchor="mm", fill="black", font_size=20)
        anchor = "mm"
        font_size = 20
        align = "center"
        left, top, right, bottom = draw.textbbox(centroid, text, anchor=anchor, font_size=font_size, align=align)
        draw.rectangle((left-1, top-1, right+1, bottom+1), fill="white")
        draw.text(centroid, text, align=align, anchor=anchor, font_size=font_size, fill="black")

    return img


def assert_sanity(territories: typing.Sequence[Territory], guilds: typing.Sequence[Guild]):
    for guild in guilds:
        for territory_name in guild.controlled:
            for territory in territories:
                if territory.name == territory_name:
                    break
            else:
                raise Exception("Guild '%s' controls unknown territory '%s'" % (guild.name, territory_name))


def main():
    kalimdor = Continent(ContinentEnum.KALIMDOR, "highres\\wow_classic_high_resolution_world_terrain_map_kalimdor.png", "lowres_kalimdor.jpg")
    continents = (kalimdor,)
    zones = (
        Zone(ZoneEnum.ASHENVALE, kalimdor, 1873, 3822, 4557, 5402),
        Zone(ZoneEnum.BARRENS, kalimdor, 2901, 5136, 6760, 8413),
    )
    guilds = (
        Guild("Red Sand Charter", "RSC", FactionEnum.HORDE, (
            "Ratchet",
            "Merchant Coast",
            "Raptor Grounds",
            "Fray Island",
            "Northwatch Hold",
        )),
        Guild("Dwarven Overlords", "DO", FactionEnum.ALLIANCE, (
            "Shady Rest Inn",
            "Bael'dun Keep",
        )),
        Guild("Azeroth Adventurer Guild", "AAG", FactionEnum.ALLIANCE, (
            "Roadside Inn",
            "Maestra's Post",
            "Bathran's Haunt",
            "Ruins of Ordil'Aran",
            "Lake Falanthim",
        )),
        Guild("Dragonforged", "DF", FactionEnum.HORDE, (
            "Warsong Lumber Camp",
            "Felfire Hill",
        )),
        Guild("Fires of Elune", "FoE", FactionEnum.ALLIANCE, (
            "Silverwing Outpost",
        )),
    )
    territories = (
        # -- ASHENVALE -- #
        # Ashenvale Western Coast
        Territory("Zoram'gar Outpost", ZoneEnum.ASHENVALE, ((2000, 4250), (2000, 4450), (2300, 4450), (2300, 4250))),
        Territory("The Zoram Strand", ZoneEnum.ASHENVALE, ((2000, 4050), (2000, 4250), (2300, 4250), (2300, 4050))),
        Territory("Blackfathom Depths", ZoneEnum.ASHENVALE, ((2000, 3850), (2000, 4050), (2300, 4050), (2300, 3850))),
        # Ashenvale West
        Territory("Maestra's Post", ZoneEnum.ASHENVALE, ((2420, 4350), (2420, 4500), (2570, 4500), (2570, 4350))),
        Territory("Bathran's Haunt", ZoneEnum.ASHENVALE, ((2550, 4050), (2550, 4230), (2725, 4230), (2725, 4050))),
        Territory("Ruins of Ordil'Aran", ZoneEnum.ASHENVALE, ((2520, 4230), (2520, 4325), (2700, 4325), (2700, 4230))),
        Territory("Lake Falanthim", ZoneEnum.ASHENVALE, ((2250, 4450), (2250, 4570), (2380, 4570), (2380, 4450))),
        Territory("Roadside Inn", ZoneEnum.ASHENVALE, ((2380, 4000), (2380, 4200), (2550, 4200), (2550, 4000))),
        # Southern Ashenvale
        #Territory("Splintertree Post (C, S)", ()),
        Territory("Silverwing Outpost", ZoneEnum.ASHENVALE, ((3525, 5040), (3430, 5185), (3635, 5185), (3615, 5040))),
        #Territory("Warsong Labor Camp", ()),
        #Territory("The Dor'danil Barrow Den", ()),
        # Eastern Ashenvale
        #Territory("Kargathia Keep (C, S)", ()),
        Territory("Warsong Lumber Camp", ZoneEnum.ASHENVALE, ((4050, 4733), (4050, 4884), (4192, 4955), (4192, 4733))),
        #Territory("Forest Song", ()),
        Territory("Felfire Hill", ZoneEnum.ASHENVALE, ((3970, 4925), (3970, 5055), (4140, 5055), (4080, 4925))),
        #Territory("Demon Fall Canyon", ()),
        #Territory("Satyrnaar", ()),
        #Territory("Xavian", ()),
        #Territory("Bough Shadow", ()),

        # -- STONETALON MOUNTAINS -- #
        # Stonetalon Summit
        #Territory("Stonetalon Peak (C)", tuple()),
        #Territory("Talon Den", ZoneEnum.STONETALON_MOUNTAINS, ((1650, 4745), (1650, 4900), (1780, 4900), (1780, 4745))),
        #Territory("Lumber Yard", tuple())),
        #Territory("Western Ruins", tuple()),
        
        # -- BARRENS -- #
        # Northeastern Barrens
        Territory("Mor'shan Ramparts", ZoneEnum.BARRENS, ((3550, 5350), (3900, 5350), (3900, 5700), (3550, 5700))),
        Territory("Far Watch Post", ZoneEnum.BARRENS, ((4150, 5725), (4150, 5933), (4370, 5933), (4370, 5725))),
        Territory("The Sludge Fen", ZoneEnum.BARRENS, ((3928, 5313), (4228, 5313), (4228, 5613), (3928, 5613))),
        Territory("Boulder Lode Mine", ZoneEnum.BARRENS, ((4230, 5225), (4230, 5420), (4440, 5420), (4440, 5225))),
        # Northwestern Barrens
        #Territory("Honor's Stand (C, S)", (())),
        #Territory("The Dry Hills", (())),
        #Territory("The Forgotten Pools", (())),
        #Territory("Dreadmist Peak", (())),
        #Territory("Vrang's House", (())),
        # Central Barrens
        #Territory("Crossroads (C, S)", (())),
        #Territory("The Stagnant Oasis", (())),
        #Territory("Lushwater Oasis", (())),
        #Territory("Wailing Caverns", (())),
        #Territory("Thorn Hill", (())),
        # Eastern Barrens
        Territory("Northwatch Hold", ZoneEnum.BARRENS, ((4200, 6875), (4200, 7075), (4436, 7075), (4436, 6875))),
        Territory("Ratchet", ZoneEnum.BARRENS, ((4225, 6300), (4225, 6520), (4475, 6520), (4475, 6300))),
        Territory("Merchant Coast", ZoneEnum.BARRENS, ((4340, 6560), (4340, 6840), (4533, 6840), (4533, 6560))),
        Territory("Fray Island", ZoneEnum.BARRENS, ((4533, 6666), (4533, 6860), (4763, 6860), (4763, 6666))),
        Territory("Raptor Grounds", ZoneEnum.BARRENS, ((4000, 6830), (4000, 7040), (4200, 7040), (4200, 6830))),
        # Lower Barrens
        Territory("Camp Taurajo", ZoneEnum.BARRENS, ((3310, 7025), (3310, 7180), (3650, 7180), (3650, 7025))),
        Territory("Field of Giants", ZoneEnum.BARRENS, ((3325, 7375), (3325, 7575), (3775, 7575), (3775, 7375))),
        Territory("Agama'gor", ZoneEnum.BARRENS, ((3370, 6800), (3370, 7025), (3666, 7025), (3666, 6800))),
        Territory("Bramblescar", ZoneEnum.BARRENS, ((3666, 6825), (3666, 7120), (3965, 7120), (3965, 6825))),
        Territory("Shady Rest Inn", ZoneEnum.BARRENS, ((3650, 7650), (3650, 7830), (3830, 7830), (3838, 7650))),
        # Southern Barrens
        Territory("Bael'dun Keep", ZoneEnum.BARRENS, ((3580, 7830), (3580, 7900), (3800, 7980), (3800, 7830))),
        Territory("Bael Modan Digsite", ZoneEnum.BARRENS, ((3580, 7900), (3580, 8030), (3800, 8125), (3800, 7980))),
        #Territory("The Great Lift", (())),
        #Territory("Blackthorn Ridge", (())),
        #Territory("Razorfen Downs", (())),
    )

    assert_sanity(territories, guilds)
    for continent in continents:
        img = make_continent_map(continent, zones, territories, guilds)
        for zone in zones:
            if zone.continent == continent:
                make_zone_map(img, zone)


if __name__ == "__main__":
    main()