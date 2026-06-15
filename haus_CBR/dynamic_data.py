import pandas as pd
import json

with open("haus.json", "r", encoding="utf-8") as f:
    data = json.load(f)


df = pd.DataFrame(data)


numeric_fields = [
    "Sweetness", "Creaminess", "Spiciness",
    "Crispiness", "Seafood", "Cheesiness", "Recommended"
]

for col in numeric_fields:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

categorical_cols = ["Type", "Subtype", "Serving Type", "Primary", "Secondary"]

encoders = {}
decoders = {}

for col in categorical_cols:
    vals = df[col].dropna()
    vals = vals[vals != "None"]

    mapping = {v: i+1 for i, v in enumerate(vals.unique())}
    reverse = {v: k for k, v in mapping.items()}

    encoders[col] = mapping
    decoders[col] = reverse

    df[col] = df[col].map(mapping)

def get_choices(attr, filters):
    temp = df.copy()

    for key in ["Type", "Subtype"]:
        if filters.get(key) is not None:
            temp = temp[temp[key] == filters[key]]

    vals = temp[attr].dropna().unique()

    if len(vals) == 0:
        vals = df[attr].dropna().unique()

    return sorted(vals)

def input_choice(attr, filters=None):
    if filters is None:
        filters = {}

    choices_encoded = get_choices(attr, filters)
    choices = [decoders[attr][c] for c in choices_encoded]

    print(f"\n{attr}:")
    for i, c in enumerate(choices, 1):
        print(f"{i}. {c}")

    while True:
        val = input("Pilih nomor (enter skip): ")
        if val == "":
            return None
        if val.isdigit() and 1 <= int(val) <= len(choices):
            return choices_encoded[int(val)-1]
        print("Input tidak valid!")

def input_range(prompt, min_val, max_val):
    while True:
        val = input(f"{prompt} ({min_val}-{max_val}, enter skip): ")
        if val == "":
            return None
        if val.isdigit():
            val = int(val)
            if min_val <= val <= max_val:
                return val
        print("Input tidak valid!")

def input_binary(prompt):
    while True:
        val = input(f"{prompt} (0/1, enter skip): ")
        if val == "":
            return None
        if val in ["0", "1"]:
            return int(val)
        print("Harus 0 atau 1!")

print("KUISIONER HAUS")

print("\nPilih kategori:")
print("1. Drink")
print("2. Food")
print("3. Drink and Food")

while True:
    first_choice = input("Pilih nomor: ")

    if first_choice in ["1", "2", "3"]:
        break

    print("Input tidak valid!")

all_users = []

def drink_questionnaire():

    user = {}
    filters = {}

    type_val = encoders["Type"].get("Drink")

    user["Type"] = type_val
    filters["Type"] = type_val

    print("\n=== DRINK QUESTIONNAIRE ===")

    user["Primary"] = input_choice("Primary", filters)
    user["Secondary"] = input_choice("Secondary", filters)

    user["Sweetness"] = input_range("Sweetness", 1, 2)
    user["Creaminess"] = input_range("Creaminess", 0, 2)

    return user

def food_questionnaire():

    user = {}
    filters = {}

    type_val = encoders["Type"].get("Food")

    user["Type"] = type_val
    filters["Type"] = type_val

    print("\n=== FOOD QUESTIONNAIRE ===")

    subtype_val = input_choice("Subtype", filters)

    user["Subtype"] = subtype_val
    filters["Subtype"] = subtype_val

    if subtype_val == encoders["Subtype"].get("Main Dish"):
        user["Serving Type"] = input_choice("Serving Type", filters)
        user["Spiciness"] = input_range("Spiciness", 0, 2)
        user["Cheesiness"] = input_range("Cheesiness", 0, 2)

    elif subtype_val == encoders["Subtype"].get("Side Dish"):
        user["Serving Type"] = input_choice("Serving Type", filters)
        user["Spiciness"] = input_binary("Spiciness")
        user["Cheesiness"] = input_binary("Cheesiness")
        user["Seafood"] = input_binary("Seafood")
        user["Crispiness"] = input_binary("Crispiness")

    elif subtype_val == encoders["Subtype"].get("Bread"):
        user["Serving Type"] = input_choice("Serving Type", filters)
        user["Primary"] = input_choice("Primary", filters)
        user["Secondary"] = input_choice("Secondary", filters)
        user["Crispiness"] = input_binary("Crispiness")

    elif subtype_val == encoders["Subtype"].get("Dessert"):
        user["Primary"] = input_choice("Primary", filters)

    return user

if first_choice == "1":
    all_users.append(drink_questionnaire())

elif first_choice == "2":
    all_users.append(food_questionnaire())

elif first_choice == "3":
    all_users.append(drink_questionnaire())
    all_users.append(food_questionnaire())

food_trays = [
    {"tray": "Cimol Mozzarella Cheese Sauce with Mango Yakult", "food": "Cimol", "drink": "Ice Mango mix Yakult"},
    {"tray": "Cimol Mozzarella Cheese Powder with Mango Yakult", "food": "Cimol", "drink": "Ice Mango mix Yakult"},

    {"tray": "Ramyeon Tray Choco Cheese Crunchy", "food": "Spicy Cheese Ramyeon", "drink": "Choco Cheese Crunchy"},
    {"tray": "Ramyeon Tray Drink Beng Beng", "food": "Spicy Cheese Ramyeon", "drink": "Drink Beng-Beng Cream Caramel"},
    {"tray": "Ramyeon Tray Thai Tea", "food": "Spicy Cheese Ramyeon", "drink": "Thai Tea"},
    {"tray": "Ramyeon Tray Green Thai Tea", "food": "Spicy Cheese Ramyeon", "drink": "Green Thai Tea"},
    {"tray": "Ramyeon Tray Taro", "food": "Spicy Cheese Ramyeon", "drink": "Taro"},
    {"tray": "Ramyeon Tray Choco Ovaltine", "food": "Spicy Cheese Ramyeon", "drink": "Choco Ovaltine"},
    {"tray": "Ramyeon Tray Choco Hazelnut", "food": "Spicy Cheese Ramyeon", "drink": "Choco Hazelnut"},
    {"tray": "Ramyeon Tray Choco Lava", "food": "Spicy Cheese Ramyeon", "drink": "Choco Lava"},
    {"tray": "Ramyeon Tray Choco Avocado", "food": "Spicy Cheese Ramyeon", "drink": "Choco Avocado"},
    {"tray": "Ramyeon Tray Boba Brown Sugar Fresh Milk", "food": "Spicy Cheese Ramyeon", "drink": "Boba Brown Sugar Fresh Milk"},
    {"tray": "Ramyeon Tray Boba Brown Sugar Milk Tea", "food": "Spicy Cheese Ramyeon", "drink": "Boba Brown Sugar Milk Tea"},
    {"tray": "Ramyeon Tray Jasmine Tea", "food": "Spicy Cheese Ramyeon", "drink": "Jasmine Tea"},
    {"tray": "Ramyeon Tray Fresh Lemon Tea", "food": "Spicy Cheese Ramyeon", "drink": "Fresh Lemon Tea"},
    {"tray": "Ramyeon Tray Lychee Tea", "food": "Spicy Cheese Ramyeon", "drink": "Lychee Tea"},
    {"tray": "Ramyeon Tray Mango Tea", "food": "Spicy Cheese Ramyeon", "drink": "Mango Tea"},
    {"tray": "Ramyeon Tray Strawberry Tea", "food": "Spicy Cheese Ramyeon", "drink": "Strawberry Tea"},
    {"tray": "Ramyeon Tray Cookies & Cream", "food": "Spicy Cheese Ramyeon", "drink": "Cookies & Cream"},
    {"tray": "Ramyeon Tray Cotton Candy", "food": "Spicy Cheese Ramyeon", "drink": "Cotton Candy"},
    {"tray": "Ramyeon Tray Mango Yakult", "food": "Spicy Cheese Ramyeon", "drink": "Ice Mango mix Yakult"},

    {"tray": "Snack Tray Choco Cheese Crunchy", "food": "Otteoke Cheese", "drink": "Choco Cheese Crunchy"},
    {"tray": "Snack Tray Drink Beng Beng", "food": "Otteoke Cheese", "drink": "Drink Beng-Beng Cream Caramel"},
    {"tray": "Snack Tray Thai Tea", "food": "Otteoke Cheese", "drink": "Thai Tea"},
    {"tray": "Snack Tray Green Thai Tea", "food": "Otteoke Cheese", "drink": "Green Thai Tea"},
    {"tray": "Snack Tray Taro", "food": "Otteoke Cheese", "drink": "Taro"},
    {"tray": "Snack Tray Choco Ovaltine", "food": "Otteoke Cheese", "drink": "Choco Ovaltine"},
    {"tray": "Snack Tray Choco Hazelnut", "food": "Otteoke Cheese", "drink": "Choco Hazelnut"},
    {"tray": "Snack Tray Choco Lava", "food": "Otteoke Cheese", "drink": "Choco Lava"},
    {"tray": "Snack Tray Choco Avocado", "food": "Otteoke Cheese", "drink": "Choco Avocado"},
    {"tray": "Snack Tray Boba Brown Sugar Fresh Milk", "food": "Otteoke Cheese", "drink": "Boba Brown Sugar Fresh Milk"},
    {"tray": "Snack Tray Boba Brown Sugar Milk Tea", "food": "Otteoke Cheese", "drink": "Boba Brown Sugar Milk Tea"},
    {"tray": "Snack Tray Jasmine Tea", "food": "Otteoke Cheese", "drink": "Jasmine Tea"},
    {"tray": "Snack Tray Fresh Lemon Tea", "food": "Otteoke Cheese", "drink": "Fresh Lemon Tea"},
    {"tray": "Snack Tray Lychee Tea", "food": "Otteoke Cheese", "drink": "Lychee Tea"},
    {"tray": "Snack Tray Mango Tea", "food": "Otteoke Cheese", "drink": "Mango Tea"},
    {"tray": "Snack Tray Strawberry Tea", "food": "Otteoke Cheese", "drink": "Strawberry Tea"},
    {"tray": "Snack Tray Cookies & Cream", "food": "Otteoke Cheese", "drink": "Cookies & Cream"},
    {"tray": "Snack Tray Cotton Candy", "food": "Otteoke Cheese", "drink": "Cotton Candy"},
    {"tray": "Snack Tray Mango Yakult", "food": "Otteoke Cheese", "drink": "Ice Mango mix Yakult"},
]

def sim_numeric(a, b, max_range=2):
    if a is None or pd.isna(a) or pd.isna(b):
        return None
    return 1 - abs(a - b) / max_range

def sim_categorical(a, b):
    if a is None or pd.isna(a) or pd.isna(b):
        return None
    return 1 if a == b else 0

WEIGHT = {
    "Type": 9,
    "Subtype": 9,
    "Serving Type": 7,
    "Primary": 9,
    "Secondary": 7,
    "Sweetness": 5,
    "Creaminess": 5,
    "Spiciness": 5,
    "Crispiness": 5,
    "Cheesiness": 5,
    "Seafood": 7,
}

BIAS_STRENGTH = 0.05

def score(row, user):
    total_score = 0
    total_weight = 0

    for attr, w in WEIGHT.items():
        u = user.get(attr)
        r = row.get(attr)

        sim = sim_categorical(u, r) if attr in categorical_cols else sim_numeric(u, r)

        if sim is not None:
            total_score += sim * w
            total_weight += w

    base = total_score / total_weight if total_weight else 0

    rec = 1 if row.get("Recommended") == 1 else 0
    bias = rec * BIAS_STRENGTH

    return (base + bias) / (1 + BIAS_STRENGTH)

print("\nREKOMENDASI")

top_results = {}
all_result_dfs = {}

for idx, user in enumerate(all_users, 1):

    df["Score"] = df.apply(lambda r: score(r, user), axis=1)

    type_name = decoders["Type"].get(user["Type"], "Unknown")

    print(f"\n=== REKOMENDASI {type_name.upper()} ===")

    top3 = df.sort_values("Score", ascending=False).head(3)

    all_result_dfs[type_name] = df.sort_values("Score", ascending=False)

    for _, r in top3.iterrows():
        print(f"{r['Menu']} -> {r['Score']:.3f}")\

    top_results[type_name] = top3["Menu"].tolist()


if "Drink" in top_results and "Food" in top_results:
    top_foods = top_results["Food"]
    top_drinks = top_results["Drink"]

    matched_trays = []
    food_scores = {}
    drink_scores = {}

    food_df = all_result_dfs["Food"]
    for _, r in food_df.iterrows():
        food_scores[r["Menu"]] = r["Score"]

    drink_df = all_result_dfs["Drink"]
    for _, r in drink_df.iterrows():
        drink_scores[r["Menu"]] = r["Score"]

    for tray in food_trays:

        tray_food = tray["food"]
        tray_drink = tray["drink"]

        if tray_food in top_foods and tray_drink in top_drinks:
            food_score = food_scores[tray_food]
            drink_score = drink_scores[tray_drink]
            tray_score = (food_score + drink_score) / 2

            matched_trays.append({
                "tray": tray["tray"],
                "score": tray_score
            })

    matched_trays = sorted(
        matched_trays,
        key=lambda x: x["score"],
        reverse=True
    )

    matched_trays = matched_trays[:3]

    if matched_trays:
        print("\n=== REKOMENDASI FOOD TRAY ===")
        for tray in matched_trays:
            print(f"- {tray['tray']} -> {tray['score']:.3f}")
    else:
        print("\nTidak ada food tray yang cocok.")