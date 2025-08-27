TYPE_OSM = "OSM"
TYPE_ONLINE = "ONLINE"
TYPE_LIST = [TYPE_OSM, TYPE_ONLINE]
TYPE_CHOICES = [(key, key) for key in TYPE_LIST]

OSM_TYPE_NODE = "NODE"
OSM_TYPE_WAY = "WAY"
OSM_TYPE_RELATION = "RELATION"

OSM_TYPE_LIST = [OSM_TYPE_NODE, OSM_TYPE_WAY, OSM_TYPE_RELATION]
OSM_TYPE_CHOICES = [(key, key) for key in OSM_TYPE_LIST]


OSM_ID_OK_LIST = [652825274, 5]
OSM_ID_NOT_OK_LIST = [-5, 0, "test", None, "None", True, "true", False, "false"]
OSM_TYPE_OK_LIST = [OSM_TYPE_NODE, OSM_TYPE_WAY]
OSM_TYPE_NOT_OK_LIST = ["way", "W", "test", None, "None"]

WEBSITE_URL_OK_TUPLE_LIST = [
    # (input, output)
    ("https://www.decathlon.fr/", "https://www.decathlon.fr"),
    ("https://www.alltricks.fr", "https://www.alltricks.fr"),
    ("www.ekosport.fr/produit/1234", "https://www.ekosport.fr"),
    ("auvieuxcampeur.fr", "https://auvieuxcampeur.fr"),
]


TYPE_OSM_UNIQUE_CONSTRAINT_NAME = "unique_osm_constraint"
TYPE_ONLINE_UNIQUE_CONSTRAINT_NAME = "unique_online_constraint"
UNIQUE_CONSTRAINT_NAME_LIST = [
    TYPE_OSM_UNIQUE_CONSTRAINT_NAME,
    TYPE_ONLINE_UNIQUE_CONSTRAINT_NAME,
]
