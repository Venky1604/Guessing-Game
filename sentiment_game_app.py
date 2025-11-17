import random
import time

import pandas as pd
import streamlit as st
from textblob import TextBlob

# ================== CONFIG ================== #
QUESTION_TIME_LIMIT = 20  # seconds per question

HAPPY_GIFS = [
    "https://media.giphy.com/media/111ebonMs90YLu/giphy.gif",
    "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/OPU6wzx8JrHna/giphy.gif",
]

SAD_GIFS = [
    "https://media.giphy.com/media/9Y5BbDSkSTiY8/giphy.gif",
    "https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif",
    "https://media.giphy.com/media/RHZ8QdsAFZRug/giphy.gif",
    "https://media.giphy.com/media/3og0IPxMM0erATueVW/giphy.gif",
]

# ================== PAGE CONFIG & CSS ================== #
st.set_page_config(
    page_title="Sentiment Guessing Game 🎮",
    layout="wide",
    page_icon="🤖",
)

st.markdown(
    """
    <style>
    .main-title {
        font-size: 2.6rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .subtitle {
        text-align: center;
        font-size: 1.0rem;
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
        margin-top: 0.4rem;
        margin-bottom: 0.6rem;
    }
    .result-card {
        border-radius: 14px;
        padding: 1.2rem 1.4rem;
        background-color: #ffffff;
        border: 1px solid #e8e8e8;
        box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    }
    .winner-text {
        font-size: 1.5rem;
        font-weight: 750;
        text-align: center;
    }
    @keyframes nod {
        0%   {transform: translateY(0) rotate(0deg);}
        25%  {transform: translateY(-4px) rotate(-5deg);}
        50%  {transform: translateY(0) rotate(0deg);}
        75%  {transform: translateY(-4px) rotate(5deg);}
        100% {transform: translateY(0) rotate(0deg);}
    }
    .nodding-bot {
        font-size: 3rem;
        display: inline-block;
        animation: nod 1.2s infinite;
        margin-bottom: 0.3rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ================== HELPER FUNCTIONS ================== #

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


def pick_new_review():
    """Pick a random review from stored df and update session_state."""
    df = st.session_state.df
    idx = random.randrange(len(df))
    row = df.iloc[idx]

    st.session_state.current_index = idx
    st.session_state.current_review = str(row["review"])
    st.session_state.current_truth = normalize_label(row["sentiment"])
    st.session_state.show_result = False
    st.session_state.human_guess = None
    st.session_state.ai_guess = None
    st.session_state.ai_confidence = None
    st.session_state.round_start_time = time.time()
    st.session_state.time_up = False


def init_game(total_rounds: int):
    """Initialize a new game: scores, round, history, phase, timer."""
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
    st.session_state.phase = "game"  # now we're in game phase
    st.session_state.time_limit = QUESTION_TIME_LIMIT
    pick_new_review()


# ================== HEADER ================== #

st.markdown(
    "<div class='main-title'>Sentiment Guessing Game 🤖🆚🧠</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>AI Guess Bot will ask you questions, one review at a time. "
    "Are you ready to play?</div>",
    unsafe_allow_html=True,
)
st.write("")

# Nodding AI bot always visible
st.markdown(
    "<div style='text-align:center; margin-bottom: 0.6rem;'>"
    "<span class='nodding-bot'>🤖</span>"
    "</div>",
    unsafe_allow_html=True,
)

# ================== PHASE MANAGEMENT ================== #

if "phase" not in st.session_state:
    st.session_state.phase = "intro"   # intro -> upload -> game

# ---------- PHASE 1: INTRO (Are you ready? Yes/No) ---------- #

if st.session_state.phase == "intro":
    st.markdown(
        "<div class='chat-bubble-bot'>"
        "🤖 <b>AI Guess Bot:</b> Hey! I'm the <b>AI Guess Bot</b>, and I'm happy to see you here 😊<br>"
        "Are you ready to start the game?"
        "</div>",
        unsafe_allow_html=True,
    )

    ready_option = st.selectbox(
        "Please select an option:",
        ["Select...", "Yes, let's start!", "No, not yet"],
    )

    if ready_option == "Yes, let's start!":
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> Awesome! Let's get things ready 🎉<br>"
            "First, I need your reviews dataset so I can start asking questions."
            "</div>",
            unsafe_allow_html=True,
    )
        st.session_state.phase = "upload"
        st.rerun()

    elif ready_option == "No, not yet":
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> No worries! I'll be nodding here until you're ready 😄<br>"
            "Just pick <b>Yes, let's start!</b> when you're ready to play."
            "</div>",
            unsafe_allow_html=True,
        )

    st.stop()

# ---------- PHASE 2: UPLOAD (Ask for CSV, rounds, then start) ---------- #

if st.session_state.phase == "upload":
    st.markdown(
        "<div class='chat-bubble-bot'>"
        "🤖 <b>AI Guess Bot:</b> Can you upload the <b>reviews dataset</b> to start the game?<br>"
        "I need a CSV file with columns <code>review</code> and <code>sentiment</code>."
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your review dataset CSV here 👇",
        type=["csv"],
    )

    st.markdown(
        "<div class='chat-bubble-bot'>"
        "🤖 <b>AI Guess Bot:</b> And how many questions do you want me to ask you?"
        "</div>",
        unsafe_allow_html=True,
    )

    rounds = st.slider(
        "Select number of rounds:",
        min_value=5,
        max_value=30,
        value=10,
        step=5,
    )

    start = st.button("✅ Upload & Start Game", use_container_width=True)

    if start:
        if uploaded_file is None:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Guess Bot:</b> Oops! I can't see any file yet 😅<br>"
                "Please upload a CSV so I can read the reviews."
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()
        try:
            df = pd.read_csv(uploaded_file)
        except Exception as e:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                f"🤖 <b>AI Guess Bot:</b> I tried to read the file but got an error: "
                f"<code>{e}</code><br>"
                "Can you check the file and try again?"
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        if "review" not in df.columns or "sentiment" not in df.columns:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Guess Bot:</b> Hmmm... your file is missing "
                "<code>review</code> and/or <code>sentiment</code> columns 😢<br>"
                "Please fix it and upload again."
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        df = df.dropna(subset=["review", "sentiment"])
        if df.empty:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Guess Bot:</b> After cleaning, I found no valid rows. "
                "Please try another dataset."
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        # Bot nods that we're ready
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> Nice! Your dataset looks good. "
            "We are <b>ready to start the game</b> now! 🚀"
            "</div>",
            unsafe_allow_html=True,
        )

        # Save and move to game
        st.session_state.df = df
        init_game(rounds)
        st.rerun()

    st.stop()

# ---------- FROM HERE: GAME PHASE ---------- #

df = st.session_state.df

# Scoreboard
col_score1, col_score2, col_score3 = st.columns(3)
with col_score1:
    st.metric("👤 Human Score", st.session_state.human_score)
with col_score2:
    st.metric("🤖 AI Score", st.session_state.ai_score)
with col_score3:
    st.metric(
        "🧠 Agreement",
        st.session_state.agreement,
        help="Rounds where you and the AI picked the same sentiment.",
    )

# Game progress
game_progress = st.session_state.round / st.session_state.total_rounds
st.progress(game_progress, text=f"Game Progress: Round {st.session_state.round} of {st.session_state.total_rounds}")
st.write("")

# ---------- GAME LOOP ---------- #

if not st.session_state.game_over:

    # TIMER
    if "time_limit" not in st.session_state:
        st.session_state.time_limit = QUESTION_TIME_LIMIT
    if "round_start_time" not in st.session_state:
        st.session_state.round_start_time = time.time()
    if "time_up" not in st.session_state:
        st.session_state.time_up = False

    elapsed = time.time() - st.session_state.round_start_time
    remaining = max(0, int(st.session_state.time_limit - elapsed))
    if st.session_state.time_limit > 0:
        timer_ratio = max(0.0, min(1.0, remaining / st.session_state.time_limit))
    else:
        timer_ratio = 0.0

    timer_col1, timer_col2 = st.columns([3, 1])
    with timer_col1:
        st.progress(timer_ratio, text=f"⏳ Time left for this question: {remaining} seconds")
    with timer_col2:
        st.metric("⏱️ Time", f"{remaining}s")

    # Time up auto-reveal
    if remaining == 0 and not st.session_state.show_result and not st.session_state.time_up:
        st.session_state.time_up = True
        st.session_state.human_guess = "⏰ Time Up (No Answer)"

        ai_label, ai_conf = ai_textblob_sentiment(st.session_state.current_review)
        st.session_state.ai_guess = ai_label
        st.session_state.ai_confidence = ai_conf

        truth = st.session_state.current_truth
        if ai_label == truth:
            st.session_state.ai_score += 1

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

    # Bot asks the question
    st.markdown("### 💬 AI Guess Bot")

    fun_round_lines = [
        "Let's see if your brain can beat my circuits this time 😏",
        "Don't overthink it... or do. I love watching humans think 🤖",
        "This one has some spice 🌶️, be careful!",
        "Is this review happy, meh, or mad? You tell me 😄",
    ]
    st.markdown(
        "<div class='chat-bubble-bot'>"
        f"🤖 <b>AI Guess Bot:</b> Round <b>{st.session_state.round}</b>! "
        f"{random.choice(fun_round_lines)}<br>"
        "Read this review carefully 👇"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        f"<div class='review-card'>“{st.session_state.current_review}”</div>",
        unsafe_allow_html=True,
    )

    # Let user answer
    if not st.session_state.show_result and not st.session_state.time_up:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> What do you think this review feels like? "
            "Choose one option:"
            "</div>",
            unsafe_allow_html=True,
        )

        col_p, col_nu, col_ne = st.columns(3)
        human_choice = None

        with col_p:
            if st.button("😄 Positive", use_container_width=True, key=f"btn_pos_{st.session_state.round}"):
                human_choice = "Positive"
        with col_nu:
            if st.button("😐 Neutral", use_container_width=True, key=f"btn_neu_{st.session_state.round}"):
                human_choice = "Neutral"
        with col_ne:
            if st.button("☹️ Negative", use_container_width=True, key=f"btn_neg_{st.session_state.round}"):
                human_choice = "Negative"

        if human_choice is not None:
            st.session_state.human_guess = human_choice

            ai_label, ai_conf = ai_textblob_sentiment(st.session_state.current_review)
            st.session_state.ai_guess = ai_label
            st.session_state.ai_confidence = ai_conf

            truth = st.session_state.current_truth

            human_correct = st.session_state.human_guess == truth
            ai_correct = st.session_state.ai_guess == truth

            if human_correct:
                st.session_state.human_score += 1
            if ai_correct:
                st.session_state.ai_score += 1
            if st.session_state.human_guess == st.session_state.ai_guess:
                st.session_state.agreement += 1

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

            if human_correct and not ai_correct:
                st.balloons()

    # ---------- SHOW RESULT ---------- #

    if st.session_state.show_result:
        truth = st.session_state.current_truth
        human = st.session_state.human_guess
        ai_label = st.session_state.ai_guess
        ai_conf = st.session_state.ai_confidence

        st.write("")
        st.markdown("### 🧾 Round Result")

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
                st.error(f"{human} (Incorrect or Time Up) 😅")
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

        # Bot reaction
        if human == truth:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Guess Bot:</b> Hurray! You are right on track! 😄🔥 "
                "That was a great call!"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                random.choice(HAPPY_GIFS),
                caption="AI Guess Bot is super happy with your answer!",
                use_container_width=False,
            )
        else:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Guess Bot:</b> Aww, not this time 😢 "
                "Either you missed it or the timer got you. "
                "But don't worry, the next one is yours!"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                random.choice(SAD_GIFS),
                caption="AI Guess Bot is a little sad this round.",
                use_container_width=False,
            )

        st.write("")
        col_next1, col_next2 = st.columns([2, 1])
        with col_next1:
            next_btn = st.button("Next Question ➡️", use_container_width=True)

        if next_btn:
            if st.session_state.round >= st.session_state.total_rounds:
                st.session_state.game_over = True
            else:
                st.session_state.round += 1
                pick_new_review()
            st.rerun()

# ---------- GAME OVER ---------- #

if st.session_state.game_over:
    st.markdown("## 🏁 Game Over")

    human = st.session_state.human_score
    ai_score = st.session_state.ai_score

    if human > ai_score:
        msg = "You beat the AI Guess Bot! 🏆🔥"
        st.balloons()
    elif human < ai_score:
        msg = "The AI Guess Bot wins this time… 🤖👑"
    else:
        msg = "It's a tie! Perfect balance ⚖️"

    st.markdown(f"<div class='winner-text'>{msg}</div>", unsafe_allow_html=True)
    st.write("")
    st.markdown(
        f"**Final Score:** 👤 Human **{human}** vs 🤖 AI **{ai_score}** · "
        f"Agreement rounds: **{st.session_state.agreement}**"
    )
    st.write("")

    # 🎉 Winner dance GIFs reusing working pools
    if human > ai_score:
        st.markdown(
            "<div class='chat-bubble-human'>"
            "🧑 <b>You:</b> Time for my victory dance! 🕺🎉"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            random.choice(HAPPY_GIFS),
            caption="Human dances in celebration! 🎉",
            use_container_width=False,
        )
    elif human < ai_score:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> I won! Let me show you my dance moves! 💃✨"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            random.choice(HAPPY_GIFS),
            caption="AI Guess Bot is dancing in victory! 🤖💃",
            use_container_width=False,
        )
    else:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Guess Bot:</b> It's a tie! Let's both dance together 😄"
            "</div>",
            unsafe_allow_html=True,
        )
        st.image(
            random.choice(HAPPY_GIFS),
            caption="Human and AI dancing together! 🕺🤖",
            use_container_width=False,
        )

    st.write("")
    if st.button("Play Again 🔁", use_container_width=True):
        # Reset everything and go back to intro
        keys_to_clear = [
            "df", "round", "total_rounds", "human_score", "ai_score",
            "agreement", "history", "game_over",
            "show_result", "human_guess", "ai_guess",
            "ai_confidence", "current_index",
            "current_review", "current_truth",
            "round_start_time", "time_up", "time_limit",
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state.phase = "intro"
        st.rerun()

# ---------- HISTORY ---------- #

with st.expander("📊 Round-by-round history (for analysis & grading)"):
    if "history" in st.session_state and st.session_state.history:
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
