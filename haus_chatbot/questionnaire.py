"""
questionnaire.py
----------------
Recommendation questionnaire flow.
All NLP (normalize, match_choice, detect_*) delegated to nlp.py.
"""
import recommendation as rec
from nlp import (
    normalize,
    match_choice,
    detect_scale,
    detect_sweetness,
    detect_spicy,
    detect_yes_no,
    detect_food_subtype,
    COMBO_TRIGGERS,
    DRINK_TRIGGERS,
    FOOD_TRIGGERS,
)

chat_state = {
    "recommending":  False,
    "type":          None,
    "subtype":       None,
    "questions":     [],
    "current_index": 0,
    "answers":       {},
    "drink_answers": {},
    "food_answers":  {},
    "combo_mode":    False,
}
DRINK_FLOW     = ["Primary", "Secondary", "Sweetness", "Creaminess"]
MAIN_DISH_FLOW = ["Serving Type", "Spiciness", "Cheesiness"]
SIDE_DISH_FLOW = ["Serving Type", "Spiciness", "Cheesiness", "Seafood", "Crispiness"]
BREAD_FLOW     = ["Serving Type", "Primary", "Secondary", "Crispiness"]
DESSERT_FLOW   = ["Primary"]
QUESTION_TEXT = {
    "Primary":      "Kamu suka rasa apa?",
    "Secondary":    "Kalau dipadukan rasa lain kamu suka apa?",
    "Sweetness":    "Tingkat kemanisan:\n\n- manis\n- sangat manis",
    "Creaminess":   "Creamy level:\n\n- tidak creamy\n- creamy normal\n- creamy banget",
    "Serving Type": "Mau yang seperti apa?",
    "Spiciness":    "Level pedas:\n\n- tidak pedas\n- pedas normal\n- sangat pedas",
    "Cheesiness":   "Level keju:\n\n- tidak cheesy\n- sedikit cheesy\n- cheesy banget",
    "Seafood":      "Mau yang ada seafood:\n\n- iya\n- tidak",
    "Crispiness":   "Mau yang crispy:\n\n- iya\n- tidak",
}
FLOW_MAP = {
    "Main Dish": MAIN_DISH_FLOW,
    "Side Dish": SIDE_DISH_FLOW,
    "Bread":     BREAD_FLOW,
    "Dessert":   DESSERT_FLOW,
}

def _get_choices(attr, filters=None):
    return rec.get_choices(attr, filters or {})

def _ask_current_question():
    q = chat_state["questions"][chat_state["current_index"]]
    text = QUESTION_TEXT[q]
    if q in ["Primary", "Secondary", "Serving Type"]:
        choices = _get_choices(q, {
            "Type":    chat_state["type"],
            "Subtype": chat_state["subtype"],
        })
        if choices:
            text += "\n\nPilihan:\n\n" + "\n".join([f"- {c}" for c in choices])
    return text.strip()

def _save_answer(question, user):
    filters = {"Type": chat_state["type"]}
    if chat_state["subtype"]:
        filters["Subtype"] = chat_state["subtype"]

    if question in ["Primary", "Secondary", "Serving Type"]:
        choices = _get_choices(question, filters)
        val = match_choice(user, choices)
    elif question == "Sweetness":
        val = detect_sweetness(user)
    elif question == "Spiciness":
        val = detect_spicy(user)
    elif question in ["Creaminess", "Cheesiness"]:
        val = detect_scale(user)
    elif question in ["Seafood", "Crispiness"]:
        val = detect_yes_no(user)
    else:
        val = None

    if val is None:
        return False
    chat_state["answers"][question] = val
    return True

def _format_result(title, result):
    text = f"Aku rekomendasiin {title} ini buat kamu 😄\n\n"
    for i, r in enumerate(result, 1):
        text += f"{i}. {r['Menu']} ({r['Score']:.3f})\n"
    return text

def reset_chat():
    chat_state.update({
        "recommending":  False,
        "type":          None,
        "subtype":       None,
        "questions":     [],
        "current_index": 0,
        "answers":       {},
        "drink_answers": {},
        "food_answers":  {},
        "combo_mode":    False,
    })

def recommendation_chat(user):
    cleaned = normalize(user)

    if not chat_state["recommending"]:
        if any(t in cleaned for t in COMBO_TRIGGERS):
            chat_state.update({"recommending": True, "type": "Drink", "combo_mode": True, "questions": DRINK_FLOW, "current_index": 0,})
            return "Kita mulai dari minuman dulu 😄\n\n" + _ask_current_question()

        if any(t in cleaned for t in DRINK_TRIGGERS):
            chat_state.update({"recommending": True, "type": "Drink", "questions": DRINK_FLOW, "current_index": 0,})
            return _ask_current_question()

        if any(t in cleaned for t in FOOD_TRIGGERS):
            chat_state.update({"recommending": True, "type": "Food"})
            return "Kamu pengen jenis makanan apa?\n\n- makanan berat\n- snack\n- roti\n- dessert"

        return "Siap 😄 Kamu mau:\n\n- Minuman\n- Makanan\n- Keduanya"

    if chat_state["type"] == "Food" and chat_state["subtype"] is None:
        subtype = detect_food_subtype(cleaned)
        if not subtype:
            return "Kategori tidak dikenali. Silahkan pilih:\n\n- makanan berat\n- snack\n- roti\n- dessert"

        chat_state["subtype"]       = subtype
        chat_state["questions"]     = FLOW_MAP[subtype]
        chat_state["current_index"] = 0
        return _ask_current_question()

    q = chat_state["questions"][chat_state["current_index"]]
    if not _save_answer(q, user):
        return _ask_current_question()

    chat_state["current_index"] += 1
    if chat_state["current_index"] < len(chat_state["questions"]):
        return _ask_current_question()

    if chat_state["type"] == "Drink" and chat_state["combo_mode"]:
        chat_state["drink_answers"] = {"Type": "Drink", **chat_state["answers"]}
        chat_state.update({"type": "Food", "subtype": None, "questions": [], "current_index": 0, "answers": {},})
        return "Sekarang lanjut ke makanan 😋\n\nKamu mau jenis apa?\n\n- makanan berat\n- snack\n- roti\n- dessert"

    data = {"Type": chat_state["type"]}
    if chat_state["subtype"]:
        data["Subtype"] = chat_state["subtype"]
    data.update(chat_state["answers"])

    result = rec.get_recommendation(data)
    title  = "minuman" if chat_state["type"] == "Drink" else "makanan"
    text   = _format_result(title, result)

    if chat_state["combo_mode"]:
        drink_result = rec.get_recommendation(chat_state["drink_answers"])
        text = _format_result("minuman", drink_result) + "\n" + _format_result("makanan", result)

        tray = []
        if hasattr(rec, "get_food_tray_recommendation"):
            tray = rec.get_food_tray_recommendation(drink_result, result)
        if tray:
            text += "\nCombo yang cocok buat kamu 👀:\n\n"
            for i, t in enumerate(tray, 1):
                text += f"{i}. {t['tray']} ({t['score']:.3f})\n"

    reset_chat()
    return text.strip()