from openfoodfacts import Flavor

SOURCE_LIST = [Flavor.off, Flavor.obf, Flavor.opff, Flavor.opf, Flavor.off_pro]
SOURCE_CHOICES = ((key, key) for key in SOURCE_LIST)
