import streamlit as st
import random
import json
import re
import questionnaire as q
import menu_browser as mb
from nlp import correct_typo, normalize, detect_intent, NAV_NEXT, NAV_PREV
import main
from main import get_available_sizes, get_price

st.set_page_config(page_title="HAUS Chatbot")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght=400;500;600;700;800&display=swap');
html, body, [class*="css"]{ font-family:'Poppins',sans-serif; }
.stApp{ background:#efe2d3; }
#MainMenu, footer, header{ visibility:hidden; }
.chat-header{
    background:linear-gradient(135deg, #d24d9c, #c45cad);
    border-radius:30px; padding:30px; margin-bottom:25px;
    color:white; text-align:center; box-shadow:0 8px 25px rgba(0,0,0,0.12);
}
.chat-title{ font-size:42px; font-weight:800; }
.chat-subtitle{ font-size:18px; opacity:0.95; }
[data-testid="stChatInput"]{ background: transparent !important; border: none !important; }
[data-testid="stChatInput"] > div{background: #ffffff !important; border: 3px solid #d24d9c !important;border-radius: 28px !important; box-shadow: 0 4px 15px rgba(210,77,156,.15) !important;}
[data-testid="stChatInput"] textarea{ background: #ffffff !important; color: #5f4b5c !important; font-size: 16px !important; }
[data-testid="stChatInput"] button{ background: #d24d9c !important; border-radius: 50% !important; }
[data-testid="stBottomBlockContainer"] button svg{ background: #efe2d3 !important; color-scheme: light; }
[data-testid="stBottom"] {
    background: rgba(210, 77, 156, 0.5) !important;
    padding-top: 15px !important;
    padding-bottom: 15px !important;
}
[data-testid="stBottomBlockContainer"] {background: rgba(210, 77, 156, 0.8) !important;color-scheme: light !important;}
#root > div:nth-child(1) > div.withScreencast > div > div > div > section > div.stBottom.st-emotion-cache-1p2n2i4.eqt0gmo2 > div {
    background: transparent !important;
    color-scheme: light !important;
    padding-top: 15px !important;
    padding-bottom: 15px !important;
}
[data-testid="stChatInput"] button div, [data-testid="stChatInput"] button span, [data-testid="stBottomBlockContainer"] button svg {background: transparent !important;color-scheme: light;}
[data-testid="stChatInput"] button svg {fill: white !important;background: transparent !important;}
[data-testid="stChatInput"] textarea{background: #ffffff !important;color: #5f4b5c !important;font-size: 16px !important;caret-color: #d24d9c !important;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="chat-header">
    <div class="chat-title">🧋 HAUS Chatbot</div>
    <div class="chat-subtitle">Cari menu, dapatkan rekomendasi, dan pesan langsung 😄</div>
</div>
""", unsafe_allow_html=True)


def render_message(role, text):
    if role == "user":
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-end; margin:12px 0;">
            <div style="background:#d24d9c; color:white; padding:12px 18px; border-radius:20px 20px 5px 20px; max-width:70%; font-weight:500;">
                {text}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display:flex; justify-content:flex-start; margin:12px 0;">
            <div style="background:#9B77E9; color:white; padding:12px 18px; border-radius:20px 20px 20px 5px; max-width:70%; font-weight:500;">
                {text}
            </div>
        </div>
        """, unsafe_allow_html=True)


def clear_pending():
    st.session_state.pending_order = None
    st.session_state.pending_step = None


def commit_order(item, qty, size=None):
    if "Tray" in item:
        price = int(item["Price"])
        for _ in range(qty):
            entry = dict(item)
            entry["size"] = None
            entry["price"] = price
            st.session_state.cart.append(entry)
        subtotal = qty * price
        st.session_state.last_order = [{"item": item, "qty": qty}]
        return f"Berhasil ditambahkan 😄\n\n• {item['Tray']} x{qty} - Rp{subtotal}.000"

    available_sizes = get_available_sizes(item)

    if size and size not in available_sizes:
        return None

    price = get_price(item, size)

    for _ in range(qty):
        entry = dict(item)
        entry["size"] = size
        entry["price"] = price
        st.session_state.cart.append(entry)

    size_label = f" ({size})" if size else ""
    subtotal = price * qty
    st.session_state.last_order = [{"item": item, "qty": qty, "size": size}]

    return (
        f"Berhasil ditambahkan 😄\n\n"
        f"• {item['Menu']}{size_label} x{qty} - Rp{subtotal}.000"
    )


if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant",
                                  "content": "Selamat datang di HAUS! 😄\n\nSilahkan mau pesan langsung atau mau kami rekomendasikan?"}]
if "cart" not in st.session_state:
    st.session_state.cart = []
if "ordering" not in st.session_state:
    st.session_state.ordering = False
if "last_order" not in st.session_state:
    st.session_state.last_order = []
if "browse_category" not in st.session_state:
    st.session_state.browse_category = None
if "browse_page" not in st.session_state:
    st.session_state.browse_page = 0
if "browse_page_items" not in st.session_state:
    st.session_state.browse_page_items = []
if "pending_order" not in st.session_state:
    st.session_state.pending_order = None
if "pending_step" not in st.session_state:
    st.session_state.pending_step = None
if "recommending_pending" not in st.session_state:
    st.session_state.recommending_pending = False

for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"])

prompt = st.chat_input("Tulis pesan...")

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})

    lower = correct_typo(prompt.lower())
    intent = detect_intent(lower)
    menus_found = main.find_menu(lower)

    if st.session_state.pending_order and st.session_state.pending_step:
        is_queue = isinstance(st.session_state.pending_order, list)
        pending = st.session_state.pending_order[0] if is_queue else st.session_state.pending_order
        step = st.session_state.pending_step

        if step == "qty":
            qty = main.qty_from_text(lower)
            if not qty:
                response = "Berapa jumlahnya? (contoh: 1, 2, 3)"
            else:
                pending["qty"] = qty
                item = pending["item"]
                if main.is_drink(item):
                    sizes = main.get_available_sizes(item)
                    if len(sizes) == 1:
                        response = commit_order(item, qty, sizes[0])
                        if is_queue:
                            st.session_state.pending_order.pop(0)
                            if not st.session_state.pending_order: clear_pending()
                        else:
                            clear_pending()
                    else:
                        st.session_state.pending_step = "size"
                        response = main.ask_size_question(item)
                else:
                    response = commit_order(item, qty, None)
                    if is_queue:
                        st.session_state.pending_order.pop(0)
                        if not st.session_state.pending_order: clear_pending()
                    else:
                        clear_pending()

        elif step == "size":
            item = pending["item"]
            sizes = main.get_available_sizes(item)
            text_for_mapping = lower
            word_to_num = {
                "satu": "1", "dua": "2", "tiga": "3", "empat": "4", "lima": "5", "enam": "6", "tujuh": "7", "delapan": "8", "sembilan":"9", "sepuluh":"10",
                "one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six":"6", "seven":"7", "eight":"8", "nine":"9", "ten":"10"
            }

            for w, n in word_to_num.items():
                text_for_mapping = re.sub(rf"\b{w}\b", n, text_for_mapping)
            parts = re.findall(r"(\d+)\s*([a-zA-Z]+)", text_for_mapping)
            success = False
            resp_texts = []

            if parts:
                for qty_str, size_str in parts:
                    qty_val = int(qty_str)
                    size_val = main.size_from_text(size_str)
                    if size_val and size_val in sizes:
                        commit_text = commit_order(item, qty_val, size_val)
                        if commit_text:
                            resp_texts.append(commit_text.replace("Berhasil ditambahkan 😄\n\n", ""))
                            success = True

            if not success:
                size = main.size_from_text(lower)
                if not size or size not in sizes:
                    opts = " / ".join([f"{main.SIZE_LABELS[s]} ({s})" for s in sizes])
                    response = f"Ukuran tidak tersedia. Pilih: {opts}"
                else:
                    commit_text = commit_order(item, pending["qty"], size)
                    resp_texts.append(commit_text.replace("Berhasil ditambahkan 😄\n\n", ""))
                    success = True

            if success:
                if is_queue:
                    st.session_state.pending_order.pop(0)
                    if st.session_state.pending_order:
                        next_item = st.session_state.pending_order[0]["item"]
                        response = "Berhasil ditambahkan 😄\n\n" + "\n".join(
                            resp_texts) + "\n\n" + main.ask_size_question(next_item)
                    else:
                        response = "Berhasil ditambahkan 😄\n\n" + "\n".join(resp_texts)
                        clear_pending()
                else:
                    response = "Berhasil ditambahkan 😄\n\n" + "\n".join(resp_texts)
                    clear_pending()

    elif st.session_state.recommending_pending and any(
            x in lower for x in ["minuman", "makanan", "keduanya", "both", "dua", "kedua"]):
        st.session_state.ordering = False
        st.session_state.recommending_pending = False
        response = q.recommendation_chat(lower)

    elif q.chat_state["recommending"]:
        response = q.recommendation_chat(lower)

    else:
        blocked_auto_order_words = ["lihat", "daftar", "show", "cart", "keranjang", "pesanan", "order", "bayar",
                                    "payment", "harga", "berapa"]
        contains_blocked = any(word in lower for word in blocked_auto_order_words)

        if intent == "unknown" and menus_found and st.session_state.ordering and not contains_blocked:
            intent = "order"

        if intent == "price":
            if menus_found:
                response = "\n\n".join(main.show_price(d) for d in menus_found)
            else:
                response = "Menu yang mau dicek harganya apa? 😄"

        elif intent == "show_cart":
            response = main.show_cart(st.session_state.cart)

        elif intent == "remove":
            if not menus_found and st.session_state.last_order:
                menus_found = st.session_state.last_order

            if not menus_found:
                response = "Menu yang mau dibatalkan apa? 😄"
            else:
                removed_text = []
                for data in menus_found:
                    item = data["item"]
                    qty = data.get("qty", 1)
                    item_name = item.get("Menu") or item.get("Tray")
                    current_qty = main.count_cart_item(st.session_state.cart, item_name)
                    qty = min(qty, current_qty) or 1
                    remaining_cart, removed = main.remove_from_cart(st.session_state.cart, item_name, qty)
                    st.session_state.cart = remaining_cart
                    if removed > 0:
                        removed_text.append(f"• {item_name} x{removed}")
                response = "Berhasil dibatalkan 😄\n\n" + "\n".join(
                    removed_text) if removed_text else "Menu tidak ditemukan 😄"

        elif intent == "cancel":
            st.session_state.cart = []
            st.session_state.ordering = False
            clear_pending()
            q.reset_chat()
            response = "Oke semua pesanan dibatalin 😄"

        elif intent == "pay":
            if not st.session_state.cart:
                response = "Belum ada pesanan 😄"
            else:
                payment_method = None
                if "cash" in lower:
                    payment_method = "Cash"
                elif "qris" in lower:
                    payment_method = "QRIS"
                elif "transfer" in lower:
                    payment_method = "Transfer"

                if payment_method is None:
                    response = main.show_cart(
                        st.session_state.cart) + "\n\nMau bayar pakai apa?\n\n- Cash\n- QRIS\n- Transfer"
                else:
                    response = f"Pembayaran berhasil 😄\n\nMetode pembayaran: {payment_method}\n\n" + main.show_cart(
                        st.session_state.cart) + "\n\nTerima kasih sudah pesan di HAUS 💖"
                    st.session_state.cart = []
                    st.session_state.ordering = False
                    st.session_state.last_order = []

        elif intent == "payment_confirm":
            if not st.session_state.cart:
                response = "Belum ada pesanan 😄"
            else:
                payment_method = "Cash"
                if "qris" in lower:
                    payment_method = "QRIS"
                elif "transfer" in lower:
                    payment_method = "Transfer"
                response = f"Pembayaran berhasil 😄\n\nMetode pembayaran: {payment_method}\n\n" + main.show_cart(
                    st.session_state.cart) + "\n\nTerima kasih sudah pesan di HAUS 💖"
                st.session_state.cart = []
                st.session_state.ordering = False
                st.session_state.last_order = []

        elif intent == "order":
            st.session_state.ordering = True
            num_match = re.search(r"\b(\d+)\b", lower)
            if num_match and st.session_state.browse_page_items and not menus_found:
                idx = int(num_match.group(1)) - 1
                items = st.session_state.browse_page_items
                if 0 <= idx < len(items):
                    menus_found = [{"item": items[idx], "qty": 1}]
                else:
                    response = "Nomor tidak valid 😄"
                    menus_found = []

            if menus_found:
                if len(menus_found) == 1:
                    data = menus_found[0]
                    item = data["item"]
                    qty = data["qty"]

                    detected_size = main.size_from_text(lower)

                    if main.is_drink(item):
                        sizes = main.get_available_sizes(item)

                        if detected_size and detected_size in sizes:
                            response = commit_order(item, qty, detected_size)
                        elif len(sizes) > 1:
                            st.session_state.pending_order = [{
                                "item": item,
                                "qty": qty
                            }]
                            st.session_state.pending_step = "size"
                            response = main.ask_size_question(item)
                        else:
                            response = commit_order(item, qty, sizes[0])
                    else:
                        response = commit_order(item, qty, None)
                else:
                    added_text = []
                    pending_size_queue = []

                    for data in menus_found:
                        item = data["item"]
                        qty = data["qty"]
                        item_name = item.get("Menu") or item.get("Tray")

                        sizes = main.get_available_sizes(item) if main.is_drink(item) else []

                        if len(sizes) > 1:
                            pending_size_queue.append({
                                "item": item,
                                "qty": qty
                            })
                            continue

                        size = sizes[0] if sizes else None

                        if main.is_drink(item) and not sizes:
                            added_text.append(f"• {item_name} — ukuran tidak tersedia, dilewati")
                            continue

                        price = main.get_price(item, size)
                        for _ in range(qty):
                            entry = dict(item)
                            entry["size"] = size
                            entry["price"] = price
                            st.session_state.cart.append(entry)

                        subtotal = price * qty
                        size_label = f" ({size})" if size else ""
                        added_text.append(f"• {item_name}{size_label} x{qty} - Rp{subtotal}.000")

                    if pending_size_queue:
                        st.session_state.pending_order = pending_size_queue
                        st.session_state.pending_step = "size"

                        prefix = "Berhasil ditambahkan 😄\n\n" + "\n".join(added_text) + "\n\n" if added_text else ""
                        response = prefix + main.ask_size_question(pending_size_queue[0]["item"])
                    else:
                        response = "Berhasil ditambahkan 😄\n\n" + "\n".join(added_text)

            elif response is None:
                recs = main.get_recommended_menus()

                lines = ["Mau pesan apa? 😄", "", "Beberapa rekomendasi menu dari outlet kami:"]

                icon_map = {
                    "Drink": "🥤",
                    "Food": "🍜",
                    "Main Dish": "🍜",
                    "Side Dish": "🥟",
                    "Dessert": "🍰",
                    "Bread": "🥖"
                }

                for category, menus in recs.items():
                    icon = icon_map.get(category, "✨")
                    lines.append(f"\n{icon} {category}")
                    lines.extend([f"• {menu}" for menu in menus])

                response = "\n".join(lines)

        elif intent == "recommendation":
            st.session_state.ordering = False
            q.reset_chat()

            with open("nlp.json", "r", encoding="utf-8") as f:
                nlp_data = json.load(f)
            food_subtypes = nlp_data.get("food_subtypes", {})
            combo_triggers = nlp_data.get("combo_triggers", [])
            drink_triggers = nlp_data.get("drink_triggers", [])
            food_triggers = nlp_data.get("food_triggers", [])

            detected_subtype = None
            for subtype, keywords in food_subtypes.items():
                if any(word in lower for word in keywords):
                    detected_subtype = subtype
                    break
            if detected_subtype:
                st.session_state.recommending_pending = False
                response = q.recommendation_chat(detected_subtype)
            elif any(x in lower for x in combo_triggers) or (
                    any(x in lower for x in drink_triggers) and any(x in lower for x in food_triggers)):
                st.session_state.recommending_pending = False
                response = q.recommendation_chat("keduanya")
            elif any(x in lower for x in drink_triggers):
                st.session_state.recommending_pending = False
                response = q.recommendation_chat("minuman")
            elif any(x in lower for x in food_triggers):
                st.session_state.recommending_pending = False
                response = q.recommendation_chat("makanan")
            else:
                st.session_state.recommending_pending = True
                response = "Siap 😄\n\nKamu mau:\n\n- Minuman\n- Makanan\n- Keduanya"

        elif st.session_state.recommending_pending and any(
                x in lower for x in ["minuman", "makanan", "keduanya", "both", "dua", "kedua"]):
            st.session_state.ordering = False
            st.session_state.recommending_pending = False
            response = q.recommendation_chat(lower)

        elif intent == "menu":
            category = mb.resolve_category(lower)
            if category:
                st.session_state.browse_category = category
                st.session_state.browse_page = 0
                text, page_items, _, _, _ = mb.get_menu_page(category, 0)
                st.session_state.browse_page_items = page_items
                response = text
            else:
                response = mb.get_category_list()

        elif any(w in lower for w in NAV_NEXT) and st.session_state.browse_category:
            st.session_state.browse_page += 1
            text, page_items, _, has_next, _ = mb.get_menu_page(st.session_state.browse_category,
                                                                st.session_state.browse_page)
            if not page_items:
                st.session_state.browse_page -= 1
                response = "Sudah halaman terakhir 😄"
            else:
                st.session_state.browse_page_items = page_items
                response = text

        elif any(w in lower for w in NAV_PREV) and st.session_state.browse_category:
            if st.session_state.browse_page > 0:
                st.session_state.browse_page -= 1
            text, page_items, _, _, _ = mb.get_menu_page(st.session_state.browse_category, st.session_state.browse_page)
            st.session_state.browse_page_items = page_items
            response = text

        elif intent == "greeting":
            greetings = [
                "Halo juga 😄\n\nMau cari minuman atau makanan?",
                "Haiii 😄\n\nKalau bingung pilih menu aku bisa bantu rekomendasi 😄",
                "Halo 😄\n\nMau pesan langsung atau mau direkomendasikan menu?"
            ]
            response = random.choice(greetings)

        elif "saran" in lower or "enaknya" in lower:
            drink = main.random_recommendation("Drink")
            food = main.random_recommendation("Food")
            response = f"Rekomendasi buat kamu 😄\n\n🍹 {drink}\n\n🍴 {food}"

        else:
            response = "Kalau bingung pilih menu, aku bisa bantu rekomendasi 😄"

    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()