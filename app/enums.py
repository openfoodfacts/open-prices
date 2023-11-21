from enum import Enum


class ProductOFFSource(Enum):
    OFF = "OFF"  # Open Food Facts
    OPF = "OPF"  # Open Products Facts
    OPFF = "OPFF"  # Open Pet Food Facts
    OBF = "OBF"  # Open Beauty Facts


class LocationOSMType(Enum):
    NODE = "NODE"
    WAY = "WAY"
    RELATION = "RELATION"
