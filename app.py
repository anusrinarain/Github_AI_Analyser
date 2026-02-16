import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="AI GitHub Analyzer", layout="wide", page_icon="🚀")

st.markdown("""
<style>
.main { background-color: #0d1117; color: #c9d1d9; }
.stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
[data-testid="stMetricValue"] { color: #58a6ff; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# ---------------- LOAD SECRETS ----------------
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Missing secrets! Check your .streamlit/secrets.toml file.")
    st.stop()

# ---------------- INIT GEMINI (NEW SDK) ----------------
client = genai.Client(api_key=GEMINI_API_KEY)

# ---------------- FETCH GITHUB DATA ----------------
def fetch_github_data(username):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    user = requests.get(f"https://api.github.com/users/{username}", headers=headers).json()
    repos = requests.get(f"https://api.github.com/users/{username}/repos", headers=headers).json()
    return user, repos

# ---------------- UI ----------------
st.title("📂 AI GitHub Profile Dashboard")
username = st.text_input("Enter GitHub Username", "anusrinarain")

if username:
    with st.spinner("Analyzing profile..."):
        user_data, repos = fetch_github_data(username)

    if "login" in user_data:

        col1, col2 = st.columns([1, 2.5])

        with col1:
            st.image(user_data["avatar_url"], width=150)
            st.header(user_data.get("name") or username)
            st.write(user_data.get("bio") or "Developer")

        with col2:
            st.subheader("🤖 AI Technical Insights")

            try:
                repo_names = [r["name"] for r in repos[:5] if "name" in r]

                prompt = f"""
                Analyze this developer based on these GitHub projects:
                {', '.join(repo_names)}

                Give 3 short professional bullet points about strengths.
                """

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                st.success(response.text)

            except Exception as e:
                st.error(f"Gemini API Error: {e}")

        st.divider()

        # ---------------- METRICS ----------------
        m1, m2, m3 = st.columns(3)
        m1.metric("Public Repos", user_data.get("public_repos", 0))
        m2.metric("Followers", user_data.get("followers", 0))
        m3.metric("Following", user_data.get("following", 0))

        st.divider()

        # ---------------- VISUALIZATION ----------------
        st.subheader("📊 Skills Distribution")

        langs = [r["language"] for r in repos if r.get("language")]

        if langs:
            df = pd.Series(langs).value_counts().reset_index()
            df.columns = ["Language", "Count"]

            g1, g2 = st.columns(2)

            with g1:
                fig_pie = px.pie(
                    df,
                    values="Count",
                    names="Language",
                    hole=0.6
                )
                fig_pie.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with g2:
                fig_radar = go.Figure(
                    data=go.Scatterpolar(
                        r=df["Count"],
                        theta=df["Language"],
                        fill="toself"
                    )
                )
                fig_radar.update_layout(
                    polar=dict(
                        bgcolor="#0d1117",
                        radialaxis=dict(visible=True)
                    ),
                    paper_bgcolor="rgba(0,0,0,0)",
                    font_color="white"
                )
                st.plotly_chart(fig_radar, use_container_width=True)

    else:
        st.error("GitHub Error: Invalid username or token.")
client = genai.Client(api_key="YOUR_NEW_KEY")

for m in client.models.list():
    print(m.name)