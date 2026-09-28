from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HERO_IMAGE = PROJECT_ROOT / "assets" / "dataprep-career-hero.png"


APP_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Space+Grotesk:wght@600;700&display=swap');

:root {
  --dp-ink: #111827;
  --dp-navy: #111a45;
  --dp-blue: #4158d0;
  --dp-violet: #7c3aed;
  --dp-cyan: #06b6d4;
  --dp-coral: #ff6b6b;
  --dp-green: #10b981;
  --dp-soft: #f6f7ff;
  --dp-border: #dfe3f4;
  --dp-shadow: 0 22px 55px rgba(26, 33, 75, .11);
}

html, body, [class*="css"], [data-testid="stAppViewContainer"], button, input, textarea {
  font-family: 'Manrope', 'Segoe UI', sans-serif;
}
h1, h2, h3, [data-testid="stHeadingWithActionElements"] {
  font-family: 'Space Grotesk', 'Manrope', sans-serif;
  letter-spacing: -.035em;
}
[data-testid="stAppViewContainer"] {
  background:
    radial-gradient(circle at 8% 8%, rgba(6,182,212,.18), transparent 25rem),
    radial-gradient(circle at 94% 16%, rgba(124,58,237,.15), transparent 28rem),
    linear-gradient(145deg, #eef3ff 0%, #faf8ff 45%, #eefcfb 100%);
  background-attachment: fixed;
}
[data-testid="stAppViewContainer"]::before,
[data-testid="stAppViewContainer"]::after {
  content: '';
  position: fixed;
  z-index: 0;
  width: 19rem;
  height: 19rem;
  border-radius: 999px;
  filter: blur(75px);
  opacity: .2;
  pointer-events: none;
  animation: dp-float 13s ease-in-out infinite alternate;
}
[data-testid="stAppViewContainer"]::before {background:#22d3ee; left:-8rem; bottom:4rem;}
[data-testid="stAppViewContainer"]::after {background:#a855f7; right:-7rem; top:15rem; animation-delay:-5s;}
[data-testid="stMain"] {position:relative; z-index:1;}
.block-container {max-width: 1240px; padding-top: 1.45rem; padding-bottom: 4rem;}

.dp-hero-copy {
  min-height: 370px;
  padding: 2.7rem 2.55rem;
  border-radius: 1.65rem;
  background:
    radial-gradient(circle at 92% 12%, rgba(6,182,212,.38), transparent 29%),
    linear-gradient(138deg, #10183f 0%, #24235f 55%, #4933a4 100%);
  border: 1px solid rgba(255,255,255,.15);
  box-shadow: var(--dp-shadow);
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  overflow: hidden;
  isolation: isolate;
  animation: dp-rise .7s cubic-bezier(.2,.75,.25,1) both;
}
.dp-hero-copy::after {
  content:'';
  position:absolute;
  width:12rem;
  height:12rem;
  border:1px solid rgba(255,255,255,.18);
  border-radius:50%;
  right:-4.5rem;
  bottom:-5rem;
  box-shadow:0 0 0 2.7rem rgba(255,255,255,.035), 0 0 0 5.4rem rgba(255,255,255,.025);
  z-index:-1;
  animation: dp-pulse 7s ease-in-out infinite;
}
.dp-kicker {font-size: .73rem; font-weight: 800; letter-spacing: .14em; text-transform: uppercase; color: #67e8f9;}
.dp-hero-copy h1 {font-size: clamp(2.4rem, 4.35vw, 3.65rem); margin: .55rem 0 .9rem; line-height: 1; color: #fff; max-width: 12ch; text-wrap:balance;}
.dp-hero-copy p {font-size: 1.04rem; line-height:1.65; color: #d9e1ff; margin: 0 0 1.3rem; max-width: 38rem;}
.dp-capabilities {font-size:.72rem; color:#fff; font-weight:800; letter-spacing:.1em; opacity:.92;}
.dp-hero-note {font-size:.8rem; color:#b9c8ff; margin-top:.6rem;}
[data-testid="stImage"] {animation:dp-image-in .85s .1s cubic-bezier(.2,.75,.25,1) both;}
[data-testid="stImage"] img {border-radius:1.65rem; min-height:370px; object-fit:cover; box-shadow:var(--dp-shadow); border:1px solid rgba(255,255,255,.8); transition:transform .45s ease, box-shadow .45s ease;}
[data-testid="stImage"] img:hover {transform:translateY(-4px) scale(1.008); box-shadow:0 28px 65px rgba(26,33,75,.18);}
[data-testid="stImageCaption"] {font-size:.76rem; color:#68708f; padding:.3rem .35rem 0;}

.dp-section-intro {padding: 1.15rem 1.25rem; border: 1px solid rgba(65,88,208,.18); border-left: 5px solid var(--dp-cyan); border-radius: 1rem; background:linear-gradient(120deg, rgba(255,255,255,.94), rgba(239,243,255,.94)); margin: .4rem 0 1.15rem; box-shadow:0 10px 30px rgba(30,41,87,.06);}
.dp-section-intro h3 {margin:0 0 .25rem; font-size:1.05rem; color:var(--dp-navy);}
.dp-section-intro p {margin:0; color:#505978;}
.dp-step-grid {display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:.85rem; margin:.75rem 0 1.15rem;}
.dp-step {border:1px solid rgba(255,255,255,.8); background:rgba(255,255,255,.76); backdrop-filter:blur(12px); border-radius:1rem; padding:1rem; min-height:112px; box-shadow:0 12px 30px rgba(30,41,87,.07); transition:transform .25s ease, box-shadow .25s ease, border-color .25s ease;}
.dp-step:hover {transform:translateY(-3px); border-color:rgba(65,88,208,.35); box-shadow:0 17px 36px rgba(30,41,87,.12);}
.dp-step-number {display:inline-grid; place-items:center; width:1.8rem; height:1.8rem; border-radius:50%; background:linear-gradient(135deg,#dbeafe,#ede9fe); color:#4933a4; font-weight:800; margin-bottom:.45rem;}
.dp-step strong {display:block; color:var(--dp-navy); margin-bottom:.2rem;}
.dp-step span {font-size:.86rem; color:#68708f; line-height:1.45;}
.dp-process {display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); margin:.85rem 0 1.5rem; padding:.25rem 1.05rem 1rem; border-radius:1rem; background:rgba(255,255,255,.58); border:1px solid rgba(255,255,255,.8); box-shadow:0 10px 30px rgba(30,41,87,.05);}
.dp-process-item {position:relative; padding:1.15rem 1rem .1rem 0; color:#505978; animation:dp-rise .55s ease both;}
.dp-process-item:nth-child(2) {animation-delay:.08s}.dp-process-item:nth-child(3) {animation-delay:.16s}.dp-process-item:nth-child(4) {animation-delay:.24s}
.dp-process-item:not(:last-child)::after {content:'›'; position:absolute; right:.65rem; top:.9rem; color:#8b93b4; font-size:1.5rem;}
.dp-process-number {display:block; color:var(--dp-violet); font-size:.7rem; font-weight:850; letter-spacing:.1em; margin-bottom:.25rem;}
.dp-process-item strong {display:block; color:var(--dp-navy); font-size:.94rem; margin-bottom:.16rem;}
.dp-process-item span:last-child {font-size:.8rem; line-height:1.35;}
.dp-help {font-size:.86rem; color:#68708f; margin-top:-.35rem; margin-bottom:.75rem;}

[data-testid="stTabs"] {margin-top:.45rem; background:rgba(255,255,255,.74); backdrop-filter:blur(16px); border:1px solid rgba(255,255,255,.9); border-radius:1.35rem; padding:.65rem 1.15rem 1.45rem; box-shadow:0 18px 50px rgba(30,41,87,.09);}
[data-testid="stTabs"] [data-baseweb="tab-list"] {gap:1.1rem; background:transparent; padding:0; border-bottom:1px solid #dde2f1;}
[data-testid="stTabs"] [data-baseweb="tab"] {border-radius:0; padding:.72rem .1rem; color:#5c6380; font-weight:650; transition:color .2s ease, transform .2s ease;}
[data-testid="stTabs"] [data-baseweb="tab"]:hover {color:var(--dp-violet); transform:translateY(-1px);}
[data-testid="stTabs"] [aria-selected="true"] {color:var(--dp-violet); font-weight:800; border-bottom:3px solid var(--dp-violet);}
[data-testid="stExpander"] {background:rgba(255,255,255,.68); border-color:rgba(65,88,208,.14)!important; border-radius:1rem!important; box-shadow:0 8px 24px rgba(30,41,87,.05);}
[data-testid="stMetric"] {background:linear-gradient(145deg,#fff,#f5f3ff); border:1px solid rgba(65,88,208,.15); padding:.95rem; border-radius:1rem; box-shadow:0 10px 28px rgba(30,41,87,.07); transition:transform .25s ease;}
[data-testid="stMetric"]:hover {transform:translateY(-3px);}
[data-testid="stMetricLabel"] {font-weight:750; color:#505978;}
[data-testid="stMetricValue"] {font-family:'Space Grotesk','Manrope',sans-serif; color:var(--dp-navy);}
[data-testid="stFileUploader"] {background:linear-gradient(145deg,rgba(246,247,255,.9),rgba(238,252,251,.9)); border-radius:1rem; padding:.4rem;}
div.stButton > button {border-radius:.65rem; border:1px solid #9ca5c4; font-weight:800; padding:.48rem 1.05rem; background:#fff; color:var(--dp-navy); box-shadow:0 5px 13px rgba(30,41,87,.06); transition:transform .2s ease, box-shadow .2s ease, border-color .2s ease;}
div.stButton > button:hover {border-color:var(--dp-violet); color:var(--dp-violet); transform:translateY(-2px); box-shadow:0 9px 20px rgba(30,41,87,.12);}
div.stButton > button[kind="primary"] {background:linear-gradient(115deg,var(--dp-blue),var(--dp-violet)); color:white; border:0; box-shadow:0 8px 22px rgba(80,63,190,.28);}
div.stButton > button[kind="primary"]:hover {background:linear-gradient(115deg,#334cc8,#6d28d9); color:white; box-shadow:0 12px 28px rgba(80,63,190,.38);}

@keyframes dp-rise {from {opacity:0; transform:translateY(18px)} to {opacity:1; transform:translateY(0)}}
@keyframes dp-image-in {from {opacity:0; transform:translateX(22px)} to {opacity:1; transform:translateX(0)}}
@keyframes dp-float {from {transform:translate3d(0,0,0) scale(1)} to {transform:translate3d(2rem,-2.5rem,0) scale(1.14)}}
@keyframes dp-pulse {0%,100% {transform:scale(1); opacity:.8} 50% {transform:scale(1.08); opacity:1}}

@media (max-width: 760px) {
  .block-container {padding-top:.8rem;}
  .dp-hero-copy {min-height:auto; padding:1.8rem; border-radius:1.25rem;}
  .dp-hero-copy h1 {font-size:2.5rem;}
  [data-testid="stImage"] img {min-height:260px; border-radius:1.25rem;}
  [data-testid="stTabs"] {padding:.45rem .65rem 1rem; border-radius:1rem;}
  .dp-step-grid {grid-template-columns:1fr;}
  .dp-process {grid-template-columns:1fr 1fr;}
  .dp-process-item:nth-child(2)::after {display:none;}
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {animation-duration:.01ms!important; animation-iteration-count:1!important; transition-duration:.01ms!important;}
}
</style>
"""


def apply_app_style():
    st.markdown(APP_CSS, unsafe_allow_html=True)


def render_hero():
    copy_column, image_column = st.columns([1.02, 0.98], gap="medium", vertical_alignment="center")
    with copy_column:
        st.markdown(
            """
            <div class="dp-hero-copy">
              <div class="dp-kicker">Practical interview preparation for data engineers</div>
              <h1>Prepare with evidence, not guesswork.</h1>
              <p>Use your résumé, target job, and technical notes to build a focused study plan and practice stronger interview answers.</p>
              <div class="dp-capabilities">DOCUMENT ANSWERS&nbsp;&nbsp; / &nbsp;&nbsp;JOB MATCH&nbsp;&nbsp; / &nbsp;&nbsp;INTERVIEW PRACTICE</div>
              <div class="dp-hero-note">Start with the guide below. Safe sample files are included.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with image_column:
        st.image(
            str(HERO_IMAGE),
            caption="Prepare for technical interviews with a clear, evidence-based plan.",
            width="stretch",
        )


def render_getting_started():
    st.markdown(
        """
        <div class="dp-step-grid">
          <div class="dp-step"><span class="dp-step-number">1</span><strong>Add your information</strong><span>Upload a résumé, job posting, or study notes - or try the safe sample files.</span></div>
          <div class="dp-step"><span class="dp-step-number">2</span><strong>Choose a tool</strong><span>Ask a question, compare a role, or start a practice interview.</span></div>
          <div class="dp-step"><span class="dp-step-number">3</span><strong>Use the results</strong><span>Review cited evidence, skill gaps, a study plan, and practical feedback.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_intro(title: str, description: str):
    st.markdown(
        f'<div class="dp-section-intro"><h3>{title}</h3><p>{description}</p></div>',
        unsafe_allow_html=True,
    )


def render_document_flow():
    st.markdown(
        """
        <div class="dp-process">
          <div class="dp-process-item"><span class="dp-process-number">STEP 01</span><strong>Add files</strong><span>Your résumé, job post, or notes</span></div>
          <div class="dp-process-item"><span class="dp-process-number">STEP 02</span><strong>Organize</strong><span>Readable sections are prepared</span></div>
          <div class="dp-process-item"><span class="dp-process-number">STEP 03</span><strong>Find evidence</strong><span>Useful passages are selected</span></div>
          <div class="dp-process-item"><span class="dp-process-number">STEP 04</span><strong>Answer</strong><span>You receive an answer with sources</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_example_questions(items):
    st.markdown("**Try asking:**")
    st.caption("  •  ".join(items))
