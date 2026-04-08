from crewai import Agent, Task, Crew
from crewai.tools import tool
from security_vault import get_key
import os
import requests
from bs4 import BeautifulSoup
from crawl4ai import Crawl4AI
import whois
import validators
from groq import Groq
import googleapiclient.discovery
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import base64
import webbrowser

# Set API keys
groq_key = get_key('groq_api_key')
if groq_key:
    # os.environ['GROQ_API_KEY'] = groq_key  # Removed for security

# For Gmail - Initialize as None, will be set during authentication
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.drafts']
creds = None
service = None

def authenticate_gmail(client_secret_path):
    """
    Authenticate with Gmail using browser popup with account selection.
    Opens browser for user to select Gmail account and authorize.
    Returns: (credentials object, service object) or (None, None) on failure
    """
    global creds, service
    try:
        token_path = 'token.json'
        
        # Check if token already exists
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            if creds and creds.valid:
                service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
                return creds, service
            elif creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
                return creds, service
        
        # If no valid token, create new flow with browser popup
        if not os.path.exists(client_secret_path):
            return None, None
        
        flow = InstalledAppFlow.from_client_secrets_file(client_secret_path, SCOPES)
        # Run local server with browser popup (opens in default browser with account selection)
        creds = flow.run_local_server(port=8080, open_browser=True)
        
        # Save credentials for future use
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
        
        service = googleapiclient.discovery.build('gmail', 'v1', credentials=creds)
        return creds, service
    except Exception as e:
        print(f"Gmail authentication failed: {str(e)}")
        return None, None

def get_gmail_service():
    """Get the current Gmail service instance"""
    return service

def is_gmail_authenticated():
    """Check if Gmail is currently authenticated"""
    return service is not None and creds is not None

# Tools
@tool
def scrape_portal(portal: str, keywords: str) -> str:
    if portal == 'Indeed':
        url = f'https://ae.indeed.com/jobs?q={keywords.replace(" ", "+")}'
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('div', class_='job_seen_beacon')
        results = []
        for job in jobs[:5]:
            title_elem = job.find('h2')
            company_elem = job.find('span', class_='companyName')
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                results.append(f'Title: {title}, Company: {company}')
        return '\n'.join(results)
    return 'Scraping not implemented for this portal'

@tool
def crawl_url(url: str) -> str:
    try:
        crawler = Crawl4AI()
        result = crawler.crawl(url)
        return result.text
    except:
        return 'Failed to crawl'

@tool
def check_whois(domain: str) -> str:
    try:
        w = whois.whois(domain)
        return str(w)
    except:
        return 'Invalid domain'

@tool
def validate_email(email: str) -> bool:
    return validators.email(email)

@tool
def draft_email(job_info: str, tone: float) -> str:
    try:
        client = Groq(api_key=groq_key)
        prompt = f'Draft a human-like email for job application based on: {job_info}. Tone level: {tone} (0.1 formal, 1.0 creative). Max 8 lines, no AI clichés, end with UAE-specific closing like "Best regards from Dubai".'
        response = client.chat.completions.create(
            model='llama3-8b-8192',
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response.choices[0].message.content
    except:
        return 'Failed to draft'

@tool
def save_draft(content: str) -> str:
    if service:
        draft = {'message': {'raw': base64.urlsafe_b64encode(content.encode()).decode()}}
        service.users().drafts().create(userId='me', body=draft).execute()
        return 'Draft saved'
    return 'Gmail not configured'

@tool
def check_bounces() -> list:
    if service:
        results = service.users().messages().list(userId='me', q='from:mailer-daemon OR subject:bounce').execute()
        messages = results.get('messages', [])
        bounces = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            bounces.append(msg_data['snippet'])
        return bounces
    return []

# Agents
researcher = Agent(
    role='Researcher',
    goal='Find job listings and contact emails from portals or custom URLs',
    backstory='Expert in web scraping and job market research',
    tools=[scrape_portal, crawl_url],
    verbose=True
)

auditor = Agent(
    role='Auditor',
    goal='Verify company legitimacy and email validity',
    backstory='Cybersecurity specialist for job scam detection',
    tools=[check_whois, validate_email],
    verbose=True
)

ghostwriter = Agent(
    role='Ghostwriter',
    goal='Draft personalized, human-like outreach emails',
    backstory='Professional writer crafting authentic job application emails',
    tools=[draft_email, save_draft],
    verbose=True
)

manager = Agent(
    role='Manager',
    goal='Orchestrate the team and handle email bounce recovery',
    backstory='Project manager coordinating job search efforts and recovery processes',
    tools=[check_bounces],
    verbose=True
)

# Functions
def run_research(portal, keywords, url):
    if url:
        task = Task(description=f'Crawl the custom URL {url} to extract job titles and contact emails', agent=researcher)
    else:
        task = Task(description=f'Scrape {portal} for job listings matching keywords: {keywords}', agent=researcher)
    crew = Crew(agents=[researcher], tasks=[task])
    return crew.kickoff()

def run_audit(company, domain, email):
    task = Task(description=f'Perform legitimacy check on company {company}, domain {domain}, email {email}', agent=auditor)
    crew = Crew(agents=[auditor], tasks=[task])
    return crew.kickoff()

def run_draft(job_info, tone):
    task = Task(description=f'Draft an email for job: {job_info} with tone {tone}', agent=ghostwriter)
    crew = Crew(agents=[ghostwriter], tasks=[task])
    return crew.kickoff()

def run_manager_check():
    task = Task(description='Scan inbox for bounced emails and identify companies for recovery', agent=manager)
    crew = Crew(agents=[manager], tasks=[task])
    return crew.kickoff()
