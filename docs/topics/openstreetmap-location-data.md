# OpenStreetMap (Location data)

Open Prices uses OpenStreetMap as the main source for physical location data.

## Why

Having location data directly in Open Prices allows for a better contributor experience and easy filtering/aggregation/stats.

## What is used

### Backend

- Location table
  - a `Location` is created only when a contributor adds the first price (or proof) for a new OSM ID: shops existing in OSM but without any price are not in Open Prices (`GET /api/v1/locations/osm/{osm_type}/{osm_id}` returns a 404)
  - on creation, we fetch the OSM data (Nominatim & OSM API) and keep only a subset of fields (name, type, brand, address, lat, lng, version, a few tags...)

see `open_prices/common/openstreetmap.py`

### Frontend

- Location search
  - by name: we use Komoot Photon (restricted to `shop`, `amenity`, `tourism` & `leisure` places)
  - by OSM ID (e.g. `N14365327207` or `14365327207`): we use a Nominatim lookup
  - both search engines are fed by OSM data, but with some delay (see [Known limitations](#known-limitations))
- Brand data
  - we regularly contribute to [nsi.guide](https://nsi.guide) to add missing brands
  - we display brand logos thanks to [openfoodfacts/brand-images](https://github.com/openfoodfacts/brand-images)
- Contributing back
  - not yet... but discussed regularly :)

## Data sync

Location data is fetched & stored on creation, and not kept in sync automatically.

The `detect_location_osm_version_change` command (run manually) compares each location's OSM version with the current one:

- minor changes (e.g. new tags) are fetched & the location is updated
- major changes (name, brand, type or a move of more than 100 m, e.g. a shop that changed brand) are only reported, for manual review
- deleted OSM elements are only reported

There is an ongoing discussion on managing location updates, see [this issue](https://github.com/openfoodfacts/open-prices/issues/1018).

## Known limitations

- **a shop recently added to OSM can't be found by name**: the Photon (Komoot) database is only synced with OSM once a week, on Tuesdays (see [komoot/photon#614](https://github.com/komoot/photon/issues/614)), so a new shop can be missing for up to a week. Workaround: search by its OSM ID (e.g. `N14365327207`), which goes through Nominatim and is usually up to date within minutes
- **a shop in OSM is "missing" from the Open Prices API**: expected, it will be created when the first price is added (see [Backend](#backend))
- **a shop that changed on OSM (new brand, moved...) keeps its old data in Open Prices**: see [Data sync](#data-sync)
- **a price linked to the wrong shop**: contributors can flag the price (`WRONG_LOCATION`), but not the location itself (see [Moderation](moderation.md) & [this issue](https://github.com/openfoodfacts/open-prices/issues/1136))
- **name search is not very precise**: adding the city or street name helps (e.g. `Carrefour 75013 Paris`)
