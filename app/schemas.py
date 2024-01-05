import datetime

from fastapi_filters import FilterField, FilterOperator
from openfoodfacts import Flavor
from openfoodfacts.taxonomy import get_taxonomy
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.enums import CurrencyEnum, LocationOSMEnum, ProofTypeEnum


class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: str
    token: str


class ProductCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    code: str = Field(
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["8001505005707"],
    )


class ProductBase(ProductCreate):
    id: int
    source: Flavor | None = Field(
        description="source of data, either `off` (Open Food Facts), "
        "`obf` (Open Beauty Facts), `opff` (Open Pet Food Facts) or `obf` (Open Beauty Facts)"
    )
    product_name: str | None = Field(
        description="name of the product.", examples=["Nocciolata"]
    )
    product_quantity: int | None = Field(
        description="quantity of the product, normalized in g or mL (depending on the product).",
        examples=[700],
    )
    brands: str | None = Field(
        description="brand(s) of the product.",
        examples=["Rigoni di Asiago", "Lindt"],
    )
    image_url: AnyHttpUrl | None = Field(
        description="URL of the product image.",
        examples=[
            "https://images.openfoodfacts.org/images/products/800/150/500/5707/front_fr.161.400.jpg"
        ],
    )
    unique_scans_n: int | None = Field(
        description="number of unique scans of the product on Open Food Facts.",
        examples=[15],
    )
    created: datetime.datetime = Field(description="datetime of the creation.")
    updated: datetime.datetime | None = Field(
        description="datetime of the last update."
    )


class LocationCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    osm_id: int = Field(gt=0)
    osm_type: LocationOSMEnum


class LocationBase(LocationCreate):
    id: int
    osm_name: str | None
    osm_display_name: str | None
    osm_address_postcode: str | None
    osm_address_city: str | None
    osm_address_country: str | None
    osm_lat: float | None
    osm_lon: float | None
    created: datetime.datetime
    updated: datetime.datetime | None


class PriceCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    product_code: str | None = Field(
        default=None,
        min_length=1,
        pattern="^[0-9]+$",
        description="barcode (EAN) of the product, as a string.",
        examples=["16584958", "8001505005707"],
    )
    product_name: str | None = Field(
        default=None,
        min_length=1,
        description="name of the product, as displayed on the receipt or the price tag.",
        examples=["PATE NOCCIOLATA BIO 700G"],
    )
    category_tag: str | None = Field(
        default=None,
        min_length=3,
        pattern=r"^[a-z]{2,}:[a-zA-Z\-]+$",
        examples=["en:tomatoes", "en:apples"],
        description="""ID of the Open Food Facts category of the product for
        products without barcode.

        This is mostly for raw products such as vegetables or fruits. This
        field is exclusive with `product_code`: if this field is set, it means
        that the product does not have a barcode.

        This ID must be a canonical category ID in the Open Food Facts taxonomy.
        If the ID is not valid, the price will be rejected.""",
    )
    labels_tags: list[str] | None = Field(
        default=None,
        description="""labels of the product, only for products without barcode.

        The labels must be valid labels in the Open Food Facts taxonomy.
        If one of the labels is not valid, the price will be rejected.

        The most common labels are:
        - `en:organic`: the product is organic
        - `fr:ab-agriculture-biologique`: the product is organic, in France
        - `en:fair-trade`: the product is fair-trade

        Other labels can be provided if relevant.
        """,
        examples=["en:organic", "fr:ab-agriculture-biologique", "en:fair-trade"],
    )
    origins_tags: list[str] | None = Field(
        default=None,
        description="""origins of the product, only for products without barcode.

        This field is a list as some products may be a mix of several origins,
        but most products have only one origin.

        The origins must be valid origins in the Open Food Facts taxonomy.
        If one of the origins is not valid, the price will be rejected.""",
        examples=["en:california", "en:france", "en:italy", "en:spain"],
    )
    price: float = Field(
        gt=0,
        description="price of the product, without its currency, taxes included. "
        "If the price is about a barcode-less product, it must be the price per "
        "kilogram or per liter.",
        examples=["1.99"],
    )
    currency: CurrencyEnum = Field(
        description="currency of the price, as a string. "
        "The currency must be a valid currency code. "
        "See https://en.wikipedia.org/wiki/ISO_4217 for a list of valid currency codes.",
        examples=["EUR", "USD"],
    )
    location_osm_id: int = Field(
        gt=0,
        description="ID of the location in OpenStreetMap: the store where the product was bought.",
        examples=[1234567890],
    )
    location_osm_type: LocationOSMEnum = Field(
        description="type of the OpenStreetMap location object. Stores can be represented as nodes, "
        "ways or relations in OpenStreetMap. It is necessary to be able to fetch the correct "
        "information about the store using the ID.",
    )
    date: datetime.date = Field(description="date when the product was bought.")
    proof_id: int | None = Field(
        default=None,
        description="ID of the proof, if any. The proof is a file (receipt or price tag image) "
        "uploaded by the user to prove the price of the product. "
        "The proof must be uploaded before the price, and the authenticated user must be the "
        "owner of the proof.",
        examples=[15],
    )


class PriceCreateWithValidation(PriceCreate):
    """A version of `PriceCreate` with taxonomy validations.

    These validations are not done in the `PriceCreate` model because they
    they are time-consuming and only necessary when creating a price from
    the API.
    """

    @field_validator("labels_tags")
    def labels_tags_is_valid(cls, v: list[str] | None):
        if v is not None:
            if len(v) == 0:
                raise ValueError("`labels_tags` cannot be empty")
            v = [label_tag.lower() for label_tag in v]
            labels_taxonomy = get_taxonomy("label")
            for label_tag in v:
                if label_tag not in labels_taxonomy:
                    raise ValueError(
                        f"Invalid label tag: label '{label_tag}' does not exist in the taxonomy",
                    )
        return v

    @field_validator("origins_tags")
    def origins_tags_is_valid(cls, v: list[str] | None):
        if v is not None:
            if len(v) == 0:
                raise ValueError("`origins_tags` cannot be empty")
            v = [origin_tag.lower() for origin_tag in v]
            origins_taxonomy = get_taxonomy("origin")
            for origin_tag in v:
                if origin_tag not in origins_taxonomy:
                    raise ValueError(
                        f"Invalid origin tag: origin '{origin_tag}' does not exist in the taxonomy",
                    )
        return v

    @field_validator("category_tag")
    def category_tag_is_valid(cls, v: str | None):
        if v is not None:
            v = v.lower()
            category_taxonomy = get_taxonomy("category")
            if v not in category_taxonomy:
                raise ValueError(
                    f"Invalid category tag: category '{v}' does not exist in the taxonomy"
                )
        return v

    @model_validator(mode="after")
    def product_code_and_category_tag_are_exclusive(self):
        """Validator that checks that `product_code` and `category_tag` are
        exclusive, and that at least one of them is set."""
        if self.product_code is not None:
            if self.category_tag is not None:
                raise ValueError(
                    "`product_code` and `category_tag` are exclusive, you can't set both"
                )
            if self.labels_tags is not None:
                raise ValueError(
                    "`labels_tags` can only be set for products without barcode"
                )
            if self.origins_tags is not None:
                raise ValueError(
                    "`origins_tags` can only be set for products without barcode"
                )
        if self.product_code is None and self.category_tag is None:
            raise ValueError("either `product_code` or `category_tag` must be set")
        return self


class PriceBase(PriceCreate):
    product_id: int | None
    location_id: int | None
    owner: str
    created: datetime.datetime


class PriceFull(PriceBase):
    product: ProductBase | None
    location: LocationBase | None


# class ProofCreate(BaseModel):
#     file: UploadFile
#     type: ProofTypeEnum


class ProofBase(BaseModel):
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

    id: int
    file_path: str
    mimetype: str
    type: ProofTypeEnum | None = None
    owner: str
    created: datetime.datetime


PRICE_FILTERS = {
    "product_code": FilterField(str, operators={FilterOperator.eq}),
    "product_id": FilterField(int, operators={FilterOperator.eq}),
    "category_tag": FilterField(str, operators={FilterOperator.eq}),
    "labels_tags": FilterField(list[str], operators={FilterOperator.like}),
    "origins_tags": FilterField(list[str], operators={FilterOperator.like}),
    "location_osm_id": FilterField(int, operators={FilterOperator.eq}),
    "location_osm_type": FilterField(LocationOSMEnum, operators={FilterOperator.eq}),
    "location_id": FilterField(int, operators={FilterOperator.eq}),
    "price": FilterField(
        float,
        operators={
            FilterOperator.eq,
            FilterOperator.gt,
            FilterOperator.lt,
            FilterOperator.ge,
            FilterOperator.le,
        },
    ),
    "currency": FilterField(str, operators={FilterOperator.eq}),
    "date": FilterField(
        datetime.date,
        operators={
            FilterOperator.eq,
            FilterOperator.gt,
            FilterOperator.lt,
            FilterOperator.ge,
            FilterOperator.le,
        },
    ),
    "owner": FilterField(str, operators={FilterOperator.eq}),
}
