import pandas as pd
import json

with open("haus.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

_NUMERIC_FIELDS = ["Sweetness", "Creaminess", "Spiciness", "Crispiness", "Seafood", "Cheesiness", "Recommended",]

for col in _NUMERIC_FIELDS:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

_CATEGORICAL = ["Type", "Subtype", "Serving Type", "Primary", "Secondary"]

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

with open("tray.json", "r", encoding="utf-8") as _ft:
    _TRAY_RAW = json.load(_ft)

FOOD_TRAYS = [{"tray": entry["Tray"], "food": entry["Food"], "drink": entry["Drink"]} for entry in _TRAY_RAW]

def _is_none(val) -> bool:
    if val is None:
        return True
    try:
        if pd.isna(val):
            return True
    except (TypeError, ValueError):
        pass
    return str(val).strip().lower() == "none"

def sim_numeric(a, b, max_range: float = 2) -> float | None:
    if _is_none(a) or _is_none(b):
        return None
    try:
        return 1.0 - abs(float(a) - float(b)) / max_range
    except (TypeError, ValueError):
        return None

def sim_categorical(a, b) -> float | None:
    if _is_none(a) or _is_none(b):
        return None
    return 1.0 if str(a) == str(b) else 0.0

def _score_item(row: pd.Series, user: dict) -> float:
    total_score  = 0.0
    total_weight = 0.0

    for attr, weight in WEIGHT.items():
        user_val = user.get(attr)
        if _is_none(user_val):
            continue

        row_val = row.get(attr)

        if attr in _CATEGORICAL:
            sim = sim_categorical(user_val, row_val)
        else:
            sim = sim_numeric(user_val, row_val)

        if sim is not None:
            total_score  += sim * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0

    base = total_score / total_weight

    bias = BIAS_STRENGTH if row.get("Recommended") == 1 else 0.0

    return (base + bias) / (1.0 + BIAS_STRENGTH)

def get_choices(attr: str, filters: dict | None = None) -> list:
    if filters is None:
        filters = {}

    temp = df.copy()

    for key in ["Type", "Subtype"]:
        val = filters.get(key)
        if not _is_none(val):
            temp = temp[temp[key] == val]

    vals = temp[attr].dropna().unique()
    vals = [v for v in vals if not _is_none(v)]

    if len(vals) == 0:
        vals = df[attr].dropna().unique()
        vals = [v for v in vals if not _is_none(v)]

    return sorted(str(v) for v in vals)


def get_recommendation(user: dict, top_n: int = 3) -> list[dict]:
    temp = df.copy()

    if not _is_none(user.get("Type")):
        temp = temp[temp["Type"] == user["Type"]]

    if not _is_none(user.get("Subtype")):
        temp = temp[temp["Subtype"] == user["Subtype"]]

    temp = temp.copy()
    temp["Score"] = temp.apply(lambda r: _score_item(r, user), axis=1)
    temp = temp.sort_values("Score", ascending=False)

    return [
        {"Menu": row["Menu"], "Score": row["Score"]}
        for _, row in temp.head(top_n).iterrows()
    ]

def get_food_tray_recommendation(drink_result: list[dict],food_result:  list[dict],) -> list[dict]:
    if not drink_result or not food_result:
        return []
    drink_scores = {r["Menu"]: r["Score"] for r in drink_result}
    food_scores  = {r["Menu"]: r["Score"] for r in food_result}

    top_drinks = set(drink_scores)
    top_foods  = set(food_scores)

    matched: list[dict] = []
    for tray in FOOD_TRAYS:
        d, f = tray["drink"], tray["food"]
        if d in top_drinks and f in top_foods:
            tray_score = (drink_scores[d] + food_scores[f]) / 2
            matched.append({"tray": tray["tray"], "score": tray_score})

    if matched:
        matched.sort(key=lambda x: x["score"], reverse=True)
        return matched[:3]

    fallback: list[dict] = []
    for d_item in drink_result[:3]:
        for f_item in food_result[:3]:
            tray_name  = f"{d_item['Menu']} + {f_item['Menu']}"
            tray_score = (d_item["Score"] + f_item["Score"]) / 2
            fallback.append({"tray": tray_name, "score": tray_score})

    fallback.sort(key=lambda x: x["score"], reverse=True)
    return fallback[:3]
