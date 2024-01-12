# Changelog

## [1.9.1](https://github.com/openfoodfacts/open-prices/compare/v1.9.0...v1.9.1) (2024-01-12)


### Bug Fixes

* add missing filter on Product.product_id field. ref [#134](https://github.com/openfoodfacts/open-prices/issues/134) ([0ab9f9d](https://github.com/openfoodfacts/open-prices/commit/0ab9f9d286e83c926ece1e8719ab2323a88b1596))

## [1.9.0](https://github.com/openfoodfacts/open-prices/compare/v1.8.0...v1.9.0) (2024-01-11)


### Features

* add product filter on price_count ([#134](https://github.com/openfoodfacts/open-prices/issues/134)) ([3f687d2](https://github.com/openfoodfacts/open-prices/commit/3f687d257f8470a74fadf439731cd8c7201d8ae9))


### Bug Fixes

* always return proof.file_path for proof uploaded by the user ([#132](https://github.com/openfoodfacts/open-prices/issues/132)) ([fe14346](https://github.com/openfoodfacts/open-prices/commit/fe14346286fd5b645d610598bc3f70e5d8e8d831))

## [1.8.0](https://github.com/openfoodfacts/open-prices/compare/v1.7.0...v1.8.0) (2024-01-11)


### Features

* add price.price_per field ([#127](https://github.com/openfoodfacts/open-prices/issues/127)) ([5740271](https://github.com/openfoodfacts/open-prices/commit/57402714cb0eee7962d48d340da07e76115ffe33))
* add price.price_without_discount field ([#130](https://github.com/openfoodfacts/open-prices/issues/130)) ([5e3be73](https://github.com/openfoodfacts/open-prices/commit/5e3be7309572bd2082023f5775f16c34875bfedc))
* add product.price_count field to keep track of number of prices ([#129](https://github.com/openfoodfacts/open-prices/issues/129)) ([73b32e6](https://github.com/openfoodfacts/open-prices/commit/73b32e69377075e24d4768503c1530c483f9115e))
* add proof object in price response ([#131](https://github.com/openfoodfacts/open-prices/issues/131)) ([450b82e](https://github.com/openfoodfacts/open-prices/commit/450b82eb7d4da22d06eda4e9a29662a42e3a1a47))


### Bug Fixes

* add index on products.price_count field ([9fdfdcd](https://github.com/openfoodfacts/open-prices/commit/9fdfdcd14fc8322697f6d35a27846c310d552122))


### Technical

* add typing information ([cc5e383](https://github.com/openfoodfacts/open-prices/commit/cc5e383c88bfb9fd69a309230ad691f3b1ac5757))

## [1.7.0](https://github.com/openfoodfacts/open-prices/compare/v1.6.1...v1.7.0) (2024-01-10)


### Features

* add proof.is_public field ([#126](https://github.com/openfoodfacts/open-prices/issues/126)) ([20a4b16](https://github.com/openfoodfacts/open-prices/commit/20a4b16651467c82c134f5e5532e3b44a23802b0))
* import product DB every day ([#119](https://github.com/openfoodfacts/open-prices/issues/119)) ([b60c3ac](https://github.com/openfoodfacts/open-prices/commit/b60c3ac867d972f31a2c8dd731246d21437e2ecc))
* products GET endpoint ([#122](https://github.com/openfoodfacts/open-prices/issues/122)) ([f80d80b](https://github.com/openfoodfacts/open-prices/commit/f80d80bf6370f80da5fe4eaa6551a92b01459e88))


### Bug Fixes

* add --batch-size param to CLI command ([dca9098](https://github.com/openfoodfacts/open-prices/commit/dca9098e949c538e811ecb34a3439ad79137212c))
* fix db error ([#125](https://github.com/openfoodfacts/open-prices/issues/125)) ([57e4adb](https://github.com/openfoodfacts/open-prices/commit/57e4adb41bf29ef94fc5542e3179141f28727c09))
* fix duplicate key error due to duplicate products ([bd6ff9c](https://github.com/openfoodfacts/open-prices/commit/bd6ff9c8b2d531a83469c232988a6c0352583887))
* fix product_quantity DB error ([8196bc2](https://github.com/openfoodfacts/open-prices/commit/8196bc238b645d3f22d50e87bf3ba3d038fa7f85))
* fix product.unique_scans_n server_default ([54202d0](https://github.com/openfoodfacts/open-prices/commit/54202d002aad78f0ab3adf036f8eb8b1f7f27403))
* fix unique_scans_n null values ([b967d5a](https://github.com/openfoodfacts/open-prices/commit/b967d5a4eb3a09f93aab4562f7c052d8db7f684a))

## [1.6.1](https://github.com/openfoodfacts/open-prices/compare/v1.6.0...v1.6.1) (2024-01-03)


### Bug Fixes

* improve price fetch performance ([#118](https://github.com/openfoodfacts/open-prices/issues/118)) ([1b65ea2](https://github.com/openfoodfacts/open-prices/commit/1b65ea22e31fdf38bcbadb58314e200ff095964c))


### Technical

* add tutorial + improve main doc page ([#116](https://github.com/openfoodfacts/open-prices/issues/116)) ([a01a5a0](https://github.com/openfoodfacts/open-prices/commit/a01a5a0b043954fb0f5b7c7d078cfed5c91e55fb))

## [1.6.0](https://github.com/openfoodfacts/open-prices/compare/v1.5.0...v1.6.0) (2023-12-31)


### Features

* add price filters on category_tag, labels_tags & origins_tags ([#113](https://github.com/openfoodfacts/open-prices/issues/113)) ([2a1e350](https://github.com/openfoodfacts/open-prices/commit/2a1e350e7ecc5bb6b3aaa0d9042f96a6153c219e))


### Technical

* add a link to the frontend repo ([#111](https://github.com/openfoodfacts/open-prices/issues/111)) ([cd2f34b](https://github.com/openfoodfacts/open-prices/commit/cd2f34b90d454ae708e08fb5994b0cecb256e728))

## [1.5.0](https://github.com/openfoodfacts/open-prices/compare/v1.4.2...v1.5.0) (2023-12-29)


### Features

* add endpoint to retrieve location by osm data ([#108](https://github.com/openfoodfacts/open-prices/issues/108)) ([b317014](https://github.com/openfoodfacts/open-prices/commit/b3170148fb4585448de82336fcb871c315228130))
* add endpoint to retrieve product by code ([#106](https://github.com/openfoodfacts/open-prices/issues/106)) ([70f4567](https://github.com/openfoodfacts/open-prices/commit/70f4567bf5a97d7014064bae2b0454e04cd6f7e1))
* add price.origins_tags field ([#110](https://github.com/openfoodfacts/open-prices/issues/110)) ([46e0c7f](https://github.com/openfoodfacts/open-prices/commit/46e0c7fc8de9bf66dd401786cfd83fc7468f6584))
* return Price.owner info ([6e922f3](https://github.com/openfoodfacts/open-prices/commit/6e922f30029a9f9558ff070d3dc7c4330dd7e08f))


### Technical

* improve landing page ([#109](https://github.com/openfoodfacts/open-prices/issues/109)) ([ee2cbd8](https://github.com/openfoodfacts/open-prices/commit/ee2cbd869f25157204d942db3ce2c3e17b4439b5))

## [1.4.2](https://github.com/openfoodfacts/open-prices/compare/v1.4.1...v1.4.2) (2023-12-23)


### Bug Fixes

* better fetch location city from OSM. ref [#38](https://github.com/openfoodfacts/open-prices/issues/38) ([c37e7a6](https://github.com/openfoodfacts/open-prices/commit/c37e7a6e85b4999622cd503d7f65481f69050540))

## [1.4.1](https://github.com/openfoodfacts/open-prices/compare/v1.4.0...v1.4.1) (2023-12-23)


### Bug Fixes

* Product.brands should be a string. ref [#93](https://github.com/openfoodfacts/open-prices/issues/93) ([7bbf1fc](https://github.com/openfoodfacts/open-prices/commit/7bbf1fcdf470bf74546ac740870694017b1a35a1))

## [1.4.0](https://github.com/openfoodfacts/open-prices/compare/v1.3.0...v1.4.0) (2023-12-23)


### Features

* add extra filters on GET /prices ([#100](https://github.com/openfoodfacts/open-prices/issues/100)) ([27edae3](https://github.com/openfoodfacts/open-prices/commit/27edae3db6fb00b352192b3e9cdb30f05d6c87e2))
* ask for proof type when creating ([#95](https://github.com/openfoodfacts/open-prices/issues/95)) ([529cdce](https://github.com/openfoodfacts/open-prices/commit/529cdcebb75d95f8f1e3e5596da36cdc51c8b444))
* manage webp proof uploads ([#98](https://github.com/openfoodfacts/open-prices/issues/98)) ([830315b](https://github.com/openfoodfacts/open-prices/commit/830315bff181761eb9c015d931471f81db9a429b))
* new Product.brands field ([#93](https://github.com/openfoodfacts/open-prices/issues/93)) ([fd359dc](https://github.com/openfoodfacts/open-prices/commit/fd359dc3b6635455e21c1df8393559d0a7c62224))

## [1.3.0](https://github.com/openfoodfacts/open-prices/compare/v1.2.1...v1.3.0) (2023-12-18)


### Features

* add openapi tags on endpoints ([#88](https://github.com/openfoodfacts/open-prices/issues/88)) ([e7b0c14](https://github.com/openfoodfacts/open-prices/commit/e7b0c14f88e8ae11279ffe7abed06172fda1998b))
* add Price.product_name field ([#83](https://github.com/openfoodfacts/open-prices/issues/83)) ([36d551f](https://github.com/openfoodfacts/open-prices/commit/36d551f441c2cbe83c76680a0f69e98c34a963c4))
* add relationship objects in response of GET /prices ([#92](https://github.com/openfoodfacts/open-prices/issues/92)) ([2156690](https://github.com/openfoodfacts/open-prices/commit/21566904373fde48a4b5f5a7af11450bf2606896))
* add sorting on GET /prices ([#90](https://github.com/openfoodfacts/open-prices/issues/90)) ([7139ec9](https://github.com/openfoodfacts/open-prices/commit/7139ec950fd44d42d9d6e3a6816c579ca91a4dde))
* add vue.js frontend on /app ([ca38cbf](https://github.com/openfoodfacts/open-prices/commit/ca38cbf0fd5222be59c53e650ea114d249c72834))


### Bug Fixes

* fix ProofCreate schema ([ed34567](https://github.com/openfoodfacts/open-prices/commit/ed345675a414a6f6aea43036de52a914239f9fc6))


### Technical

* make migration files available in dev ([494bb96](https://github.com/openfoodfacts/open-prices/commit/494bb96564830d4557c935e54fac8d105238e73d))

## [1.2.1](https://github.com/openfoodfacts/open-prices/compare/v1.2.0...v1.2.1) (2023-12-04)


### Bug Fixes

* add /api/v1 prefix to all relevant routes ([#74](https://github.com/openfoodfacts/open-prices/issues/74)) ([353e59f](https://github.com/openfoodfacts/open-prices/commit/353e59fb772c3067a1db5db4ecd8d6ad3fe49e60))
* bump release please version ([a37e7da](https://github.com/openfoodfacts/open-prices/commit/a37e7daf66548b3c168491d7c68585ed4753c90e))
* fix github config ([7edfa8d](https://github.com/openfoodfacts/open-prices/commit/7edfa8dd9b777c50be2f4f78aa43ef87dd7c93e2))
* fix release please ([#78](https://github.com/openfoodfacts/open-prices/issues/78)) ([86bb591](https://github.com/openfoodfacts/open-prices/commit/86bb5911758c359d6e2218ac836191f58b91fc4f))

## [1.2.0](https://github.com/openfoodfacts/open-prices/compare/v1.1.0...v1.2.0) (2023-11-27)


### Features

* add CORS configuration ([#62](https://github.com/openfoodfacts/open-prices/issues/62)) ([79de31b](https://github.com/openfoodfacts/open-prices/commit/79de31bb867c1ea945adf8bab6f12d841012d207))
* add labels_tags field ([ea2bdb0](https://github.com/openfoodfacts/open-prices/commit/ea2bdb07e66a6c302a929a6f1ca348f3f5bf5a54))
* add Proof.type field ([#68](https://github.com/openfoodfacts/open-prices/issues/68)) ([d211c0a](https://github.com/openfoodfacts/open-prices/commit/d211c0a8b920bc8dc1b9e19c6af0995fed9c15eb))
* add support for cookie authentication ([9e8413d](https://github.com/openfoodfacts/open-prices/commit/9e8413d83ed1916cf170a0d1c286a4990adcd540))
* additional tests on Price create ([#60](https://github.com/openfoodfacts/open-prices/issues/60)) ([bcbcc2a](https://github.com/openfoodfacts/open-prices/commit/bcbcc2aa96767e5ce5abbcb1155f4b5208236e71))
* allow to upload price of barcode-less products ([#53](https://github.com/openfoodfacts/open-prices/issues/53)) ([d44d86d](https://github.com/openfoodfacts/open-prices/commit/d44d86df2829b62db5441904a0644f062923cde3))
* simply Price.currency validation ([#67](https://github.com/openfoodfacts/open-prices/issues/67)) ([d7dfb0c](https://github.com/openfoodfacts/open-prices/commit/d7dfb0cbb3d8e8efeb2f5e6b92cffb5296ab9863))


### Bug Fixes

* add image serving ([5808b7a](https://github.com/openfoodfacts/open-prices/commit/5808b7a1effad8ccccdf88681f5a31aa2c77a891))
* CORS: revert configuration. add openfoodfacts-explorer to whitelist ([e3e9098](https://github.com/openfoodfacts/open-prices/commit/e3e9098a766785833500f4bcd0db545f4a374bbd))
* CORS: temporarily allow all origins in deployed envs. ref [#65](https://github.com/openfoodfacts/open-prices/issues/65) ([06f2560](https://github.com/openfoodfacts/open-prices/commit/06f2560906f64ceb5add4d850cb15ec15a98b425))
* fix labels_tags field validator ([#69](https://github.com/openfoodfacts/open-prices/issues/69)) ([5f23977](https://github.com/openfoodfacts/open-prices/commit/5f23977116d846acf288a031f70da0adac5ce34f))
* improve landing page ([#71](https://github.com/openfoodfacts/open-prices/issues/71)) ([ec79ccc](https://github.com/openfoodfacts/open-prices/commit/ec79ccc3ff1eac44e65b98ed2e3561227648e674))
* lint last alembic version ([1b0667d](https://github.com/openfoodfacts/open-prices/commit/1b0667d09b19c4dc531c74eabdec85ec44caa23c))
* return 201 instead of 200 on price (& proof) create ([#66](https://github.com/openfoodfacts/open-prices/issues/66)) ([af543cf](https://github.com/openfoodfacts/open-prices/commit/af543cf924f7502000d13b369717d7c22967d980))
* use time.sleep instead of asyncio.sleep in non-corountine function ([1ccffd6](https://github.com/openfoodfacts/open-prices/commit/1ccffd6f5dfb22342bea65f63cb2cde39d5ac352))

## [1.1.0](https://github.com/openfoodfacts/open-prices/compare/v1.0.3...v1.1.0) (2023-11-22)


### Features

* fetch location data from OpenStreetMap Nominatim ([#38](https://github.com/openfoodfacts/open-prices/issues/38)) ([2044e6b](https://github.com/openfoodfacts/open-prices/commit/2044e6bdc287e361e891505dca55df8ce9140082))
* fetch product data from OpenFoodFacts ([#49](https://github.com/openfoodfacts/open-prices/issues/49)) ([cc5a778](https://github.com/openfoodfacts/open-prices/commit/cc5a778d11bb0596582c488614b45c176ea7b123))
* GET /locations/id endpoint to get location details ([#37](https://github.com/openfoodfacts/open-prices/issues/37)) ([4a4eca1](https://github.com/openfoodfacts/open-prices/commit/4a4eca1c1a8fc4e618d189f66a6e2bea5467c6d4))
* GET /products/id endpoint to get product details ([#46](https://github.com/openfoodfacts/open-prices/issues/46)) ([74f011c](https://github.com/openfoodfacts/open-prices/commit/74f011ce1d112445f18a132de060edf612683e53))
* on Price create, create (or get) Location, and link them ([#36](https://github.com/openfoodfacts/open-prices/issues/36)) ([003de11](https://github.com/openfoodfacts/open-prices/commit/003de11bb2ffc30e0e4af5631b1aa1fabc24a763))
* on Price create, create (or get) Product, and link them ([#45](https://github.com/openfoodfacts/open-prices/issues/45)) ([71cf40a](https://github.com/openfoodfacts/open-prices/commit/71cf40ac914599d7884f848ae09dde02402cf1c7))
* simple Location model ([#35](https://github.com/openfoodfacts/open-prices/issues/35)) ([32562ad](https://github.com/openfoodfacts/open-prices/commit/32562adcf52544a0ac388bdefa7df0cccdc3fb67))
* simple Product model ([#44](https://github.com/openfoodfacts/open-prices/issues/44)) ([2bfa8f6](https://github.com/openfoodfacts/open-prices/commit/2bfa8f682148b97299be2c7e483e16e93d743d0c))


### Bug Fixes

* fix landing page ([cf9bb9d](https://github.com/openfoodfacts/open-prices/commit/cf9bb9d44c324e7b7a016be9ff2e1fdc23795917))
* fix some typos in the landing page ([#51](https://github.com/openfoodfacts/open-prices/issues/51)) ([e5fee84](https://github.com/openfoodfacts/open-prices/commit/e5fee84246304e375c3fa0421e08cdd53ba07ad1))

## [1.0.3](https://github.com/openfoodfacts/open-prices/compare/v1.0.2...v1.0.3) (2023-11-20)


### Bug Fixes

* fix container deploy config ([36c4f1b](https://github.com/openfoodfacts/open-prices/commit/36c4f1b060045a98d9a00065664d945d3cd7e5b1))

## [1.0.2](https://github.com/openfoodfacts/open-prices/compare/v1.0.1...v1.0.2) (2023-11-16)


### Bug Fixes

* add prod env config ([8ced9d1](https://github.com/openfoodfacts/open-prices/commit/8ced9d17b1e7c2d56880cdff743fe81bf6c214b6))

## [1.0.1](https://github.com/openfoodfacts/open-prices/compare/v1.0.0...v1.0.1) (2023-11-16)


### Bug Fixes

* transform async func into func ([22a5f0d](https://github.com/openfoodfacts/open-prices/commit/22a5f0d32c44151b6816987c87829877d54ab798))

## 1.0.0 (2023-11-16)


### Features

* add a route to get all user proofs ([c4b6a7a](https://github.com/openfoodfacts/open-prices/commit/c4b6a7aa4661bb4bc2e632aa9f6aa3ed321a8363))
* add advanced filtering on GET /prices ([#29](https://github.com/openfoodfacts/open-prices/issues/29)) ([9b52406](https://github.com/openfoodfacts/open-prices/commit/9b52406167b8338499274157dbe2690fc962af27))
* add pagination on GET /prices ([#28](https://github.com/openfoodfacts/open-prices/issues/28)) ([4e39b71](https://github.com/openfoodfacts/open-prices/commit/4e39b712e12a6a3877c71acde768809c69b2c138))
* add proof support ([19ee604](https://github.com/openfoodfacts/open-prices/commit/19ee604e702ae5ce5d5a05d6380a82ade547910c))
* authentication workflow and store user token ([#22](https://github.com/openfoodfacts/open-prices/issues/22)) ([81bab91](https://github.com/openfoodfacts/open-prices/commit/81bab912dca1b0c0c9305a794a19e8f23bd9148d))
* Price model ([#23](https://github.com/openfoodfacts/open-prices/issues/23)) ([56a853b](https://github.com/openfoodfacts/open-prices/commit/56a853bc6c5da2271821e9b6d8ecaab661a9d232))
* price POST endpoint ([#24](https://github.com/openfoodfacts/open-prices/issues/24)) ([0bf98ca](https://github.com/openfoodfacts/open-prices/commit/0bf98cab7da5cae0554458b4bc7d03b8af896aff))
* prices GET endpoint ([#26](https://github.com/openfoodfacts/open-prices/issues/26)) ([a769910](https://github.com/openfoodfacts/open-prices/commit/a769910b6aaded9c7f6c52942fdf93ba17a6e72c))
* User model ([#21](https://github.com/openfoodfacts/open-prices/issues/21)) ([556cc6f](https://github.com/openfoodfacts/open-prices/commit/556cc6f65ab25474c9be9ecd505ca99841906832))


### Bug Fixes

* add status endpoint ([b3ddad9](https://github.com/openfoodfacts/open-prices/commit/b3ddad955d80b18b47e8a6fc855692eba16b1f55))
* stop using global db, use get_db instead ([#30](https://github.com/openfoodfacts/open-prices/issues/30)) ([9739734](https://github.com/openfoodfacts/open-prices/commit/97397344b1e7ef7af17bc7a86445a651815a4f29))
* update docker-compose.yml to add postgres service ([0b5c8af](https://github.com/openfoodfacts/open-prices/commit/0b5c8af7f713fd4a48a6bf56e011aa57dd1be588))
* update pre-commit config ([5cc63f4](https://github.com/openfoodfacts/open-prices/commit/5cc63f4116aa85c42f22aeae7a7531d946efb950))
* use black + isort on all files ([877f3c6](https://github.com/openfoodfacts/open-prices/commit/877f3c6a4a57553ae9604722b81ddacd426d722a))
