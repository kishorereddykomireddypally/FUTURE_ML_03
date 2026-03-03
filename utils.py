import spacy
import fitz  # PyMuPDF
import re
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model...")
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# Common Skills Database (Expand as needed + Case Insensitive Matching Support)
SKILLS_DB = [
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi",
    "sql", "mysql", "postgresql", "mongodb", "aws", "azure", "docker", "kubernetes",
    "git", "machine learning", "deep learning", "nlp", "scikit-learn", "tensorflow",
    "pytorch", "pandas", "numpy", "matplotlib", "seaborn", "tableau", "power bi",
    "linux", "bash", "jenkins", "jira", "agile", "scrum", "excel"
]

def extract_contact_info(text):
    """
    Extracts email and phone number from text using Regex.
    """
    text = str(text)
    # Email Regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    
    # Phone Regex
    # Matches: +1-234-567-8900, (123) 456-7890, 123 456 7890, 123-456-7890
    phone_pattern = r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    phones = re.findall(phone_pattern, text)
    
    return {
        "email": ", ".join(set(emails)) if emails else "N/A",
        "phone": ", ".join(set(phones)) if phones else "N/A"
    }

def extract_text_from_pdf(file):
    """Extracts text from a PDF file object."""
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def clean_text(text):
    """
    Cleans the input text by:
    - Lowercasing
    - Removing special characters
    - Removing stopwords using spaCy
    - Lemmatization
    """
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = re.sub(r'[^a-z\s]', '', text)  # Keep only alphabets and spaces
    
    doc = nlp(text)
    cleaned_tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
    
    return " ".join(cleaned_tokens)

def load_data(file_path):
    """
    Loads candidate data from a CSV file.
    """
    try:
        df = pd.read_csv(file_path)
        # Ensure 'job_description' column exists, if not, try to find a relevant text column
        if 'job_description' not in df.columns:
            # Fallback or error if structure is different
            # For the provided dataset, 'job_description' seems correct based on view_file
            pass
        return df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def extract_skills(text):
    """
    Extracts skills from the text by matching with a predefined skills database.
    """
    doc = nlp(text.lower())
    found_skills = set()
    
    # Token matching
    for token in doc:
        if token.text in SKILLS_DB:
            found_skills.add(token.text)
            
    # Mwe (Multi-word expression) matching for skills like "machine learning"
    text_lower = text.lower()
    for skill in SKILLS_DB:
        if " " in skill and skill in text_lower:
             found_skills.add(skill)
             
    return list(found_skills)

def calculate_similarity(job_desc, resumes):
    """
    Calculates cosine similarity between job description and a list of resumes.
    Args:
        job_desc (str): The job description text.
        resumes (list of str): List of resume texts.
    Returns:
        list of float: Similarity scores corresponding to each resume.
    """
    documents = [job_desc] + resumes
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(documents)
    
    # Calculate cosine similarity between the first document (Job Desc) and the rest (Resumes)
    similarity_matrix = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    
    return similarity_matrix[0].tolist()
