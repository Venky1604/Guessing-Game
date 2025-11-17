import random
import time

import pandas as pd
import streamlit as st
from textblob import TextBlob

# -------------------- CONFIG -------------------- #
QUESTION_TIME_LIMIT = 20  # seconds per question

# Happy & sad GIF pools
HAPPY_GIFS = [
    "https://media.giphy.com/media/111ebonMs90YLu/giphy.gif",  # confetti
    "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif",   # happy dance
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",  # victory
    "https://media.giphy.com/media/OPU6wzx8JrHna/giphy.gif",   # excited
]

SAD_GIFS = [
    "https://media.giphy.com/media/9Y5BbDSkSTiY8/giphy.gif",   # sad dog
    "https://media.giphy.com/media/d2lcHJTG5Tscg/giphy.gif",   # crying panda
    "https://media.giphy.com/media/RHZ8QdsAFZRug/giphy.gif",   # disappointed
    "https://media.giphy.com/media/3og0IPxMM0erATueVW/giphy.gif",  # facepalm
]

# -------------------- PAGE CONFIG & STYLE -------------------- #
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
    @keyframes dance {
        0%   {transform: translateY(0) rotate(0deg);}
        25%  {transform: translateY(-6px) rotate(-6deg);}
        50%  {transform: translateY(0) rotate(0deg);}
        75%  {transform: translateY(-6px) rotate(6deg);}
        100% {transform: translateY(0) rotate(0deg);}
    }
    .dancing-bot {
        font-size: 2.8rem;
        display: inline-block;
        animation: dance 0.9s infinite;
        margin-bottom: 0.3rem;
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


# -------------------- HEADER -------------------- #

st.markdown(
    "<div class='main-title'>Sentiment Guessing Game 🤖🆚🧠</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='subtitle'>An AI bot host will quiz you on real reviews. "
    "Upload a dataset, beat the timer, and try to outsmart the machine!</div>",
    unsafe_allow_html=True,
)
st.write("")

# Dancing bot always visible at top to grab attention
st.markdown(
    "<div style='text-align:center; margin-bottom: 0.6rem;'>"
    "<span class='dancing-bot'>🤖</span>"
    "</div>",
    unsafe_allow_html=True,
)

# Initialize phase
if "phase" not in st.session_state:
    st.session_state.phase = "setup"

# -------------------- PHASE 1: SETUP (AI bot asks to upload CSV) -------------------- #

if st.session_state.phase == "setup":
    fun_lines = [
        "I'm all charged up and ready to roast your predictions 😏",
        "Feed me a CSV and I'll feed you tricky questions 🤓",
        "Today we find out... are *you* smarter than an AI? 👀",
    ]
    st.markdown(
        "<div class='chat-bubble-bot'>"
        f"🤖 <b>AI Bot:</b> Hey! I'm your Sentiment Quiz Bot.<br>{random.choice(fun_lines)}"
        "<br><br>First, upload a CSV file with customer reviews.<br>"
        "<b>Required columns:</b> <code>review</code> and <code>sentiment</code> "
        "(e.g., positive / negative / neutral)."
        "</div>",
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload your review dataset CSV here 👇",
        type=["csv"],
    )

    st.markdown(
        "<div class='chat-bubble-bot'>"
        "🤖 <b>AI Bot:</b> And how many questions do you want me to throw at you?"
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

    start = st.button("🚀 Start Game with this file", use_container_width=True)

    if start:
        if uploaded_file is None:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Oops! I don't see a file yet 😅 "
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
                f"🤖 <b>AI Bot:</b> I tried to read the file but ran into an error: "
                f"<code>{e}</code><br>"
                "Can you check the file and try again?"
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        if "review" not in df.columns or "sentiment" not in df.columns:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Hmmm... your file is missing the required "
                "<code>review</code> and/or <code>sentiment</code> columns 😢<br>"
                "Please fix the columns and upload again."
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        df = df.dropna(subset=["review", "sentiment"])
        if df.empty:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> After cleaning, I found no valid rows in your file. "
                "Please try with another dataset."
                "</div>",
                unsafe_allow_html=True,
            )
            st.stop()

        # Store df and start game
        st.session_state.df = df
        init_game(rounds)
        st.rerun()

    st.stop()  # stop here in setup phase

# -------------------- FROM HERE: WE ARE IN GAME PHASE -------------------- #

df = st.session_state.df  # loaded in setup

# Scoreboard on top
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

# Overall game progress (rounds)
game_progress = st.session_state.round / st.session_state.total_rounds
st.progress(game_progress, text=f"Game Progress: Round {st.session_state.round} of {st.session_state.total_rounds}")

st.write("")

# -------------------- PHASE 2: GAME LOOP -------------------- #

if not st.session_state.game_over:

    # TIMER LOGIC
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

    # If time is up and no result yet -> AI auto reveals
    if remaining == 0 and not st.session_state.show_result and not st.session_state.time_up:
        st.session_state.time_up = True
        st.session_state.human_guess = "⏰ Time Up (No Answer)"

        # AI prediction
        ai_label, ai_conf = ai_textblob_sentiment(st.session_state.current_review)
        st.session_state.ai_guess = ai_label
        st.session_state.ai_confidence = ai_conf

        truth = st.session_state.current_truth
        ai_correct = ai_label == truth

        if ai_correct:
            st.session_state.ai_score += 1

        # agreement (only if AI also "no answer"? here: no)
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

    st.markdown("### 💬 AI Bot Chat")

    # Fun dynamic line each round
    fun_round_lines = [
        "Let's see if your brain can beat my circuits this time 😏",
        "Don't overthink it... or do. I love watching humans think 🤖",
        "This one has some spice 🌶️, be careful!",
        "Is this review happy, meh, or mad? You tell me 😄",
    ]
    st.markdown(
        "<div class='chat-bubble-bot'>"
        f"🤖 <b>AI Bot:</b> Okay, Round <b>{st.session_state.round}</b>! "
        f"{random.choice(fun_round_lines)}<br>"
        "Read this review carefully 👇"
        "</div>",
        unsafe_allow_html=True,
    )

    # Show review
    st.markdown(
        f"<div class='review-card'>“{st.session_state.current_review}”</div>",
        unsafe_allow_html=True,
    )

    # If we haven't shown result yet, ask for answer
    if not st.session_state.show_result and not st.session_state.time_up:
        st.markdown(
            "<div class='chat-bubble-bot'>"
            "🤖 <b>AI Bot:</b> What do you think this review feels like? "
            "Click one of the options below:"
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

            # AI prediction
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

            # Fun balloons when human correct and AI wrong
            if human_correct and not ai_correct:
                st.balloons()

    # -------------------- SHOW RESULT AFTER CHOICE / TIME UP -------------------- #

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

        # AI bot emotional reaction
        if human == truth:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Hurray! You are right on track! 😄🔥 "
                "That was a great call!"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                random.choice(HAPPY_GIFS),
                caption="AI Bot is super happy with your answer!",
                use_container_width=False,
            )
        else:
            st.markdown(
                "<div class='chat-bubble-bot'>"
                "🤖 <b>AI Bot:</b> Aww, not this time 😢 "
                "Either you missed it or the timer got you. "
                "But don't worry, the next one is yours!"
                "</div>",
                unsafe_allow_html=True,
            )
            st.image(
                random.choice(SAD_GIFS),
                caption="AI Bot is a little sad this round.",
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

# -------------------- PHASE 3: GAME OVER SCREEN -------------------- #

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

    # Winner dance
    if human > ai_score:
        st.markdown(
            "<div class='chat-bubble-human'>"
            "🧑 <b>You:</b> Time for my victory dance! 🕺🎉"
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
        # Go back to setup so bot again asks for CSV & rounds from beginning
        st.session_state.phase = "setup"
        for key in [
            "df", "round", "total_rounds", "human_score", "ai_score",
            "agreement", "history", "game_over",
            "show_result", "human_guess", "ai_guess",
            "ai_confidence", "current_index",
            "current_review", "current_truth",
            "round_start_time", "time_up",
        ]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

# -------------------- HISTORY (OPTIONAL) -------------------- #

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
