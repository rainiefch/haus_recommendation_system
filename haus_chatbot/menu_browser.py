import json
import math
import pandas as pd

from nlp import detect_category

with open("tray.json", "r", encoding="utf-8") as f:
    TRAY_DATA = json.load(f)
tray_df = pd.DataFrame(TRAY_DATA)

with open("haus.json", "r", encoding="utf-8") as f:
    MENU_DATA = json.load(f)
df = pd.DataFrame(MENU_DATA)

PAGE_SIZE = 8

CATEGORY_LABELS = {
    "Drink": "🍹 Minuman",
    "Main Dish": "🍽️ Makanan Berat",
    "Side Dish": "🍟 Snack",
    "Bread": "🍞 Roti",
    "Dessert": "🍰 Dessert",
    "Tray": "🎉 Food Tray"
}

def resolve_category(text):
    return detect_category(text)

def get_category_list():
    return (
        "Mau lihat kategori apa? 😄\n\n"
        "🍹 Minuman\n"
        "🍽️ Makanan Berat\n"
        "🍟 Snack\n"
        "🍞 Roti\n"
        "🍰 Dessert\n"
        "🎉 Food Tray"
    )

def get_category_items(category):
    if category == "Tray":
        return tray_df.reset_index(drop=True)
    if category == "Drink":
        return (df[df["Type"].str.lower() == "drink"].reset_index(drop=True))
    return (df[df["Subtype"] == category].reset_index(drop=True))

def format_menu_price(menu):
    available = []
    for size in ["S", "M", "L"]:
        value = menu.get(size)
        if (value and str(value).strip().lower() != "none"):
            available.append((size, int(value)))
    if not available:
        return "-"
    if len(available) == 1: #if 1 harga langsung aja
        return f"Rp{available[0][1]}.000"
    return " | ".join(f"{s}: Rp{p}.000" for s, p in available)

def get_menu_page(category, page=0):
    items = get_category_items(category)
    total_items = len(items)
    if total_items == 0:
        return (
            "Tidak ada menu untuk kategori tersebut 😄",
            [],
            1,
            False,
            False
        )
    total_pages = math.ceil(total_items / PAGE_SIZE)
    page = max(0,min(page, total_pages - 1))
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    page_df = items.iloc[start:end]
    has_prev = page > 0
    has_next = end < total_items
    label = CATEGORY_LABELS.get(category,category)
    lines = [f"**{label} — Halaman {page + 1}/{total_pages}**",""]

    page_items = []
    for idx, (_, row) in enumerate(page_df.iterrows(),start=1):
        menu = dict(row)
        page_items.append(menu)
        if category == "Tray":
            lines.append(f"{idx}. {menu['Tray']} — Rp{menu['Price']}.000")
        else:
            price_text = format_menu_price(menu)
            lines.append(f"{idx}. {menu['Menu']} — {price_text}")

    lines.append("")
    lines.append(
        "Ketik:\n"
        "- pesan 1\n"
        "- pesan 2\n"
        "- dst"
    )
    nav = []
    if has_prev:
        nav.append("sebelumnya")
    if has_next:
        nav.append("selanjutnya")
    if nav:
        lines.append("")
        lines.append("Navigasi: "+ " | ".join(nav))
    return ("\n".join(lines),page_items,total_pages,has_next,has_prev)