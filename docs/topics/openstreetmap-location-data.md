# OpenStreetMap (Location data)

Open Prices uses OpenStreetMap as the main source for physical location data.

## Why

Having location data directly in Open Prices allows for a better contributor experience and easy filtering/aggregation/stats.

## What is used

### Backend

- Location table
    - when a new OSM ID is added by a contributor, we store it
    - we keep only a subset of fields (name, type, brand, lat, lng, version...)

see `open_prices/common/openstreetmap.py`

### Frontend

- Location search
    - we use a combination of Komoot Photon & Nominatim
- Brand data
    - we regularly contribute to [nsi.guide](https://nsi.guide) to add missing brands
    - we display brand logos thanks to [openfoodfacts/brand-images](https://github.com/openfoodfacts/brand-images)
- Contributing back
    - not yet... but discussed regularly :)

## Data sync

Currently, we fetch & store location data on creation only.

There is an ongoing discussion on managing location updates (e.g. a shop changes brand), see [this issue](https://github.com/openfoodfacts/open-prices/issues/1018).
