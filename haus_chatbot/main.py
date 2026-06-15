import json
import re
import difflib
import random
import recommendation as rec
import menu_browser as mb
from nlp import normalize, correct_typo, IGNORE_WORDS

with open("tray.json", "r", encoding="utf-8") as f:
    TRAY_DATA = json.load(f)

with open("haus.json", "r", encoding="utf-8") as f:
    MENU_DATA = json.load(f)

SIZE_LABELS = {"L": "Large", "M": "Medium", "S": "Small"}


def get_available_sizes(item):
    sizes = []
    for s in ["L", "M", "S"]:
        val = item.get(s)
        if val and str(val).strip() not in ("", "None", "none"):
            sizes.append(s)
    if not sizes and item.get("Price"):
        sizes = ["L"]
    return sizes


def get_price(item, size=None):
    if size and item.get(size) and str(item[size]).strip() not in ("", "None", "none"):
        return int(item[size])
    for s in ["L", "M", "S"]:
        val = item.get(s)
        if val and str(val).strip() not in ("", "None", "none"):
            return int(val)
    if item.get("Price"):
        return int(item["Price"])
    return 0


def get_item_name(item):
    return item.get("Menu") or item.get("Tray", "Unknown")


def is_tray(item):
    return "Tray" in item


def is_drink(item):
    return str(item.get("Type", "")).lower() == "drink"


def size_from_text(text):
    t = normalize(text)
    words = t.split()

    from nlp import _CFG
    aliases = _CFG.get("size_aliases", {})

    for size_key, alias_list in aliases.items():
        for alias in alias_list:
            if alias.lower() in words:
                return size_key

    return None


def qty_from_text(text):
    m = re.search(r"\b(\d+)\b", text)
    if m:
        return int(m.group(1))
    words = {
        "satu": 1, "dua": 2, "tiga": 3, "empat": 4,"lima": 5, "enam": 6, "tujuh": 7, "delapan": 8,"sembilan": 9, "sepuluh": 10,
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six":6, "seven":7, "eight":8, "nine":9, "ten":10
    }
    for w, v in words.items():
        if re.search(rf"\b{w}\b", text.lower()):
            return v
    return None


def remove_from_cart(cart, menu_name, qty=1):
    removed = 0
    remaining = []
    for item in cart:
        name = item.get("Menu") or item.get("Tray", "")
        if name.lower() == menu_name.lower() and removed < qty:
            removed += 1
        else:
            remaining.append(item)
    return remaining, removed


def count_cart_item(cart, menu_name):
    return sum(1 for item in cart if (item.get("Menu") or item.get("Tray", "")).lower() == menu_name.lower())


def show_cart(cart):
    if not cart:
        return "Belum ada pesanan 😄"
    grouped = {}
    total = 0
    for entry in cart:
        name = entry.get("Menu") or entry.get("Tray")
        size = entry.get("size")
        price = entry.get("price", 0)
        key = f"{name}|{size}" if size else name
        if key not in grouped:
            grouped[key] = {"name": name, "size": size, "qty": 0, "price": price}
        grouped[key]["qty"] += 1
    lines = []
    for data in grouped.values():
        subtotal = data["qty"] * data["price"]
        total += subtotal
        size_label = f" ({data['size']})" if data["size"] else ""
        lines.append(f"• {data['name']}{size_label} x{data['qty']} - Rp{subtotal}.000")
    return "Pesanan kamu 😄\n\n" + "\n".join(lines) + f"\n\n💰 Total: Rp{total}.000"

def show_price(menu_data):
    item = menu_data["item"]

    if "Tray" in item:
        return f"Harga {item['Tray']} 😄\n\n💰 Rp{item['Price']}.000"
    if not is_drink(item):
        price_val = item.get("Price") or item.get("L") or item.get("M") or item.get("S")
        return f"Harga {item['Menu']} 😄\n\n💰 Rp{int(price_val)}.000"
    sizes = get_available_sizes(item)
    if len(sizes) == 1 and not any(item.get(s) for s in ["M", "S"]):
        return f"Harga {item['Menu']} 😄\n\n💰 Rp{get_price(item)}.000"

    lines = [f"Harga {item['Menu']} 😄\n"]
    for s in sizes:
        val = item.get(s) or (item.get("Price") if s == "L" else None)
        if val:
            lines.append(f"• {SIZE_LABELS[s]} ({s}): Rp{int(val)}.000")

    return "\n".join(lines)

def random_recommendation(type_name=None):
    df = rec.df.copy()
    if "Recommended" in df.columns:
        try:
            df = df[df["Recommended"] == 1]
        except:
            pass
    if type_name:
        df = df[df["Type"].str.lower() == type_name.lower()]
    if len(df) == 0:
        return None
    return df.sample(1).iloc[0]["Menu"]


def get_menu_list(type_name=None):
    df = rec.df.copy()
    if type_name:
        df = df[df["Type"].str.lower() == type_name.lower()]
    return sorted(df["Menu"].dropna().astype(str).unique())


def find_menu(text):
    text = normalize(text)
    results = []
    parts = re.split(r",| dan | & ", text)

    for part in parts:
        part = part.strip()
        detected_qty = qty_from_text(part)
        quantity = detected_qty if detected_qty else 1
        part = re.sub(r"\d+", "", part)
        number_words = ["satu", "dua", "tiga", "empat", "lima", "enam", "tujuh", "delapan", "sembilan", "sepuluh", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"]

        for w in number_words:
            part = re.sub(rf"\b{w}\b", "", part)
        part = re.sub(r"\bporsi\b", "", part)
        words = part.split()
        filtered_words = [w for w in words if w not in IGNORE_WORDS]
        part = " ".join(filtered_words).strip()

        if len(part) < 2:
            continue

        best_item = None
        best_score = 0

        ALL_ITEMS = MENU_DATA + TRAY_DATA

        for item in ALL_ITEMS:
            name = item.get("Menu") or item.get("Tray")
            menu_name = normalize(name)
            if menu_name == part:
                score = 1.0
            elif part in menu_name:
                score = 0.95
            else:
                score = difflib.SequenceMatcher(None, part, menu_name).ratio()
            if score > best_score:
                best_score = score
                best_item = item

        if best_item and best_score >= 0.75:
            results.append({"item": best_item, "qty": quantity})
    return results

def ask_size_question(item):
    sizes = get_available_sizes(item)
    opts = " / ".join([f"{SIZE_LABELS[s]} ({s}) - Rp{get_price(item, s)}.000" for s in sizes])
    return f"Pilih ukuran yang tersedia:\n\n{opts}"

def get_recommended_menus():
    df = rec.df.copy()
    if "Recommended" in df.columns:
        df = df[df["Recommended"] == 1]
    recommendations = {}
    categories = df["Type"].dropna().unique()
    for category in categories:
        cat_df = df[df["Type"] == category]
        sample_size = min(3, len(cat_df))
        recommendations[category] = (cat_df.sample(sample_size)["Menu"].tolist())
    return recommendations