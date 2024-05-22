import os

os.environ['PYTHONPATH'] = "/opt/open-prices"

import yaml
from sqlalchemy.orm import Session
from app.db import Base, engine
from app.models import User, Session as UserSession, Product, Location, Proof, Price
from app.enums import CurrencyEnum, LocationOSMEnum, PricePerEnum, ProofTypeEnum
from openfoodfacts import Flavor



# Database connection
Base.metadata.create_all(bind=engine)

def load_fixtures(session, file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)

    # Import Users
    for user_data in data["users"]:
        user = User(**user_data)
        session.add(user)

    # Import Sessions
    for session_data in data["sessions"]:
        session_obj = UserSession(**session_data)
        session.add(session_obj)

    # Import Products
    for product_data in data["products"]:
        if product_data.get("source"):
            product_data["source"] = Flavor[product_data["source"]]
        product = Product(**product_data)
        session.add(product)

    # Import Locations
    for location_data in data["locations"]:
        location_data["osm_type"] = LocationOSMEnum[location_data["osm_type"]]
        location = Location(**location_data)
        session.add(location)

    # Import Proofs
    for proof_data in data["proofs"]:
        proof_data["type"] = ProofTypeEnum[proof_data["type"]]
        proof = Proof(**proof_data)
        session.add(proof)

    # Import Prices
    for price_data in data["prices"]:
        price_data["currency"] = CurrencyEnum[price_data["currency"]]
        if price_data.get("price_per"):
            price_data["price_per"] = PricePerEnum[price_data["price_per"]]
        price_data["location_osm_type"] = LocationOSMEnum[price_data["location_osm_type"]]
        price = Price(**price_data)
        session.add(price)

    session.commit()

def main():
    with Session(engine) as session:
        load_fixtures(session, "fixtures/data.yaml")

if __name__ == "__main__":
    main()
