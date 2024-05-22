import yaml
from openfoodfacts import Flavor
from sqlalchemy.orm import Session
from app.db import Base, engine
from app.enums import CurrencyEnum, LocationOSMEnum, PricePerEnum, ProofTypeEnum
from app.models import Location, Price, Product, Proof
from app.models import Session as UserSession
from app.models import User


# Database creation
Base.metadata.create_all(bind=engine)


def load_fixtures(session, file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)

    # Load data from YAML file
    # Import users
    for user_data in data["users"]:
        user = User(**user_data)
        session.add(user)

    # Import sessions
    for session_data in data["sessions"]:
        session_obj = UserSession(**session_data)
        session.add(session_obj)

    # Import products
    for product_data in data["products"]:
        if product_data.get("source"):
            product_data["source"] = Flavor[product_data["source"]]
        product = Product(**product_data)
        session.add(product)

    # Import locations
    for location_data in data["locations"]:
        location_data["osm_type"] = LocationOSMEnum[location_data["osm_type"]]
        location = Location(**location_data)
        session.add(location)

    # Import proofs
    for proof_data in data["proofs"]:
        proof_data["type"] = ProofTypeEnum[proof_data["type"]]
        proof = Proof(**proof_data)
        session.add(proof)

    # Import prices
    for price_data in data["prices"]:
        price_data["currency"] = CurrencyEnum[price_data.get("currency", "")]
        price_data["price_per"] = PricePerEnum.get(
            price_data.get("price_per"), PricePerEnum.DEFAULT
        )
        price_data["location_osm_type"] = LocationOSMEnum[
            price_data.get("location_osm_type", "DEFAULT_OSM_TYPE")
        ]
        # Create and add the Price object in a single step
        session.add(Price(**price_data))

    session.commit()


# Main function to run the script
def main():
    with Session(engine) as session:
        load_fixtures(session, "fixtures/data.yaml")


# Entry point of the script
if __name__ == "__main__":
    main()
