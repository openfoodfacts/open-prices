import requests

OFF_SEARCHLICIOUS_API_ENDPOINT = "https://search.openfoodfacts.org/search"
PICARD_GS1_PREFIX = "327016"


def get_picard_product_from_subcode(op_price_dict):
    # the Picard product_code is incomplete
    # use Search-a-licious API to get the full product code
    # if needed, prompt the user to select the correct one
    full_product_code = None

    print(
        "----- Input:",
        op_price_dict["product_code"],
        op_price_dict["product_name"],
        op_price_dict["price"],
    )

    STEPS = [
        f"code:{PICARD_GS1_PREFIX}?{op_price_dict['product_code']}? brands:picard",
        f"code:{PICARD_GS1_PREFIX}?{op_price_dict['product_code']}?",
        f"code:*{op_price_dict['product_code']}? brands:picard",
        f"code:*{op_price_dict['product_code']}?&page_size=50",
    ]
    for q_index, q_params in enumerate(STEPS):
        response = requests.get(
            OFF_SEARCHLICIOUS_API_ENDPOINT,
            params={"q": q_params},
        )
        print(response.url)
        if response.status_code == 200:
            response_product_count = response.json()["count"]
            print("Products found:", response_product_count)
            # loop until at least 1 product is returned
            if response_product_count:
                # confidence strong enough: take the first product
                if (q_index < 2) and (response_product_count == 1):
                    full_product_code = response.json()["hits"][0]["code"]
                    print("Chosen product code:", full_product_code)
                else:
                    # multiple results: prompt the user to select
                    response_product_list = response.json()["hits"]
                    for index, response_product in enumerate(response_product_list):
                        print(
                            index + 1,
                            ":",
                            response_product.get("code"),
                            response_product.get("product_name", ""),
                            response_product.get("brands_tags", ""),
                            response_product.get("stores", ""),
                        )
                    user_choice_number_str = input(
                        "Which product ? Type 0 to skip. Or provide the correct code: "
                    )
                    if len(user_choice_number_str) == 1:
                        full_product_code = response_product_list[
                            int(user_choice_number_str) - 1
                        ]["code"]
                        print("Chosen product code:", full_product_code)
                    elif 3 < len(user_choice_number_str) <= 13:
                        full_product_code = user_choice_number_str
                        print("Chosen product code:", full_product_code)
                    else:
                        print("Product not found...")
                break
            else:
                if q_index == len(STEPS) - 1:
                    # Last chance: prompt the user to type a EAN
                    user_choice_number_str = input(
                        "Which product ? Type 0 to skip. Or provide the correct code: "
                    )
                    if len(user_choice_number_str) == 13:
                        full_product_code = user_choice_number_str
                        print("Chosen product code:", full_product_code)
                    else:
                        print("Product not found...")

    return full_product_code
