from utils import extract_skills, calculate_similarity, clean_text, extract_contact_info

# Sample Data
job_desc = "We need a python developer with machine learning and sql skills."
resume_1 = "I am a python developer with experience in machine learning and deep learning. Contact: john@example.com, +1-555-0199."
resume_2 = "I am a java developer with sql experience. Phone: 123-456-7890."

# Test Cleaning
print("Original Job Desc:", job_desc)
cleaned_jd = clean_text(job_desc)
print("Cleaned Job Desc:", cleaned_jd)

# Test Skill Extraction
skills_jd = extract_skills(job_desc)
print("Extracted Skills (JD):", skills_jd)

skills_r1 = extract_skills(resume_1)
print("Extracted Skills (R1):", skills_r1)

# Test Contact Extraction
print("Contact Info R1:", extract_contact_info(resume_1))
print("Contact Info R2:", extract_contact_info(resume_2))

# Test Ranking
scores = calculate_similarity(cleaned_jd, [clean_text(resume_1), clean_text(resume_2)])
print("Similarity Scores:", scores)
