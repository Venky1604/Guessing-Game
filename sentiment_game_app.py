import random

import pandas as pd
import streamlit as st
from textblob import TextBlob

# -------------------- PAGE CONFIG & STYLE -------------------- #
st.set_page_config(
    page_title="Sentiment Guessing Game 🎮",
    layout="wide",
    page_icon="🎯",
)

# Custom CSS to make UI fun & eye-catching
st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.4rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.05rem;
        color: #555;
        margin-bottom: 1.2rem;
    }
    .review-card {
        background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%);
        border-radius: 14px;
        padding: 1.4rem 1.6rem;
        border: 1px solid #e0e0e0;
        box-shadow: 0 6px 16px rgba(0,0,0,0.06);
        font-size: 1.02rem;
    }
    .result-card {
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        background-color: #ffffff;
        border: 1px solid #e8e8e8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    .winner-text {
        font-size: 1.4rem;
        font-weight: 700;
        text-align: center;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------- HELPER FUNCTIONS -------------------- #

def normalize_label(label: str) -> str:
    """
    Normalize labels like 'pos', 'positive', '4', 'good'
    into 'Positive', 'Negative', 'Neutral'.
    """
    if not isinstance(label, str):
        return "Neutral"

    l = label.strip().lower()

    if "pos" in l or l in ("4", "5", "good", "great", "excellent"):
        return "Positive"
    if "neg" in l or l in ("1", "2", "bad", "terrible", "poor", "awful"):
        return "Negative"
    if "neu" in l or l in ("3", "okay", "ok", "neutral", "average"):
        return "Neutral"

    # Fallback
    return "Neutral"


def ai_textblob_sentiment(text: str):
    """
    Use TextBlob for simple sentiment.
    Returns (label, polarity score).
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity

    if polarity > 0.15:
        label = "Positive"
    elif polarity < -0.15:
        label = "Negative"
    else:
        label = "Neutral"

    return label, polarity


def pick_new_review(df: pd.DataFrame):
    """
    Pick a random review from df and store it in session_state.
    This implements: Display a random review.
    """
    idx = random.randrange(len(df))
    row = df.iloc[idx]

    st.session_state.current_index = idx
    st.session_state.current_review = str(row["review"])
    st.session_state.current_truth = normalize_label(row["sentiment"])
    st.session_state.show_result = False
    st.session_state.human_guess = None
    st.session_state.ai_guess = None
    st.session_state.ai_confidence = None


def init_game(total_rounds: int):
    """
    Initialize a new game: scores, round, history.
    """
    st.session_state.round = 1
    st.session_state.total_rounds = total_rounds
    st.session_state.human_score = 0
    st.session_state.ai_score = 0
    st.session_state.agreement = 0
    st.session_state.history = []
    st.session_state.game_over = False


# -------------------- SIDEBAR: DATA & SETTINGS -------------------- #

st.sidebar.header("🎛 Game Setup")

uploaded_file = st.sidebar.file_uploader(
    "Upload CSV with `review` and `sentiment` columns",
    type=["csv"],
    help="Example columns: review, sentiment (positive/negative/neutral)",
)

default_rounds = st.sidebar.slider(
    "Number of rounds",
    min_value=5,
    max_value=30,
    value=10,
    step=5,
    help="How many reviews to play this session?",
)

start_button = st.sidebar.button("🚀 Start / Restart Game")

st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ How it works")
st.sidebar.write(
    """
    1. Upload a CSV.\n
    2. Hit **Start / Restart Game**.\n
    3. Read the review.\n
    4. Guess the sentiment.\n
    5. See how you compare with the **AI** 🤖!
    """
)

# -------------------- LOAD DATA -------------------- #

if uploaded_file is None:
    st.markdown(
        "<div class='main-title'>Sentiment Guessing Game 🎯 vs 🤖</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div class='subtitle'>Upload a CSV in the sidebar to begin. "
        "Make your friends or classmates cheer while you battle the AI!</div>",
        unsafe_allow_html=True,
    )
    st.info("⬅️ Please upload a CSV file to start the game.")
    st.stop()

try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"Could not read CSV: {e}")
    st.stop()

if "review" not in df.columns or "sentiment" not in df.columns:
    st.error("CSV must contain `review` and `sentiment` columns.")
    st.stop()

df = df.dropna(subset=["review", "sentiment"])
if df.empty:
    st.error("No valid rows found after dropping missing values.")
    st.stop()

# -------------------- SESSION STATE INIT -------------------- #

if "round" not in st.session_state or start_button:
    init_game(default_rounds)
    pick_new_review(df)

if "current_review" not in st.session_state:
    pick_new_review(df)

# -------------------- HEADER -------------------- #

st.markdown(
    "<div class='main-title'>Sentiment Guessing Game 🎮 Human vs AI</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>Guess the sentiment of real customer reviews and "
    "see if you can outsmart the AI in front of everyone 😎</div>",
    unsafe_allow_html=True,
)

# -------------------- SCOREBOARD -------------------- #

col_score1, col_score2, col_score3 = st.columns(3)

with col_score1:
    st.metric("👤 Human Score", st.session_state.human_score)
with col_score2:
    st.metric("🤖 AI Score", st.session_state.ai_score)
with col_score3:
    st.metric(
        "🧠 Human & AI Agreement",
        st.session_state.agreement,
        help="Number of rounds where you and the AI picked the same label.",
    )

progress = st.session_state.round / st.session_state.total_rounds
st.progress(progress, text=f"Round {st.session_state.round} of {st.session_state.total_rounds}")

st.write("")  # spacing

# -------------------- MAIN ROUND UI -------------------- #

if not st.session_state.game_over:

    # 1. Display random review (already selected in session_state)
    st.markdown("#### 🔍 Read this review")
    st.markdown(
        f"<div class='review-card'>“{st.session_state.current_review}”</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown("#### 🎯 Your Guess")

    # 2. Player selects sentiment
    guess = st.radio(
        "What is the sentiment?",
        ["Positive", "Negative", "Neutral"],
        key="guess_radio",
        horizontal=True,
    )

    col_btn1, col_btn2 = st.columns([2, 1])
    with col_btn1:
        submit = st.button("Lock in my guess 🏹", use_container_width=True)
    with col_btn2:
        skip = st.button("Skip this review ⏭", use_container_width=True)

    if skip and not st.session_state.show_result:
        pick_new_review(df)
        st.experimental_rerun()

    # 3. AI predicts sentiment + 4. Reveal true sentiment + 5. Award points
    if submit and not st.session_state.show_result:
        st.session_state.human_guess = guess

        # 3. AI model predicts sentiment
        ai_label, ai_conf = ai_textblob_sentiment(st.session_state.current_review)
        st.session_state.ai_guess = ai_label
        st.session_state.ai_confidence = ai_conf

        truth = st.session_state.current_truth

        # 5. Award points based on matches
        human_correct = st.session_state.human_guess == truth
        ai_correct = st.session_state.ai_guess == truth

        if human_correct:
            st.session_state.human_score += 1
        if ai_correct:
            st.session_state.ai_score += 1
        if st.session_state.human_guess == st.session_state.ai_guess:
            st.session_state.agreement += 1

        # History logging
        st.session_state.history.append(
            {
                "round": st.session_state.round,
                "review": st.session_state.current_review,
                "truth": truth,
                "human": st.session_state.human_guess,
                "ai": st.session_state.ai_guess,
                "ai_conf": st.session_state.ai_confidence,
            }
        )

        st.session_state.show_result = True

        # Small celebration when human gets it right and AI is wrong
        if human_correct and not ai_correct:
            st.balloons()

    # ----- Show round result ----- #
    if st.session_state.show_result:
        st.write("")
        st.markdown("### 🧾 Round Result")

        truth = st.session_state.current_truth
        human = st.session_state.human_guess
        ai_label = st.session_state.ai_guess
        ai_conf = st.session_state.ai_confidence

        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.markdown("**✅ Ground Truth Sentiment:**")
            st.write(f"**{truth}**")
            st.markdown("---")
            st.markdown("**👤 Your Guess:**")
            if human == truth:
                st.success(f"{human} (Correct!) 🎉")
            else:
                st.error(f"{human} (Incorrect) 😅")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_res2:
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.markdown("**🤖 AI Guess (TextBlob):**")
            if ai_label == truth:
                st.success(f"{ai_label} (Correct!) 🤖✨")
            else:
                st.warning(f"{ai_label} (Incorrect) 🤔")
            if ai_conf is not None:
                st.caption(f"AI polarity score: {ai_conf:.3f}")
            st.markdown("---")
            if human == ai_label:
                st.info("You and the AI agreed this round 🧠🧠")
            else:
                st.caption("Different brains, different vibes 😄")
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("")

        col_next1, col_next2 = st.columns([2, 1])
        with col_next1:
            next_btn = st.button("Next Review ➡️", use_container_width=True)

        if next_btn:
            if st.session_state.round >= st.session_state.total_rounds:
                st.session_state.game_over = True
            else:
                st.session_state.round += 1
                pick_new_review(df)
            st.experimental_rerun()

# -------------------- GAME OVER SCREEN -------------------- #

if st.session_state.game_over:
    st.markdown("## 🏁 Game Over")

    human = st.session_state.human_score
    ai_score = st.session_state.ai_score

    if human > ai_score:
        msg = "You beat the AI! 🏆🔥"
        st.balloons()
    elif human < ai_score:
        msg = "The AI wins this time… 🤖👑"
    else:
        msg = "It's a tie! Perfect balance ⚖️"

    st.markdown(f"<div class='winner-text'>{msg}</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"**Final Score:** 👤 Human **{human}** vs 🤖 AI **{ai_score}** · "
        f"Agreement rounds: **{st.session_state.agreement}**"
    )

    st.write("")
    if st.button("Play Again 🔁", use_container_width=True):
        init_game(default_rounds)
        pick_new_review(df)
        st.experimental_rerun()

# -------------------- HISTORY (OPTIONAL ANALYTICS) -------------------- #

with st.expander("📊 Round-by-round history (for analysis & grading)"):
    if st.session_state.history:
        hist_df = pd.DataFrame(st.session_state.history)
        hist_df_display = hist_df[
            ["round", "truth", "human", "ai", "ai_conf"]
        ].rename(
            columns={
                "round": "Round",
                "truth": "Truth",
                "human": "Human Guess",
                "ai": "AI Guess",
                "ai_conf": "AI Polarity",
            }
        )
        st.dataframe(hist_df_display, use_container_width=True)
    else:
        st.caption("Play a few rounds to see history here!")
