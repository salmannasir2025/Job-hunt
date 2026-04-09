from crewai import Agent, Task, Crew
from crewai.tools import tool
from security_vault import get_key
from email_client import get_email_client  # NEW: rich Gmail client
import os
import requests
from bs4 import BeautifulSoup
from crawl4ai import Crawl4AI
import whois
import validators
import re
from groq import Groq

# ---------------------------------------------------------------------------
# API key bootstrap
# ---------------------------------------------------------------------------
groq_key = get_key('groq_api_key')

# ---------------------------------------------------------------------------
# Gmail – thin wrappers over EmailClient (keeps gui.py import surface intact)
# ---------------------------------------------------------------------------

def authenticate_gmail(client_secret_path: str = None):
    """
    Authenticate with Gmail via the EmailClient singleton.

    Returns a (creds, service) tuple for backward-compatibility with gui.py,
    or (None, None) on failure.
    """
    client = get_email_client()
    ok = client.authenticate(client_secret_path)
    if ok:
        return client.creds, client.service
    return None, None


def get_gmail_service():
    """Return the underlying Gmail service from the EmailClient singleton."""
    return get_email_client().service


def is_gmail_authenticated() -> bool:
    """Return True when the EmailClient singleton is authenticated."""
    return get_email_client().is_authenticated()


def find_emails_in_text(text: str) -> list:
    emails = re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', text)
    return list(dict.fromkeys(emails))


def normalize_domain(company: str) -> str:
    normalized = re.sub(r'[^a-z0-9]', '', company.lower())
    return f'{normalized}.com'


def find_contact_email(company: str, url: str = None) -> str:
    candidates = []
    if url:
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            candidates.extend(find_emails_in_text(response.text))
        except Exception as e:
            print(f'Contact email fetch failed: {e}')

    domain = normalize_domain(company)
    common_prefixes = ['hr', 'careers', 'jobs', 'apply', 'recruitment', 'contact', 'info']
    for prefix in common_prefixes:
        email = f'{prefix}@{domain}'
        if validators.email(email):
            candidates.append(email)

    return candidates[0] if candidates else ''


# Tools
@tool
def scrape_portal(portal: str, keywords: str) -> str:
    def parse_job_entry(title, company, link=''):
        entry = f'Title: {title}, Company: {company}'
        if link:
            entry += f', Link: {link}'
        return entry

    if portal == 'All Portals':
        portals = ['Indeed', 'GulfTalent', 'Bayt', 'LinkedIn']
        results = []
        for p in portals:
            results.append(f'--- {p} ---')
            results.append(scrape_portal(p, keywords))
        return '\n'.join(results)

    if portal == 'Indeed':
        url = f'https://ae.indeed.com/jobs?q={keywords.replace(' ', '+')}'
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('div', class_='job_seen_beacon')
        results = []
        for job in jobs[:8]:
            title_elem = job.find('h2')
            company_elem = job.find('span', class_='companyName')
            link_elem = job.find('a', href=True)
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                link = f"https://ae.indeed.com{link_elem['href']}" if link_elem else ''
                results.append(parse_job_entry(title, company, link))
        return '\n'.join(results)

    if portal == 'GulfTalent':
        url = f'https://www.gulftalent.com/uae/jobs/search?keywords={keywords.replace(' ', '+')}'
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('a', class_='job-card-link') or soup.find_all('li', class_='search-result')
        results = []
        for job in jobs[:8]:
            title_elem = job.find('h2') or job.find('span', class_='job-title')
            company_elem = job.find('div', class_='company-name') or job.find('span', class_='company')
            link = job['href'] if job.has_attr('href') else ''
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                if link and not link.startswith('http'):
                    link = f'https://www.gulftalent.com{link}'
                results.append(parse_job_entry(title, company, link))
        return '\n'.join(results)

    if portal == 'Bayt':
        url = f'https://www.bayt.com/en/uae/jobs/search/?keywords={keywords.replace(' ', '+')}'
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('article', class_='job-card') or soup.find_all('div', class_='search-result')
        results = []
        for job in jobs[:8]:
            title_elem = job.find('h2') or job.find('a', class_='job-card-title')
            company_elem = job.find('div', class_='company') or job.find('span', class_='company-name')
            link_elem = job.find('a', href=True)
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                link = link_elem['href'] if link_elem else ''
                if link and not link.startswith('http'):
                    link = f'https://www.bayt.com{link}'
                results.append(parse_job_entry(title, company, link))
        return '\n'.join(results)

    if portal == 'LinkedIn':
        url = f'https://www.linkedin.com/jobs/search?keywords={keywords.replace(' ', '%20')}'
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        jobs = soup.find_all('li', class_='result-card') or soup.find_all('div', class_='base-search-card')
        results = []
        for job in jobs[:8]:
            title_elem = job.find('h3') or job.find('span', class_='screen-reader-text')
            company_elem = job.find('h4') or job.find('a', class_='result-card__subtitle-link')
            link_elem = job.find('a', href=True)
            if title_elem and company_elem:
                title = title_elem.text.strip()
                company = company_elem.text.strip()
                link = link_elem['href'] if link_elem else ''
                results.append(parse_job_entry(title, company, link))
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
def save_draft(to_email: str, subject: str, body: str) -> str:
    """Save a composed email as a Gmail draft via EmailClient."""
    client = get_email_client()
    if not client.is_authenticated():
        return 'Gmail not configured'
    draft_id = client.save_draft(to=to_email, subject=subject, body=body)
    return f'Draft saved (id={draft_id})' if draft_id else 'Draft save failed'

@tool
def check_bounces() -> list:
    """Scan the inbox for bounce notifications via EmailClient."""
    client = get_email_client()
    if not client.is_authenticated():
        return []
    emails = client.search('from:mailer-daemon OR subject:bounce', limit=20)
    return [e.snippet for e in emails]

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
