import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google import genai
import datetime
st.set_page_config(
    page_title="DevProfile AI | Career Analytics",
    layout="wide",
    page_icon="👨‍💻",
    initial_sidebar_state="expanded"
)
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
    }
    
    /* Typography */
    h1, h2, h3 {
        color: #f0f6fc !important;
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom Metrics Cards */
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    div[data-testid="stMetricLabel"] {
        color: #8b949e;
    }
    div[data-testid="stMetricValue"] {
        color: #58a6ff;
    }

    /* AI Insight Box */
    .ai-box {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-left: 5px solid #8b5cf6;
        padding: 20px;
        border-radius: 8px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    }
    
    /* Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #30363d;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)
try:
    GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except Exception:
    st.error("Secrets missing! Please check .streamlit/secrets.toml")
    st.stop()
client = genai.Client(api_key=GEMINI_API_KEY)
@st.cache_data(ttl=600)
def get_github_data(username):
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    try:
        user = requests.get(f"https://api.github.com/users/{username}", headers=headers).json()
        repos = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated", headers=headers).json()
        return user, repos
    except Exception as e:
        return None, None

def get_ai_analysis(user, repos):
    
    repo_context = []
    for r in repos[:6]: 
        repo_context.append(
            f"- {r['name']} (Lang: {r['language']}, Stars: {r['stargazers_count']}): {r['description']}"
        )
    repo_text = "\n".join(repo_context)
    
    prompt = f"""
    Act as a **Senior Technical Recruiter** at a top tech company hiring B.Tech graduates. 
    Analyze this candidate's GitHub profile.
    
    **Candidate Profile:**
    - Bio: {user.get('bio', 'N/A')}
    - Public Repos: {user.get('public_repos')}
    - Followers: {user.get('followers')}
    
    **Top Projects:**
    {repo_text}
    
    **Output Requirement:**
    Provide a structured Markdown report with:
    1. 🏆 **Hiring Verdict**: A 1-sentence summary of their employability.
    2. 🛠 **Tech Stack Strength**: Core languages/frameworks they seem proficient in.
    3. 💡 **Project Complexity Analysis**: Are these simple tutorials or complex applications?
    4. 🚀 **Career Recommendation**: Which specific role fits them best? (e.g., Backend Engineer, Data Scientist, Frontend Dev).
    
    Tone: Professional, insightful, and constructive.
    """
    
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt
    )
    return response.text

# Sidebar Inputs
with st.sidebar:
    st.title("Profile Config")
    target_user = st.text_input("GitHub Username", "anusrinarain")
    analyze_btn = st.button("Analyze Profile", type="primary")
    st.divider()
    st.info("Tip: Use a username with public repositories for the best analysis.")

# Main Content
if target_user:
    with st.spinner(f"Scouting GitHub data for {target_user}..."):
        user_data, repos = get_github_data(target_user)

    if user_data and "login" in user_data:
       
        col1, col2 = st.columns([1, 4])
        with col1:
            st.image(user_data['avatar_url'], width=150)
        with col2:
            st.title(user_data.get('name') or target_user)
            st.markdown(f"**{user_data.get('bio') or 'No bio provided'}**")
            st.caption(f"{user_data.get('location', 'Global')} | 🏢 {user_data.get('company', 'Open Source')}")
            st.markdown(f"[View on GitHub]({user_data['html_url']})", unsafe_allow_html=True)

        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📦 Repositories", user_data['public_repos'])
        m2.metric("⭐ Total Stars", sum([r['stargazers_count'] for r in repos]))
        m3.metric("👥 Followers", user_data['followers'])
        created_at = datetime.datetime.strptime(user_data['created_at'], "%Y-%m-%dT%H:%M:%SZ")
        years_active = datetime.datetime.now().year - created_at.year
        m4.metric("Years Active", f"{years_active}+ Years")

        st.divider()

        #AI ANALYSIS SECTION
        st.subheader("Recruiter's Evaluation")
        with st.container():
            if GEMINI_API_KEY:
                try:
                    with st.spinner("AI Recruiter is reviewing code..."):
                        analysis = get_ai_analysis(user_data, repos)
                    st.markdown(f"""<div class='ai-box'>{analysis}</div>""", unsafe_allow_html=True)
                except Exception as e:
                    st.warning(f"AI Analysis unavailable: {e}")
            else:
                st.error("Please add GEMINI_API_KEY to secrets.toml")
        st.subheader("Technical Deep Dive")
        
        # Data Prep
        langs = [r['language'] for r in repos if r['language']]
        df_lang = pd.DataFrame(langs, columns=['Language']).value_counts().reset_index()
        df_lang.columns = ['Language', 'Count']
        
        repo_dates = [r['created_at'][:4] for r in repos]
        df_activity = pd.DataFrame(repo_dates, columns=['Year']).value_counts().reset_index().sort_values('Year')
        df_activity.columns = ['Year', 'Repo Count']

        #Tech Stack & Activity Timeline
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("#### 🛠 Tech Stack Distribution")
            if not df_lang.empty:
                fig_pie = px.pie(df_lang, values='Count', names='Language', hole=0.5, 
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', font_color="white", showlegend=True)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("No language data found.")

        with c2:
            st.markdown("#### Consistency Timeline")
            if not df_activity.empty:
                fig_bar = px.bar(df_activity, x='Year', y='Repo Count', 
                                 color='Repo Count', color_continuous_scale='Bluyl')
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="white")
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                st.info("No activity data found.")

        #Impact Analysis
        st.markdown("#### ⚡ Project Impact (Size vs. Stars)")
        
        repo_data = [{
            'Name': r['name'],
            'Stars': r['stargazers_count'],
            'Size': r['size'],
            'Language': r['language'] or 'Unknown'
        } for r in repos]
        
        df_repos = pd.DataFrame(repo_data)
        
        if not df_repos.empty:
            fig_scatter = px.scatter(
                df_repos, 
                x="Size", 
                y="Stars", 
                size="Stars", 
                color="Language",
                hover_name="Name",
                size_max=60,
                log_x=True 
            )
            fig_scatter.update_layout(
                paper_bgcolor='rgba(0,0,0,0)', 
                plot_bgcolor='rgba(0,0,0,0)', 
                font_color="white",
                xaxis_title="Repository Size (KB) - Log Scale",
                yaxis_title="Stars"
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

    else:
        st.error(f"User '{target_user}' not found. Please check the spelling.")
else:
    st.info("Enter a GitHub username in the sidebar to start!")