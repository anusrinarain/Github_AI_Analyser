import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
st.set_page_config(page_title="AI GitHub Analyzer", layout="wide", page_icon="🚀")

st.markdown("""
<style>
.main { background-color: #0d1117; color: #c9d1d9; }
.stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
[data-testid="stMetricValue"] { color: #58a6ff; font-weight: bold; }
/* Sidebar AI Box Styling */
.sidebar-box {
    background-color: #161b22;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #38bdf8;
    margin-bottom: 10px;
    font-size: 14px;
}
.skill-badge {
    background-color: #238636;
    color: white;
    padding: 4px 10px;
    border-radius: 15px;
    display: inline-block;
    margin: 3px;
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except KeyError:
    st.error("Missing secrets! Check your .streamlit/secrets.toml file.")
    st.stop()

client = genai.Client(api_key=GEMINI_API_KEY)
def fetch_github_data(username):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    user = requests.get(f"https://api.github.com/users/{username}", headers=headers).json()
    repos = requests.get(f"https://api.github.com/users/{username}/repos?sort=updated&per_page=100", headers=headers).json()
    return user, repos
with st.sidebar:
    st.title("Dashboard Settings")
    username = st.text_input("Enter GitHub Username", "anusrinarain")
    st.info("Please enter a public GitHub username for the best results and analysis.")
    st.divider()
    
    st.subheader("AI Recruiter Insights")
    ai_sidebar_area = st.empty()
    st.divider()
    st.subheader("Top 5 Skills")
    skills_sidebar_area = st.empty()
st.title("AI GitHub Profile Dashboard")

if username:
    with st.spinner("Analyzing profile..."):
        user_data, repos = fetch_github_data(username)

    if "login" in user_data:
        # Profile Header
        col_img, col_info = st.columns([1, 4])
        with col_img:
            st.image(user_data["avatar_url"], width=150)
        with col_info:
            st.header(user_data.get("name") or username)
            st.write(user_data.get("bio") or "Developer | Engineer")
            st.markdown(f"🔗 [Visit GitHub Profile]({user_data['html_url']})")

        st.divider()

        # Metrics Row
        m1, m2, m3 = st.columns(3)
        m1.metric("Public Repos", user_data.get("public_repos", 0))
        m2.metric("Followers", user_data.get("followers", 0))
        m3.metric("Following", user_data.get("following", 0))

        st.divider()
        try:
            repo_names = [r["name"] for r in repos[:5] if "name" in r]
            repo_desc = " ".join([str(r['description']) for r in repos if r['description']])
            prompt = f"Act as an HR Manager. Analyze these projects: {', '.join(repo_names)}. Give 3 short professional bullet points."
            response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
            ai_sidebar_area.markdown(f"<div class='sidebar-box'>{response.text}</div>", unsafe_allow_html=True)
            skill_prompt = f"List exactly the top 5 technical skills from: {repo_desc}. Format: S1, S2, S3, S4, S5."
            skill_res = client.models.generate_content(model="gemini-2.0-flash", contents=skill_prompt)
            skills = skill_res.text.split(',')
            
            skill_html = "".join([f"<span class='skill-badge'>{s.strip()}</span>" for s in skills[:5]])
            skills_sidebar_area.markdown(skill_html, unsafe_allow_html=True)
            
        except Exception:
            ai_sidebar_area.warning("AI Insights temporarily unavailable.")
            skills_sidebar_area.info("Skills unavailable right now.")
        st.subheader("Performance Analytics")

        langs = [r["language"] for r in repos if r.get("language")]
        if langs:
            df = pd.Series(langs).value_counts().reset_index()
            df.columns = ["Language", "Count"]

            g1, g2 = st.columns(2)
            with g1:
                fig_pie = px.pie(df, values="Count", names="Language", hole=0.6,
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)", font_color="white")
                st.plotly_chart(fig_pie, use_container_width=True)

            with g2:
                fig_radar = go.Figure(data=go.Scatterpolar(r=df["Count"], theta=df["Language"], fill="toself", line_color="#a5d6a7"))
                fig_radar.update_layout(
                    height=600,
                    polar=dict(bgcolor="#161b22", radialaxis=dict(visible=True, gridcolor="#30363d")),
                    paper_bgcolor="rgba(0,0,0,0)", font_color="white"
                )
                st.plotly_chart(fig_radar, use_container_width=True)

        st.divider()
        
        # Timeline Chart
        st.subheader("Consistency Timeline")
        repo_years = [r['created_at'][:4] for r in repos]
        if repo_years:
            df_years = pd.Series(repo_years).value_counts().reset_index().sort_values('index')
            df_years.columns = ['Year', 'Count']
            
            fig_timeline = px.bar(df_years, x='Year', y='Count', color_discrete_sequence=['#90caf9'])
            fig_timeline.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="white")
            st.plotly_chart(fig_timeline, use_container_width=True)

        st.divider()

        
        st.subheader("Top 5 Repositories by Size")
        top_repos = sorted(repos, key=lambda x: x.get('size', 0), reverse=True)[:5]
        
        table_data = []
        for r in top_repos:
            table_data.append({
                "Project Name": r.get('name'),
                "Language": r.get('language') or "Unknown",
                "Size (KB)": r.get('size'),
                "Stars": r.get('stargazers_count'),
                "Link": r.get('html_url')
            })
        
        df_table = pd.DataFrame(table_data)
        st.dataframe(
            df_table,
            column_config={
                "Link": st.column_config.LinkColumn("Project URL")
            },
            hide_index=True,
            use_container_width=True
        )

    else:
        st.error("GitHub Error: Invalid username or token.")