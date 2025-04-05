
from flask import Flask, request, render_template, jsonify
import spacy
import PyPDF2
import docx
import os
import re
from fuzzywuzzy import fuzz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from threading import Thread

app = Flask(__name__, template_folder="templates")
nlp = spacy.load("en_core_web_sm")

# Predefined skill set
SKILL_SET = {
    "Python", "Machine Learning", "SQL", "Java", "C++", "C", "Data Structures",
    "Algorithms", "Excel", "PowerBi", "Tableau", "Deep Learning", "NLP",
    "Cloud Computing", "Cybersecurity", "Git", "TensorFlow", "PyTorch",
    "IoT", "Embedded Systems", "MongoDB", "NumPy", "Pandas", "Data Analytics",
    "Linux", "Firewalls", "Threat Analysis", "Encryption", "AWS", "Kubernetes",
    "Terraform", "Security", "RTOS", "Microcontrollers", "PCB Design", "UART",
    "SPI", "Firmware Development", "Ethereum", "Solidity", "Smart Contracts",
    "Cryptography", "HTML", "CSS", "VS Code", "GitHub", "MySQL", "React.js",
    "Node.js", "Express", "Neo4j", "Seaborn", "Matplotlib", "Networking",
    "DevOps", "Jenkins", "Docker", "Kotlin", "Swift", "Rust", "Go",
    "TypeScript", "Scala", "Hadoop", "Spark", "Snowflake", "Google Cloud",
    "Azure", "Agile", "Scrum", "Testing", "Selenium", "Jira", "Ansible",
    "Elasticsearch", "Kibana", "Grafana", "Flutter", "React Native", "Prometheus",
    "Unreal Engine", "Unity", "C#", "Automation Testing", "Bootstrap", "Django",
    "Flask", "FastAPI", "PySpark", "BigQuery", "PostgreSQL", "NoSQL", "REST API",
    "GraphQL", "Jupyter Notebook", "Mathematics", "Statistics",
}

# Alternative skill names mapping
ALTERNATIVE_NAMES = {
    "vs-code": "VS Code",
    "git": "Git",
    "github": "GitHub",
    "mysql": "MySQL",
    "data structures": "Data Structures",
    "react": "React.js",
    "node": "Node.js",
    "nodejs": "Node.js",
    "expressjs": "Express",
    "mongodb": "MongoDB",
    "c++": "C++",
    "c": "C"
}

# Job role skill mapping
JOB_ROLE_SKILLS = {
    "Data Scientist": ["Python", "Machine Learning", "SQL", "Deep Learning", "NLP", "TensorFlow"],
    "Software Engineer": ["Python", "Java", "C++", "Data Structures", "Algorithms", "Git"],
    "Data Analyst": ["SQL", "Excel", "PowerBi", "Tableau", "Python", "Data Visualization", "Statistics"],
    "Cybersecurity Analyst": ["Cybersecurity", "Linux", "Firewalls", "Threat Analysis", "Encryption"],
    "Cloud Engineer": ["Cloud Computing", "AWS", "Kubernetes", "Terraform", "Security"],
    "AI Engineer": ["Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch"],
    "Embedded Systems Engineer": ["C", "C++", "RTOS", "Embedded Linux", "Microcontrollers"],
    "IoT Engineer": ["IoT", "Embedded Systems", "Networking", "Cloud Computing"],
    "Backend Developer": ["Java", "SQL", "MongoDB", "Express", "Node.js", "Django", "Flask", "FastAPI"],
    "Blockchain Developer": ["Blockchain", "Ethereum", "Solidity", "Smart Contracts"],
    "DevOps Engineer": ["DevOps", "Jenkins", "Docker", "Kubernetes", "Terraform", "Ansible"],
    "Frontend Developer": ["JavaScript", "React.js", "CSS", "HTML", "TypeScript", "Bootstrap"],
    "Mobile Developer": ["Kotlin", "Swift", "Flutter", "React Native"],
    "Big Data Engineer": ["Hadoop", "Spark", "Snowflake", "Google Cloud", "Azure", "PySpark", "BigQuery"],
    "Site Reliability Engineer": ["Cloud Computing", "Kubernetes", "Terraform", "Grafana", "Prometheus"],
    "Game Developer": ["C++", "Unity", "Unreal Engine", "C#"],
    "Full Stack Developer": ["JavaScript", "Node.js", "React.js", "MongoDB", "Express", "HTML", "CSS", "Django", "Flask"],
    "Database Administrator": ["SQL", "PostgreSQL", "MongoDB", "NoSQL", "MySQL"],
    "Mathematician": ["Mathematics", "Statistics", "Python", "R", "Jupyter Notebook"]
}

# Load environment variables for LinkedIn
load_dotenv()
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")

# Selenium WebDriver Setup
options = webdriver.ChromeOptions()
options.add_argument("--disable-blink-features=AutomationControlled")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
wait = WebDriverWait(driver, 10)

# LinkedIn login function
def linkedin_login():
    """Logs into LinkedIn."""
    driver.get("https://www.linkedin.com/login")
    
    try:
        wait.until(EC.presence_of_element_located((By.NAME, "session_key"))).send_keys(LINKEDIN_EMAIL)
        driver.find_element(By.NAME, "session_password").send_keys(LINKEDIN_PASSWORD)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()
        wait.until(EC.url_contains("feed"))
        print("✅ Successfully logged into LinkedIn!")
    except Exception as e:
        print(f"❌ LinkedIn login failed: {e}")
        driver.quit()
        exit()

# LinkedIn scraping function
def scrape_linkedin_jobs(job_role, location, max_pages=3):
    job_listings = []
    linkedin_login()

    for page in range(max_pages):
        url = f"https://www.linkedin.com/jobs/search/?keywords={job_role}&location={location}&start={page * 25}"
        driver.get(url)
        
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "job-card-container")))
            jobs = driver.find_elements(By.CLASS_NAME, "job-card-container")

            if not jobs:
                print(f"❌ No jobs found on page {page + 1}. Stopping.")
                break

            for job in jobs:
                try:
                    title = job.find_element(By.CSS_SELECTOR, "a.job-card-container__link").text
                    company = job.find_element(By.CLASS_NAME, "artdeco-entity-lockup__subtitle").text
                    location = job.find_element(By.CLASS_NAME, "job-card-container__metadata-wrapper").text
                    job_link = job.find_element(By.CLASS_NAME, "job-card-container__link").get_attribute("href")

                    job_listings.append({
                        "Title": title,
                        "Company": company,
                        "Location": location,
                        "Job Link": job_link
                    })
                except Exception as e:
                    print(f"⚠️ Error scraping a job: {e}")
                    continue

            print(f"✅ Scraped Page {page + 1}")

        except Exception as e:
            print(f"❌ Error loading job listings on Page {page + 1}: {e}")

    return job_listings

# Flask route for job scraping
job_results = [] 
@app.route("/scrape_jobs", methods=["POST"])
def scrape_jobs():
    data = request.form
    job_role = data.get("job_role")
    location = data.get("location")

    if not job_role or not location:
        return jsonify({"error": "Job role and location are required"}), 400

    # Run scraping in a separate thread to avoid blocking
    def run_scraping():
        global job_results
        job_results = scrape_linkedin_jobs(job_role, location, max_pages=3)

    thread = Thread(target=run_scraping)
    thread.start()
    thread.join()

    return jsonify(job_results)

# Extract text from PDF
def extract_text_from_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + " "
    except Exception as e:
        return str(e)
    return text.strip()

# Extract text from DOCX
def extract_text_from_docx(file_path):
    try:
        doc = docx.Document(file_path)
        return " ".join([para.text for para in doc.paragraphs]).strip()
    except Exception as e:
        return str(e)

# Extract skills from text
def extract_skills(text):
    text = text.lower()

    # Extract skills within parentheses
    matches = re.findall(r"(\b\w+\b)\((.*?)\)", text)
    extracted_terms = set()

    for main_skill, sub_skills in matches:
        extracted_terms.add(main_skill.strip())
        sub_skills_list = [s.strip() for s in sub_skills.split(",")]
        extracted_terms.update(sub_skills_list)

    # Remove matched patterns from text
    text = re.sub(r"\b\w+\(.*?\)", "", text)

    # Replace alternative names
    for alt_name, correct_name in ALTERNATIVE_NAMES.items():
        text = text.replace(alt_name, correct_name.lower())

    # Use NLP for tokenization
    doc = nlp(text)
    detected_skills = set(token.text.strip().lower() for token in doc)

    # Use fuzzy matching to handle spelling errors
    for skill in SKILL_SET:
        skill_lower = skill.lower()
        for word in detected_skills:
            if fuzz.ratio(skill_lower, word) >= 80:
                extracted_terms.add(skill)

    return extracted_terms
def calculate_resume_score(extracted_skills, job_role):
    """Calculate a feature score for the resume based on the required skills for a job role."""
    if job_role not in JOB_ROLE_SKILLS:
        return 0  # Job role not found

    required_skills = set(JOB_ROLE_SKILLS[job_role])
    matching_skills = required_skills & extracted_skills

    # Calculate the score as a percentage of matching skills
    if len(required_skills) == 0:
        return 0  # Avoid division by zero
    score = (len(matching_skills) / len(required_skills)) * 100
    return round(score, 2)

# Existing Flask routes and functions remain the same
@app.route("/")
def index():
    return render_template("ind.html")

@app.route("/upload", methods=["POST"])
def upload_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files["resume"]
    file_ext = file.filename.split(".")[-1].lower()
    if file_ext not in ["pdf", "docx"]:
        return jsonify({"error": "Unsupported file format. Upload a PDF or DOCX file."}), 400
    
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    text = extract_text_from_pdf(file_path) if file_ext == "pdf" else extract_text_from_docx(file_path)
    extracted_skills = extract_skills(text)
    
    role_scores = {}
    related_roles = {}
    for role, required_skills in JOB_ROLE_SKILLS.items():
        matching_skills = set(required_skills) & extracted_skills
        score = calculate_resume_score(extracted_skills, role)
        if len(matching_skills) / len(required_skills) >= 0.5:
            missing_skills = list(set(required_skills) - extracted_skills)
            related_roles[role] = missing_skills
            role_scores[role] = score

    response = {
        "extracted_skills": list(extracted_skills),
        "role_scores": role_scores,
        "related_roles": related_roles
    }
    return jsonify(response)


if __name__ == "__main__":
    os.makedirs("uploads", exist_ok=True)
    app.run(debug=True,port=5004)