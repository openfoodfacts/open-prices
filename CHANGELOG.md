# Changelog

## [1.24.0](https://github.com/openfoodfacts/open-prices/compare/v1.23.0...v1.24.0) (2024-03-18)


### Features

* new Product.ecoscore_grade field ([#247](https://github.com/openfoodfacts/open-prices/issues/247)) ([fa89ef8](https://github.com/openfoodfacts/open-prices/commit/fa89ef8b988e1796697539d3fc72292b0021b74a))
* new Product.nova_group field ([#251](https://github.com/openfoodfacts/open-prices/issues/251)) ([e611b11](https://github.com/openfoodfacts/open-prices/commit/e611b1116be30ddda2d029ee2770b62bedc1ab0e))
* **prices:** allow moderators to delete prices ([#260](https://github.com/openfoodfacts/open-prices/issues/260)) ([0c3d232](https://github.com/openfoodfacts/open-prices/commit/0c3d2328a81b2e8c0bb04bf60039e56719ae8ceb))
* **prices:** allow moderators to edit prices ([#259](https://github.com/openfoodfacts/open-prices/issues/259)) ([dcb463b](https://github.com/openfoodfacts/open-prices/commit/dcb463b95dae8916781ee7c952a3b246f848fe59))
* **product:** new source_last_synced field ([#256](https://github.com/openfoodfacts/open-prices/issues/256)) ([e6be855](https://github.com/openfoodfacts/open-prices/commit/e6be855e822f8c0e304293e2a8b68fd6dfaa5ed4))


### Bug Fixes

* **products:** fix filter by labels_tags ([#252](https://github.com/openfoodfacts/open-prices/issues/252)) ([ac68218](https://github.com/openfoodfacts/open-prices/commit/ac682184085ea0781b1a0bf634fc9a79c105316e))
* **products:** update products added first in Open Prices ([#250](https://github.com/openfoodfacts/open-prices/issues/250)) ([bef2932](https://github.com/openfoodfacts/open-prices/commit/bef29325ba7ac5c6d7e113174a290a988fc82d5c))
* **sync:** tentative fix of Product sync with OFF ([#257](https://github.com/openfoodfacts/open-prices/issues/257)) ([68f0b6c](https://github.com/openfoodfacts/open-prices/commit/68f0b6c729aba9f9c76ae140aa226d5f358f63f4))
* **tests:** use ProductFull for fixtures ([#253](https://github.com/openfoodfacts/open-prices/issues/253)) ([2d7b83c](https://github.com/openfoodfacts/open-prices/commit/2d7b83c2e3b149a58f51dd7614e8728f9db3b997))


### Technical

* improve examples of Price schema ([#248](https://github.com/openfoodfacts/open-prices/issues/248)) ([2527942](https://github.com/openfoodfacts/open-prices/commit/25279427a482f7a5b1135c939e6a4033eca00b65))
* Improve typing, pre-commit, updates openfoodfacts package ([#198](https://github.com/openfoodfacts/open-prices/issues/198)) ([ff03b0c](https://github.com/openfoodfacts/open-prices/commit/ff03b0cbbe4e43994fb6e924b19f1dd343e19444))

## [1.23.0](https://github.com/openfoodfacts/open-prices/compare/v1.22.0...v1.23.0) (2024-03-05)


### Features

* add PATCH endpoint to update proof ([#235](https://github.com/openfoodfacts/open-prices/issues/235)) ([6d05821](https://github.com/openfoodfacts/open-prices/commit/6d0582124c8d885416144e367e7d5495921c902e))
* new Product.nutriscore_grade field ([#239](https://github.com/openfoodfacts/open-prices/issues/239)) ([2724893](https://github.com/openfoodfacts/open-prices/commit/272489399bd5f5a565a732a8e03145a9a69116c1))
* **products:** new filter by categories_tags ([#234](https://github.com/openfoodfacts/open-prices/issues/234)) ([3676381](https://github.com/openfoodfacts/open-prices/commit/3676381be957e990d1328a1b373a5b4f58fc4bbb))
* **products:** new filter by labels_tags ([#238](https://github.com/openfoodfacts/open-prices/issues/238)) ([09fb20d](https://github.com/openfoodfacts/open-prices/commit/09fb20dd17e5779a4d14ea88965da93b4e37c710))


### Bug Fixes

* **prices:** improve private proof filtering depending on user ([#241](https://github.com/openfoodfacts/open-prices/issues/241)) ([a3503b0](https://github.com/openfoodfacts/open-prices/commit/a3503b0a3c912be1f88ecdf0c81b2da797754c46))
* remove trailing slash in API endpoints ([#233](https://github.com/openfoodfacts/open-prices/issues/233)) ([31a840d](https://github.com/openfoodfacts/open-prices/commit/31a840d08e27d581d91f7eb18d9599a6a5c69741))
* **tests:** use LocationFull for fixtures ([#240](https://github.com/openfoodfacts/open-prices/issues/240)) ([f04a53f](https://github.com/openfoodfacts/open-prices/commit/f04a53f6132905ff2f5c16b7bd9854992092885e))


### Technical

* fix restart policy for nginx ([#232](https://github.com/openfoodfacts/open-prices/issues/232)) ([e924d00](https://github.com/openfoodfacts/open-prices/commit/e924d0021fb97b5126b80fab859a486c5d273e49))
* Simplify api.py (move endpoints to their own routers) ([#226](https://github.com/openfoodfacts/open-prices/issues/226)) ([683600b](https://github.com/openfoodfacts/open-prices/commit/683600b320b0f2dc5908c1cdc2293d5a8009e94a))

## [1.22.0](https://github.com/openfoodfacts/open-prices/compare/v1.21.0...v1.22.0) (2024-02-24)


### Features

* add endpoint to update price ([#202](https://github.com/openfoodfacts/open-prices/issues/202)) ([a4b66a6](https://github.com/openfoodfacts/open-prices/commit/a4b66a673771835533bd615e0495e495552c97da))
* allow filtering Prices by proof_id([#219](https://github.com/openfoodfacts/open-prices/issues/219)) ([a26d1b2](https://github.com/openfoodfacts/open-prices/commit/a26d1b22b445d7baadc7020baf560f966c394d91))
* new GET proof by id endpoint ([#228](https://github.com/openfoodfacts/open-prices/issues/228)) ([177a8d2](https://github.com/openfoodfacts/open-prices/commit/177a8d2ebf11450739dfb94c8abd7d73df93d573))
* translate landing page in spanish ([#230](https://github.com/openfoodfacts/open-prices/issues/230)) ([ef019fc](https://github.com/openfoodfacts/open-prices/commit/ef019fc45de7cc39b3c31d4c92c0d2fbca51f80a))


### Bug Fixes

* fix price update endpoint ([#227](https://github.com/openfoodfacts/open-prices/issues/227)) ([5ec2e2e](https://github.com/openfoodfacts/open-prices/commit/5ec2e2e6bfe3ef8fc87f561942b1f2150c8c3e4e))

## [1.21.0](https://github.com/openfoodfacts/open-prices/compare/v1.20.0...v1.21.0) (2024-02-21)


### Features

* add a route to get all user proofs ([c4b6a7a](https://github.com/openfoodfacts/open-prices/commit/c4b6a7aa4661bb4bc2e632aa9f6aa3ed321a8363))
* add advanced filtering on GET /prices ([#29](https://github.com/openfoodfacts/open-prices/issues/29)) ([9b52406](https://github.com/openfoodfacts/open-prices/commit/9b52406167b8338499274157dbe2690fc962af27))
* add an endpoint to delete a session ([#174](https://github.com/openfoodfacts/open-prices/issues/174)) ([a2955dc](https://github.com/openfoodfacts/open-prices/commit/a2955dc130c4edaa05177682a16c61a075615110))
* add CORS configuration ([#62](https://github.com/openfoodfacts/open-prices/issues/62)) ([79de31b](https://github.com/openfoodfacts/open-prices/commit/79de31bb867c1ea945adf8bab6f12d841012d207))
* add endpoint to retrieve location by osm data ([#108](https://github.com/openfoodfacts/open-prices/issues/108)) ([b317014](https://github.com/openfoodfacts/open-prices/commit/b3170148fb4585448de82336fcb871c315228130))
* add endpoint to retrieve product by code ([#106](https://github.com/openfoodfacts/open-prices/issues/106)) ([70f4567](https://github.com/openfoodfacts/open-prices/commit/70f4567bf5a97d7014064bae2b0454e04cd6f7e1))
* add extra filters on GET /prices ([#100](https://github.com/openfoodfacts/open-prices/issues/100)) ([27edae3](https://github.com/openfoodfacts/open-prices/commit/27edae3db6fb00b352192b3e9cdb30f05d6c87e2))
* add filter on Proof.price_count field ([#187](https://github.com/openfoodfacts/open-prices/issues/187)) ([0068cd5](https://github.com/openfoodfacts/open-prices/commit/0068cd56c4b585e95d02f885911de5bd88556c31))
* add labels_tags field ([ea2bdb0](https://github.com/openfoodfacts/open-prices/commit/ea2bdb07e66a6c302a929a6f1ca348f3f5bf5a54))
* add location filter on price_count ([#142](https://github.com/openfoodfacts/open-prices/issues/142)) ([1237687](https://github.com/openfoodfacts/open-prices/commit/12376873395eedebcd9f0246c9a7cb5ebffa9ff7))
* add location.price_count to keep track of number of prices ([#140](https://github.com/openfoodfacts/open-prices/issues/140)) ([817663f](https://github.com/openfoodfacts/open-prices/commit/817663f4d2564fb3e0b3e0ba913652ac934a7b74))
* add openapi tags on endpoints ([#88](https://github.com/openfoodfacts/open-prices/issues/88)) ([e7b0c14](https://github.com/openfoodfacts/open-prices/commit/e7b0c14f88e8ae11279ffe7abed06172fda1998b))
* add pagination on GET /prices ([#28](https://github.com/openfoodfacts/open-prices/issues/28)) ([4e39b71](https://github.com/openfoodfacts/open-prices/commit/4e39b712e12a6a3877c71acde768809c69b2c138))
* add price filters on category_tag, labels_tags & origins_tags ([#113](https://github.com/openfoodfacts/open-prices/issues/113)) ([2a1e350](https://github.com/openfoodfacts/open-prices/commit/2a1e350e7ecc5bb6b3aaa0d9042f96a6153c219e))
* add price.origins_tags field ([#110](https://github.com/openfoodfacts/open-prices/issues/110)) ([46e0c7f](https://github.com/openfoodfacts/open-prices/commit/46e0c7fc8de9bf66dd401786cfd83fc7468f6584))
* add price.price_is_discounted field ([#163](https://github.com/openfoodfacts/open-prices/issues/163)) ([a73e460](https://github.com/openfoodfacts/open-prices/commit/a73e4606846e08261a9cc00d1d56fa82c5d23382))
* add price.price_per field ([#127](https://github.com/openfoodfacts/open-prices/issues/127)) ([5740271](https://github.com/openfoodfacts/open-prices/commit/57402714cb0eee7962d48d340da07e76115ffe33))
* add price.price_without_discount field ([#130](https://github.com/openfoodfacts/open-prices/issues/130)) ([5e3be73](https://github.com/openfoodfacts/open-prices/commit/5e3be7309572bd2082023f5775f16c34875bfedc))
* add Price.product_name field ([#83](https://github.com/openfoodfacts/open-prices/issues/83)) ([36d551f](https://github.com/openfoodfacts/open-prices/commit/36d551f441c2cbe83c76680a0f69e98c34a963c4))
* add product filter on price_count ([#134](https://github.com/openfoodfacts/open-prices/issues/134)) ([3f687d2](https://github.com/openfoodfacts/open-prices/commit/3f687d257f8470a74fadf439731cd8c7201d8ae9))
* add product.price_count field to keep track of number of prices ([#129](https://github.com/openfoodfacts/open-prices/issues/129)) ([73b32e6](https://github.com/openfoodfacts/open-prices/commit/73b32e69377075e24d4768503c1530c483f9115e))
* add proof object in price response ([#131](https://github.com/openfoodfacts/open-prices/issues/131)) ([450b82e](https://github.com/openfoodfacts/open-prices/commit/450b82eb7d4da22d06eda4e9a29662a42e3a1a47))
* add proof support ([19ee604](https://github.com/openfoodfacts/open-prices/commit/19ee604e702ae5ce5d5a05d6380a82ade547910c))
* add proof.is_public field ([#126](https://github.com/openfoodfacts/open-prices/issues/126)) ([20a4b16](https://github.com/openfoodfacts/open-prices/commit/20a4b16651467c82c134f5e5532e3b44a23802b0))
* add proof.price_count to keep track of number of prices ([#185](https://github.com/openfoodfacts/open-prices/issues/185)) ([1637f36](https://github.com/openfoodfacts/open-prices/commit/1637f362a0353801c3813da29709f3c202fea31c))
* add Proof.type field ([#68](https://github.com/openfoodfacts/open-prices/issues/68)) ([d211c0a](https://github.com/openfoodfacts/open-prices/commit/d211c0a8b920bc8dc1b9e19c6af0995fed9c15eb))
* add relationship objects in response of GET /prices ([#92](https://github.com/openfoodfacts/open-prices/issues/92)) ([2156690](https://github.com/openfoodfacts/open-prices/commit/21566904373fde48a4b5f5a7af11450bf2606896))
* add sorting on GET /prices ([#90](https://github.com/openfoodfacts/open-prices/issues/90)) ([7139ec9](https://github.com/openfoodfacts/open-prices/commit/7139ec950fd44d42d9d6e3a6816c579ca91a4dde))
* add support for cookie authentication ([9e8413d](https://github.com/openfoodfacts/open-prices/commit/9e8413d83ed1916cf170a0d1c286a4990adcd540))
* add user sessions ([#149](https://github.com/openfoodfacts/open-prices/issues/149)) ([a23977e](https://github.com/openfoodfacts/open-prices/commit/a23977e2b1943ecda64fccb22f3b399121c5ab89)), closes [#148](https://github.com/openfoodfacts/open-prices/issues/148)
* add user.price_count to keep track of number of prices ([#143](https://github.com/openfoodfacts/open-prices/issues/143)) ([0f13566](https://github.com/openfoodfacts/open-prices/commit/0f135668cc949c5d19d4fa0bbb6d5bb396576428))
* add vue.js frontend on /app ([ca38cbf](https://github.com/openfoodfacts/open-prices/commit/ca38cbf0fd5222be59c53e650ea114d249c72834))
* additional tests on Price create ([#60](https://github.com/openfoodfacts/open-prices/issues/60)) ([bcbcc2a](https://github.com/openfoodfacts/open-prices/commit/bcbcc2aa96767e5ce5abbcb1155f4b5208236e71))
* allow to upload price of barcode-less products ([#53](https://github.com/openfoodfacts/open-prices/issues/53)) ([d44d86d](https://github.com/openfoodfacts/open-prices/commit/d44d86df2829b62db5441904a0644f062923cde3))
* ask for proof type when creating ([#95](https://github.com/openfoodfacts/open-prices/issues/95)) ([529cdce](https://github.com/openfoodfacts/open-prices/commit/529cdcebb75d95f8f1e3e5596da36cdc51c8b444))
* **auth:** avoid recreating existing user on login ([#144](https://github.com/openfoodfacts/open-prices/issues/144)) ([502539c](https://github.com/openfoodfacts/open-prices/commit/502539cfbbc06a70912ee153744658526f4dd6a4))
* authentication workflow and store user token ([#22](https://github.com/openfoodfacts/open-prices/issues/22)) ([81bab91](https://github.com/openfoodfacts/open-prices/commit/81bab912dca1b0c0c9305a794a19e8f23bd9148d))
* fetch location data from OpenStreetMap Nominatim ([#38](https://github.com/openfoodfacts/open-prices/issues/38)) ([2044e6b](https://github.com/openfoodfacts/open-prices/commit/2044e6bdc287e361e891505dca55df8ce9140082))
* fetch product data from OpenFoodFacts ([#49](https://github.com/openfoodfacts/open-prices/issues/49)) ([cc5a778](https://github.com/openfoodfacts/open-prices/commit/cc5a778d11bb0596582c488614b45c176ea7b123))
* GET /locations/id endpoint to get location details ([#37](https://github.com/openfoodfacts/open-prices/issues/37)) ([4a4eca1](https://github.com/openfoodfacts/open-prices/commit/4a4eca1c1a8fc4e618d189f66a6e2bea5467c6d4))
* GET /products/id endpoint to get product details ([#46](https://github.com/openfoodfacts/open-prices/issues/46)) ([74f011c](https://github.com/openfoodfacts/open-prices/commit/74f011ce1d112445f18a132de060edf612683e53))
* import product DB every day ([#119](https://github.com/openfoodfacts/open-prices/issues/119)) ([b60c3ac](https://github.com/openfoodfacts/open-prices/commit/b60c3ac867d972f31a2c8dd731246d21437e2ecc))
* import script for GDPR requests csv (Auchan, Carrefour, E.Leclerc, Intermarché) ([#209](https://github.com/openfoodfacts/open-prices/issues/209)) ([0c491e4](https://github.com/openfoodfacts/open-prices/commit/0c491e4c5d19f06dedd112db46f7ff2e3c10a8ce))
* locations GET endpoint ([#138](https://github.com/openfoodfacts/open-prices/issues/138)) ([300697f](https://github.com/openfoodfacts/open-prices/commit/300697f0f7c12ae308a5e0a04cd5515afdda720f))
* manage webp proof uploads ([#98](https://github.com/openfoodfacts/open-prices/issues/98)) ([830315b](https://github.com/openfoodfacts/open-prices/commit/830315bff181761eb9c015d931471f81db9a429b))
* new DELETE prices endpoint ([#179](https://github.com/openfoodfacts/open-prices/issues/179)) ([35d9f6e](https://github.com/openfoodfacts/open-prices/commit/35d9f6e96e65102af34382d03670f5e6bb55a761))
* new DELETE proofs endpoint ([#197](https://github.com/openfoodfacts/open-prices/issues/197)) ([6066982](https://github.com/openfoodfacts/open-prices/commit/6066982a0d31458fe65ab23b8c503e86280a424c))
* new Product.brands field ([#93](https://github.com/openfoodfacts/open-prices/issues/93)) ([fd359dc](https://github.com/openfoodfacts/open-prices/commit/fd359dc3b6635455e21c1df8393559d0a7c62224))
* new Product.brands_tags array field ([#207](https://github.com/openfoodfacts/open-prices/issues/207)) ([ba5b917](https://github.com/openfoodfacts/open-prices/commit/ba5b91711fe5585a46588219d68c763cf49ef57e))
* new Product.categories_tags array field ([#192](https://github.com/openfoodfacts/open-prices/issues/192)) ([e9d73ae](https://github.com/openfoodfacts/open-prices/commit/e9d73ae194629f52509a3098e88858536530e1d2))
* new Product.labels_tags array field ([#208](https://github.com/openfoodfacts/open-prices/issues/208)) ([95aa5fb](https://github.com/openfoodfacts/open-prices/commit/95aa5fb467011c2f566b7315b715c212de665056))
* new Product.product_quantity_unit field ([#194](https://github.com/openfoodfacts/open-prices/issues/194)) ([aa353bf](https://github.com/openfoodfacts/open-prices/commit/aa353bfa4a9730fd0fef1092e92fe5f070761bf5))
* new user.is_moderator field ([#183](https://github.com/openfoodfacts/open-prices/issues/183)) ([450305b](https://github.com/openfoodfacts/open-prices/commit/450305ba7c0868b2649a1b66e2867efa9632b1a1))
* on Price create, create (or get) Location, and link them ([#36](https://github.com/openfoodfacts/open-prices/issues/36)) ([003de11](https://github.com/openfoodfacts/open-prices/commit/003de11bb2ffc30e0e4af5631b1aa1fabc24a763))
* on Price create, create (or get) Product, and link them ([#45](https://github.com/openfoodfacts/open-prices/issues/45)) ([71cf40a](https://github.com/openfoodfacts/open-prices/commit/71cf40ac914599d7884f848ae09dde02402cf1c7))
* paginate, filter & order proofs ([#150](https://github.com/openfoodfacts/open-prices/issues/150)) ([ed53599](https://github.com/openfoodfacts/open-prices/commit/ed535992b4dc5228a82efe4163125dc45a942b18))
* Price model ([#23](https://github.com/openfoodfacts/open-prices/issues/23)) ([56a853b](https://github.com/openfoodfacts/open-prices/commit/56a853bc6c5da2271821e9b6d8ecaab661a9d232))
* price POST endpoint ([#24](https://github.com/openfoodfacts/open-prices/issues/24)) ([0bf98ca](https://github.com/openfoodfacts/open-prices/commit/0bf98cab7da5cae0554458b4bc7d03b8af896aff))
* **price:** add filter on created field ([689d4ab](https://github.com/openfoodfacts/open-prices/commit/689d4abc32ac487863985a896f58d36149dcc3f0))
* prices GET endpoint ([#26](https://github.com/openfoodfacts/open-prices/issues/26)) ([a769910](https://github.com/openfoodfacts/open-prices/commit/a769910b6aaded9c7f6c52942fdf93ba17a6e72c))
* products GET endpoint ([#122](https://github.com/openfoodfacts/open-prices/issues/122)) ([f80d80b](https://github.com/openfoodfacts/open-prices/commit/f80d80bf6370f80da5fe4eaa6551a92b01459e88))
* return Price.owner info ([6e922f3](https://github.com/openfoodfacts/open-prices/commit/6e922f30029a9f9558ff070d3dc7c4330dd7e08f))
* simple Location model ([#35](https://github.com/openfoodfacts/open-prices/issues/35)) ([32562ad](https://github.com/openfoodfacts/open-prices/commit/32562adcf52544a0ac388bdefa7df0cccdc3fb67))
* simple Product model ([#44](https://github.com/openfoodfacts/open-prices/issues/44)) ([2bfa8f6](https://github.com/openfoodfacts/open-prices/commit/2bfa8f682148b97299be2c7e483e16e93d743d0c))
* simply Price.currency validation ([#67](https://github.com/openfoodfacts/open-prices/issues/67)) ([d7dfb0c](https://github.com/openfoodfacts/open-prices/commit/d7dfb0cbb3d8e8efeb2f5e6b92cffb5296ab9863))
* User model ([#21](https://github.com/openfoodfacts/open-prices/issues/21)) ([556cc6f](https://github.com/openfoodfacts/open-prices/commit/556cc6f65ab25474c9be9ecd505ca99841906832))
* users GET endpoint ([#147](https://github.com/openfoodfacts/open-prices/issues/147)) ([6fdb640](https://github.com/openfoodfacts/open-prices/commit/6fdb640ade463d35356f8c6dfde56808520ebe00))


### Bug Fixes

* add --batch-size param to CLI command ([dca9098](https://github.com/openfoodfacts/open-prices/commit/dca9098e949c538e811ecb34a3439ad79137212c))
* add /api/v1 prefix to all relevant routes ([#74](https://github.com/openfoodfacts/open-prices/issues/74)) ([353e59f](https://github.com/openfoodfacts/open-prices/commit/353e59fb772c3067a1db5db4ecd8d6ad3fe49e60))
* add image serving ([5808b7a](https://github.com/openfoodfacts/open-prices/commit/5808b7a1effad8ccccdf88681f5a31aa2c77a891))
* add index on products.price_count field ([9fdfdcd](https://github.com/openfoodfacts/open-prices/commit/9fdfdcd14fc8322697f6d35a27846c310d552122))
* add missing filter on Product.product_id field. ref [#134](https://github.com/openfoodfacts/open-prices/issues/134) ([0ab9f9d](https://github.com/openfoodfacts/open-prices/commit/0ab9f9d286e83c926ece1e8719ab2323a88b1596))
* add prod env config ([8ced9d1](https://github.com/openfoodfacts/open-prices/commit/8ced9d17b1e7c2d56880cdff743fe81bf6c214b6))
* add status endpoint ([b3ddad9](https://github.com/openfoodfacts/open-prices/commit/b3ddad955d80b18b47e8a6fc855692eba16b1f55))
* always return proof.file_path for proof uploaded by the user ([#132](https://github.com/openfoodfacts/open-prices/issues/132)) ([fe14346](https://github.com/openfoodfacts/open-prices/commit/fe14346286fd5b645d610598bc3f70e5d8e8d831))
* better fetch location city from OSM. ref [#38](https://github.com/openfoodfacts/open-prices/issues/38) ([c37e7a6](https://github.com/openfoodfacts/open-prices/commit/c37e7a6e85b4999622cd503d7f65481f69050540))
* bump release please version ([a37e7da](https://github.com/openfoodfacts/open-prices/commit/a37e7daf66548b3c168491d7c68585ed4753c90e))
* CORS: revert configuration. add openfoodfacts-explorer to whitelist ([e3e9098](https://github.com/openfoodfacts/open-prices/commit/e3e9098a766785833500f4bcd0db545f4a374bbd))
* CORS: temporarily allow all origins in deployed envs. ref [#65](https://github.com/openfoodfacts/open-prices/issues/65) ([06f2560](https://github.com/openfoodfacts/open-prices/commit/06f2560906f64ceb5add4d850cb15ec15a98b425))
* fix AttributeError in fetch_product_openfoodfacts_details ([#161](https://github.com/openfoodfacts/open-prices/issues/161)) ([ffd9d65](https://github.com/openfoodfacts/open-prices/commit/ffd9d65bef7e744bdf6e3171e5cc6a3315287035))
* fix container deploy config ([36c4f1b](https://github.com/openfoodfacts/open-prices/commit/36c4f1b060045a98d9a00065664d945d3cd7e5b1))
* fix db error ([#125](https://github.com/openfoodfacts/open-prices/issues/125)) ([57e4adb](https://github.com/openfoodfacts/open-prices/commit/57e4adb41bf29ef94fc5542e3179141f28727c09))
* fix duplicate key error due to duplicate products ([bd6ff9c](https://github.com/openfoodfacts/open-prices/commit/bd6ff9c8b2d531a83469c232988a6c0352583887))
* fix email sign-in ([#170](https://github.com/openfoodfacts/open-prices/issues/170)) ([69d65c0](https://github.com/openfoodfacts/open-prices/commit/69d65c0278092bd43f461caa1913c891fee5174b))
* fix github config ([7edfa8d](https://github.com/openfoodfacts/open-prices/commit/7edfa8dd9b777c50be2f4f78aa43ef87dd7c93e2))
* fix labels_tags field validator ([#69](https://github.com/openfoodfacts/open-prices/issues/69)) ([5f23977](https://github.com/openfoodfacts/open-prices/commit/5f23977116d846acf288a031f70da0adac5ce34f))
* fix landing page ([cf9bb9d](https://github.com/openfoodfacts/open-prices/commit/cf9bb9d44c324e7b7a016be9ff2e1fdc23795917))
* fix locations GET filters. ref [#138](https://github.com/openfoodfacts/open-prices/issues/138) ([3d75e16](https://github.com/openfoodfacts/open-prices/commit/3d75e165d76b74e1ca352c080533d11cc66e0699))
* fix migration parent id. ref [#183](https://github.com/openfoodfacts/open-prices/issues/183) ([c62c52a](https://github.com/openfoodfacts/open-prices/commit/c62c52a33d1dde92e1e16f676afd9b79e27a365d))
* fix parsing bug in import_product_db ([#164](https://github.com/openfoodfacts/open-prices/issues/164)) ([40f2c2a](https://github.com/openfoodfacts/open-prices/commit/40f2c2afd094eef225ac8af3a1d89bd34d970e25))
* fix product_quantity DB error ([8196bc2](https://github.com/openfoodfacts/open-prices/commit/8196bc238b645d3f22d50e87bf3ba3d038fa7f85))
* fix product.unique_scans_n server_default ([54202d0](https://github.com/openfoodfacts/open-prices/commit/54202d002aad78f0ab3adf036f8eb8b1f7f27403))
* fix ProofCreate schema ([ed34567](https://github.com/openfoodfacts/open-prices/commit/ed345675a414a6f6aea43036de52a914239f9fc6))
* fix release please ([#78](https://github.com/openfoodfacts/open-prices/issues/78)) ([86bb591](https://github.com/openfoodfacts/open-prices/commit/86bb5911758c359d6e2218ac836191f58b91fc4f))
* fix some typos in the landing page ([#51](https://github.com/openfoodfacts/open-prices/issues/51)) ([e5fee84](https://github.com/openfoodfacts/open-prices/commit/e5fee84246304e375c3fa0421e08cdd53ba07ad1))
* fix tests following addition of Price.id field in schema. ref [#179](https://github.com/openfoodfacts/open-prices/issues/179) ([2818540](https://github.com/openfoodfacts/open-prices/commit/2818540040943bf56741909c8dbc7511564bcea5))
* fix unique_scans_n null values ([b967d5a](https://github.com/openfoodfacts/open-prices/commit/b967d5a4eb3a09f93aab4562f7c052d8db7f684a))
* improve landing page ([#71](https://github.com/openfoodfacts/open-prices/issues/71)) ([ec79ccc](https://github.com/openfoodfacts/open-prices/commit/ec79ccc3ff1eac44e65b98ed2e3561227648e674))
* improve price fetch performance ([#118](https://github.com/openfoodfacts/open-prices/issues/118)) ([1b65ea2](https://github.com/openfoodfacts/open-prices/commit/1b65ea22e31fdf38bcbadb58314e200ff095964c))
* lint last alembic version ([1b0667d](https://github.com/openfoodfacts/open-prices/commit/1b0667d09b19c4dc531c74eabdec85ec44caa23c))
* lowercase the user_id ([#215](https://github.com/openfoodfacts/open-prices/issues/215)) ([21444ff](https://github.com/openfoodfacts/open-prices/commit/21444ffeb86c9b3feaa9468ffcbb28e0421f7663))
* normalize all tags values ([9402bbb](https://github.com/openfoodfacts/open-prices/commit/9402bbb7dcbcfa44c65ce45639865ec91bd2e172))
* Product.brands should be a string. ref [#93](https://github.com/openfoodfacts/open-prices/issues/93) ([7bbf1fc](https://github.com/openfoodfacts/open-prices/commit/7bbf1fcdf470bf74546ac740870694017b1a35a1))
* return 201 instead of 200 on price (& proof) create ([#66](https://github.com/openfoodfacts/open-prices/issues/66)) ([af543cf](https://github.com/openfoodfacts/open-prices/commit/af543cf924f7502000d13b369717d7c22967d980))
* stop using global db, use get_db instead ([#30](https://github.com/openfoodfacts/open-prices/issues/30)) ([9739734](https://github.com/openfoodfacts/open-prices/commit/97397344b1e7ef7af17bc7a86445a651815a4f29))
* strip user_id ([66a9c04](https://github.com/openfoodfacts/open-prices/commit/66a9c046b4090fd9cc8db3dd923d6cb199925239))
* transform async func into func ([22a5f0d](https://github.com/openfoodfacts/open-prices/commit/22a5f0d32c44151b6816987c87829877d54ab798))
* update docker-compose.yml to add postgres service ([0b5c8af](https://github.com/openfoodfacts/open-prices/commit/0b5c8af7f713fd4a48a6bf56e011aa57dd1be588))
* update pre-commit config ([5cc63f4](https://github.com/openfoodfacts/open-prices/commit/5cc63f4116aa85c42f22aeae7a7531d946efb950))
* use black + isort on all files ([877f3c6](https://github.com/openfoodfacts/open-prices/commit/877f3c6a4a57553ae9604722b81ddacd426d722a))
* use opsession instead of session as cookie name ([#177](https://github.com/openfoodfacts/open-prices/issues/177)) ([dfd3e6a](https://github.com/openfoodfacts/open-prices/commit/dfd3e6ad18960b4560fdceb74171651256219fd4))
* use time.sleep instead of asyncio.sleep in non-corountine function ([1ccffd6](https://github.com/openfoodfacts/open-prices/commit/1ccffd6f5dfb22342bea65f63cb2cde39d5ac352))


### Technical

* add a link to the frontend repo ([#111](https://github.com/openfoodfacts/open-prices/issues/111)) ([cd2f34b](https://github.com/openfoodfacts/open-prices/commit/cd2f34b90d454ae708e08fb5994b0cecb256e728))
* add fr landing page ([#155](https://github.com/openfoodfacts/open-prices/issues/155)) ([c163bfd](https://github.com/openfoodfacts/open-prices/commit/c163bfda88c6dd842ce0938bae43c3de69ec3a3e))
* add gh_pages documentation ([6f8bf6e](https://github.com/openfoodfacts/open-prices/commit/6f8bf6e9de54ce5d9795871499d8c8190966d718))
* add github workflow to generate doc ([afb8344](https://github.com/openfoodfacts/open-prices/commit/afb83441d2f62e3f7294fb20c8e451989dc769f5))
* add migration files to docker image ([895fe93](https://github.com/openfoodfacts/open-prices/commit/895fe9329064b84067199d320492accaf3e29379))
* add poetry config instead of requirements.txt ([8791d8a](https://github.com/openfoodfacts/open-prices/commit/8791d8a5f213d6c7f27230a0a64b2acc1d6a1be9))
* add tutorial + improve main doc page ([#116](https://github.com/openfoodfacts/open-prices/issues/116)) ([a01a5a0](https://github.com/openfoodfacts/open-prices/commit/a01a5a0b043954fb0f5b7c7d078cfed5c91e55fb))
* add tutorial for multiple products (shop shelf) ([#176](https://github.com/openfoodfacts/open-prices/issues/176)) ([ab33fc2](https://github.com/openfoodfacts/open-prices/commit/ab33fc21b13fa1403d8720640749918fa2fec2ff))
* add typing information ([cc5e383](https://github.com/openfoodfacts/open-prices/commit/cc5e383c88bfb9fd69a309230ad691f3b1ac5757))
* allow deployment in prod ([e174992](https://github.com/openfoodfacts/open-prices/commit/e1749928b807c386842ab6634302bc90b7f28c75))
* fix container deploy ([87e245c](https://github.com/openfoodfacts/open-prices/commit/87e245c5f907978245294639f10b0db83e83a5ce))
* fix CORS config ([d4e363a](https://github.com/openfoodfacts/open-prices/commit/d4e363a1ccc24d883187cb370df1d15f7327a87b))
* fix deployment ([0722ee3](https://github.com/openfoodfacts/open-prices/commit/0722ee34c0dbe1639d955a14d59446f8dc7b39fd))
* fix deployment ([7c5e460](https://github.com/openfoodfacts/open-prices/commit/7c5e4607609493c88e7285ad4acc9b786aab476a))
* improve landing page ([#109](https://github.com/openfoodfacts/open-prices/issues/109)) ([ee2cbd8](https://github.com/openfoodfacts/open-prices/commit/ee2cbd869f25157204d942db3ce2c3e17b4439b5))
* improve setup documentation ([#15](https://github.com/openfoodfacts/open-prices/issues/15)) ([fa662c4](https://github.com/openfoodfacts/open-prices/commit/fa662c4346d4604f495a8520455d60f0c6b572f2))
* **main:** release 1.0.0 ([ef1c578](https://github.com/openfoodfacts/open-prices/commit/ef1c578206702f254e8c521a999b3123b282552f))
* **main:** release 1.0.1 ([0c306e3](https://github.com/openfoodfacts/open-prices/commit/0c306e372983c4b6ef65679bf7aed474bfd24d21))
* **main:** release 1.0.2 ([72d803b](https://github.com/openfoodfacts/open-prices/commit/72d803b34f6612e5c5a1912f6006998a62a7944f))
* **main:** release 1.0.3 ([fb949a3](https://github.com/openfoodfacts/open-prices/commit/fb949a3c337f921dae96ba4696d1c790ee293e88))
* **main:** release 1.1.0 ([#41](https://github.com/openfoodfacts/open-prices/issues/41)) ([954e0e7](https://github.com/openfoodfacts/open-prices/commit/954e0e7f5191b6b60a3876beb589a4cdb4c1108e))
* **main:** release 1.10.0 ([#139](https://github.com/openfoodfacts/open-prices/issues/139)) ([b36ab9f](https://github.com/openfoodfacts/open-prices/commit/b36ab9fc6651bb159170756cc81b94143cb75a7c))
* **main:** release 1.11.0 ([#141](https://github.com/openfoodfacts/open-prices/issues/141)) ([ea0f8e6](https://github.com/openfoodfacts/open-prices/commit/ea0f8e6f1c34faf6eb85678c83009275182eed0d))
* **main:** release 1.12.0 ([#145](https://github.com/openfoodfacts/open-prices/issues/145)) ([e343113](https://github.com/openfoodfacts/open-prices/commit/e343113b1e76520b417a31c5a275fe06abafd471))
* **main:** release 1.13.0 ([#151](https://github.com/openfoodfacts/open-prices/issues/151)) ([af856ea](https://github.com/openfoodfacts/open-prices/commit/af856ea5886b5c43c78127285b842e465908cf92))
* **main:** release 1.13.1 ([#159](https://github.com/openfoodfacts/open-prices/issues/159)) ([284a252](https://github.com/openfoodfacts/open-prices/commit/284a252ec6db7a86ed918d10f0d4071342b60b0b))
* **main:** release 1.14.0 ([#162](https://github.com/openfoodfacts/open-prices/issues/162)) ([1b8cd54](https://github.com/openfoodfacts/open-prices/commit/1b8cd547232be1929f03bedf422006439d0ed177))
* **main:** release 1.15.0 ([#169](https://github.com/openfoodfacts/open-prices/issues/169)) ([3d006b5](https://github.com/openfoodfacts/open-prices/commit/3d006b55162c53a34b0dda3e2c7e9c77ca825e30))
* **main:** release 1.16.0 ([#175](https://github.com/openfoodfacts/open-prices/issues/175)) ([2f039fe](https://github.com/openfoodfacts/open-prices/commit/2f039fe5138d3dea57807baa82bb0ba5238b305e))
* **main:** release 1.17.0 ([#186](https://github.com/openfoodfacts/open-prices/issues/186)) ([cf82069](https://github.com/openfoodfacts/open-prices/commit/cf8206932a900877981773418758d413b27e9503))
* **main:** release 1.18.0 ([#189](https://github.com/openfoodfacts/open-prices/issues/189)) ([8019beb](https://github.com/openfoodfacts/open-prices/commit/8019bebdd2191761af8c0baee48924d0420fa242))
* **main:** release 1.19.0 ([#196](https://github.com/openfoodfacts/open-prices/issues/196)) ([55b1e2e](https://github.com/openfoodfacts/open-prices/commit/55b1e2e2320dbc07e1154956f9fbd163c7b48c80))
* **main:** release 1.2.0 ([#55](https://github.com/openfoodfacts/open-prices/issues/55)) ([3f61b06](https://github.com/openfoodfacts/open-prices/commit/3f61b069f57f84af1347219b3ae2c1a1b69d63d1))
* **main:** release 1.2.1 ([#75](https://github.com/openfoodfacts/open-prices/issues/75)) ([25fdec8](https://github.com/openfoodfacts/open-prices/commit/25fdec8f23894fabb668f53f83af7d67880afe64))
* **main:** release 1.20.0 ([#211](https://github.com/openfoodfacts/open-prices/issues/211)) ([5dd11b0](https://github.com/openfoodfacts/open-prices/commit/5dd11b0b154e3e2812ce7d405e6b4bbf60acfba6))
* **main:** release 1.3.0 ([#86](https://github.com/openfoodfacts/open-prices/issues/86)) ([8b98d0d](https://github.com/openfoodfacts/open-prices/commit/8b98d0d062c47868c7bdf4940a1076ecda52ef57))
* **main:** release 1.4.0 ([#99](https://github.com/openfoodfacts/open-prices/issues/99)) ([4c355ce](https://github.com/openfoodfacts/open-prices/commit/4c355cece2e202b2b9ad07dea8817ab227340f80))
* **main:** release 1.4.1 ([#101](https://github.com/openfoodfacts/open-prices/issues/101)) ([1c51e73](https://github.com/openfoodfacts/open-prices/commit/1c51e734a6b37cea5c7f7e4c09de37dda122048b))
* **main:** release 1.4.2 ([#102](https://github.com/openfoodfacts/open-prices/issues/102)) ([3ed09e2](https://github.com/openfoodfacts/open-prices/commit/3ed09e21639596c460573c13a72694703f3fe3df))
* **main:** release 1.5.0 ([#105](https://github.com/openfoodfacts/open-prices/issues/105)) ([4bfc6b9](https://github.com/openfoodfacts/open-prices/commit/4bfc6b91d3e546da19184a258100570fcf9abdda))
* **main:** release 1.6.0 ([#112](https://github.com/openfoodfacts/open-prices/issues/112)) ([7f006ab](https://github.com/openfoodfacts/open-prices/commit/7f006abed633c5dad9a55c5af938119c45e6ba12))
* **main:** release 1.6.1 ([#117](https://github.com/openfoodfacts/open-prices/issues/117)) ([970ff2c](https://github.com/openfoodfacts/open-prices/commit/970ff2c2cfc55c57cda21e79b15d891e5dce9f4b))
* **main:** release 1.7.0 ([#120](https://github.com/openfoodfacts/open-prices/issues/120)) ([27b7f0f](https://github.com/openfoodfacts/open-prices/commit/27b7f0faac4642f44657ca4668c99c11b891e1f9))
* **main:** release 1.8.0 ([#128](https://github.com/openfoodfacts/open-prices/issues/128)) ([e3acac0](https://github.com/openfoodfacts/open-prices/commit/e3acac0b9fb7c29582661fe73351f88b85fd7e3b))
* **main:** release 1.9.0 ([#133](https://github.com/openfoodfacts/open-prices/issues/133)) ([8c32836](https://github.com/openfoodfacts/open-prices/commit/8c32836382c46ea71eb7055eb9c7cc22866a3cfd))
* **main:** release 1.9.1 ([#136](https://github.com/openfoodfacts/open-prices/issues/136)) ([415336c](https://github.com/openfoodfacts/open-prices/commit/415336cbd5b21c35ed3985856603b0d3919d1476))
* make migration files available in dev ([494bb96](https://github.com/openfoodfacts/open-prices/commit/494bb96564830d4557c935e54fac8d105238e73d))
* migrate before deployment ([#52](https://github.com/openfoodfacts/open-prices/issues/52)) ([bb91bfc](https://github.com/openfoodfacts/open-prices/commit/bb91bfc4242a5ea541856f0332c5519a0d01deeb))
* rename schemas to clarify ([#146](https://github.com/openfoodfacts/open-prices/issues/146)) ([e0e3896](https://github.com/openfoodfacts/open-prices/commit/e0e3896777b84b1d572a2a82056f7247aed49e3e))
* replace venv with poetry ([#54](https://github.com/openfoodfacts/open-prices/issues/54)) ([249c092](https://github.com/openfoodfacts/open-prices/commit/249c09286a0062f2e0f153e8b2a2cc86acc1c3b3))
* **tutorial:** fix OpenStreetMap name ([#168](https://github.com/openfoodfacts/open-prices/issues/168)) ([180c6e6](https://github.com/openfoodfacts/open-prices/commit/180c6e64a6285b5846d0adc61aeb2abcf49cd395))
* update tutorial to add a price ([#157](https://github.com/openfoodfacts/open-prices/issues/157)) ([0ebbbe0](https://github.com/openfoodfacts/open-prices/commit/0ebbbe0c9c41dc83377366f29ada964cb5a487b6))
* Welcome users ([#173](https://github.com/openfoodfacts/open-prices/issues/173)) ([d59d1da](https://github.com/openfoodfacts/open-prices/commit/d59d1da77c5eda449a997c863195e900433a41ee))

## [1.20.0](https://github.com/openfoodfacts/open-prices/compare/v1.19.0...v1.20.0) (2024-02-21)


### Features

* new Product.brands_tags array field ([#207](https://github.com/openfoodfacts/open-prices/issues/207)) ([ba5b917](https://github.com/openfoodfacts/open-prices/commit/ba5b91711fe5585a46588219d68c763cf49ef57e))
* new Product.categories_tags array field ([#192](https://github.com/openfoodfacts/open-prices/issues/192)) ([e9d73ae](https://github.com/openfoodfacts/open-prices/commit/e9d73ae194629f52509a3098e88858536530e1d2))
* new Product.labels_tags array field ([#208](https://github.com/openfoodfacts/open-prices/issues/208)) ([95aa5fb](https://github.com/openfoodfacts/open-prices/commit/95aa5fb467011c2f566b7315b715c212de665056))


### Bug Fixes

* normalize all tags values ([9402bbb](https://github.com/openfoodfacts/open-prices/commit/9402bbb7dcbcfa44c65ce45639865ec91bd2e172))

## [1.19.0](https://github.com/openfoodfacts/open-prices/compare/v1.18.0...v1.19.0) (2024-02-08)


### Features

* new DELETE proofs endpoint ([#197](https://github.com/openfoodfacts/open-prices/issues/197)) ([6066982](https://github.com/openfoodfacts/open-prices/commit/6066982a0d31458fe65ab23b8c503e86280a424c))
* new Product.product_quantity_unit field ([#194](https://github.com/openfoodfacts/open-prices/issues/194)) ([aa353bf](https://github.com/openfoodfacts/open-prices/commit/aa353bfa4a9730fd0fef1092e92fe5f070761bf5))


### Bug Fixes

* fix tests following addition of Price.id field in schema. ref [#179](https://github.com/openfoodfacts/open-prices/issues/179) ([2818540](https://github.com/openfoodfacts/open-prices/commit/2818540040943bf56741909c8dbc7511564bcea5))

## [1.18.0](https://github.com/openfoodfacts/open-prices/compare/v1.17.0...v1.18.0) (2024-02-06)


### Features

* new DELETE prices endpoint ([#179](https://github.com/openfoodfacts/open-prices/issues/179)) ([35d9f6e](https://github.com/openfoodfacts/open-prices/commit/35d9f6e96e65102af34382d03670f5e6bb55a761))
* new user.is_moderator field ([#183](https://github.com/openfoodfacts/open-prices/issues/183)) ([450305b](https://github.com/openfoodfacts/open-prices/commit/450305ba7c0868b2649a1b66e2867efa9632b1a1))


### Bug Fixes

* fix migration parent id. ref [#183](https://github.com/openfoodfacts/open-prices/issues/183) ([c62c52a](https://github.com/openfoodfacts/open-prices/commit/c62c52a33d1dde92e1e16f676afd9b79e27a365d))

## [1.17.0](https://github.com/openfoodfacts/open-prices/compare/v1.16.0...v1.17.0) (2024-02-04)


### Features

* add filter on Proof.price_count field ([#187](https://github.com/openfoodfacts/open-prices/issues/187)) ([0068cd5](https://github.com/openfoodfacts/open-prices/commit/0068cd56c4b585e95d02f885911de5bd88556c31))
* add proof.price_count to keep track of number of prices ([#185](https://github.com/openfoodfacts/open-prices/issues/185)) ([1637f36](https://github.com/openfoodfacts/open-prices/commit/1637f362a0353801c3813da29709f3c202fea31c))

## [1.16.0](https://github.com/openfoodfacts/open-prices/compare/v1.15.0...v1.16.0) (2024-01-31)


### Features

* add an endpoint to delete a session ([#174](https://github.com/openfoodfacts/open-prices/issues/174)) ([a2955dc](https://github.com/openfoodfacts/open-prices/commit/a2955dc130c4edaa05177682a16c61a075615110))


### Bug Fixes

* use opsession instead of session as cookie name ([#177](https://github.com/openfoodfacts/open-prices/issues/177)) ([dfd3e6a](https://github.com/openfoodfacts/open-prices/commit/dfd3e6ad18960b4560fdceb74171651256219fd4))


### Technical

* add tutorial for multiple products (shop shelf) ([#176](https://github.com/openfoodfacts/open-prices/issues/176)) ([ab33fc2](https://github.com/openfoodfacts/open-prices/commit/ab33fc21b13fa1403d8720640749918fa2fec2ff))
* Welcome users ([#173](https://github.com/openfoodfacts/open-prices/issues/173)) ([d59d1da](https://github.com/openfoodfacts/open-prices/commit/d59d1da77c5eda449a997c863195e900433a41ee))

## [1.15.0](https://github.com/openfoodfacts/open-prices/compare/v1.14.0...v1.15.0) (2024-01-26)


### Features

* **price:** add filter on created field ([689d4ab](https://github.com/openfoodfacts/open-prices/commit/689d4abc32ac487863985a896f58d36149dcc3f0))


### Bug Fixes

* fix email sign-in ([#170](https://github.com/openfoodfacts/open-prices/issues/170)) ([69d65c0](https://github.com/openfoodfacts/open-prices/commit/69d65c0278092bd43f461caa1913c891fee5174b))


### Technical

* **tutorial:** fix OpenStreetMap name ([#168](https://github.com/openfoodfacts/open-prices/issues/168)) ([180c6e6](https://github.com/openfoodfacts/open-prices/commit/180c6e64a6285b5846d0adc61aeb2abcf49cd395))

## [1.14.0](https://github.com/openfoodfacts/open-prices/compare/v1.13.1...v1.14.0) (2024-01-25)


### Features

* add price.price_is_discounted field ([#163](https://github.com/openfoodfacts/open-prices/issues/163)) ([a73e460](https://github.com/openfoodfacts/open-prices/commit/a73e4606846e08261a9cc00d1d56fa82c5d23382))


### Bug Fixes

* fix AttributeError in fetch_product_openfoodfacts_details ([#161](https://github.com/openfoodfacts/open-prices/issues/161)) ([ffd9d65](https://github.com/openfoodfacts/open-prices/commit/ffd9d65bef7e744bdf6e3171e5cc6a3315287035))
* fix parsing bug in import_product_db ([#164](https://github.com/openfoodfacts/open-prices/issues/164)) ([40f2c2a](https://github.com/openfoodfacts/open-prices/commit/40f2c2afd094eef225ac8af3a1d89bd34d970e25))

## [1.13.1](https://github.com/openfoodfacts/open-prices/compare/v1.13.0...v1.13.1) (2024-01-24)


### Technical

* update tutorial to add a price ([#157](https://github.com/openfoodfacts/open-prices/issues/157)) ([0ebbbe0](https://github.com/openfoodfacts/open-prices/commit/0ebbbe0c9c41dc83377366f29ada964cb5a487b6))

## [1.13.0](https://github.com/openfoodfacts/open-prices/compare/v1.12.0...v1.13.0) (2024-01-19)


### Features

* add user sessions ([#149](https://github.com/openfoodfacts/open-prices/issues/149)) ([a23977e](https://github.com/openfoodfacts/open-prices/commit/a23977e2b1943ecda64fccb22f3b399121c5ab89)), closes [#148](https://github.com/openfoodfacts/open-prices/issues/148)
* paginate, filter & order proofs ([#150](https://github.com/openfoodfacts/open-prices/issues/150)) ([ed53599](https://github.com/openfoodfacts/open-prices/commit/ed535992b4dc5228a82efe4163125dc45a942b18))


### Technical

* add fr landing page ([#155](https://github.com/openfoodfacts/open-prices/issues/155)) ([c163bfd](https://github.com/openfoodfacts/open-prices/commit/c163bfda88c6dd842ce0938bae43c3de69ec3a3e))

## [1.12.0](https://github.com/openfoodfacts/open-prices/compare/v1.11.0...v1.12.0) (2024-01-14)


### Features

* add user.price_count to keep track of number of prices ([#143](https://github.com/openfoodfacts/open-prices/issues/143)) ([0f13566](https://github.com/openfoodfacts/open-prices/commit/0f135668cc949c5d19d4fa0bbb6d5bb396576428))
* **auth:** avoid recreating existing user on login ([#144](https://github.com/openfoodfacts/open-prices/issues/144)) ([502539c](https://github.com/openfoodfacts/open-prices/commit/502539cfbbc06a70912ee153744658526f4dd6a4))
* users GET endpoint ([#147](https://github.com/openfoodfacts/open-prices/issues/147)) ([6fdb640](https://github.com/openfoodfacts/open-prices/commit/6fdb640ade463d35356f8c6dfde56808520ebe00))


### Bug Fixes

* fix locations GET filters. ref [#138](https://github.com/openfoodfacts/open-prices/issues/138) ([3d75e16](https://github.com/openfoodfacts/open-prices/commit/3d75e165d76b74e1ca352c080533d11cc66e0699))


### Technical

* rename schemas to clarify ([#146](https://github.com/openfoodfacts/open-prices/issues/146)) ([e0e3896](https://github.com/openfoodfacts/open-prices/commit/e0e3896777b84b1d572a2a82056f7247aed49e3e))

## [1.11.0](https://github.com/openfoodfacts/open-prices/compare/v1.10.0...v1.11.0) (2024-01-14)


### Features

* add location filter on price_count ([#142](https://github.com/openfoodfacts/open-prices/issues/142)) ([1237687](https://github.com/openfoodfacts/open-prices/commit/12376873395eedebcd9f0246c9a7cb5ebffa9ff7))
* add location.price_count to keep track of number of prices ([#140](https://github.com/openfoodfacts/open-prices/issues/140)) ([817663f](https://github.com/openfoodfacts/open-prices/commit/817663f4d2564fb3e0b3e0ba913652ac934a7b74))

## [1.10.0](https://github.com/openfoodfacts/open-prices/compare/v1.9.1...v1.10.0) (2024-01-13)


### Features

* locations GET endpoint ([#138](https://github.com/openfoodfacts/open-prices/issues/138)) ([300697f](https://github.com/openfoodfacts/open-prices/commit/300697f0f7c12ae308a5e0a04cd5515afdda720f))

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
