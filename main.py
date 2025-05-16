from dotenv import load_dotenv
import base64
import streamlit as st
import os
import io
from PIL import Image
import pdf2image
import google.generativeai as genai
from docx import Document
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import re
import plotly.graph_objects as go
from fpdf import FPDF
import tempfile

# Load environment variables
load_dotenv()

# Configure Gemini API
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    st.error("Google API key not found in environment variables.")
    st.stop()

genai.configure(api_key=API_KEY)

def get_gemini_response(input_text, pdf_content, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([input_text, pdf_content[0], prompt])
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

def input_file_setup(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=200)
            first_page = images[0]
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            file_parts = [{
                "mime_type": "image/jpeg",
                "data": base64.b64encode(img_byte_arr.getvalue()).decode()
            }]
            return file_parts
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(uploaded_file)
            doc_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return [{"mime_type": "text/plain", "data": doc_text}]
        elif uploaded_file.type == "text/plain":
            text_content = uploaded_file.read().decode("utf-8")
            return [{"mime_type": "text/plain", "data": text_content}]
        else:
            st.error("Unsupported file format. Please upload a PDF, DOCX, or TXT file.")
            return None
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

def log_user_action(action, response):
    with open("user_activity_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {action} - Response: {response[:200]}...\n")

def extract_percentage_match(response):
    try:
        match = re.search(r'(\d{1,3})%\s', response)
        return int(match.group(1)) if match else None
    except:
        return None

def create_pdf_report(analysis_results, match_percentages=None):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    def safe_text(text):
        return text.encode('latin1', 'replace').decode('latin1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt=safe_text("Resume Analysis Report"), ln=1, align='C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    
    if match_percentages:
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(200, 10, txt=safe_text("Candidate Match Scores:"), ln=1)
        pdf.ln(5)
        
        for i, (name, score) in enumerate(match_percentages.items(), 1):
            pdf.cell(200, 10, txt=safe_text(f"{i}. {name}: {score}%"), ln=1)
        pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(200, 10, txt=safe_text("Detailed Analysis:"), ln=1)
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    for line in analysis_results.split('\n'):
        pdf.multi_cell(0, 10, txt=safe_text(line))
    
    return pdf.output(dest='S').encode('latin1', 'replace')

def analyze_resumes(job_description, resumes):
    analysis_results = {}
    match_percentages = {}
    
    with st.spinner('🔍 Analyzing resumes...'):
        progress_bar = st.progress(0)
        total_files = len(resumes)
        
        for i, (name, resume) in enumerate(resumes.items()):
            progress_bar.progress((i + 1) / total_files)
            file_content = input_file_setup(resume)
            if file_content:
                prompt = prompts["match"]
                response = get_gemini_response(job_description, file_content, prompt)
                if response:
                    analysis_results[name] = response
                    percentage = extract_percentage_match(response)
                    if percentage is not None:
                        match_percentages[name] = percentage
    
    return analysis_results, match_percentages

def create_3d_graph(match_percentages):
    names = list(match_percentages.keys())
    scores = list(match_percentages.values())
    
    fig = go.Figure(data=[go.Bar(
        x=names,
        y=scores,
        text=scores,
        textposition='auto',
        marker=dict(
            color=scores,
            colorscale='Viridis',
            line=dict(color='rgb(8,48,107)', width=1.5)
        ),
        opacity=0.8
    )])
    
    fig.update_layout(
        title='Candidate Match Scores',
        xaxis_title='Candidates',
        yaxis_title='Match Percentage',
        height=500,
        margin=dict(l=50, r=50, b=150, t=50, pad=4),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig

# Prompts for Gemini AI
prompts = {
    "analysis": """
    You are an experienced Technical Human Resource Manager. Review the provided resume against the job description.
    Provide a detailed professional evaluation, highlighting strengths and weaknesses in relation to the specified job requirements.
    """,
    "match": """
    You are a skilled ATS (Applicant Tracking System) scanner. Evaluate the resume against the provided job description.
    Provide the percentage match, list missing keywords, and share your final thoughts.
    """,
    "keyword_analysis": """
    You are an advanced AI-powered career consultant. Analyze the job description and the uploaded resume to identify critical keywords.
    List the most important keywords from the job description that are missing in the resume and suggest areas for improvement.
    """
}

# Streamlit app setup
st.set_page_config(
    page_title="Resume Expert Pro+",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with new background color
st.markdown("""
<style>
:root {
    --primary-color: #4361ee;
    --secondary-color: #3a0ca3;
    --accent-color: #f72585;
    --background-color: #f0f2f6;
    --card-color: #ffffff;
    --text-color: #2b2d42;
    --light-text: #8d99ae;
}

body {
    background-color: var(--background-color);
    color: var(--text-color);
    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
}

/* Header Styles */
.header-container {
    margin-bottom: 2.5rem;
    position: relative;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    padding: 2rem;
    border-radius: 12px;
    color: white;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.main-header {
    color: white;
    font-size: 2.8rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
}

.subheader {
    color: rgba(255, 255, 255, 0.9);
    font-size: 1.2rem;
    margin-bottom: 0;
}

.header-decoration {
    height: 4px;
    width: 100px;
    background: white;
    margin: 1rem 0;
    border-radius: 2px;
}

/* Sidebar Styles */
.sidebar-header {
    padding: 1.5rem 0;
    margin-bottom: 1.5rem;
    position: relative;
}

.logo-container {
    display: flex;
    align-items: center;
    gap: 10px;
}

.logo-sparkle {
    font-size: 1.8rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 0.8; transform: scale(1); }
    50% { opacity: 1; transform: scale(1.1); }
    100% { opacity: 0.8; transform: scale(1); }
}

.tagline {
    color: var(--light-text);
    font-size: 0.95rem;
    margin-top: 0.5rem;
}

.progress-tracker {
    margin: 1rem 0;
}

.progress-bar {
    height: 4px;
    width: 100%;
    background-color: #e0e0e0;
    border-radius: 2px;
    margin-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
}

.progress-bar::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 80%;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    animation: progress 2s ease-in-out infinite;
}

@keyframes progress {
    0% { width: 80%; }
    50% { width: 100%; }
    100% { width: 80%; }
}

/* Match Percentage Styles */
.match-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    margin: 2rem 0;
}

.match-circle {
    width: 160px;
    height: 160px;
    border-radius: 50%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    color: white;
    box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
    background: linear-gradient(135deg, var(--primary-color), var(--accent-color));
}

.match-circle:hover {
    transform: scale(1.05);
}

.match-percentage {
    font-size: 3rem;
    font-weight: bold;
    margin-bottom: -10px;
}

.match-label {
    font-size: 1.1rem;
    opacity: 0.9;
}

.score-feedback {
    margin-top: 1rem;
    padding: 0.5rem 1rem;
    border-radius: 20px;
    background-color: rgba(255, 255, 255, 0.2);
    font-weight: 500;
    color: var(--text-color);
}

/* Analysis Results */
.analysis-results {
    background-color: var(--card-color);
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    border-left: 5px solid var(--primary-color);
    margin: 1.5rem 0;
}

/* Steps Container */
.steps-container {
    display: flex;
    justify-content: space-between;
    margin: 1.5rem 0;
}

.step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    padding: 0 1rem;
}

.step-number {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: var(--primary-color);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.step-content {
    text-align: center;
    font-size: 0.9rem;
    color: var(--light-text);
}

/* Button Styles */
.stButton>button {
    border-radius: 8px;
    padding: 0.75rem 1.5rem;
    transition: all 0.3s ease;
    font-weight: 500;
    border: none;
    background: linear-gradient(45deg, var(--primary-color), var(--secondary-color));
    color: white;
}

.stButton>button:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 12px rgba(67, 97, 238, 0.2);
}

/* Footer Styles */
.footer {
    margin-top: 4rem;
    padding: 2rem 0;
    text-align: center;
    color: var(--light-text);
    font-size: 0.9rem;
    border-top: 1px solid rgba(0, 0, 0, 0.1);
}

.footer-content {
    max-width: 600px;
    margin: 0 auto;
}

.social-links {
    margin: 0.5rem 0;
}

.social-links a {
    color: var(--primary-color);
    text-decoration: none;
    margin: 0 0.5rem;
}

/* Card Styles */
.resume-card {
    background-color: var(--card-color);
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 1rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    transition: transform 0.3s ease;
}

.resume-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.candidate-rank {
    background-color: var(--primary-color);
    color: white;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 1rem;
    font-weight: bold;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
    .main-header {
        font-size: 2rem;
    }
    
    .steps-container {
        flex-direction: column;
        gap: 1.5rem;
    }
    
    .step {
        flex-direction: row;
        gap: 1rem;
        align-items: flex-start;
        text-align: left;
    }
    
    .match-circle {
        width: 130px;
        height: 130px;
    }
}
</style>
""", unsafe_allow_html=True)

# Enhanced Sidebar
with st.sidebar:
    st.markdown("""
    <div class="sidebar-header">
        <div class="logo-container">
            <h1>Resume Expert Pro+</h1>
            <div class="logo-sparkle">✨</div>
        </div>
        <p class="tagline">AI-Powered Hiring Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    role = st.radio(
        "Select Your Role:",
        ["Applicant", "Interviewer"],
        key="role_select",
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    
    if role == "Applicant":
        st.markdown("### Quick Tips")
        with st.expander("💡 Resume Writing Tips"):
            st.write("""
            - Use action verbs (e.g., 'developed', 'managed')
            - Quantify achievements (e.g., 'Increased sales by 30%')
            - Tailor to each job description
            """)
    else:
        st.markdown("### Interviewer Tools")
        with st.expander("📊 Analysis Guide"):
            st.write("""
            - Upload multiple resumes
            - Add job description
            - Get ranked candidates
            - View detailed analysis
            """)
    
    st.markdown("""
    <div class="sidebar-footer">
        <div class="progress-tracker">
            <div class="progress-bar"></div>
            <span>System Status: Optimal</span>
        </div>
        <small>v2.3.0</small>
    </div>
    """, unsafe_allow_html=True)

# Main Content
if role == "Applicant":
    st.markdown("""
    <div class="header-container">
        <h1 class="main-header">Resume Optimization Studio</h1>
        <p class="subheader">Transform your resume into a job-winning document</p>
        <div class="header-decoration"></div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("🚀 How It Works", expanded=False):
        st.markdown("""
        <div class="steps-container">
            <div class="step">
                <div class="step-number">1</div>
                <div class="step-content">Enter job description</div>
            </div>
            <div class="step">
                <div class="step-number">2</div>
                <div class="step-content">Upload your resume</div>
            </div>
            <div class="step">
                <div class="step-number">3</div>
                <div class="step-content">Get AI-powered analysis</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1], gap="large")
    
    with col1:
        st.markdown("### 📝 Job Description")
        input_text = st.text_area(
            "Paste the job description here:",
            height=300,
            placeholder="Paste the complete job description you're applying for...",
            label_visibility="collapsed"
        )
    
    with col2:
        st.markdown("### 📄 Your Resume")
        uploaded_file = st.file_uploader(
            "Drag and drop or click to upload:",
            type=["pdf", "docx"],
            accept_multiple_files=False,
            help="We support PDF and DOCX formats",
            label_visibility="collapsed"
        )
        if uploaded_file:
            st.success("✅ File uploaded successfully!")
    
    st.markdown("---")
    st.markdown("### 🔍 Analysis Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        analyze_button = st.button(
            "📊 Comprehensive Analysis",
            help="Get detailed evaluation of your resume",
            use_container_width=True
        )
    
    with col2:
        match_button = st.button(
            "🔢 Match Score",
            help="Calculate ATS compatibility score",
            use_container_width=True
        )
    
    with col3:
        keyword_button = st.button(
            "🔑 Smart Keywords",
            help="Identify missing keywords",
            use_container_width=True
        )
    
    if analyze_button or match_button or keyword_button:
        if not input_text.strip():
            st.error("Please enter a job description")
        elif not uploaded_file:
            st.error("Please upload your resume")
        else:
            with st.spinner('🔍 Analyzing your resume...'):
                file_content = input_file_setup(uploaded_file)
                if file_content:
                    if analyze_button:
                        selected_prompt = prompts["analysis"]
                        action = "Comprehensive Analysis"
                    elif match_button:
                        selected_prompt = prompts["match"]
                        action = "Match Percentage"
                    else:
                        selected_prompt = prompts["keyword_analysis"]
                        action = "Keyword Analysis"
                    
                    response = get_gemini_response(input_text, file_content, selected_prompt)
                    
                    if response:
                        st.balloons()
                        st.markdown("---")
                        st.markdown("## 📋 Analysis Report")
                        
                        with st.expander("View Full Analysis", expanded=True):
                            if match_button or analyze_button:
                                percentage = extract_percentage_match(response)
                                if percentage is not None:
                                    color = "#4CAF50" if percentage >= 70 else "#FFC107" if percentage >= 50 else "#F44336"
                                    st.markdown(f"""
                                    <div class="match-container">
                                        <div class="match-circle" style="background: linear-gradient(135deg, {color}, #2196F3);">
                                            <span class="match-percentage">{percentage}%</span>
                                            <span class="match-label">Match Score</span>
                                        </div>
                                        <div class="score-feedback">
                                            {"> 85%: Excellent match!" if percentage >= 85 else 
                                             "70-84%: Good match" if percentage >= 70 else 
                                             "50-69%: Needs improvement" if percentage >= 50 else 
                                             "<50%: Significant improvements needed"}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="analysis-results">
                                {response}
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.download_button(
                            label="📥 Download Full Report",
                            data=response,
                            file_name=f"resume_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )
                        
                        log_user_action(action, response)

elif role == "Interviewer":
    st.markdown("""
    <div class="header-container">
        <h1 class="main-header">Interviewer Portal</h1>
        <p class="subheader">Efficient candidate screening powered by AI</p>
        <div class="header-decoration"></div>
    </div>
    """, unsafe_allow_html=True)
    
    with st.expander("📌 How to use the Interviewer Portal", expanded=False):
        st.markdown("""
        1. **Upload Job Description**: Provide the job description in PDF, TXT, or DOCX format.
        2. **Upload Resumes**: Add multiple candidate resumes in PDF format.
        3. **Analyze**: The system will rank candidates based on match percentage.
        4. **Review**: See detailed analysis and interactive visualizations.
        5. **Download**: Export the full report in PDF format.
        """)
    
    with st.container():
        st.markdown("### 📋 Job Description")
        job_desc_option = st.radio(
            "Job Description Input:",
            ["Text Input", "File Upload"],
            horizontal=True
        )
        
        job_description = ""
        
        if job_desc_option == "Text Input":
            job_description = st.text_area(
                "Enter job description text:",
                height=200,
                placeholder="Paste the complete job description here...",
                label_visibility="collapsed"
            )
        else:
            jd_file = st.file_uploader(
                "Upload job description file:",
                type=["pdf", "txt", "docx"],
                accept_multiple_files=False,
                help="Supported formats: PDF, TXT, DOCX",
                key="jd_uploader"
            )
            if jd_file:
                file_content = input_file_setup(jd_file)
                if file_content and file_content[0]["mime_type"] == "text/plain":
                    job_description = file_content[0]["data"]
                else:
                    st.error("Could not extract text from the job description file.")
    
    with st.container():
        st.markdown("### 📄 Candidate Resumes")
        resume_files = st.file_uploader(
            "Upload candidate resumes (PDF only):",
            type=["pdf"],
            accept_multiple_files=True,
            help="Upload multiple resumes in PDF format",
            key="resume_uploader"
        )
        
        if resume_files:
            st.success(f"✅ {len(resume_files)} resumes uploaded successfully!")
    
    if st.button("🚀 Analyze Candidates", use_container_width=True):
        if not job_description.strip():
            st.error("Please provide a job description")
        elif not resume_files or len(resume_files) == 0:
            st.error("Please upload at least one resume")
        else:
            resumes = {file.name: file for file in resume_files}
            analysis_results, match_percentages = analyze_resumes(job_description, resumes)
            
            if analysis_results and match_percentages:
                st.balloons()
                sorted_candidates = sorted(match_percentages.items(), key=lambda x: x[1], reverse=True)
                
                st.markdown("---")
                st.markdown("## 📊 Candidate Ranking")
                
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    st.markdown("### 🏆 Top Candidates")
                    for rank, (name, score) in enumerate(sorted_candidates, 1):
                        with st.container():
                            st.markdown(f"""
                            <div class="resume-card">
                                <div style="display: flex; align-items: center;">
                                    <span class="candidate-rank">#{rank}</span>
                                    <div>
                                        <strong>{name}</strong><br>
                                        Match Score: <strong>{score}%</strong>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("### 📈 Match Percentage Visualization")
                    fig = create_3d_graph(match_percentages)
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("## 🔍 Detailed Analysis")
                
                for name, analysis in analysis_results.items():
                    with st.expander(f"Analysis for {name} ({match_percentages[name]}%)", expanded=False):
                        st.markdown(f"""
                        <div class="analysis-results">
                            {analysis}
                        </div>
                        """, unsafe_allow_html=True)
                
                combined_analysis = "\n\n".join(
                    [f"=== {name} ===\n{analysis}" for name, analysis in analysis_results.items()]
                )
                
                pdf_report = create_pdf_report(combined_analysis, match_percentages)
                
                st.download_button(
                    label="📥 Download Full Analysis Report (PDF)",
                    data=pdf_report,
                    file_name=f"candidate_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

# Footer
st.markdown("---")
st.markdown("""
<div class="footer">
    <div class="footer-content">
        <p>🚀 Powered by Gemini AI • 🔒 Secure and confidential</p>
        <div class="social-links">
            <a href="#">Twitter</a> • <a href="#">LinkedIn</a> • <a href="#">Contact</a>
        </div>
        <small>© {datetime.now().year} Resume Expert Pro+. All rights reserved.</small>
    </div>
</div>
""", unsafe_allow_html=True)