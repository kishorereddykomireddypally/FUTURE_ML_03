import streamlit as st
import pandas as pd
import plotly.express as px
from utils import load_data, clean_text, extract_skills, calculate_similarity, extract_text_from_pdf, extract_contact_info
import base64

# Streamlit App Config
st.set_page_config(page_title="Resume Screening AI", page_icon="🚀", layout="wide")

# Function to load local CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Load Custom CSS
local_css("assets/style.css")

# --- UI Components ---

def render_hero():
    st.markdown("""
        <div class="hero-section">
            <h1 class="hero-title">Smart Resume Screening</h1>
            <p class="hero-subtitle">Next-Generation AI for Talent Acquisition</p>
        </div>
    """, unsafe_allow_html=True)

def render_metric_card(label, value, icon="📊"):
    st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 2rem; margin-bottom: 8px;">{icon}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-label">{label}</div>
        </div>
    """, unsafe_allow_html=True)

def render_candidate_card(row, match_score):
    skills_html = ""
    if row['Extracted Skills']:
        skills_list = row['Extracted Skills'].split(", ")[:5] # Show top 5 skills
        for skill in skills_list:
            skills_html += f'<span class="skill-tag match">{skill}</span>'
    
    missing_html = ""
    if 'Missing Skills' in row and row['Missing Skills']:
        missing_list = row['Missing Skills'].split(", ")[:3] # Show top 3 missing
        for skill in missing_list:
            missing_html += f'<span class="skill-tag missing">{skill}</span>'
            
    st.markdown(f"""
        <div class="candidate-card">
            <div class="candidate-header">
                <div class="candidate-name">{row.get('job_title', row.get('Name', 'Candidate'))}</div>
                <div class="match-score-badge">{match_score}% Match</div>
            </div>
            <div class="candidate-info">📧 {row.get('Email', 'N/A')}</div>
            <div class="candidate-info">📞 {row.get('Phone', 'N/A')}</div>
            <div class="candidate-info">📍 {row.get('location', 'N/A')}</div>
            <hr style="margin: 12px 0; border-top: 1px solid #F1F5F9;">
            <div style="margin-bottom: 8px; font-weight: 600; font-size: 0.9em; color: #475569;">Top Skills</div>
            <div>{skills_html}</div>
            <div style="margin-top: 8px; margin-bottom: 8px; font-weight: 600; font-size: 0.9em; color: #DC2626;">Missing</div>
            <div>{missing_html if missing_html else '<span style="color:#94A3B8; font-size:0.9em;">None detected</span>'}</div>
        </div>
    """, unsafe_allow_html=True)

# --- Main App Logic ---

# Check if database exists
DATA_PATH = "data/resumes.csv"
try:
    df_master = load_data(DATA_PATH)
except:
    df_master = pd.DataFrame()

# Sidebar
with st.sidebar:
    st.markdown("### 📋 Analysis Controls")
    
    # Initialize Session State
    if "job_description" not in st.session_state:
        st.session_state["job_description"] = ""
    
    SAMPLE_JDS = {
        "Custom (Empty)": "",
        "Python Developer": "Looking for a Python Developer with 3+ years of experience. Key Skills: Python, Django, Flask, SQL, REST APIs.",
        "Data Scientist": "Seeking a Data Scientist. Skills: Python, Pandas, Scikit-learn, TensorFlow, SQL, Data Visualization.",
        "Frontend Developer": "Need a Frontend Developer proficient in React.js, TypeScript, Redux, HTML5, CSS3."
    }
    
    selected_sample = st.selectbox("Load Sample JD", list(SAMPLE_JDS.keys()))
    if selected_sample != "Custom (Empty)":
        st.session_state["job_description"] = SAMPLE_JDS[selected_sample]

    job_description = st.text_area("Job Description", value=st.session_state["job_description"], height=250, placeholder="Paste JD here...")
    
    st.markdown("---")
    top_n = st.slider("Top Candidates", 1, 50, 10)
    st.markdown("---")
    st.caption("v2.0 | Premium Edition")

# Render Hero
render_hero()

# Main Tabs
tab1, tab2 = st.tabs(["🔍 Database Search", "📂 Document Upload"])

with tab1:
    if df_master.empty:
        st.error("Database not found. Please check data/resumes.csv")
    else:
        # Metrics Section
        c1, c2, c3 = st.columns(3)
        with c1:
            render_metric_card("Total Candidates", len(df_master), "👥")
        with c2:
            render_metric_card("Avg. Experience", "3.2 Yrs", "⏳") # Placeholder logic
        with c3:
            render_metric_card("System Status", "Online", "🟢")
        
        st.markdown("###") # Spacer
        
        if st.button("Run AI Screening", type="primary"):
            if not job_description:
                st.warning("Please enter a job description to proceed.")
            else:
                with st.spinner("Analyzing Database..."):
                    # Analysis Logic
                    cleaned_jd = clean_text(job_description)
                    jd_skills = set(extract_skills(job_description))
                    
                    # Process Candidates
                    candidate_texts = df_master['job_description'].astype(str).tolist()
                    cleaned_candidate_texts = [clean_text(text) for text in candidate_texts]
                    scores = calculate_similarity(cleaned_jd, cleaned_candidate_texts)
                    
                    df_master['Match Score (%)'] = [round(score * 100, 1) for score in scores]
                    
                    # Sort
                    ranked_df = df_master.sort_values(by="Match Score (%)", ascending=False).head(top_n).copy()
                    
                    # Extract Meta Data
                    ranked_df['Extracted Skills'] = ranked_df['job_description'].apply(lambda x: ", ".join(extract_skills(str(x))))
                    
                    skill_gaps = []
                    for _, row in ranked_df.iterrows():
                        cand_skills = set(row['Extracted Skills'].split(", ")) if row['Extracted Skills'] else set()
                        missing = jd_skills - cand_skills
                        skill_gaps.append(", ".join(missing))
                    ranked_df['Missing Skills'] = skill_gaps
                    
                    contact_info = ranked_df['job_description'].apply(extract_contact_info)
                    ranked_df['Email'] = contact_info.apply(lambda x: x['email'])
                    ranked_df['Phone'] = contact_info.apply(lambda x: x['phone'])

                    # Results Display
                    st.markdown("### 🏆 Top Matches")
                    
                    # Grid Layout for Cards
                    row1 = st.columns(2)
                    row2 = st.columns(2)
                    grid_cols = row1 + row2 
                    
                    # Only show top 4 as cards for clean layout, rest in table if needed
                    top_4 = ranked_df.head(4)
                    
                    for i, (index, row) in enumerate(top_4.iterrows()):
                        col = grid_cols[i] if i < 4 else None
                        if col:
                            with col:
                                render_candidate_card(row, row['Match Score (%)'])
                    
                    # Full Data Table for transparency
                    with st.expander("📄 View Full Detailed List", expanded=False):
                        st.dataframe(ranked_df[['job_title', 'Match Score (%)', 'Email', 'Extracted Skills']].style.background_gradient(cmap='Blues', subset=['Match Score (%)']), use_container_width=True)
                    
                    # Charts
                    st.markdown("### 📊 Analytics")
                    chart_col1, chart_col2 = st.columns(2)
                    with chart_col1:
                        fig = px.bar(ranked_df, x='job_title', y='Match Score (%)', color='Match Score (%)', title="Match Distribution", template="plotly_white")
                        st.plotly_chart(fig, use_container_width=True)
                    with chart_col2:
                         # Quick Skill Stats
                        all_skills = []
                        for s in ranked_df['Extracted Skills']:
                            all_skills.extend(s.split(", "))
                        if all_skills:
                            s_counts = pd.Series(all_skills).value_counts().head(7).reset_index()
                            s_counts.columns = ['Skill', 'Count']
                            fig2 = px.pie(s_counts, values='Count', names='Skill', title="Top Skills Found", hole=0.4, template="plotly_white")
                            st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.markdown("### 📂 Bulk Resume Analysis")
    uploaded_files = st.file_uploader("Upload PDF Resumes", type=["pdf"], accept_multiple_files=True)
    
    if st.button("Compare Uploaded Resumes"):
        if not uploaded_files or not job_description:
            st.error("Please upload files and provide a Job Description.")
        else:
            with st.spinner("Processing Documents..."):
                cleaned_jd = clean_text(job_description)
                jd_skills = set(extract_skills(job_description))
                
                resume_data = []
                texts = []
                
                for file in uploaded_files:
                    text = extract_text_from_pdf(file)
                    texts.append(clean_text(text))
                    
                    skills = set(extract_skills(text))
                    missing = jd_skills - skills
                    contact = extract_contact_info(text)
                    
                    resume_data.append({
                        "Name": file.name,
                        "Email": contact['email'],
                        "Phone": contact['phone'],
                        "Extracted Skills": ", ".join(skills),
                        "Missing Skills": ", ".join(missing),
                        "job_title": file.name, # reusing field for card compat
                        "location": "Uploaded"
                    })
                
                scores = calculate_similarity(cleaned_jd, texts)
                for i, score in enumerate(scores):
                    resume_data[i]["Match Score (%)"] = round(score * 100, 1)
                
                results_df = pd.DataFrame(resume_data).sort_values(by="Match Score (%)", ascending=False)
                
                # Render Cards
                st.markdown("### 🏆 Analysis Results")
                cols = st.columns(2)
                for i, (idx, row) in enumerate(results_df.iterrows()):
                    with cols[i % 2]:
                        render_candidate_card(row, row['Match Score (%)'])

