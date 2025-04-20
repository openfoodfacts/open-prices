# Changelog

## [1.74.2](https://github.com/openfoodfacts/open-prices/compare/v1.74.1...v1.74.2) (2025-04-20)


### Technical

* **Challenges:** move 'status' to a property (instead of a field) ([#803](https://github.com/openfoodfacts/open-prices/issues/803)) ([1369fb6](https://github.com/openfoodfacts/open-prices/commit/1369fb6e11a5f43a4e060a557f1c70b1f535d5c5))

## [1.74.1](https://github.com/openfoodfacts/open-prices/compare/v1.74.0...v1.74.1) (2025-04-18)


### Technical

* **API:** Prices: allow multiple (overlap) filter on product categories_tags field ([#799](https://github.com/openfoodfacts/open-prices/issues/799)) ([9fd1d28](https://github.com/openfoodfacts/open-prices/commit/9fd1d284b6e6697fa728a114dc9d06fdb65dc6c8))

## [1.74.0](https://github.com/openfoodfacts/open-prices/compare/v1.73.0...v1.74.0) (2025-04-10)


### Features

* **Receipt Item:** script to match historical ReceiptItem with their prices ([#788](https://github.com/openfoodfacts/open-prices/issues/788)) ([d7a0421](https://github.com/openfoodfacts/open-prices/commit/d7a0421c65b0609a5f504302166b6fcc0af27c62))


### Bug Fixes

* **Prices:** Allow 3 decimals on the receipt_quantity field ([#795](https://github.com/openfoodfacts/open-prices/issues/795)) ([eb23a0b](https://github.com/openfoodfacts/open-prices/commit/eb23a0bbd847f42e8fa02831dd327182821bb184))

## [1.73.0](https://github.com/openfoodfacts/open-prices/compare/v1.72.0...v1.73.0) (2025-03-30)


### Features

* **ProofMl:** Added ReceiptItem model and API ([#778](https://github.com/openfoodfacts/open-prices/issues/778)) ([fc22a1c](https://github.com/openfoodfacts/open-prices/commit/fc22a1c687d51137c4667478494237bfd9ce972d))


### Technical

* **docs:** create dotenv example file, ignore the local one ([#784](https://github.com/openfoodfacts/open-prices/issues/784)) ([f55299b](https://github.com/openfoodfacts/open-prices/commit/f55299bbf8fdb82c0a30264877de1ab9f5f15ec0))
* **docs:** revert [#784](https://github.com/openfoodfacts/open-prices/issues/784) (create dotenv example file, ignore the local one) ([#787](https://github.com/openfoodfacts/open-prices/issues/787)) ([3918972](https://github.com/openfoodfacts/open-prices/commit/3918972db92edf16cee3480d6bd681d558980070))
* Move match_decimal_with_float to common utils. Add tests ([2f55f53](https://github.com/openfoodfacts/open-prices/commit/2f55f534e7c4e94278ea61dc25a944c88c7107f0))
* **Price tags:** matching script: fix script for category_tag. add tests ([#786](https://github.com/openfoodfacts/open-prices/issues/786)) ([9783439](https://github.com/openfoodfacts/open-prices/commit/9783439f584af7ea149ee8de3a825f75a6dd3102))

## [1.72.0](https://github.com/openfoodfacts/open-prices/compare/v1.71.1...v1.72.0) (2025-03-23)


### Features

* **Prices:** API: new filter on `kind` ([#777](https://github.com/openfoodfacts/open-prices/issues/777)) ([5edfb71](https://github.com/openfoodfacts/open-prices/commit/5edfb71ee497c1d3e79470031f361da2fae12b18))
* **Proofs:** API: new filter on `kind` ([#776](https://github.com/openfoodfacts/open-prices/issues/776)) ([308d49b](https://github.com/openfoodfacts/open-prices/commit/308d49b56a27da491c12b8c6c9c91cf000174ba5))
* **Users:** new price count per type (product or category) ([#771](https://github.com/openfoodfacts/open-prices/issues/771)) ([4160eea](https://github.com/openfoodfacts/open-prices/commit/4160eeaedabbb26ab355c1df1963252295686581))


### Technical

* **Auth:** Drop invalid json parser from post api ([#769](https://github.com/openfoodfacts/open-prices/issues/769)) ([8dc930e](https://github.com/openfoodfacts/open-prices/commit/8dc930e1a4d81c8404ef4d5840b7024e37efc6db))
* **Prices:** rename type_group to kind (community & consumption) ([#775](https://github.com/openfoodfacts/open-prices/issues/775)) ([5461b99](https://github.com/openfoodfacts/open-prices/commit/5461b998029f6d124177abf07092979d7156cc78))
* **Proofs:** rename type_group to kind (community & consumption) ([#774](https://github.com/openfoodfacts/open-prices/issues/774)) ([c298144](https://github.com/openfoodfacts/open-prices/commit/c298144d5311f3e29b44a87d5ea3120371861d34))
* **Proofs:** take owner_consumption into account to differentiate community & consumption ([#773](https://github.com/openfoodfacts/open-prices/issues/773)) ([1ffb7e0](https://github.com/openfoodfacts/open-prices/commit/1ffb7e0a98d39e680b32716a5fa830f8d7414e32))

## [1.71.1](https://github.com/openfoodfacts/open-prices/compare/v1.71.0...v1.71.1) (2025-03-22)


### Technical

* **deps:** Update django-related packages ([#768](https://github.com/openfoodfacts/open-prices/issues/768)) ([3dbc5d1](https://github.com/openfoodfacts/open-prices/commit/3dbc5d1df68f270375b007833f81164e73196ef7))
* **Proofs:** API: allow multiple filters on `type` ([#766](https://github.com/openfoodfacts/open-prices/issues/766)) ([2085158](https://github.com/openfoodfacts/open-prices/commit/2085158b4cfa526279603de7d15b6f1b80c9c7a0))

## [1.71.0](https://github.com/openfoodfacts/open-prices/compare/v1.70.0...v1.71.0) (2025-03-18)


### Features

* **Moderation:** script to remove Products (and their prices) with invalid barcodes ([#761](https://github.com/openfoodfacts/open-prices/issues/761)) ([b39ea42](https://github.com/openfoodfacts/open-prices/commit/b39ea4215a00c7e0607973fb358e6c3784fb3043))


### Technical

* **PriceTags:** new FK to link to the proof_prediction ([#763](https://github.com/openfoodfacts/open-prices/issues/763)) ([02ecb0e](https://github.com/openfoodfacts/open-prices/commit/02ecb0e228d49344ed1466dd36825efe98bd7e43))

## [1.70.0](https://github.com/openfoodfacts/open-prices/compare/v1.69.0...v1.70.0) (2025-03-17)


### Features

* **Challenges:** add a new `status` field (read-only, calculated) ([#759](https://github.com/openfoodfacts/open-prices/issues/759)) ([c3880ba](https://github.com/openfoodfacts/open-prices/commit/c3880ba250de1181b5e21cacaead052887c49c0b))
* **Challenges:** basic model and API endpoint ([#758](https://github.com/openfoodfacts/open-prices/issues/758)) ([48c4348](https://github.com/openfoodfacts/open-prices/commit/48c4348c2af063db2bd38c61c2660c81f8587364))


### Technical

* **API:** better indicate which endpoints require authentication ([#754](https://github.com/openfoodfacts/open-prices/issues/754)) ([3659f8b](https://github.com/openfoodfacts/open-prices/commit/3659f8b4055dfeb6f2a32c16fee19060fd3e3668))

## [1.69.0](https://github.com/openfoodfacts/open-prices/compare/v1.68.1...v1.69.0) (2025-03-08)


### Features

* **Prices:** new owner_comment field ([#747](https://github.com/openfoodfacts/open-prices/issues/747)) ([2443716](https://github.com/openfoodfacts/open-prices/commit/24437165299abe9b35a8c040ac365cc407e3589f))
* **Proofs:** new owner_comment field ([#748](https://github.com/openfoodfacts/open-prices/issues/748)) ([04672c7](https://github.com/openfoodfacts/open-prices/commit/04672c73138c7ae4299c7410038e6886d48a4eba))
* **Proofs:** new owner_consumption field ([#750](https://github.com/openfoodfacts/open-prices/issues/750)) ([9349374](https://github.com/openfoodfacts/open-prices/commit/934937428804003903993f25c803ac2db5812f93))
* **Users:** new price count on owned (and not owned) proofs ([#744](https://github.com/openfoodfacts/open-prices/issues/744)) ([0e56244](https://github.com/openfoodfacts/open-prices/commit/0e56244c03c02d550f853d96c8ba4df00833c37b))


### Technical

* **API:** custom paginated response schema ([#751](https://github.com/openfoodfacts/open-prices/issues/751)) ([eb719a3](https://github.com/openfoodfacts/open-prices/commit/eb719a32f76a65b48937445e12d2984e371f9564))
* **API:** set default size to 10. and limit max size to 100 ([#752](https://github.com/openfoodfacts/open-prices/issues/752)) ([7f0434b](https://github.com/openfoodfacts/open-prices/commit/7f0434b87e4b5b82fc7398239907bf7a4ce8de99))
* **Users:** rename stat field to price_not_owned_in_proof_owned_count. ref [#744](https://github.com/openfoodfacts/open-prices/issues/744) ([8f70777](https://github.com/openfoodfacts/open-prices/commit/8f707771cd65bb89a4139f6c9ca894cb6460d02c))

## [1.68.1](https://github.com/openfoodfacts/open-prices/compare/v1.68.0...v1.68.1) (2025-03-04)


### Bug Fixes

* **Proofs:** allow updating the receipt_online_delivery_costs field. ref [#724](https://github.com/openfoodfacts/open-prices/issues/724) ([49fb711](https://github.com/openfoodfacts/open-prices/commit/49fb711e530de64f8cd9f4f0dec60eb39542712f))

## [1.68.0](https://github.com/openfoodfacts/open-prices/compare/v1.67.0...v1.68.0) (2025-03-02)


### Features

* **Prices:** API: new filter on proof type ([#741](https://github.com/openfoodfacts/open-prices/issues/741)) ([a41c868](https://github.com/openfoodfacts/open-prices/commit/a41c868bafd445ffc52316a87bc7f66e8662a923))
* **Stats:** new price_location_country_count field ([#740](https://github.com/openfoodfacts/open-prices/issues/740)) ([94fb106](https://github.com/openfoodfacts/open-prices/commit/94fb1064a0d89cb760c144fea4fa34873561a5dd))
* **Stats:** new price_year_count field ([#738](https://github.com/openfoodfacts/open-prices/issues/738)) ([16e0e59](https://github.com/openfoodfacts/open-prices/commit/16e0e59556b3fa7bd5c40de8b1b16736c93a5424))

## [1.67.0](https://github.com/openfoodfacts/open-prices/compare/v1.66.0...v1.67.0) (2025-03-01)


### Features

* **Stats:** new Price & Proof counts per source ([#736](https://github.com/openfoodfacts/open-prices/issues/736)) ([c3352bd](https://github.com/openfoodfacts/open-prices/commit/c3352bd90104045c0f2ad67979a1d6158eefb0f7))


### Technical

* **GDPR:** Improve script (fixes for Carrefour, Auchan) ([#731](https://github.com/openfoodfacts/open-prices/issues/731)) ([509dad6](https://github.com/openfoodfacts/open-prices/commit/509dad6578fb473e8fc196e006767c3b382aa347))

## [1.66.0](https://github.com/openfoodfacts/open-prices/compare/v1.65.1...v1.66.0) (2025-02-23)


### Features

* **Prices:** Stats: new community & consumption counts ([#728](https://github.com/openfoodfacts/open-prices/issues/728)) ([5320afc](https://github.com/openfoodfacts/open-prices/commit/5320afc6004f0714d20dcfe1bd8a58a4f3fd028d))
* **Proofs:** new receipt_online_delivery_costs field ([#724](https://github.com/openfoodfacts/open-prices/issues/724)) ([e2d56d4](https://github.com/openfoodfacts/open-prices/commit/e2d56d4ae3000f017c378ab3af862fda96ec167b))
* **Proofs:** Stats: new community & consumption counts ([#725](https://github.com/openfoodfacts/open-prices/issues/725)) ([f9960d0](https://github.com/openfoodfacts/open-prices/commit/f9960d0c86d0168172628a5db7ce4b25185c345d))
* **Users:** new price counts per community & consumption type groups ([#729](https://github.com/openfoodfacts/open-prices/issues/729)) ([5431923](https://github.com/openfoodfacts/open-prices/commit/54319239e8a4755f947d09bd481ad5085597ce99))
* **Users:** new proof counts per community & consumption type groups ([#730](https://github.com/openfoodfacts/open-prices/issues/730)) ([ccf25e8](https://github.com/openfoodfacts/open-prices/commit/ccf25e8e2024c0b37ebad1d7820a99ba47636226))


### Bug Fixes

* **Proofs:** Stats: fix typo in proof_type_group_community_count calculation. ref [#725](https://github.com/openfoodfacts/open-prices/issues/725) ([e25ae64](https://github.com/openfoodfacts/open-prices/commit/e25ae64e784aad9f9333fcba1e107f8314c4451e))


### Technical

* **Prices:** add a new discount_type: Second hand ([#722](https://github.com/openfoodfacts/open-prices/issues/722)) ([ae6782f](https://github.com/openfoodfacts/open-prices/commit/ae6782f05c3629778de279345c84502b9f2ac05b))
* **Proofs:** rename some constants, introduce GROUP_COMMUNITY & GROUP_CONSUMPTION ([#726](https://github.com/openfoodfacts/open-prices/issues/726)) ([4d3799b](https://github.com/openfoodfacts/open-prices/commit/4d3799b6b2cdd3e37f3a99e012a2814153df39b5))

## [1.65.1](https://github.com/openfoodfacts/open-prices/compare/v1.65.0...v1.65.1) (2025-02-22)


### Bug Fixes

* **Proofs:** ML: fix typo in gemini result. ref [#718](https://github.com/openfoodfacts/open-prices/issues/718) ([e133216](https://github.com/openfoodfacts/open-prices/commit/e1332167aac9ac63c531d2cb7059c77f5ec88d01))

## [1.65.0](https://github.com/openfoodfacts/open-prices/compare/v1.64.0...v1.65.0) (2025-02-22)


### Features

* **Proofs:** ML: receipt content extraction ([#715](https://github.com/openfoodfacts/open-prices/issues/715)) ([11dad87](https://github.com/openfoodfacts/open-prices/commit/11dad873450ece30a6d560bc7041b9495979b33b))


### Technical

* **API:** return proof/price/location source field ([#719](https://github.com/openfoodfacts/open-prices/issues/719)) ([5a6cb3e](https://github.com/openfoodfacts/open-prices/commit/5a6cb3ed392a9351b8ab2ee21894b7962c5e07c3))
* **Prices:** Stats: new stat with_discount count ([#716](https://github.com/openfoodfacts/open-prices/issues/716)) ([d05320f](https://github.com/openfoodfacts/open-prices/commit/d05320fde7a9444c2cc257bcbff8246594e1378f))
* **Proofs:** ML: move some config to a dedicated google.py file ([#718](https://github.com/openfoodfacts/open-prices/issues/718)) ([3f4da4c](https://github.com/openfoodfacts/open-prices/commit/3f4da4c359941a461badce3161587def3d019ff3))

## [1.64.0](https://github.com/openfoodfacts/open-prices/compare/v1.63.0...v1.64.0) (2025-02-20)


### Features

* **Prices:** new `discount_type` field with a list of choices ([#711](https://github.com/openfoodfacts/open-prices/issues/711)) ([521dc19](https://github.com/openfoodfacts/open-prices/commit/521dc1922258a7059934bd44b412163729d4ab3c))


### Technical

* fix deploy proxy host ([#714](https://github.com/openfoodfacts/open-prices/issues/714)) ([c3da43f](https://github.com/openfoodfacts/open-prices/commit/c3da43f7939b3f24e7dc6422c41a022e3840cfb8))

## [1.63.0](https://github.com/openfoodfacts/open-prices/compare/v1.62.3...v1.63.0) (2025-02-12)


### Features

* **Products:** Stats: new counts per source (OxF flavors) ([#708](https://github.com/openfoodfacts/open-prices/issues/708)) ([3ad9f6b](https://github.com/openfoodfacts/open-prices/commit/3ad9f6b56cfa102f9848c333803ffcdca8683424))


### Technical

* **Price tags:** Make ready_for_price_tag_validation field editable by user ([#710](https://github.com/openfoodfacts/open-prices/issues/710)) ([62248a6](https://github.com/openfoodfacts/open-prices/commit/62248a6265c9fa8e1c1f11439aada7aca3d4972c))

## [1.62.3](https://github.com/openfoodfacts/open-prices/compare/v1.62.2...v1.62.3) (2025-02-05)


### Technical

* **Product sync:** add settings to opt-in to OxF daily syncs ([#705](https://github.com/openfoodfacts/open-prices/issues/705)) ([114e448](https://github.com/openfoodfacts/open-prices/commit/114e448eddc969ad3ccf3ebcf21258ba6fc64ac7))
* **Product sync:** disable OFF daily sync (now that we have Redis live updates) ([#707](https://github.com/openfoodfacts/open-prices/issues/707)) ([e81bace](https://github.com/openfoodfacts/open-prices/commit/e81bace82c599df606a78b37d3decb9057317189))

## [1.62.2](https://github.com/openfoodfacts/open-prices/compare/v1.62.1...v1.62.2) (2025-02-03)


### Technical

* **Price tags:** add a new status 'truncated' ([#702](https://github.com/openfoodfacts/open-prices/issues/702)) ([db6f4dc](https://github.com/openfoodfacts/open-prices/commit/db6f4dc6f15e87ad89bde05894846d6e831c56b4))

## [1.62.1](https://github.com/openfoodfacts/open-prices/compare/v1.62.0...v1.62.1) (2025-02-02)


### Technical

* **Price tags:** API: allow filtering by the new prediction_count field (gte & lte). ref [#695](https://github.com/openfoodfacts/open-prices/issues/695) ([512e875](https://github.com/openfoodfacts/open-prices/commit/512e87517d9dce064090839f0c22c88eac99b1a6))
* **Proofs:** API: allow filtering by the new prediction_count field (gte & lte). ref [#693](https://github.com/openfoodfacts/open-prices/issues/693) ([6539cf0](https://github.com/openfoodfacts/open-prices/commit/6539cf087f0604262dc9f7e06da127bae94c4890))

## [1.62.0](https://github.com/openfoodfacts/open-prices/compare/v1.61.0...v1.62.0) (2025-02-02)


### Features

* **Moderation:** script to remove Products with long barcodes ([#700](https://github.com/openfoodfacts/open-prices/issues/700)) ([33ff94d](https://github.com/openfoodfacts/open-prices/commit/33ff94d9ac14d57378092529c4038a70fb33f49f))
* **Products:** Stats: new location country count & price currency count ([#699](https://github.com/openfoodfacts/open-prices/issues/699)) ([3e9c58c](https://github.com/openfoodfacts/open-prices/commit/3e9c58cc6d6b0a6d03440257cfac95fa6b4b25c5))
* **Users:** Stats: new location country count & price currency count ([#698](https://github.com/openfoodfacts/open-prices/issues/698)) ([6834f9c](https://github.com/openfoodfacts/open-prices/commit/6834f9cb49c3ad04e4fd70db90c63dfc67ef9705))


### Technical

* **Stats:** New location country count & price currency count ([#696](https://github.com/openfoodfacts/open-prices/issues/696)) ([0e2f575](https://github.com/openfoodfacts/open-prices/commit/0e2f575699c7cdaee8ec8fcece76c0d2a2d48631))

## [1.61.0](https://github.com/openfoodfacts/open-prices/compare/v1.60.3...v1.61.0) (2025-02-02)


### Features

* **Price tags:** new prediction_count field (automatically incremented) ([#695](https://github.com/openfoodfacts/open-prices/issues/695)) ([f1a5884](https://github.com/openfoodfacts/open-prices/commit/f1a5884299b0fca8bde03bbf0891b8f1a3130a5f))
* **Proofs:** new prediction_count field (automatically incremented) ([#693](https://github.com/openfoodfacts/open-prices/issues/693)) ([8bbae67](https://github.com/openfoodfacts/open-prices/commit/8bbae67fa762d1734e82acb658eb888d7888ff51))


### Technical

* **Price tags:** API: allow filtering by the new prediction_count field. ref [#695](https://github.com/openfoodfacts/open-prices/issues/695) ([6c319be](https://github.com/openfoodfacts/open-prices/commit/6c319bea787753d3dc57800fac01ea7e3ca29df2))

## [1.60.3](https://github.com/openfoodfacts/open-prices/compare/v1.60.2...v1.60.3) (2025-01-26)


### Technical

* **Users:** allow anyone to query any user ([#689](https://github.com/openfoodfacts/open-prices/issues/689)) ([44e1179](https://github.com/openfoodfacts/open-prices/commit/44e1179a2663390ec9dd87e15dc35e03c2d63150))

## [1.60.2](https://github.com/openfoodfacts/open-prices/compare/v1.60.1...v1.60.2) (2025-01-19)


### Bug Fixes

* **Prices:** on price delete, also update any related PriceTag status ([#684](https://github.com/openfoodfacts/open-prices/issues/684)) ([2b46cbb](https://github.com/openfoodfacts/open-prices/commit/2b46cbbef4023931db5194138c56155547e7df39))

## [1.60.1](https://github.com/openfoodfacts/open-prices/compare/v1.60.0...v1.60.1) (2025-01-19)


### Bug Fixes

* **Proofs:** Run price tag prediction only on PRICE_TAG proofs ([#683](https://github.com/openfoodfacts/open-prices/issues/683)) ([4c10f86](https://github.com/openfoodfacts/open-prices/commit/4c10f86bca7880549eced8b7d0da682726be9648))


### Technical

* **Proofs:** Add test to make sure we don't run price_tag detection on RECEIPT proofs. ref [#683](https://github.com/openfoodfacts/open-prices/issues/683) ([c388e5b](https://github.com/openfoodfacts/open-prices/commit/c388e5bbb2ff2d23f780337a4c3490896c72e74e))
* **Proofs:** move OCR script in the ML file ([#679](https://github.com/openfoodfacts/open-prices/issues/679)) ([9268606](https://github.com/openfoodfacts/open-prices/commit/926860632f8696bf20cc5141a62e4888aee5808c))

## [1.60.0](https://github.com/openfoodfacts/open-prices/compare/v1.59.6...v1.60.0) (2025-01-12)


### Features

* **Prices:** API: allow editing category-related fields ([#677](https://github.com/openfoodfacts/open-prices/issues/677)) ([fc157a6](https://github.com/openfoodfacts/open-prices/commit/fc157a61241886001ffcb9aa713c0215be4b89b4))
* **Prices:** API: new filter on product categories_tags ([#676](https://github.com/openfoodfacts/open-prices/issues/676)) ([458089e](https://github.com/openfoodfacts/open-prices/commit/458089ec8c85648e4b08a91a3d6b64b6e209a584))

## [1.59.6](https://github.com/openfoodfacts/open-prices/compare/v1.59.5...v1.59.6) (2025-01-06)


### Technical

* **Price tags:** allow filter by created gte & lte. ref [#656](https://github.com/openfoodfacts/open-prices/issues/656) ([d26e39c](https://github.com/openfoodfacts/open-prices/commit/d26e39c85f8cd01d26c8a905397e1af0d208540a))

## [1.59.5](https://github.com/openfoodfacts/open-prices/compare/v1.59.4...v1.59.5) (2025-01-02)


### Bug Fixes

* **Prices:** fix validation error formatting when user is not allowed to add price on proof. ref [#568](https://github.com/openfoodfacts/open-prices/issues/568) ([79407c3](https://github.com/openfoodfacts/open-prices/commit/79407c3fe9c9c94d991391f39eaaa21a5b016049))
* **Stats:** fix User & Location stats after allowing any user to add prices on PRICE_TAG proofs ([#668](https://github.com/openfoodfacts/open-prices/issues/668)) ([2481f14](https://github.com/openfoodfacts/open-prices/commit/2481f1465b0988410b58782f8fe8ebe23aacc484))

## [1.59.4](https://github.com/openfoodfacts/open-prices/compare/v1.59.3...v1.59.4) (2025-01-01)


### Technical

* **Prices:** transform receipt_quantity field to Decimal ([#666](https://github.com/openfoodfacts/open-prices/issues/666)) ([c807dee](https://github.com/openfoodfacts/open-prices/commit/c807dee2ec8ce393d12880abcb837e0aec1f7c58))

## [1.59.3](https://github.com/openfoodfacts/open-prices/compare/v1.59.2...v1.59.3) (2024-12-31)


### Technical

* **Price tags:** matching script: try to match on price only ([#664](https://github.com/openfoodfacts/open-prices/issues/664)) ([76637dc](https://github.com/openfoodfacts/open-prices/commit/76637dcb4e5ab25b3728307cae5ed3326d45435a))
* **Products:** API: fix re-add ordering via unique_scans_n. Also add other scores. closes [#662](https://github.com/openfoodfacts/open-prices/issues/662) ([9f6e9b8](https://github.com/openfoodfacts/open-prices/commit/9f6e9b8ce446522e734f2070889c562b1721c224))

## [1.59.2](https://github.com/openfoodfacts/open-prices/compare/v1.59.1...v1.59.2) (2024-12-30)


### Technical

* **Price tags:** improve matching script: manage Carrefour barcodes ([#660](https://github.com/openfoodfacts/open-prices/issues/660)) ([c2f5717](https://github.com/openfoodfacts/open-prices/commit/c2f57176f241e961afa8cc39f2e664d652a85d3b))

## [1.59.1](https://github.com/openfoodfacts/open-prices/compare/v1.59.0...v1.59.1) (2024-12-30)


### Technical

* **API:** store query params app_platform & app_page in source field ([#658](https://github.com/openfoodfacts/open-prices/issues/658)) ([96215f4](https://github.com/openfoodfacts/open-prices/commit/96215f4460214e2d647bd7ab82039bdf3003f564))
* **Proofs:** API: allow filtering by ready_for_price_tag_validation field. ref [#656](https://github.com/openfoodfacts/open-prices/issues/656) ([0936ffb](https://github.com/openfoodfacts/open-prices/commit/0936ffbeb589218e65d474795ce136c48d80aa4b))

## [1.59.0](https://github.com/openfoodfacts/open-prices/compare/v1.58.1...v1.59.0) (2024-12-26)


### Features

* **Price tags:** new Proof.ready_for_price_tag_validation field to help filter the frontend UI ([#656](https://github.com/openfoodfacts/open-prices/issues/656)) ([67b4912](https://github.com/openfoodfacts/open-prices/commit/67b4912e1ef4bdbab8ce1185d3094bf723cc83f8))

## [1.58.1](https://github.com/openfoodfacts/open-prices/compare/v1.58.0...v1.58.1) (2024-12-23)


### Technical

* **Price tags:** fix stats. move constants. cleanup ([#653](https://github.com/openfoodfacts/open-prices/issues/653)) ([08d148f](https://github.com/openfoodfacts/open-prices/commit/08d148f84ea8039d869fca680d59b2c722943d25))
* **Price tags:** improve matching script (better manage decimal/float). ref [#650](https://github.com/openfoodfacts/open-prices/issues/650) ([e0e64b3](https://github.com/openfoodfacts/open-prices/commit/e0e64b3af6260766e0cb5d0b78d449f98488d841))
* **Products:** API: send source_last_synced field as well. ref [#551](https://github.com/openfoodfacts/open-prices/issues/551) ([a2bb472](https://github.com/openfoodfacts/open-prices/commit/a2bb472d4ec15d539daa6f88a22de47f028a84f3))
* **Stats:** new PriceTag stats ([#652](https://github.com/openfoodfacts/open-prices/issues/652)) ([4643706](https://github.com/openfoodfacts/open-prices/commit/46437066f0682bff9ef19df92d6e055f9445c594))

## [1.58.0](https://github.com/openfoodfacts/open-prices/compare/v1.57.0...v1.58.0) (2024-12-22)


### Features

* **Price tags:** script to match historical PriceTag with their prices ([#650](https://github.com/openfoodfacts/open-prices/issues/650)) ([44fbf2e](https://github.com/openfoodfacts/open-prices/commit/44fbf2e4759ef585df6ab0ca9deb71fdbe53b3c9))


### Bug Fixes

* **Gemini:** rename url to use hyphens instead of underscores. ref [#569](https://github.com/openfoodfacts/open-prices/issues/569) ([433011d](https://github.com/openfoodfacts/open-prices/commit/433011d17371c90c577d0f9b3ec46690a0064d5a))
* process one image at a time with Gemini ([#648](https://github.com/openfoodfacts/open-prices/issues/648)) ([e0c251b](https://github.com/openfoodfacts/open-prices/commit/e0c251b4f60c51f1cd63c84c1adc5648a872f37d))

## [1.57.0](https://github.com/openfoodfacts/open-prices/compare/v1.56.6...v1.57.0) (2024-12-21)


### Features

* **ProofMl:** extract product_name and suggest ean-13 barcodes ([#646](https://github.com/openfoodfacts/open-prices/issues/646)) ([f3b670f](https://github.com/openfoodfacts/open-prices/commit/f3b670f5cc6a4065f35513e7a2dede7c3133dedb))


### Technical

* **Price tags:** API: allow ordering by proof_id. ref [#628](https://github.com/openfoodfacts/open-prices/issues/628) ([c68f680](https://github.com/openfoodfacts/open-prices/commit/c68f68091ff268d8bd6f9687ecfc5f2d270f4613))
* **Products:** API: allow ordering by all count fields. ref [#445](https://github.com/openfoodfacts/open-prices/issues/445) ([ca7bb76](https://github.com/openfoodfacts/open-prices/commit/ca7bb76710478d58e34f13fefdaf41287afc5f02))

## [1.56.6](https://github.com/openfoodfacts/open-prices/compare/v1.56.5...v1.56.6) (2024-12-20)


### Bug Fixes

* add a command to extract from Gemini from price tag without prediction ([#644](https://github.com/openfoodfacts/open-prices/issues/644)) ([06216c5](https://github.com/openfoodfacts/open-prices/commit/06216c5ccee44533efd5c5dd3460879c36512e95))

## [1.56.5](https://github.com/openfoodfacts/open-prices/compare/v1.56.4...v1.56.5) (2024-12-20)


### Bug Fixes

* fix bug in image.thumbnail call ([#642](https://github.com/openfoodfacts/open-prices/issues/642)) ([1566464](https://github.com/openfoodfacts/open-prices/commit/15664640b57d78f2fb2f3757a2f2daf0056c2556))

## [1.56.4](https://github.com/openfoodfacts/open-prices/compare/v1.56.3...v1.56.4) (2024-12-20)


### Bug Fixes

* add more raw categories to gemini ([#638](https://github.com/openfoodfacts/open-prices/issues/638)) ([07266f8](https://github.com/openfoodfacts/open-prices/commit/07266f8ea858513b989f7bd62d79ef9316800716))
* Improve gemini processing ([#641](https://github.com/openfoodfacts/open-prices/issues/641)) ([df5ce6e](https://github.com/openfoodfacts/open-prices/commit/df5ce6efb00c17da21de018c6aee4ae572183a34))

## [1.56.3](https://github.com/openfoodfacts/open-prices/compare/v1.56.2...v1.56.3) (2024-12-19)


### Technical

* **Price tags:** API: add filter by proof__owner. ref [#628](https://github.com/openfoodfacts/open-prices/issues/628) ([5fd45df](https://github.com/openfoodfacts/open-prices/commit/5fd45dfda6a911bec5d39eed24d96f52deb55292))
* **Price tags:** API: send proof location for context. ref [#628](https://github.com/openfoodfacts/open-prices/issues/628) ([b1cb613](https://github.com/openfoodfacts/open-prices/commit/b1cb6135878263a895860d66236fecd4c4dd7bfc))

## [1.56.2](https://github.com/openfoodfacts/open-prices/compare/v1.56.1...v1.56.2) (2024-12-18)


### Technical

* **Prices:** API: add filtering by type ([fed3214](https://github.com/openfoodfacts/open-prices/commit/fed321494536caf4fa40715497b3b8c4de3d168a))

## [1.56.1](https://github.com/openfoodfacts/open-prices/compare/v1.56.0...v1.56.1) (2024-12-18)


### Bug Fixes

* don't create price tags for proofs.type != PRICE_TAG ([#632](https://github.com/openfoodfacts/open-prices/issues/632)) ([c40f9ae](https://github.com/openfoodfacts/open-prices/commit/c40f9ae25aa58fa6ee4da4e79abfa929dfbcb354))

## [1.56.0](https://github.com/openfoodfacts/open-prices/compare/v1.55.1...v1.56.0) (2024-12-18)


### Features

* add `price_tag` table and routes ([#628](https://github.com/openfoodfacts/open-prices/issues/628)) ([fe3f745](https://github.com/openfoodfacts/open-prices/commit/fe3f74529f902ec5b74608469098f3e916f0d06a))
* create price tags from the object detector model ([#629](https://github.com/openfoodfacts/open-prices/issues/629)) ([a0c4741](https://github.com/openfoodfacts/open-prices/commit/a0c4741ab5b50a557c71e01d9fb3f5dbc14ecdbf))
* improve gemini processing ([#631](https://github.com/openfoodfacts/open-prices/issues/631)) ([8263e00](https://github.com/openfoodfacts/open-prices/commit/8263e00def466242b80004ae454b55ad16e7c0a0))
* save Gemini prediction in `price_tag_predictions` table ([#630](https://github.com/openfoodfacts/open-prices/issues/630)) ([39d3c25](https://github.com/openfoodfacts/open-prices/commit/39d3c259ac62f2f3f0e681d0ded864dc22b5b3de))


### Bug Fixes

* fix script that runs ML models for proofs without predictions ([#627](https://github.com/openfoodfacts/open-prices/issues/627)) ([c825d2c](https://github.com/openfoodfacts/open-prices/commit/c825d2c23aed60dc180861df0130b4f325bb3463))


### Technical

* pass ENVIRONMENT envvar to services ([#625](https://github.com/openfoodfacts/open-prices/issues/625)) ([59f9cd6](https://github.com/openfoodfacts/open-prices/commit/59f9cd606b2d16fb5c0613f2d35194e066b901ed))
* update redis default stream name ([824a389](https://github.com/openfoodfacts/open-prices/commit/824a3895ecd058b6539ef8e5d99f016a1de8bbbb))

## [1.55.1](https://github.com/openfoodfacts/open-prices/compare/v1.55.0...v1.55.1) (2024-12-12)


### Bug Fixes

* create a product if needed after a redis update event ([#622](https://github.com/openfoodfacts/open-prices/issues/622)) ([66010fe](https://github.com/openfoodfacts/open-prices/commit/66010fe64d88943d5729fdd17cf430d828ec2cab))
* remove legacy log message ([267568e](https://github.com/openfoodfacts/open-prices/commit/267568ebe870db409f1092b1011ba13502deb6e2))

## [1.55.0](https://github.com/openfoodfacts/open-prices/compare/v1.54.0...v1.55.0) (2024-12-12)


### Features

* listen to updates from Product Opener using Redis ([#618](https://github.com/openfoodfacts/open-prices/issues/618)) ([9e4d326](https://github.com/openfoodfacts/open-prices/commit/9e4d326b023c6bb1445b8735490c7920b6c8fd89))


### Technical

* enable fetching product updates from Redis ([#621](https://github.com/openfoodfacts/open-prices/issues/621)) ([3a81968](https://github.com/openfoodfacts/open-prices/commit/3a81968979841cb72ce4acbe4d3a7833d3648f0a))

## [1.54.0](https://github.com/openfoodfacts/open-prices/compare/v1.53.0...v1.54.0) (2024-12-11)


### Features

* run and save price tag detections in `proof_predictions` table ([#614](https://github.com/openfoodfacts/open-prices/issues/614)) ([62ecaab](https://github.com/openfoodfacts/open-prices/commit/62ecaab061dfff3ba82ee1885b7565db0966dbcc))
* **Shop import:** new script to upload prices from a shop csv ([#574](https://github.com/openfoodfacts/open-prices/issues/574)) ([7ec2eda](https://github.com/openfoodfacts/open-prices/commit/7ec2edac6039b32d0cc2cfbbd4bc9c6e29fca4f0))


### Bug Fixes

* fix bug in directory selection for proof image ([#616](https://github.com/openfoodfacts/open-prices/issues/616)) ([b32b5cf](https://github.com/openfoodfacts/open-prices/commit/b32b5cf65c6c2228b6517768c813a5e4c2dee5d4))
* use openfoodfacts.ml module for proof classification ([#613](https://github.com/openfoodfacts/open-prices/issues/613)) ([8eb37e6](https://github.com/openfoodfacts/open-prices/commit/8eb37e64b24cdd37599bad41bd20d87f07d22218))

## [1.53.0](https://github.com/openfoodfacts/open-prices/compare/v1.52.0...v1.53.0) (2024-12-06)


### Features

* **API:** allow adding prices on proofs not owned (only PRICE_TAG proofs) ([#609](https://github.com/openfoodfacts/open-prices/issues/609)) ([071fad0](https://github.com/openfoodfacts/open-prices/commit/071fad0b25093659dfa4e8977403ea3d04cdd1cd))
* **API:** Allow anonymous users to upload proofs ([#607](https://github.com/openfoodfacts/open-prices/issues/607)) ([0c68bf8](https://github.com/openfoodfacts/open-prices/commit/0c68bf877266c3e328189e276ba19498c764e46a))
* return proof predictions in `GET /api/v1/proof` route ([#601](https://github.com/openfoodfacts/open-prices/issues/601)) ([42f1c5e](https://github.com/openfoodfacts/open-prices/commit/42f1c5ee5b7460d41b5083455f82d6ea5e4ca2dc))


### Bug Fixes

* don't try to classify with the image classifier .bin files ([#604](https://github.com/openfoodfacts/open-prices/issues/604)) ([0ecca7b](https://github.com/openfoodfacts/open-prices/commit/0ecca7beb6be10e7556057d884a2b8ce63776e75))


### Technical

* **API:** allow anyone to access proof data ([#606](https://github.com/openfoodfacts/open-prices/issues/606)) ([1b4dcb5](https://github.com/openfoodfacts/open-prices/commit/1b4dcb5659262cd7c8f18c1fa68a5f3b29238272))
* **API:** only return proof.predictions in detail endpoint ([#605](https://github.com/openfoodfacts/open-prices/issues/605)) ([81f7f0f](https://github.com/openfoodfacts/open-prices/commit/81f7f0f3e1a218330b8ae3d3761c53eafd51b1b5))
* Update github-projects.yml ([e4bfe68](https://github.com/openfoodfacts/open-prices/commit/e4bfe683705ff3ed410d6d97000cbd86cd2d7dda))

## [1.52.0](https://github.com/openfoodfacts/open-prices/compare/v1.51.0...v1.52.0) (2024-12-05)


### Features

* save proof prediction for all proofs in a new table ([#588](https://github.com/openfoodfacts/open-prices/issues/588)) ([cb1fb7a](https://github.com/openfoodfacts/open-prices/commit/cb1fb7ad6b97a08fafce77a53c6ad74488049f80))


### Bug Fixes

* fix run_ocr.py script ([#600](https://github.com/openfoodfacts/open-prices/issues/600)) ([4a98976](https://github.com/openfoodfacts/open-prices/commit/4a98976db7773372bf955505148e2806c84b7e48))


### Technical

* add command to run ML models on proofs without predictions ([#599](https://github.com/openfoodfacts/open-prices/issues/599)) ([32de49b](https://github.com/openfoodfacts/open-prices/commit/32de49b8c3ec556276eb36133e2ac9a88923a2f4))
* Add unit test for proof type detection ([#597](https://github.com/openfoodfacts/open-prices/issues/597)) ([0386cff](https://github.com/openfoodfacts/open-prices/commit/0386cff9d6a121bc8dd95b164e53cecba1dcdd13))
* enable ML predictions on prod & staging ([#596](https://github.com/openfoodfacts/open-prices/issues/596)) ([8d049aa](https://github.com/openfoodfacts/open-prices/commit/8d049aa0b2a842782ba5dcd3b6f12bdcbbbb7280))
* remove deprecated command for ssh-action ([#598](https://github.com/openfoodfacts/open-prices/issues/598)) ([28afbe7](https://github.com/openfoodfacts/open-prices/commit/28afbe7c79e94da58b5bc1c674ca8f6c751f5eb0))

## [1.51.0](https://github.com/openfoodfacts/open-prices/compare/v1.50.0...v1.51.0) (2024-12-03)


### Features

* **Location:** new brand & version fields (fetch & store from OSM) ([#591](https://github.com/openfoodfacts/open-prices/issues/591)) ([63dc620](https://github.com/openfoodfacts/open-prices/commit/63dc620710f86c6c03d582f6eee60cd1a71ba681))
* **Location:** script to fill in OSM brand & version ([#592](https://github.com/openfoodfacts/open-prices/issues/592)) ([ea29002](https://github.com/openfoodfacts/open-prices/commit/ea2900279d14ad36ae2f6759ef2ae65cf36bcece))


### Bug Fixes

* **Location:** add try/catch & progress in OSM script. ref [#592](https://github.com/openfoodfacts/open-prices/issues/592) ([887b508](https://github.com/openfoodfacts/open-prices/commit/887b508dcd7e467d95b66739a1469f07bb70519a))


### Technical

* increase the number of gunicorn workers in production ([#582](https://github.com/openfoodfacts/open-prices/issues/582)) ([a922030](https://github.com/openfoodfacts/open-prices/commit/a9220306794ff584f9d886d9f3566dd8380bcc2b))

## [1.50.0](https://github.com/openfoodfacts/open-prices/compare/v1.49.0...v1.50.0) (2024-11-27)


### Features

* **Price:** new type field ([#578](https://github.com/openfoodfacts/open-prices/issues/578)) ([f6d189b](https://github.com/openfoodfacts/open-prices/commit/f6d189b85d1a69705d93fc136407ff7a9e56d282))


### Bug Fixes

* fix CSRF configuration ([#581](https://github.com/openfoodfacts/open-prices/issues/581)) ([5887073](https://github.com/openfoodfacts/open-prices/commit/5887073b79cfee91be928302b6ab22058a3c01d5))


### Technical

* **Admin:** add Price view. improve Location & Proof views. ([#580](https://github.com/openfoodfacts/open-prices/issues/580)) ([1a59b1e](https://github.com/openfoodfacts/open-prices/commit/1a59b1ebf80d230e22710ecb40bacfcccbfd054c))
* **GDPR:** improve Leclerc merge and price upload. ref [#213](https://github.com/openfoodfacts/open-prices/issues/213) ([978a401](https://github.com/openfoodfacts/open-prices/commit/978a401b99038417ba487dfbafe76eda4a40c867))

## [1.49.0](https://github.com/openfoodfacts/open-prices/compare/v1.48.0...v1.49.0) (2024-11-21)


### Features

* add CLI command to run OCR on past images ([#572](https://github.com/openfoodfacts/open-prices/issues/572)) ([2f6a94e](https://github.com/openfoodfacts/open-prices/commit/2f6a94e86c4d8c829ed35f0c1581e79b9e44f06e))


### Technical

* **proofs:** more features to OCR extraction ([#566](https://github.com/openfoodfacts/open-prices/issues/566)) ([b2e55be](https://github.com/openfoodfacts/open-prices/commit/b2e55bed1b73ba9d92b7d1551f0ba57fb4c9d062))

## [1.48.0](https://github.com/openfoodfacts/open-prices/compare/v1.47.1...v1.48.0) (2024-11-13)


### Features

* allow users to submit origin tags in their language ([#561](https://github.com/openfoodfacts/open-prices/issues/561)) ([2b867db](https://github.com/openfoodfacts/open-prices/commit/2b867dbdf78f49298cf339e981bd5bb8fcdc2378))
* **proofs:** New endpoint to extract price data from images (with Gemini) ([#557](https://github.com/openfoodfacts/open-prices/issues/557)) ([fa54a36](https://github.com/openfoodfacts/open-prices/commit/fa54a36f4276efc9b4539dd37b670e9a18a0b02d))


### Technical

* add CORS headers to data ([#564](https://github.com/openfoodfacts/open-prices/issues/564)) ([f145215](https://github.com/openfoodfacts/open-prices/commit/f145215b8fc595195c3fd3c2b618cac1c8aa3de2))

## [1.47.1](https://github.com/openfoodfacts/open-prices/compare/v1.47.0...v1.47.1) (2024-11-09)


### Technical

* **Locations:** keep only website_url domain ([#555](https://github.com/openfoodfacts/open-prices/issues/555)) ([cc5d589](https://github.com/openfoodfacts/open-prices/commit/cc5d589f2efd0c90727713f33385f6ed83933b9e))

## [1.47.0](https://github.com/openfoodfacts/open-prices/compare/v1.46.0...v1.47.0) (2024-11-08)


### Features

* allow users to submit category_tag with language prefix ([#548](https://github.com/openfoodfacts/open-prices/issues/548)) ([9aab15d](https://github.com/openfoodfacts/open-prices/commit/9aab15d82cd8146aa383efcef5e57b27558a87b9))
* **API:** on Location POST, return existing if duplicate ([#554](https://github.com/openfoodfacts/open-prices/issues/554)) ([d1efae6](https://github.com/openfoodfacts/open-prices/commit/d1efae6f6fe979e5118a49b13603c2573697d771))
* **locations:** new source field to store the app name & version ([#546](https://github.com/openfoodfacts/open-prices/issues/546)) ([a9188c9](https://github.com/openfoodfacts/open-prices/commit/a9188c9307327e4b4b1fa57e1f4ebb97be72a327))
* run OCR extraction on every new image ([#543](https://github.com/openfoodfacts/open-prices/issues/543)) ([77ed50b](https://github.com/openfoodfacts/open-prices/commit/77ed50bbaa3d4d19d4e67e3e716094af880b5679))
* **Sync:** fetch OFF obsolete products (25k items) ([#552](https://github.com/openfoodfacts/open-prices/issues/552)) ([badec8b](https://github.com/openfoodfacts/open-prices/commit/badec8b9f21430532987ac4ea1292c2557319f77))


### Bug Fixes

* add types to functions and improve docstring in proofs/utils.py ([#540](https://github.com/openfoodfacts/open-prices/issues/540)) ([506bc4a](https://github.com/openfoodfacts/open-prices/commit/506bc4a838347d08ebf0f86d1bda620caa35f88f))


### Technical

* add CORS headers to images ([#545](https://github.com/openfoodfacts/open-prices/issues/545)) ([bd3709a](https://github.com/openfoodfacts/open-prices/commit/bd3709ac4251882427d4b6c85914741433e60534))
* **proofs:** run OCR in post_save signal instead of create ([#549](https://github.com/openfoodfacts/open-prices/issues/549)) ([f3cfa79](https://github.com/openfoodfacts/open-prices/commit/f3cfa7967d7418a8a88a4fcfa6200c142f392b52))
* remove perform_create to simplify code ([2394940](https://github.com/openfoodfacts/open-prices/commit/2394940390fba31254d0db47bddf1dad81a535f0))
* update dependency openfoodfacts-python ([#550](https://github.com/openfoodfacts/open-prices/issues/550)) ([2f53957](https://github.com/openfoodfacts/open-prices/commit/2f53957d3b87a01e861a88fa27e6075d01a34f20))
* Update github-projects.yml ([d8d54d7](https://github.com/openfoodfacts/open-prices/commit/d8d54d74edca117012cf11dba6f3d071ea0ccf8a))

## [1.46.0](https://github.com/openfoodfacts/open-prices/compare/v1.45.1...v1.46.0) (2024-10-25)


### Features

* **API:** Allow updating Proof location fields ([#539](https://github.com/openfoodfacts/open-prices/issues/539)) ([8554eaf](https://github.com/openfoodfacts/open-prices/commit/8554eaf63777b2393c234302b86e8c30ca4fe050))
* **Proofs:** on update, also update proof prices ([#538](https://github.com/openfoodfacts/open-prices/issues/538)) ([d5481f2](https://github.com/openfoodfacts/open-prices/commit/d5481f2b138e825a087a789477f0b5fc027bb4ae))


### Technical

* **Proofs:** refactor method that updates proof fields from prices (1 instead of 3). ref [#481](https://github.com/openfoodfacts/open-prices/issues/481) ([e3b97f5](https://github.com/openfoodfacts/open-prices/commit/e3b97f543a700d93740483753efee1385fbc70a7))

## [1.45.1](https://github.com/openfoodfacts/open-prices/compare/v1.45.0...v1.45.1) (2024-10-23)


### Bug Fixes

* **GDPR:** Use unique location identifier instead of name ([bd681f1](https://github.com/openfoodfacts/open-prices/commit/bd681f17ca4455334571a5fb14318eac94fbe46d))


### Technical

* **API:** store app_version in Price & Proof source field ([#533](https://github.com/openfoodfacts/open-prices/issues/533)) ([bbfce93](https://github.com/openfoodfacts/open-prices/commit/bbfce93f6981cc71fb4bac6df7c8a87f417716e3))
* **GDPR:** Use new Price.receipt_quantity field. ref [#499](https://github.com/openfoodfacts/open-prices/issues/499) ([64fcd80](https://github.com/openfoodfacts/open-prices/commit/64fcd8058ae23cfdfcd26b66c8c92ffcc6cf57ff))

## [1.45.0](https://github.com/openfoodfacts/open-prices/compare/v1.44.3...v1.45.0) (2024-10-19)


### Features

* **Prices:** Allow adding new prices with a location_id ([#527](https://github.com/openfoodfacts/open-prices/issues/527)) ([99f16df](https://github.com/openfoodfacts/open-prices/commit/99f16dfa1e6d4573d8b7c9243384fdcffad3c194))
* **Prices:** new field to allow users to input the quantity bought ([#498](https://github.com/openfoodfacts/open-prices/issues/498)) ([857b813](https://github.com/openfoodfacts/open-prices/commit/857b813697e9ac5f7c8aa50cec769369de12b92e))
* **Proofs:** Allow adding new proofs with a location_id ([#528](https://github.com/openfoodfacts/open-prices/issues/528)) ([38e5599](https://github.com/openfoodfacts/open-prices/commit/38e5599931efe1aa6aa333028fc1b2a948c36b1f))
* **Proofs:** new fields to allow users to input the number of prices & total sum ([#497](https://github.com/openfoodfacts/open-prices/issues/497)) ([8a9aa50](https://github.com/openfoodfacts/open-prices/commit/8a9aa50d264fa4e792b3512bffa37ec869ed60e0))


### Bug Fixes

* **Prices:** init Price.receipt_quantity field in migration. ref [#498](https://github.com/openfoodfacts/open-prices/issues/498) ([1822b8d](https://github.com/openfoodfacts/open-prices/commit/1822b8d2e54a9c07905ff24242f9f93138b38acd))
* **Tests:** Remove proof images on test tearDown ([#529](https://github.com/openfoodfacts/open-prices/issues/529)) ([5805eea](https://github.com/openfoodfacts/open-prices/commit/5805eeadfd431e2bdc47b677861cbb7123f4cae5))


### Technical

* **Stats:** extra Proof type stats. new Location type stats ([#524](https://github.com/openfoodfacts/open-prices/issues/524)) ([411222b](https://github.com/openfoodfacts/open-prices/commit/411222be6d2da05ec3acb7a7948a6268c29b65d5))

## [1.44.3](https://github.com/openfoodfacts/open-prices/compare/v1.44.2...v1.44.3) (2024-10-13)


### Bug Fixes

* **Product sync:** Avoid setting None for missing fields. Use model default values instead ([#519](https://github.com/openfoodfacts/open-prices/issues/519)) ([e3ed44e](https://github.com/openfoodfacts/open-prices/commit/e3ed44e51f65110edfa51fdc740781274d092d6f))


### Technical

* **Product sync:** Build product dict identically if from sync or API. ref [#518](https://github.com/openfoodfacts/open-prices/issues/518) ([81766b0](https://github.com/openfoodfacts/open-prices/commit/81766b01cd7f26e66b9e57b10e8ebc661256c8eb))

## [1.44.2](https://github.com/openfoodfacts/open-prices/compare/v1.44.1...v1.44.2) (2024-10-11)


### Bug Fixes

* **Proofs:** Deny users to delete a proof with prices ([#517](https://github.com/openfoodfacts/open-prices/issues/517)) ([3b1ed29](https://github.com/openfoodfacts/open-prices/commit/3b1ed29e272afb13647ad14265953b4970f0e0b8))


### Technical

* **Proofs:** On proof delete, also remove its images. ref [#514](https://github.com/openfoodfacts/open-prices/issues/514) ([8360a06](https://github.com/openfoodfacts/open-prices/commit/8360a066a2901d30c34b01acbba74619eb1fe748))

## [1.44.1](https://github.com/openfoodfacts/open-prices/compare/v1.44.0...v1.44.1) (2024-10-09)


### Bug Fixes

* **Backups:** fix backup location. closes [#407](https://github.com/openfoodfacts/open-prices/issues/407) ([97ed9b2](https://github.com/openfoodfacts/open-prices/commit/97ed9b265bb059d9f0d9aed7cd71dedce29a4c7a))
* **Queue:** bump max_attempts to 2. ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([e83158b](https://github.com/openfoodfacts/open-prices/commit/e83158bd9a0c5999eaa22f85dc99f3025383f5e0))
* **Stats:** make sure to get all Product & Proof with prices when updating counts. ref [#492](https://github.com/openfoodfacts/open-prices/issues/492) & [#481](https://github.com/openfoodfacts/open-prices/issues/481) ([6f446b9](https://github.com/openfoodfacts/open-prices/commit/6f446b9a420725f1d4326b9ed6e65a64c91a99b1))

## [1.44.0](https://github.com/openfoodfacts/open-prices/compare/v1.43.1...v1.44.0) (2024-10-06)


### Features

* **Locations:** new type & website_url fields to start allowing ONLINE stores ([#446](https://github.com/openfoodfacts/open-prices/issues/446)) ([ce50c74](https://github.com/openfoodfacts/open-prices/commit/ce50c749a34690522c2dba218cba0f0f0dd43d58))
* **Users:** new /users/:user_id endpoint. Only for self ([#500](https://github.com/openfoodfacts/open-prices/issues/500)) ([665c44f](https://github.com/openfoodfacts/open-prices/commit/665c44fd2b5562efef815e8aaa4d0341e4eb73bb))


### Bug Fixes

* **Locations:** fix migration error. ref [#446](https://github.com/openfoodfacts/open-prices/issues/446) ([666c957](https://github.com/openfoodfacts/open-prices/commit/666c95706a32439efbeb8c1dc5d07c514009d362))


### Technical

* **Proofs:** Methods to update missing proof fields from prices ([#481](https://github.com/openfoodfacts/open-prices/issues/481)) ([ffe5e5a](https://github.com/openfoodfacts/open-prices/commit/ffe5e5a1889676faf73c48ed3df2189e16309057))
* **Stats:** simple script for top product stats (via API) ([#398](https://github.com/openfoodfacts/open-prices/issues/398)) ([14c6d39](https://github.com/openfoodfacts/open-prices/commit/14c6d3920583366e3bc122a7d870a1b8d5b5b9a2))

## [1.43.1](https://github.com/openfoodfacts/open-prices/compare/v1.43.0...v1.43.1) (2024-10-03)


### Bug Fixes

* **Proofs:** fix thumbnail generation for some JPEG images. ref [#486](https://github.com/openfoodfacts/open-prices/issues/486) ([a7f18e9](https://github.com/openfoodfacts/open-prices/commit/a7f18e9c33b2f87a04f47638b10d354899afc3fc))


### Technical

* **stats:** new Proof type stats. Rename Price type stats ([#496](https://github.com/openfoodfacts/open-prices/issues/496)) ([6401f80](https://github.com/openfoodfacts/open-prices/commit/6401f80caee1ec6fc1f31a9a4d3a7cc88774b809))

## [1.43.0](https://github.com/openfoodfacts/open-prices/compare/v1.42.0...v1.43.0) (2024-10-03)


### Features

* **products:** New Product.location_count field ([#489](https://github.com/openfoodfacts/open-prices/issues/489)) ([85cd11f](https://github.com/openfoodfacts/open-prices/commit/85cd11f7afcec627bb73d606679c0eca91ec313d))
* **products:** New Product.proof_count field ([#491](https://github.com/openfoodfacts/open-prices/issues/491)) ([f77ec80](https://github.com/openfoodfacts/open-prices/commit/f77ec803da4319225c13d9d83bdc2e86af63e7a7))
* **products:** New Product.user_count field ([#490](https://github.com/openfoodfacts/open-prices/issues/490)) ([459c6fc](https://github.com/openfoodfacts/open-prices/commit/459c6fc22febcc2764bbd865a6da1d0eadff2d99))
* **Proof:** generate image thumbnail (size 400) on create ([#486](https://github.com/openfoodfacts/open-prices/issues/486)) ([9f72de6](https://github.com/openfoodfacts/open-prices/commit/9f72de6349980a794eb15372db9c33a45c95e6a7))


### Bug Fixes

* **API:** Proofs: improve API documentation for upload ([#493](https://github.com/openfoodfacts/open-prices/issues/493)) ([0168a0f](https://github.com/openfoodfacts/open-prices/commit/0168a0fec6898c9633625e27a63757d66167281f))
* **locations:** fix count calculation when FK is null. ref [#420](https://github.com/openfoodfacts/open-prices/issues/420) ([a075918](https://github.com/openfoodfacts/open-prices/commit/a075918f4e9f3f58f28726a0ed25f36c2791cff4))
* **products:** fix update count CRON setup. ref [#492](https://github.com/openfoodfacts/open-prices/issues/492) ([7e0588b](https://github.com/openfoodfacts/open-prices/commit/7e0588bea0aac7b64b595a58e144d27024192f44))
* **users:** fix count calculation when FK is null. ref [#419](https://github.com/openfoodfacts/open-prices/issues/419) ([f2f6d9c](https://github.com/openfoodfacts/open-prices/commit/f2f6d9cdd915460517aa944d80ab2ce57483722d))


### Technical

* **Documentation:** Remove mention of /app. closes [#482](https://github.com/openfoodfacts/open-prices/issues/482) ([18f7083](https://github.com/openfoodfacts/open-prices/commit/18f7083dd684e20448e7c1f34acdf21ec12f621a))
* **products:** New weekly CRON to update Product counts ([#492](https://github.com/openfoodfacts/open-prices/issues/492)) ([dd9a239](https://github.com/openfoodfacts/open-prices/commit/dd9a2392ee6ced27f4b3742b415fdf91d859b4df))

## [1.42.0](https://github.com/openfoodfacts/open-prices/compare/v1.41.0...v1.42.0) (2024-10-02)


### Features

* **proofs:** new type SHOP_IMPORT to explicitly link shop-imported prices ([#485](https://github.com/openfoodfacts/open-prices/issues/485)) ([82da2b9](https://github.com/openfoodfacts/open-prices/commit/82da2b96331d08494e78da4457890e7e81ca5899))


### Technical

* launch vue.js app on / (instead of /app) ([#483](https://github.com/openfoodfacts/open-prices/issues/483)) ([1088f65](https://github.com/openfoodfacts/open-prices/commit/1088f65d9c3e1a32b8630197a740193d522a2742))

## [1.41.0](https://github.com/openfoodfacts/open-prices/compare/v1.40.0...v1.41.0) (2024-09-28)


### Features

* **API:** new /stats endpoint for TotalStats ([#476](https://github.com/openfoodfacts/open-prices/issues/476)) ([4f8384f](https://github.com/openfoodfacts/open-prices/commit/4f8384f0ef0c36541357bd85b23ec832647d93c4))
* **Stats:** new TotalStats model ([#475](https://github.com/openfoodfacts/open-prices/issues/475)) ([034025b](https://github.com/openfoodfacts/open-prices/commit/034025b58c07f2450215c50a779c88b42e5f43bd))


### Technical

* **locations:** add new count fields in API ordering settings. ref [#419](https://github.com/openfoodfacts/open-prices/issues/419) ([b02c480](https://github.com/openfoodfacts/open-prices/commit/b02c48008e397605e43901407e56e828120f1a2a))
* **stats:** add to admin, cleanup ([#479](https://github.com/openfoodfacts/open-prices/issues/479)) ([39866ac](https://github.com/openfoodfacts/open-prices/commit/39866ac386f4a27457c6c7c0837aa724dafedcdf))
* **stats:** New daily CRON to update TotalStats ([#478](https://github.com/openfoodfacts/open-prices/issues/478)) ([63f5a76](https://github.com/openfoodfacts/open-prices/commit/63f5a762c17c1f933d64dc027b584d0c32da4e9b))

## [1.40.0](https://github.com/openfoodfacts/open-prices/compare/v1.39.3...v1.40.0) (2024-09-27)


### Features

* **locations:** New Location.product_count field ([#470](https://github.com/openfoodfacts/open-prices/issues/470)) ([cebc523](https://github.com/openfoodfacts/open-prices/commit/cebc5236d9507263055c8c683e5e6c423ba24219))
* **locations:** New Location.proof_count field ([#468](https://github.com/openfoodfacts/open-prices/issues/468)) ([004af12](https://github.com/openfoodfacts/open-prices/commit/004af12e067df04d464f84762696fd8b9c9c099a))
* **locations:** New Location.user_count field ([#471](https://github.com/openfoodfacts/open-prices/issues/471)) ([be0c796](https://github.com/openfoodfacts/open-prices/commit/be0c7968838a283e08f98be5153e4029cbb0ac09))


### Technical

* **locations:** New weekly CRON to update Location counts ([#473](https://github.com/openfoodfacts/open-prices/issues/473)) ([07b1c4c](https://github.com/openfoodfacts/open-prices/commit/07b1c4ca3424bc885dcc5c9dfff179f6ea45a9c6))

## [1.39.3](https://github.com/openfoodfacts/open-prices/compare/v1.39.2...v1.39.3) (2024-09-24)


### Bug Fixes

* **Django:** set 2h long task timeout & retry. ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([87b6e21](https://github.com/openfoodfacts/open-prices/commit/87b6e21b1c20878de771b0d7cb3b52e47500f6b6))
* **Django:** split OFF product sync into 4 flavors. ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([4fab7b8](https://github.com/openfoodfacts/open-prices/commit/4fab7b8d0e5f6db8d9ab059f2d0f4ecbd58eb192))

## [1.39.2](https://github.com/openfoodfacts/open-prices/compare/v1.39.1...v1.39.2) (2024-09-23)


### Bug Fixes

* **Django:** fix daily DB backup task ([#461](https://github.com/openfoodfacts/open-prices/issues/461)) ([35cbb81](https://github.com/openfoodfacts/open-prices/commit/35cbb819b9469d2e7db1eb0a7b8e7129a732ae96))
* **Django:** tentative fix by removing task timeout. ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([c03af3c](https://github.com/openfoodfacts/open-prices/commit/c03af3c0a31c4e79044c6f208c3014a0ab8a92be))


### Technical

* **proofs:** extra API filtering (on date year & month, on empty location_id) ([99e88c0](https://github.com/openfoodfacts/open-prices/commit/99e88c0afabdc2a8f757a1961b1fc1fe6d641708))

## [1.39.1](https://github.com/openfoodfacts/open-prices/compare/v1.39.0...v1.39.1) (2024-09-23)


### Bug Fixes

* **Django:** set task max retry to 1. ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([2814a53](https://github.com/openfoodfacts/open-prices/commit/2814a535dcb77825cb62f20de26b361c3185916d))

## [1.39.0](https://github.com/openfoodfacts/open-prices/compare/v1.38.0...v1.39.0) (2024-09-22)


### Features

* **prices:** new querysets to calculate min, max & average ([#452](https://github.com/openfoodfacts/open-prices/issues/452)) ([ab9ed15](https://github.com/openfoodfacts/open-prices/commit/ab9ed15b0ddc7675ed4142edf1726595ecbd5bdd))
* **prices:** new stats endpoint ([#454](https://github.com/openfoodfacts/open-prices/issues/454)) ([540feba](https://github.com/openfoodfacts/open-prices/commit/540febaf3dccdb8ade02b16f9c0ab0d28477ef89))
* **products:** new properties to calculate price min, max & average ([#453](https://github.com/openfoodfacts/open-prices/issues/453)) ([f662710](https://github.com/openfoodfacts/open-prices/commit/f6627104125e13b879f95c91169fcf7e2bd9d7b1))


### Bug Fixes

* **Django:** fix daily import script (add source in updated fields). ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([fe569d7](https://github.com/openfoodfacts/open-prices/commit/fe569d7a778da99ebe3fe81ad7b7ddf5bfdb9f09))


### Technical

* Autolabel some PRs ([#436](https://github.com/openfoodfacts/open-prices/issues/436)) ([c6122be](https://github.com/openfoodfacts/open-prices/commit/c6122be842a3b3cf2e4e6a5516381221b2e6823a))
* generate price schema ([#457](https://github.com/openfoodfacts/open-prices/issues/457)) ([4d66eee](https://github.com/openfoodfacts/open-prices/commit/4d66eee7c5b415aec2d5b81909da6193ef77a89b))
* **users:** New weekly CRON to update User counts ([#458](https://github.com/openfoodfacts/open-prices/issues/458)) ([f7072b8](https://github.com/openfoodfacts/open-prices/commit/f7072b8c9eaf549ba5d4bfebe9580306d6736977))
* **users:** update is_moderator on login ([#456](https://github.com/openfoodfacts/open-prices/issues/456)) ([67caa6f](https://github.com/openfoodfacts/open-prices/commit/67caa6f6c1d609654257613a920a11d1c3a91e4e))

## [1.38.0](https://github.com/openfoodfacts/open-prices/compare/v1.37.0...v1.38.0) (2024-09-15)


### Features

* **prices:** add API filter by labels_tags & origins_tags ([#449](https://github.com/openfoodfacts/open-prices/issues/449)) ([dab02ae](https://github.com/openfoodfacts/open-prices/commit/dab02ae2d1b402bd03d3482788958e74337a1eb3))


### Bug Fixes

* **Django:** fix babel currency list order ([#447](https://github.com/openfoodfacts/open-prices/issues/447)) ([4da6da2](https://github.com/openfoodfacts/open-prices/commit/4da6da2260dc3e7fb207738156743aafdc280606))
* **Django:** fix daily import script (avoid unique_scans_n null). ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([0656431](https://github.com/openfoodfacts/open-prices/commit/0656431c6e1ac38c31ab83944edd4631609e07b3))
* **Django:** fix daily import script (seperate bulk_create & bulk_update). ref [#376](https://github.com/openfoodfacts/open-prices/issues/376) ([294261f](https://github.com/openfoodfacts/open-prices/commit/294261fecc828c5a9032c7fb0b979b05f2403707))

## [1.37.0](https://github.com/openfoodfacts/open-prices/compare/v1.36.1...v1.37.0) (2024-09-12)


### Features

* **GDPR:** improve script to manage Picard ([#430](https://github.com/openfoodfacts/open-prices/issues/430)) ([955cecc](https://github.com/openfoodfacts/open-prices/commit/955ceccdce65b147189c9d1421d02fd0bf6577e1))
* **users:** New User.location_count field ([#440](https://github.com/openfoodfacts/open-prices/issues/440)) ([ba02e6b](https://github.com/openfoodfacts/open-prices/commit/ba02e6bfc8bf37b6e2190d24062ba8a17b704346))
* **users:** New User.product_count field ([#441](https://github.com/openfoodfacts/open-prices/issues/441)) ([c440ced](https://github.com/openfoodfacts/open-prices/commit/c440ced63d86fe3862091b30ca255f233e4b1f8c))
* **users:** New User.proof_count field ([#442](https://github.com/openfoodfacts/open-prices/issues/442)) ([2cb5fb1](https://github.com/openfoodfacts/open-prices/commit/2cb5fb123f4053261708ea177313f18c3ca43989))


### Bug Fixes

* **GDPR:** fix Picard import script after testing in prod. ref [#430](https://github.com/openfoodfacts/open-prices/issues/430) ([38e50c9](https://github.com/openfoodfacts/open-prices/commit/38e50c907f12aed3bbf54b52669adb824b5ba862))


### Technical

* **GDPR:** add proof images. ref [#213](https://github.com/openfoodfacts/open-prices/issues/213) ([db749f9](https://github.com/openfoodfacts/open-prices/commit/db749f92fc3f54cb108892e3bafe56482beed91b))

## [1.36.1](https://github.com/openfoodfacts/open-prices/compare/v1.36.0...v1.36.1) (2024-09-11)


### Technical

* **Django:** Update contributing.md. ref [#431](https://github.com/openfoodfacts/open-prices/issues/431) ([c2bfb1d](https://github.com/openfoodfacts/open-prices/commit/c2bfb1d82ad1b7464f2eb7c3ffadf0839ba28e6c))
* **Django:** Updated project setup instruction ([#432](https://github.com/openfoodfacts/open-prices/issues/432)) ([d5fa2b8](https://github.com/openfoodfacts/open-prices/commit/d5fa2b8c52c7a0e081846e2b907246421a743f67))
* fix pre-commit. ref [#425](https://github.com/openfoodfacts/open-prices/issues/425) ([211beb2](https://github.com/openfoodfacts/open-prices/commit/211beb24821a164c4446c492334cb3b8a5e5533f))
* **proofs:** simple update_location() method ([#437](https://github.com/openfoodfacts/open-prices/issues/437)) ([d54ded6](https://github.com/openfoodfacts/open-prices/commit/d54ded6feee537aba8be3a97e39f42f53d92f4a2))

## [1.36.0](https://github.com/openfoodfacts/open-prices/compare/v1.35.1...v1.36.0) (2024-09-11)


### Features

* **Django:** add model init migrations ([#413](https://github.com/openfoodfacts/open-prices/issues/413)) ([8aabad6](https://github.com/openfoodfacts/open-prices/commit/8aabad60e95bd8ca51d16b1bb78310294d60eee8))


### Technical

* add model with_stats() queryset. Add tests ([5aa00e7](https://github.com/openfoodfacts/open-prices/commit/5aa00e7d6483a0f435f69bac8ec177f4aa39038e))
* **stats:** new model update_price_count() methods ([#435](https://github.com/openfoodfacts/open-prices/issues/435)) ([b25146d](https://github.com/openfoodfacts/open-prices/commit/b25146ddca79f9bd75207131f7855b222abc3241))
* **tests:** skip Product & Location post_save signals ([#434](https://github.com/openfoodfacts/open-prices/issues/434)) ([639cee6](https://github.com/openfoodfacts/open-prices/commit/639cee6ac17836a9da9e6ded712f3529446865d9))
* Update github-projects.yml ([8d82664](https://github.com/openfoodfacts/open-prices/commit/8d826644fea2391bd9a20af973a2db3e2f164363))

## [1.35.1](https://github.com/openfoodfacts/open-prices/compare/v1.35.0...v1.35.1) (2024-09-06)


### Bug Fixes

* **Django:** improve some API returns ([#426](https://github.com/openfoodfacts/open-prices/issues/426)) ([092e436](https://github.com/openfoodfacts/open-prices/commit/092e436b58195df9fa00e2c7a9d0ab0c2c821f2f))

## [1.35.0](https://github.com/openfoodfacts/open-prices/compare/v1.34.2...v1.35.0) (2024-09-05)


### Features

* **prices:** GET /prices/id detail endpoint ([#423](https://github.com/openfoodfacts/open-prices/issues/423)) ([0d67b5c](https://github.com/openfoodfacts/open-prices/commit/0d67b5c7911876afb1f345e43f36d25675ae246b))


### Technical

* Create github-projects.yml ([092f591](https://github.com/openfoodfacts/open-prices/commit/092f591ca60302c0f9cef9188c5f812452348a54))
* fix github-project.yml ([4d9a1fd](https://github.com/openfoodfacts/open-prices/commit/4d9a1fd2d87cde22e8245822ad1d7272f951b41d))
* Update github-projects.yml ([04e9e10](https://github.com/openfoodfacts/open-prices/commit/04e9e10527bedbb0d67e210af31c71d04ab3609b))

## [1.34.2](https://github.com/openfoodfacts/open-prices/compare/v1.34.1...v1.34.2) (2024-09-04)


### Bug Fixes

* **Django:** allow querying api/status with any auth ([#417](https://github.com/openfoodfacts/open-prices/issues/417)) ([3d9b486](https://github.com/openfoodfacts/open-prices/commit/3d9b4867cab27f44cae46c2da4a788e31bfd1e13))

## [1.34.1](https://github.com/openfoodfacts/open-prices/compare/v1.34.0...v1.34.1) (2024-09-04)


### Technical

* fix static configuration ([#415](https://github.com/openfoodfacts/open-prices/issues/415)) ([79002d6](https://github.com/openfoodfacts/open-prices/commit/79002d61b7257511544b24ef8088bdaaa75aeb41))

## [1.34.0](https://github.com/openfoodfacts/open-prices/compare/v1.33.0...v1.34.0) (2024-09-02)


### Features

* rewrite backend from FastAPI to Django ([#366](https://github.com/openfoodfacts/open-prices/issues/366)) ([081a22d](https://github.com/openfoodfacts/open-prices/commit/081a22dadda4b6a388c4204bad1390759d455282))


### Bug Fixes

* **Django:** extra API fixes round 2 ([#401](https://github.com/openfoodfacts/open-prices/issues/401)) ([1bb28d8](https://github.com/openfoodfacts/open-prices/commit/1bb28d835e8f87b4c7bf622d645da633f8e54b24))
* **Django:** fix update price_counts on Price create/delete ([#404](https://github.com/openfoodfacts/open-prices/issues/404)) ([9134f3c](https://github.com/openfoodfacts/open-prices/commit/9134f3cfedc9f9715266335d582856b241de56e2))
* **Django:** run Django tests instead of FastAPI ([#402](https://github.com/openfoodfacts/open-prices/issues/402)) ([0628f62](https://github.com/openfoodfacts/open-prices/commit/0628f62ad230c9caef1f0cad16c1f4f974e7e879))
* **Django:** update CI test config. ref [#402](https://github.com/openfoodfacts/open-prices/issues/402) ([5edf691](https://github.com/openfoodfacts/open-prices/commit/5edf6914b5f26935ff82879efdfa5be9bed7dfc4))


### Technical

* add compose project name ([6c83c4c](https://github.com/openfoodfacts/open-prices/commit/6c83c4c7220a0bf2bc33972acb758797162fac75))
* always launch quality checks ([18c51f8](https://github.com/openfoodfacts/open-prices/commit/18c51f8975a42315b0623d03431f1e38f7350d5c))
* **Django:** Use select_related to avoid N+1 queries ([#403](https://github.com/openfoodfacts/open-prices/issues/403)) ([7302a0e](https://github.com/openfoodfacts/open-prices/commit/7302a0ecdaf5d1a76c3c3966951c2163ca83e3b7))
* fix CI ([#406](https://github.com/openfoodfacts/open-prices/issues/406)) ([f862116](https://github.com/openfoodfacts/open-prices/commit/f862116a64bfd4cbcfa559cf1a0546bab84d64b9))
* fix test CI ([#411](https://github.com/openfoodfacts/open-prices/issues/411)) ([982c9d1](https://github.com/openfoodfacts/open-prices/commit/982c9d100da65151cba73dd3765e4b4181998fe2))
* rename data-import folder to scripts ([612c939](https://github.com/openfoodfacts/open-prices/commit/612c939e42536318e32afb6b3419f931fc9fb460))
* **Sentry:** add Sentry environment variable (net or org). ref [#400](https://github.com/openfoodfacts/open-prices/issues/400) ([554fc3f](https://github.com/openfoodfacts/open-prices/commit/554fc3f5728202bbb13073ee2b44c07a2fcde8ab))
* try to remove image in dev.yml ([b79b052](https://github.com/openfoodfacts/open-prices/commit/b79b05224d74f2ee2f108ad5da39e4fd8886e986))
* update build branch ([682955c](https://github.com/openfoodfacts/open-prices/commit/682955c17b956933209273b3b6b9baca4032e25b))

## [1.33.0](https://github.com/openfoodfacts/open-prices/compare/v1.32.1...v1.33.0) (2024-08-22)


### Features

* **locations:** add extra filter by osm_address_city ([eb27b72](https://github.com/openfoodfacts/open-prices/commit/eb27b72d914b6e51d2249299eef0be78aba0cdc6))

## [1.32.1](https://github.com/openfoodfacts/open-prices/compare/v1.32.0...v1.32.1) (2024-08-20)


### Bug Fixes

* fix permission issue ([c6e566a](https://github.com/openfoodfacts/open-prices/commit/c6e566ad99d5229aa0a532e7535a65803365f877))

## [1.32.0](https://github.com/openfoodfacts/open-prices/compare/v1.31.1...v1.32.0) (2024-08-20)


### Features

* **products:** new filter by brands_tags ([#390](https://github.com/openfoodfacts/open-prices/issues/390)) ([a4f77c0](https://github.com/openfoodfacts/open-prices/commit/a4f77c0785acdf3ea804e198ec52e95426efe5dd))


### Technical

* add home_cache volume ([#361](https://github.com/openfoodfacts/open-prices/issues/361)) ([3ec9632](https://github.com/openfoodfacts/open-prices/commit/3ec96325dba4557eff59dfa9ba259b5ce668f5ad))
* Create label.yml ([4e9d0be](https://github.com/openfoodfacts/open-prices/commit/4e9d0bebfd0059b1347e630b2faf41eb8327650b))
* Create labeler.yml ([eae407a](https://github.com/openfoodfacts/open-prices/commit/eae407ad816d5720e2ae6548c7adf1054ef5ff4a))
* fix unit test ([#359](https://github.com/openfoodfacts/open-prices/issues/359)) ([7ca1d2f](https://github.com/openfoodfacts/open-prices/commit/7ca1d2ffc0445da2993e383af175a42fb68b7c42))

## [1.31.1](https://github.com/openfoodfacts/open-prices/compare/v1.31.0...v1.31.1) (2024-07-15)


### Technical

* move images and data dump to docker volumes ([#356](https://github.com/openfoodfacts/open-prices/issues/356)) ([dee6550](https://github.com/openfoodfacts/open-prices/commit/dee6550696b6422dd11eefaa82e6511f948e2053))

## [1.31.0](https://github.com/openfoodfacts/open-prices/compare/v1.30.0...v1.31.0) (2024-07-05)


### Features

* **prices:** new date filter by year & month ([#350](https://github.com/openfoodfacts/open-prices/issues/350)) ([65e3b2d](https://github.com/openfoodfacts/open-prices/commit/65e3b2dad806da3ee86d01b56011dd6a153861ef))

## [1.30.0](https://github.com/openfoodfacts/open-prices/compare/v1.29.1...v1.30.0) (2024-06-28)


### Features

* **locations:** add POST endpoint to create a location ([#347](https://github.com/openfoodfacts/open-prices/issues/347)) ([b05925a](https://github.com/openfoodfacts/open-prices/commit/b05925aa32229a0815b97797b5717f60430c92e9))


### Technical

* **proofs:** Use ProofCreate schema when possible. Move owner field to ProofFull ([9f09534](https://github.com/openfoodfacts/open-prices/commit/9f09534a0f17216ff9c885333ed74d21848c4443))

## [1.29.1](https://github.com/openfoodfacts/open-prices/compare/v1.29.0...v1.29.1) (2024-06-27)


### Bug Fixes

* **ci:** add some missing conventional commit types in release-please config. ref [#344](https://github.com/openfoodfacts/open-prices/issues/344) ([9117657](https://github.com/openfoodfacts/open-prices/commit/91176578342371dba1d8495801701c047ae98b5c))
* **ci:** fixed branch name for release-please. ref [#344](https://github.com/openfoodfacts/open-prices/issues/344) ([056f61e](https://github.com/openfoodfacts/open-prices/commit/056f61e786fe6e2d977b80a5edd13906f01113ca))


### Technical

* **prices:** reorganise schema inheritance to validate price updates ([#342](https://github.com/openfoodfacts/open-prices/issues/342)) ([64aac06](https://github.com/openfoodfacts/open-prices/commit/64aac0640335e4b6dfcf510a57d2ddce29aff467))
* **proofs:** reorganise schema inheritance ([#343](https://github.com/openfoodfacts/open-prices/issues/343)) ([7e17a68](https://github.com/openfoodfacts/open-prices/commit/7e17a6806e8014a4a2dfefbc5ec9c53407f336b2))
* revert release-please config to v3 ([#344](https://github.com/openfoodfacts/open-prices/issues/344)) ([739e128](https://github.com/openfoodfacts/open-prices/commit/739e12886a3a9339e9f83a7015855ae78d67563f))
* update README with links ([e985ab2](https://github.com/openfoodfacts/open-prices/commit/e985ab288cad250ca69b95ae531aceb683917972))

## [1.29.0](https://github.com/openfoodfacts/open-prices/compare/v1.28.0...v1.29.0) (2024-06-24)


### Features

* **proofs:** New location fields ([#338](https://github.com/openfoodfacts/open-prices/issues/338)) ([fe54229](https://github.com/openfoodfacts/open-prices/commit/fe54229433b2868d77413702ccdf50fd0db16ea2))
* **proofs:** New proof.currency field ([#337](https://github.com/openfoodfacts/open-prices/issues/337)) ([b9d2c90](https://github.com/openfoodfacts/open-prices/commit/b9d2c905b825e127c35b3c97e4dae1b6d054f99d))
* **proofs:** New proof.date field ([#330](https://github.com/openfoodfacts/open-prices/issues/330)) ([1b41308](https://github.com/openfoodfacts/open-prices/commit/1b41308646a5785731450a0cc86a5c208c384fc7))


### Bug Fixes

* import dumps at 3PM instead of 10AM ([#332](https://github.com/openfoodfacts/open-prices/issues/332)) ([543c54c](https://github.com/openfoodfacts/open-prices/commit/543c54c403c9ab89d559ab53dda25927998bdae3))
* **proofs:** also return proof relationships when fetching detail. ref [#338](https://github.com/openfoodfacts/open-prices/issues/338) ([d323180](https://github.com/openfoodfacts/open-prices/commit/d323180f1f0c75640b4acc8b0d3d04cc3627bfd2))
* **proofs:** improve new proof date & currency optional mgmt. ref [#327](https://github.com/openfoodfacts/open-prices/issues/327) & [#337](https://github.com/openfoodfacts/open-prices/issues/337) ([5a309b4](https://github.com/openfoodfacts/open-prices/commit/5a309b42ba03b27660ba0001e1763b24513025a4))

## [1.28.0](https://github.com/openfoodfacts/open-prices/compare/v1.27.0...v1.28.0) (2024-06-04)


### Features

* **prices:** new source field to store the app name ([#301](https://github.com/openfoodfacts/open-prices/issues/301)) ([9efd923](https://github.com/openfoodfacts/open-prices/commit/9efd92385df63af12a8b5e2a7df49e9997053a31))
* **proofs:** new source field to store the app name ([#310](https://github.com/openfoodfacts/open-prices/issues/310)) ([30ab149](https://github.com/openfoodfacts/open-prices/commit/30ab149d9af87e347145dfb76ca80e1664cdba63))

## [1.27.0](https://github.com/openfoodfacts/open-prices/compare/v1.26.0...v1.27.0) (2024-05-21)


### Features

* **location:** store OSM address country_code ([#296](https://github.com/openfoodfacts/open-prices/issues/296)) ([43485ed](https://github.com/openfoodfacts/open-prices/commit/43485ed211e0b9c022ab8f0c1adde30fc0bc6552))
* **location:** store OSM tag key & value ([#294](https://github.com/openfoodfacts/open-prices/issues/294)) ([3eeccbd](https://github.com/openfoodfacts/open-prices/commit/3eeccbde8c2676bc490721d36726d14baa903374))


### Bug Fixes

* **data:** fix daily data import script ([#299](https://github.com/openfoodfacts/open-prices/issues/299)) ([588ad52](https://github.com/openfoodfacts/open-prices/commit/588ad52e4c42735ada82121124a1782e44735a95))

## [1.26.0](https://github.com/openfoodfacts/open-prices/compare/v1.25.1...v1.26.0) (2024-05-02)


### Features

* add daily dumps of DB main tables as JSONL files ([#282](https://github.com/openfoodfacts/open-prices/issues/282)) ([9d3f1a7](https://github.com/openfoodfacts/open-prices/commit/9d3f1a7d4dc1d2a995d93910526e69dfdf218f04))


### Bug Fixes

* fix KeyError: 'unique_scans_n' error ([#273](https://github.com/openfoodfacts/open-prices/issues/273)) ([bee3b0b](https://github.com/openfoodfacts/open-prices/commit/bee3b0b7ef2af79932a4e64ec5ba9caa36a41d1d))
* fix the user agent ([#276](https://github.com/openfoodfacts/open-prices/issues/276)) ([f7b0945](https://github.com/openfoodfacts/open-prices/commit/f7b094563d9e522475d2c8a5f5588e089d7a5f18))

## [1.25.1](https://github.com/openfoodfacts/open-prices/compare/v1.25.0...v1.25.1) (2024-04-17)


### Bug Fixes

* **proof:** remove is_public flag ([#267](https://github.com/openfoodfacts/open-prices/issues/267)) ([0e300c8](https://github.com/openfoodfacts/open-prices/commit/0e300c8b02799fde7e2e56eb2c7c50a6a5184d89))
* remove proof.is_public field in DB ([#270](https://github.com/openfoodfacts/open-prices/issues/270)) ([8049502](https://github.com/openfoodfacts/open-prices/commit/804950282770098555381674a4503d0e17f46009))

## [1.25.0](https://github.com/openfoodfacts/open-prices/compare/v1.24.1...v1.25.0) (2024-04-03)


### Features

* sync ALL products (obf, opff, opf) ([#264](https://github.com/openfoodfacts/open-prices/issues/264)) ([9f876c4](https://github.com/openfoodfacts/open-prices/commit/9f876c4e6c5ee7e8221273065d3f2c18163b8c34))


### Bug Fixes

* start a new db session before each flavor import. ref [#264](https://github.com/openfoodfacts/open-prices/issues/264) ([814078b](https://github.com/openfoodfacts/open-prices/commit/814078b662e629ae9861e3f10bd8375024d93f94))

## [1.24.1](https://github.com/openfoodfacts/open-prices/compare/v1.24.0...v1.24.1) (2024-03-27)


### Bug Fixes

* fix set_cookie call ([00d311f](https://github.com/openfoodfacts/open-prices/commit/00d311fa4a59a6e3810b51a0c45fc403ce4d285c))
* setting cookie on the response ([#242](https://github.com/openfoodfacts/open-prices/issues/242)) ([2969abe](https://github.com/openfoodfacts/open-prices/commit/2969abe25b765bc1c38e78d64d6d879089b2a290))

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
