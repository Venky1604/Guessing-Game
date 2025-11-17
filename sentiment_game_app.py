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
    .chat-bubble-bot {
        background: #ecf5ff;
        border-radius: 16px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.4rem;
        border: 1px solid #c9ddff;
        font-size: 0.98rem;
    }
    .chat-bubble-human {
        background: #fff7e6;
        border-radius: 16px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.4rem;
        border: 1px solid #ffe0b3;
        font-size: 0.98rem;
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
    """Normalize various label formats into 'Positive'/'Negative'/'Neutral'."""
    if not isinstance(label, str):
        return "Neutral"

    l = label.strip().lower()

    if "pos" in l or l in ("4", "5", "good", "great", "excellent", "love", "loved"):
        return "Positive"
    if "neg" in l or l in ("1", "2", "bad", "terrible", "poor", "awful", "worst"):
        return "Negative"
    if "neu" in l or l in ("3", "okay", "ok", "neutral", "average"):
        return "Neutral"

    return "Neutral"


def ai_textblob_sentiment(text: str):
    """Use TextBlob for simple sentiment: returns (label, polarity score)."""
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
    """Pick a random review from df and store in session_state."""
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
    """Initialize a new game: scores, round, history."""
    st.session_state.round = 1
    st.session_state.total_rounds = total_rounds
    st.session_state.human_score = 0
    st.session_state.ai_score = 0
    st.session_state.agreement = 0
    st.session_state.history = []
    st.session_state.game_over = False
    st.session_state.show_result = False
    st.session_state.human_guess = None
    st.session_state.ai_guess = None
    st.session_state.ai_confidence = None


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
    3. 🤖 AI bot shows you a review.\n
    4. You pick **Positive / Neutral / Negative**.\n
    5. AI reacts with happy/sad mode & scores update.
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
        "Your AI bot host is waiting to quiz you 😎</div>",
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
    "<div class='main-title'>Sentiment Guessing Game 🎮 Human vs AI Bot</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>Your AI bot host will quiz you on real reviews. "
    "Can you beat the machine? 🤖 vs 🧠</div>",
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

# -------------------- MAIN GAME AREA -------------------- #

if not st.session_state.game_over:

    # Chat-style layout
    st.markdown("### 💬 AI Bot Chat")

    # AI bot introduction text per round
    st.markdown(
        "<div class='chat-bubble-bot'>"
        f"🤖 <b>AI Bot:</b> Round {st.session_state.round}! Here's your review. "
        "Tell me what <i>you</i> feel about it – Positive, Neutral, or Negative?"
        "</div>",
        unsafe_allow_html=True,
    )

    # Show review card
    st.markdown(
        f"<div class='review-card'>“{st.session_state.current_review}”</div>",
        unsafe_allow_html=True,
    )

    st.write("")

    # Only show options if result is not yet revealed
    if not st.session_state.show_result:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Bot:</b> Choose your answer below 👇"
            "</div>",
            unsafe_allow_html=True,
        )

        col_p, col_nu, col_ne = st.columns(3)
        human_choice = None

        with col_p:
            if st.button("😄 Positive", use_container_width=True):
                human_choice = "Positive"
        with col_nu:
            if st.button("😐 Neutral", use_container_width=True):
                human_choice = "Neutral"
        with col_ne:
            if st.button("☹️ Negative", use_container_width=True):
                human_choice = "Negative"

        # When a choice is made
        if human_choice is not None:
            st.session_state.human_guess = human_choice

            # AI predicts
            ai_label, ai_conf = ai_textblob_sentiment(st.session_state.current_review)
            st.session_state.ai_guess = ai_label
            st.session_state.ai_confidence = ai_conf

            truth = st.session_state.current_truth

            human_correct = st.session_state.human_guess == truth
            ai_correct = st.session_state.ai_guess == truth

            # Score updates
            if human_correct:
                st.session_state.human_score += 1
            if ai_correct:
                st.session_state.ai_score += 1
            if st.session_state.human_guess == st.session_state.ai_guess:
                st.session_state.agreement += 1

            # Save history
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

            # Celebration when human correct and AI wrong
            if human_correct and not ai_correct:
                st.balloons()

    # ------------- SHOW RESULT (AI reactions, happy/sad) ------------- #
    if st.session_state.show_result:
        truth = st.session_state.current_truth
        human = st.session_state.human_guess
        ai_label = st.session_state.ai_guess
        ai_conf = st.session_state.ai_confidence

        st.write("")
        st.markdown("### 🧾 Round Result")

        # Human & AI result cards
        col_res1, col_res2 = st.columns(2)

        with col_res1:
            st.markdown("<div class='result-card'>", unsafe_allow_html=True)
            st.markdown("**✅ Ground Truth Sentiment:**")
            st.write(f"**{truth}**")
            st.markdown("---")
            st.markdown("**👤 Your Answer:**")
            if human == truth:
                st.success(f"{human} (Correct!) 🎉")
            else:
                st.error(f"{human} (Oops, not correct) 😅")
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
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("")

        # AI bot emotional reaction (happy/sad)
        human_correct = human == truth
        if human_correct:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Hurray! You are right on track! 😄🔥"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                "https://media.giphy.com/media/111ebonMs90YLu/giphy.gif",
                caption="AI Bot is happy with your answer!",
                use_container_width=False,
            )
        else:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Sorry, that's not quite right 😢 "
                "But don't worry, next one is yours!"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                "https://media.giphy.com/media/9Y5BbDSkSTiY8/giphy.gif",
                caption="AI Bot feels a little sad this round.",
                use_container_width=False,
            )

        st.write("")

        # Next round button
        col_next1, col_next2 = st.columns([2, 1])
        with col_next1:
            next_btn = st.button("Next Question ➡️", use_container_width=True)

        if next_btn:
            if st.session_state.round >= st.session_state.total_rounds:
                st.session_state.game_over = True
            else:
                st.session_state.round += 1
                pick_new_review(df)
            st.rerun()

# -------------------- GAME OVER SCREEN -------------------- #

if st.session_state.game_over:
    st.markdown("## 🏁 Game Over")

    human = st.session_state.human_score
    ai_score = st.session_state.ai_score

    if human > ai_score:
        msg = "You beat the AI Bot! 🏆🔥"
        st.balloons()
    elif human < ai_score:
        msg = "The AI Bot wins this time… 🤖👑"
    else:
        msg = "It's a tie! Perfect balance ⚖️"

    st.markdown(f"<div class='winner-text'>{msg}</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"**Final Score:** 👤 Human **{human}** vs 🤖 AI **{ai_score}** · "
        f"Agreement rounds: **{st.session_state.agreement}**"
    )
    st.write("")

    # Winner dance section
    if human > ai_score:
        st.markdown(
            "<div class='chat-bubble-human'>"
            "🧑 <b>You:</b> It's my victory dance time! 🕺🎉"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            "https://media.giphy.com/media/l41lUJX6ts7fj5Sbm/giphy.gif",
            caption="Human dances in celebration!",
            use_container_width=False,
        )
    elif human < ai_score:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Bot:</b> I won! Let me show you my dance moves! 💃✨"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            "https://media.giphy.com/media/26BoCVdjSJOWg6hbi/giphy.gif",
            caption="AI Bot is dancing in victory!",
            use_container_width=False,
        )
    else:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Bot:</b> It's a tie! Let's both dance together 😄"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
            caption="Human and AI dancing together!",
            use_container_width=False,
        )

    st.write("")
    if st.button("Play Again 🔁", use_container_width=True):
        init_game(default_rounds)
        pick_new_review(df)
        st.rerun()

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
