# AI Powered Resume Ranker

## Overview

**AI Powered Resume Ranker** is a web application that utilizes advanced AI models to evaluate and rank resumes based on job descriptions. It provides detailed analysis, match percentages, and keyword recommendations to help applicants improve their resumes and assist interviewers in identifying the best candidates.

## Features

- **Resume Analysis**: Get detailed professional evaluations of resumes against job descriptions.
- **Match Percentage Calculation**: Determine how well a resume matches the job description, with a percentage score and suggestions for improvement.
- **Keyword Analysis**: Identify missing keywords in resumes and suggest areas for improvement.
- **Interviewer Portal**: Analyze and compare multiple resumes to find the most suitable candidates for a job role.
- **Visualization**: Visualize match percentage distribution with pie charts.

## Technologies Used

- **Frontend**: [Streamlit](https://streamlit.io/) for creating an interactive user interface.
- **Backend**: Python-based processing and integration with the **Google Generative AI (Gemini)** API.
- **Libraries**:
  - `dotenv` for managing environment variables
  - `Pillow` for image processing
  - `pdf2image` for PDF-to-image conversion
  - `docx` for working with Word documents
  - `matplotlib` and `pandas` for data visualization and analysis

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 12 or higher
- Google API Key for the Gemini AI model

### Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/ai-powered-resume-ranker.git
   cd ai-powered-resume-ranker
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies:
   ```bash
   npm install
   ```

4. Configure the environment:
   - Create a `.env` file in the root directory.
   - Add your Google API key:
     ```
     GOOGLE_API_KEY=your_api_key_here
     ```

5. Run the application:
   ```bash
   streamlit run main.py
   ```

## Usage

1. Launch the app locally using Streamlit.
2. Select your role as either **Applicant** or **Interviewer**.
3. Upload resumes and job descriptions to receive AI-powered insights.
4. Use the analysis tools to improve resumes or identify suitable candidates.

## File Structure

- `main.py`: The core application logic, including AI integration and Streamlit UI.
- `package.json` and `package-lock.json`: Node.js configuration files for dependency management.
- `.env`: File to store environment variables (not included in the repository for security).

## Future Enhancements

- Integration with more ATS platforms.
- Support for additional file formats like TXT.
- Enhanced visualization features for deeper insights.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.


