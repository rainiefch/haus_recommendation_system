import pandas as pd
import json
import streamlit as st
import os

st.set_page_config(
    page_title="HAUS Recommendation",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# @st.cache_data
def load_data():

    with open("haus.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    df = pd.DataFrame(data)

    numeric_fields = [
        "Sweetness",
        "Creaminess",
        "Spiciness",
        "Crispiness",
        "Seafood",
        "Cheesiness",
        "Recommended"
    ]

    for col in numeric_fields:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    categorical_cols = [
        "Type",
        "Subtype",
        "Serving Type",
        "Primary",
        "Secondary"
    ]

    encoders = {}
    decoders = {}

    for col in categorical_cols:

        vals = df[col].dropna()
        vals = vals[vals != "None"]

        mapping = {v: i + 1 for i, v in enumerate(vals.unique())}
        reverse = {v: k for k, v in mapping.items()}

        encoders[col] = mapping
        decoders[col] = reverse

        df[col] = df[col].map(mapping)

    return df, encoders, decoders


df, encoders, decoders = load_data()

categorical_cols = [
    "Type",
    "Subtype",
    "Serving Type",
    "Primary",
    "Secondary"
]


st.markdown("""
<style>

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"]{
    font-family:'Poppins',sans-serif;
}

.stApp{
    background:#efe2d3;
}

#MainMenu,
footer,
header{
    visibility:hidden;
}

.block-container{
    max-width:1200px;
    padding-top:1rem;
    padding-bottom:2rem;
}

.logo-title{
    font-size:42px;
    font-weight:800;
    color:black;
}

.hero-box{
    background:linear-gradient(135deg,#d24d9c,#c45cad);
    border-radius:35px;
    padding:60px 50px;
    margin-top:10px;
    margin-bottom:40px;
    color:white;
    box-shadow:0 8px 30px rgba(0,0,0,0.12);
}

.hero-title{
    font-size:64px;
    font-weight:800;
    line-height:1;
    margin-bottom:15px;
}

.hero-subtitle{
    font-size:24px;
    font-weight:500;
    opacity:0.95;
}

.question-title{
    text-align:center;
    font-size:38px;
    font-weight:800;
    color:#8f4fa3;
    margin-bottom:30px;
    margin-top:15px;
}

.option-title{
    text-align:center;
    font-size:30px;
    font-weight:700;
    color:#8f4fa3;
    margin-top:25px;
    margin-bottom:20px;
}

.section-title{
    background:linear-gradient(135deg,#d24d9c,#c45cad);
    border-radius:15px;
    padding:28px 40px;
    margin:10px auto 35px auto;
    width:100%;
    color:white;
    text-align:center;
    font-size:46px;
    font-weight:800;
    box-shadow:0 8px 30px rgba(0,0,0,0.12);
    display:flex;
    align-items:center;
    justify-content:center;
}


.result-title{
    text-align:center;
    color:#d24d9c;
    font-size:48px;
    font-weight:800;
    margin-bottom:35px;
}

.stButton > button{
    width:100% !important;
    height:190px !important;
    border:none !important;
    border-radius:24px !important;
    transition:0.25s ease;
    box-shadow:0 6px 18px rgba(0,0,0,0.10);
    margin-bottom:18px !important;
    display:flex !important;
    align-items:center !important;
    justify-content:center !important;
}

.stButton > button p{
    font-size:32px !important;
    font-weight:800 !important;
    line-height:1.1 !important;

    padding:0 !important;
    margin:0 !important;
}

.stButton > button:hover{
    transform:translateY(-4px);
    box-shadow:0 10px 24px rgba(0,0,0,0.16);
}

div.purple-btn div.stButton > button {
    background:#A57BCF !important;
    color:white !important;
}

div.blue-btn div.stButton > button {
    background:#BFE4FA !important;
    color:#8B49B4 !important;
}

div.pink-btn div.stButton > button {
    background:#D965AE !important;
    color:white !important;
}

div.yellow-btn div.stButton > button {
    background:#F3C64E !important;
    color:#8B49B4 !important;
}

div.orange-btn div.stButton > button {
    background:#EB7C42 !important;
    color:white !important;
}

.stButton > button:hover{
    transform:translateY(-4px);
    box-shadow:0 10px 24px rgba(0,0,0,0.12);
}

.stButton > button:focus{
    outline:none !important;
    box-shadow:none !important;
}

.recommend-card{
    border-radius:30px;
    padding:28px 20px;
    text-align:center;
    min-height:360px;
    display:flex;
    flex-direction:column;
    justify-content:center;
    align-items:center;
    box-shadow:0 6px 18px rgba(0,0,0,0.08);
    margin-bottom:20px;
}

.card-purple{
    background:#b89bcc;
}

.card-blue{
    background:#97C9FB;
}

.card-pink{
    background:#cf79af;
}

.card-yellow{
    background:#e6c15d;
}

.card-orange{
    background:#dd7f48;
}

.product-name{
    color:white;
    font-size:36px;
    font-weight:800;
    line-height:1.25;

    display:flex;
    align-items:center;
    justify-content:center;

    height:100%;
}

.score-text{
    color:white;
    font-size:18px;
    font-weight:500;
    margin-top:10px;
}

button[kind="secondary"]{
    background:#8f5cc8 !important;
    color:white !important;
    min-height:70px !important;
    font-size:24px !important;
    font-weight:700 !important;
}

button:focus{
    outline:none !important;
    box-shadow:none !important;
}

</style>
""", unsafe_allow_html=True)

if "step" not in st.session_state:
    st.session_state.step = "start"

if "responses" not in st.session_state:
    st.session_state.responses = []

if "user_data" not in st.session_state:
    st.session_state.user_data = {}

CARD_COLORS = [
    "card-purple",
    "card-blue",
    "card-pink",
    "card-yellow",
    "card-orange"
]

BUTTON_CLASSES = [
    "purple-btn",
    "blue-btn",
    "pink-btn",
    "yellow-btn",
    "orange-btn"
]


def get_choices(attr, filters):

    temp = df.copy()

    for key in ["Type", "Subtype"]:
        if filters.get(key) is not None:
            temp = temp[temp[key] == filters[key]]

    vals = temp[attr].dropna().unique()

    if len(vals) == 0:
        vals = df[attr].dropna().unique()

    vals = [v for v in vals if pd.notna(v)]

    return sorted(vals)


def render_buttons(attr, choices_encoded, label=None):
    st.markdown(
        f"<div class='option-title'>{label if label else attr}</div>",
        unsafe_allow_html=True
    )

    total = len(choices_encoded)

    if total <= 2:
        per_row = 2
    elif total <= 3:
        per_row = 3
    elif total <= 4:
        per_row = 4
    else:
        per_row = 5

    for row_start in range(0, total, per_row):
        row_items = choices_encoded[row_start:row_start + per_row]
        cols = st.columns(per_row)

        for i, code in enumerate(row_items):
            name = decoders[attr][code]
            btn_class = BUTTON_CLASSES[i % len(BUTTON_CLASSES)]
            with cols[i]:
                clicked = colored_button(
                    name,
                    key=f"btn_{attr}_{code}",
                    color_class=btn_class
                )
                if clicked:
                    return code

    return None


def render_numeric_buttons(label, options_dict, key_prefix):

    st.markdown(
        f"<div class='option-title'>{label}</div>",
        unsafe_allow_html=True
    )

    items = list(options_dict.items())

    total = len(items)

    if total <= 2:
        per_row = 2
    elif total <= 3:
        per_row = 3
    elif total <= 4:
        per_row = 4
    else:
        per_row = 5

    for row_start in range(0, total, per_row):

        row_items = items[row_start:row_start + per_row]

        cols = st.columns(per_row)

        for i, (text, val) in enumerate(row_items):

            btn_class = BUTTON_CLASSES[i % len(BUTTON_CLASSES)]

            with cols[i]:

                clicked = colored_button(
                    text,
                    key=f"num_{key_prefix}_{val}",
                    color_class=btn_class
                )

                if clicked:
                    return val

    return None

def colored_button(label, key, color_class, use_container_width=True):

    st.markdown(
        f"""
        <div class="{color_class}">
        """,
        unsafe_allow_html=True
    )

    clicked = st.button(
        label,
        key=key,
        use_container_width=use_container_width
    )

    st.markdown("</div>", unsafe_allow_html=True)

    return clicked

def render_product_card(name, score, idx=0):
    color = CARD_COLORS[idx % len(CARD_COLORS)]
    st.markdown(f"""
    <div class="recommend-card {color}">
        <div>
            <div class="product-name">
                {name}
            </div>
            <div class="score-text">
                Match Score: {score:.3f}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

logo_path = "images/haus.png"

col_logo, col_space = st.columns([1, 5])

with col_logo:
    if os.path.exists(logo_path):
        st.image(logo_path, width=180)

if st.session_state.step == "start":
    st.markdown("""
    <div class="hero-box">
        <div class="hero-title">
            Welcome to Haus!
        </div>
        <div class="hero-subtitle">
            Enjoy our drink and food!
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="question-title">
        What would you like to order today?
    </div>
    """, unsafe_allow_html=True)

    col_space1, col1, col2, col3, col_space2 = st.columns([1,2,2,2,1])

    with col1:
        if colored_button(
                "Drink",
                "main_drink",
                "purple-btn"
        ):
            st.session_state.flow_type = "1"
            st.session_state.step = "drink_q"
            st.rerun()

    with col2:
        if colored_button(
                "Food",
                "main_food",
                "blue-btn"
        ):
            st.session_state.flow_type = "2"
            st.session_state.step = "food_q"
            st.rerun()

    with col3:
        if colored_button(
                "Both",
                "main_both",
                "pink-btn"
        ):
            st.session_state.flow_type = "3"
            st.session_state.step = "drink_q"
            st.rerun()

elif st.session_state.step == "drink_q":

    st.markdown("""
    <div class="section-title">
        Drink Questionnaire
    </div>
    """, unsafe_allow_html=True)

    filters = {"Type": encoders["Type"]["Drink"]}

    if "drink_data" not in st.session_state:
        st.session_state.drink_data = {
            "Type": filters["Type"]
        }

    data = st.session_state.drink_data

    if "Primary" not in data:

        choice = render_buttons(
            "Primary",
            get_choices("Primary", filters),
            "Choose your main flavor"
        )

        if choice:
            data["Primary"] = choice
            st.rerun()

    elif "Secondary" not in data:

        choice = render_buttons(
            "Secondary",
            get_choices("Secondary", filters),
            "Choose your secondary flavor"
        )

        if choice:
            data["Secondary"] = choice
            st.rerun()

    elif "Sweetness" not in data:

        choice = render_numeric_buttons(
            "How sweet would you like your drink?",
            {
                "Sweet": 1,
                "Very Sweet": 2
            },
            "sweet"
        )

        if choice is not None:
            data["Sweetness"] = choice
            st.rerun()

    elif "Creaminess" not in data:

        choice = render_numeric_buttons(
            "How creamy would you like your drink?",
            {
                "Not Creamy": 0,
                "Creamy": 1,
                "Very Creamy": 2
            },
            "cream"
        )

        if choice is not None:

            data["Creaminess"] = choice

            st.session_state.responses.append(data.copy())

            if st.session_state.flow_type == "3":
                st.session_state.step = "food_q"
            else:
                st.session_state.step = "results"

            st.rerun()

elif st.session_state.step == "food_q":

    st.markdown("""
    <div class="section-title">
        Food Questionnaire
    </div>
    """, unsafe_allow_html=True)

    filters = {"Type": encoders["Type"]["Food"]}

    if "food_data" not in st.session_state:
        st.session_state.food_data = {
            "Type": filters["Type"]
        }

    data = st.session_state.food_data

    if "Subtype" not in data:

        choice = render_buttons(
            "Subtype",
            get_choices("Subtype", filters),
            "What type of food would you like to order?"
        )
        if choice:
            data["Subtype"] = choice
            st.rerun()

    else:

        subtype_name = decoders["Subtype"][data["Subtype"]]
        filters["Subtype"] = data["Subtype"]

        if subtype_name == "Main Dish":
            if "Serving Type" not in data:
                c = render_buttons(
                    "Serving Type",
                    get_choices("Serving Type", filters),
                    "How would you like it to be served?"
                )
                if c:
                    data["Serving Type"] = c
                    st.rerun()

            elif "Spiciness" not in data:
                c = render_numeric_buttons(
                    "Spiciness Level",
                    {
                        "Not Spicy": 0,
                        "Spicy": 1,
                        "Very Spicy": 2
                    },
                    "spicy"
                )
                if c is not None:
                    data["Spiciness"] = c
                    st.rerun()

            elif "Cheesiness" not in data:

                c = render_numeric_buttons(
                    "Cheesiness Level",
                    {
                        "Not Cheesy": 0,
                        "Cheesy": 1,
                        "Very Cheesy": 2
                    },
                    "cheese"
                )

                if c is not None:

                    data["Cheesiness"] = c

                    st.session_state.responses.append(data.copy())

                    st.session_state.step = "results"

                    st.rerun()

        elif subtype_name == "Side Dish":

            if "Serving Type" not in data:

                c = render_buttons(
                    "Serving Type",
                    get_choices("Serving Type", filters),
                    "How would you like it to be cooked?"
                )

                if c:
                    data["Serving Type"] = c
                    st.rerun()

            elif "Spiciness" not in data:

                c = render_numeric_buttons(
                    "Spiciness Level",
                    {
                        "Not Spicy": 0,
                        "Spicy": 1
                    },
                    "side_spicy"
                )

                if c is not None:
                    data["Spiciness"] = c
                    st.rerun()

            elif "Cheesiness" not in data:
                c = render_numeric_buttons(
                    "Cheesiness Level",
                    {
                        "Not Cheesy": 0,
                        "Cheesy": 1
                    },
                    "side_cheese"
                )
                if c is not None:
                    data["Cheesiness"] = c
                    st.rerun()

            elif "Seafood" not in data:

                c = render_numeric_buttons(
                    "Seafood Preference",
                    {
                        "Non Seafood": 0,
                        "Seafood": 1
                    },
                    "seafood"
                )

                if c is not None:
                    data["Seafood"] = c
                    st.rerun()

            elif "Crispiness" not in data:
                c = render_numeric_buttons(
                    "Crispiness Level",
                    {
                        "Not Crispy": 0,
                        "Crispy": 1
                    },
                    "crispy"
                )

                if c is not None:
                    data["Crispiness"] = c
                    st.session_state.responses.append(data.copy())
                    st.session_state.step = "results"
                    st.rerun()

        elif subtype_name == "Bread":
            if "Serving Type" not in data:
                c = render_buttons(
                    "Serving Type",
                    get_choices("Serving Type", filters),
                    "How would like it cooked?"
                )
                if c:
                    data["Serving Type"] = c
                    st.rerun()

            elif "Primary" not in data:
                c = render_buttons(
                    "Primary",
                    get_choices("Primary", filters),
                    "Choose your main flavor"
                )
                if c:
                    data["Primary"] = c
                    st.rerun()

            elif "Secondary" not in data:
                c = render_buttons(
                    "Secondary",
                    get_choices("Secondary", filters),
                    "Choose your secondary flavor"
                )
                if c:
                    data["Secondary"] = c
                    st.rerun()

            elif "Crispiness" not in data:
                c = render_numeric_buttons(
                    "Crispiness Level",
                    {
                        "Not Crispy": 0,
                        "Crispy": 1
                    },
                    "bread_crisp"
                )

                if c is not None:
                    data["Crispiness"] = c
                    st.session_state.responses.append(data.copy())
                    st.session_state.step = "results"
                    st.rerun()

        elif subtype_name == "Dessert":
            if "Primary" not in data:
                c = render_buttons(
                    "Primary",
                    get_choices("Primary", filters),
                    "Choose your main flavor"
                )

                if c:
                    data["Primary"] = c
                    st.session_state.responses.append(data.copy())
                    st.session_state.step = "results"
                    st.rerun()

if st.session_state.step == "results":
    st.markdown("""
    <div class="section-title">
        ✨ Your Haus Recommendation ✨
    </div>
    """, unsafe_allow_html=True)

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


    def score_row(row, user):
        total_score = 0
        total_weight = 0

        for attr, w in WEIGHT.items():

            u = user.get(attr)
            r = row.get(attr)

            sim = (
                sim_categorical(u, r)
                if attr in categorical_cols
                else sim_numeric(u, r)
            )

            if sim is not None:
                total_score += sim * w
                total_weight += w

        base = total_score / total_weight if total_weight else 0

        bias = (1 if row.get("Recommended") == 1 else 0) * BIAS_STRENGTH
        return (base + bias) / (1 + BIAS_STRENGTH)

    top_results = {}
    all_scores = {}

    for user in st.session_state.responses:
        type_name = decoders["Type"][user["Type"]]
        temp_df = df.copy()
        temp_df["Score"] = temp_df.apply(lambda r: score_row(r, user),axis=1)
        top3 = temp_df.sort_values("Score",ascending=False).head(3)
        top_results[type_name] = top3["Menu"].tolist()
        all_scores[type_name] = temp_df.set_index("Menu")["Score"].to_dict()
        st.markdown(f"""
        <div class="result-title">
            Recommended {type_name}
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(3)

        for idx, (_, r) in enumerate(top3.iterrows()):
            with cols[idx]:
                render_product_card(r["Menu"],r["Score"],idx)

    if "Drink" in top_results and "Food" in top_results:

        st.markdown("""
        <div class="result-title">
            We Recommend You These Food Tray Combo
        </div>
        """, unsafe_allow_html=True)

        food_trays = [

            {
                "tray": "Cimol Mozzarella Cheese Sauce with Mango Yakult",
                "food": "Cimol Mozzarella Gwenchana Cheese Sauce",
                "drink": "Ice Mango mix Yakult"
            },

            {
                "tray": "Cimol Mozzarella Cheese Powder with Mango Yakult",
                "food": "Cimol Mozzarella Gwenchana Cheese Powder",
                "drink": "Ice Mango mix Yakult"
            },

            {
                "tray": "Ramyeon Tray Choco Cheese Crunchy",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Choco Cheese Crunchy"
            },

            {
                "tray": "Ramyeon Tray Drink Beng Beng",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Drink Beng-Beng Cream Caramel"
            },

            {
                "tray": "Ramyeon Tray Thai Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Thai Tea"
            },

            {
                "tray": "Ramyeon Tray Green Thai Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Green Thai Tea"
            },

            {
                "tray": "Ramyeon Tray Taro",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Taro"
            },

            {
                "tray": "Ramyeon Tray Choco Ovaltine",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Choco Ovaltine"
            },

            {
                "tray": "Ramyeon Tray Choco Hazelnut",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Choco Hazelnut"
            },

            {
                "tray": "Ramyeon Tray Choco Lava",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Choco Lava"
            },

            {
                "tray": "Ramyeon Tray Choco Avocado",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Choco Avocado"
            },

            {
                "tray": "Ramyeon Tray Boba Brown Sugar Fresh Milk",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Boba Brown Sugar Fresh Milk"
            },

            {
                "tray": "Ramyeon Tray Boba Brown Sugar Milk Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Boba Brown Sugar Milk Tea"
            },

            {
                "tray": "Ramyeon Tray Jasmine Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Jasmine Tea"
            },

            {
                "tray": "Ramyeon Tray Fresh Lemon Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Fresh Lemon Tea"
            },

            {
                "tray": "Ramyeon Tray Lychee Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Lychee Tea"
            },

            {
                "tray": "Ramyeon Tray Mango Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Mango Tea"
            },

            {
                "tray": "Ramyeon Tray Strawberry Tea",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Strawberry Tea"
            },

            {
                "tray": "Ramyeon Tray Cookies & Cream",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Cookies & Cream"
            },

            {
                "tray": "Ramyeon Tray Cotton Candy",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Cotton Candy"
            },

            {
                "tray": "Ramyeon Tray Mango Yakult",
                "food": "Spicy Cheese Ramyeon",
                "drink": "Ice Mango mix Yakult"
            },

            {
                "tray": "Snack Tray Choco Cheese Crunchy",
                "food": "Otteoke Cheese",
                "drink": "Choco Cheese Crunchy"
            },

            {
                "tray": "Snack Tray Drink Beng Beng",
                "food": "Otteoke Cheese",
                "drink": "Drink Beng-Beng Cream Caramel"
            },

            {
                "tray": "Snack Tray Thai Tea",
                "food": "Otteoke Cheese",
                "drink": "Thai Tea"
            },

            {
                "tray": "Snack Tray Green Thai Tea",
                "food": "Otteoke Cheese",
                "drink": "Green Thai Tea"
            },

            {
                "tray": "Snack Tray Taro",
                "food": "Otteoke Cheese",
                "drink": "Taro"
            },

            {
                "tray": "Snack Tray Choco Ovaltine",
                "food": "Otteoke Cheese",
                "drink": "Choco Ovaltine"
            },

            {
                "tray": "Snack Tray Choco Hazelnut",
                "food": "Otteoke Cheese",
                "drink": "Choco Hazelnut"
            },

            {
                "tray": "Snack Tray Choco Lava",
                "food": "Otteoke Cheese",
                "drink": "Choco Lava"
            },

            {
                "tray": "Snack Tray Choco Avocado",
                "food": "Otteoke Cheese",
                "drink": "Choco Avocado"
            },

            {
                "tray": "Snack Tray Boba Brown Sugar Fresh Milk",
                "food": "Otteoke Cheese",
                "drink": "Boba Brown Sugar Fresh Milk"
            },

            {
                "tray": "Snack Tray Boba Brown Sugar Milk Tea",
                "food": "Otteoke Cheese",
                "drink": "Boba Brown Sugar Milk Tea"
            },

            {
                "tray": "Snack Tray Jasmine Tea",
                "food": "Otteoke Cheese",
                "drink": "Jasmine Tea"
            },

            {
                "tray": "Snack Tray Fresh Lemon Tea",
                "food": "Otteoke Cheese",
                "drink": "Fresh Lemon Tea"
            },

            {
                "tray": "Snack Tray Lychee Tea",
                "food": "Otteoke Cheese",
                "drink": "Lychee Tea"
            },

            {
                "tray": "Snack Tray Mango Tea",
                "food": "Otteoke Cheese",
                "drink": "Mango Tea"
            },

            {
                "tray": "Snack Tray Strawberry Tea",
                "food": "Otteoke Cheese",
                "drink": "Strawberry Tea"
            },

            {
                "tray": "Snack Tray Cookies & Cream",
                "food": "Otteoke Cheese",
                "drink": "Cookies & Cream"
            },

            {
                "tray": "Snack Tray Cotton Candy",
                "food": "Otteoke Cheese",
                "drink": "Cotton Candy"
            },

            {
                "tray": "Snack Tray Mango Yakult",
                "food": "Otteoke Cheese",
                "drink": "Ice Mango mix Yakult"
            }
        ]

        matched = []

        for tray in food_trays:
            if (tray["food"] in top_results["Food"] and tray["drink"] in top_results["Drink"]):
                s = (all_scores["Food"][tray["food"]]+ all_scores["Drink"][tray["drink"]]) / 2
                matched.append({"tray": tray["tray"],"score": s})

        matched = sorted(matched,key=lambda x: x["score"],reverse=True)[:3]

        if matched:
            cols = st.columns(len(matched))
            for idx, m in enumerate(matched):
                with cols[idx]:
                    render_product_card( m["tray"], m["score"], idx)
        else:
            st.info("No matching food tray found.")

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("Start Again"):
        st.session_state.clear()
        st.rerun()