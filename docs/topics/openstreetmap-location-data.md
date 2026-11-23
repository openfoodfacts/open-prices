# OpenStreetMap (Location data)

Open Prices uses OpenStreetMap as the main source for physical location data.

## Why

Having location data directly in Open Prices allows for a better contributor experience and easy filtering/aggregation/stats.

## What is used

### Backend

- Location table
  - a `Location` is created only when a contributor adds the first price (or proof) for a new OSM ID
  - on creation, we fetch the OSM data directly from Nominatim & the OSM API (not Photon, see [Frontend](#frontend)), and keep only a subset of fields (name, type, brand, address, lat, lng, version, a few tags...)

see `open_prices/common/openstreetmap.py`

Limitations:

- **a shop in OSM is "missing" from the Open Prices API** (`GET /api/v1/locations/osm/{osm_type}/{osm_id}` returns a 404): expected, it will be created when the first price is added

### Frontend

- Location search
  - by name: we use Komoot Photon (restricted to `shop`, `amenity`, `tourism` & `leisure` places)
  - by OSM ID (e.g. `N14365327207` or `14365327207`): we use a Nominatim lookup
- Brand data
  - we regularly contribute to [nsi.guide](https://nsi.guide) to add missing brands
  - we display brand logos thanks to [openfoodfacts/brand-images](https://github.com/openfoodfacts/brand-images)
- Contributing back
  - not yet... but discussed regularly :)

Limitations:

- **a shop recently added to OSM can't be found by name**: the Photon (Komoot) database is only synced with OSM once a week, on Tuesdays (see [komoot/photon#614](https://github.com/komoot/photon/issues/614)), so a new shop can be missing for up to a week. Workaround: search by its OSM ID (e.g. `N14365327207`), which goes through Nominatim and is usually up to date within minutes
- **name search is not very precise**: adding the city or street name helps (e.g. `Carrefour 75013 Paris`)

### Example queries

- search by name (Photon): `https://photon.komoot.io/api/?q=monoprix grenoble`
- search by name (Nominatim): `https://nominatim.openstreetmap.org/search?q=monoprix grenoble&addressdetails=1&format=json`
- lookup by OSM ID (Nominatim, as done by the backend with [OSMPythonTools](https://github.com/mocnik-science/osm-python-tools)): `https://nominatim.openstreetmap.org/lookup?osm_ids=N4825695211&format=json`
- lookup by OSM ID (Overpass): `https://overpass-api.de/api/interpreter?data=[out:json];node(id:652825274);out;`
- the same location in Open Prices: `https://prices.openfoodfacts.org/api/v1/locations/osm/NODE/652825274`

## Data sync

Location data is fetched & stored on creation, and not kept in sync automatically.

The `detect_location_osm_version_change` command (run manually) compares each location's stored OSM version (locations without one are skipped) with the current one:

- minor changes (e.g. new tags) are fetched & the location is updated
- major changes (name, brand, type or a move of more than 100 m for nodes, e.g. a shop that changed brand) are only reported, for manual review
- deleted OSM elements are only reported

There is an ongoing discussion on managing location updates, see [this issue](https://github.com/openfoodfacts/open-prices/issues/1018).

Limitations:

- **a shop that changed on OSM (new brand, moved...) keeps its old data in Open Prices**, until the command is run and the change reviewed
- **a price linked to the wrong shop**: contributors can flag the price (`WRONG_LOCATION`), but not the location itself (see [Moderation](moderation.md) & [this issue](https://github.com/openfoodfacts/open-prices/issues/1136))
