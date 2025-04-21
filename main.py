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

# Load environment variables from .env file
load_dotenv()

# Configure the Gemini API with your API key from environment variables
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Google API key not found in environment variables.")

genai.configure(api_key=API_KEY)

# Function to generate response from Gemini AI
def get_gemini_response(input_text, pdf_content, prompt):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content([input_text, pdf_content[0], prompt])
        return response.text
    except Exception as e:
        st.error(f"Error generating response: {str(e)}")
        return None

# Function to process uploaded files (PDF or DOCX)
def input_file_setup(uploaded_file):
    try:
        if uploaded_file.type == "application/pdf":
            # Convert the PDF to images using pdf2image
            images = pdf2image.convert_from_bytes(uploaded_file.read(), dpi=200)
            
            # Get the first page as a JPEG image
            first_page = images[0]
            img_byte_arr = io.BytesIO()
            first_page.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            # Encode the image in base64 for passing to the model
            file_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(img_byte_arr).decode()  # encode to base64
                }
            ]
            return file_parts
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            # Process DOCX files
            doc = Document(uploaded_file)
            doc_text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            file_parts = [
                {
                    "mime_type": "text/plain",
                    "data": doc_text
                }
            ]
            return file_parts
        else:
            st.error("Unsupported file format. Please upload a PDF or DOCX file.")
            return None
    except Exception as e:
        st.error(f"Error processing file: {str(e)}")
        return None

# Function to log user actions and responses
def log_user_action(action, response):
    with open("user_activity_log.txt", "a") as log_file:
        log_file.write(f"{datetime.now()} - {action} - Response: {response}\n")

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

# Function to extract percentage match from the response
def extract_percentage_match(response):
    try:
        match = re.search(r'(\d{1,3})%\s', response)
        if match:
            return int(match.group(1))
        return None
    except:
        return None

# Streamlit app setup
st.set_page_config(page_title="Resume Expert", page_icon="📝", layout="wide")

# User Role Selection
role = st.sidebar.selectbox("Select Role:", ["Applicant", "Interviewer"])

if role == "Applicant":
    st.title("AI-Powered Resume Ranker - Applicant Portal")
    st.markdown(
        """
        This portal allows applicants to analyze their resumes against job descriptions. Upload your resume in PDF or DOCX format and input a job description to get started.
        """
    )

    # Input fields for job description and uploaded resume (PDF or DOCX)
    input_text = st.text_area("Enter the Job Description:", height=200, key="input_text")
    uploaded_file = st.file_uploader("Upload your Resume (PDF or DOCX):", type=["pdf", "docx"], key="uploaded_file")

    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        analyze_button = st.button("Analyze Resume")
    with col2:
        match_button = st.button("Calculate Match Percentage")
    with col3:
        keyword_button = st.button("Keyword Analysis")

    # Handle button clicks
    if analyze_button or match_button or keyword_button:
        # Validate inputs
        if not input_text.strip():
            st.error("Please enter a job description.")
        elif not uploaded_file:
            st.error("Please upload a resume (PDF or DOCX).")
        else:
            with st.spinner('Processing your request, please wait...'):
                # Convert uploaded file to base64 content or plain text
                file_content = input_file_setup(uploaded_file)
                if file_content:
                    # Choose the appropriate prompt
                    if analyze_button:
                        selected_prompt = prompts["analysis"]
                        action = "Analyze Resume"
                    elif match_button:
                        selected_prompt = prompts["match"]
                        action = "Calculate Match Percentage"
                    elif keyword_button:
                        selected_prompt = prompts["keyword_analysis"]
                        action = "Keyword Analysis"

                    # Get response from Gemini AI
                    response = get_gemini_response(input_text, file_content, selected_prompt)
                    if response:
                        st.subheader("AI Response")
                        st.write(response)

                        # Option to download the response
                        st.download_button(
                            label="Download Response",
                            data=response,
                            file_name="ai_response.txt",
                            mime="text/plain"
                        )

                        # Log user action
                        log_user_action(action, response)

elif role == "Interviewer":
    st.title("AI-Powered Resume Ranker - Interviewer Portal")
    st.markdown(
        """
        This portal allows interviewers to review and analyze applicants' resumes. Upload resumes and job descriptions to receive AI-powered insights.
        """
    )

    uploaded_files = st.file_uploader("Upload Applicants' Resumes (PDF or DOCX):", type=["pdf", "docx"], accept_multiple_files=True, key="uploaded_resumes")
    job_description_file = st.file_uploader("Upload Job Description (DOCX or TXT):", type=["docx", "txt"], key="uploaded_job_description")

    if st.button("Analyze Resumes for Interview"):
        if not uploaded_files or not job_description_file:
            st.error("Please upload resumes and the job description.")
        else:
            with st.spinner('Processing the files...'):
                job_description_content = input_file_setup(job_description_file)
                if job_description_content:
                    results = []
                    for file in uploaded_files:
                        resume_content = input_file_setup(file)
                        if resume_content:
                            # Use match prompt for analysis
                            prompt = prompts["match"]
                            response = get_gemini_response(
                                job_description_content[0]["data"], resume_content, prompt
                            )
                            if response:
                                # Extract percentage match from the response
                                percentage_match = extract_percentage_match(response)
                                results.append({
                                    "Candidate": file.name,
                                    "Match Percentage": percentage_match if percentage_match is not None else "N/A",
                                    "Response": response
                                })

                    if results:
                        # Display results in a table
                        df = pd.DataFrame(results)
                        st.subheader("Comparison Results")
                        st.dataframe(df)

                        # Visualize results with a pie chart
                        pie_data = df[df["Match Percentage"] != "N/A"]
                        pie_data = pie_data["Match Percentage"].astype(int)

                        if not pie_data.empty:
                            plt.figure(figsize=(6, 6))
                            pie_data.plot(kind='pie', labels=df["Candidate"], autopct='%1.1f%%', startangle=140)
                            plt.title("Match Percentage Distribution")
                            st.pyplot(plt)

                        # Highlight candidates suitable for hiring
                        threshold = 70
                        df["Match Percentage"] = pd.to_numeric(df["Match Percentage"], errors="coerce")
                        suitable_candidates = df[df["Match Percentage"] >= threshold]
                        if not suitable_candidates.empty:
                            st.subheader("Suitable Candidates for Hiring")
                            st.write(suitable_candidates["Candidate"].tolist())
                        else:
                            st.write("No candidates meet the hiring threshold.")

# Footer
st.markdown("---")
st.caption("Empowering career growth with advanced AI solutions. 🚀")