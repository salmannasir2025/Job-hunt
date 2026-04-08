from nicegui import ui
from agents import run_research, run_audit, run_draft, run_manager_check, authenticate_gmail, is_gmail_authenticated, get_gmail_service, find_contact_email, save_draft
from security_vault import set_key, get_key
import json
import os
import datetime
import validators

def log_progress(action):
    try:
        with open('progress.txt', 'r') as f:
            old = f.read()
    except FileNotFoundError:
        old = ''
    new_entry = f"{datetime.datetime.now()}: {action}\n"
    with open('progress.txt', 'w') as f:
        f.write(new_entry + old)

tracker_file = 'tracker.json'

def load_tracker():
    if os.path.exists(tracker_file):
        with open(tracker_file) as f:
            return json.load(f)
    return {'sent': 0, 'bounces': 0, 'leads': 0, 'companies': [], 'blacklist': []}

def save_tracker(data):
    with open(tracker_file, 'w') as f:
        json.dump(data, f)

tracker = load_tracker()

console_text = ''
results_area = None
results_count = None

def update_console(text):
    global console_text
    console_text += text + '\n'
    console.value = console_text


def append_results(text):
    global results_area
    if results_area is None:
        return
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    results_area.value = f'[{timestamp}] {text}\n\n' + results_area.value


def clear_results():
    global results_area, results_count
    if results_area is not None:
        results_area.value = ''
    if results_count is not None:
        results_count.text = 'Results: 0'
    update_console('Search results cleared')


def export_results():
    if results_area is None:
        update_console('No results available for export.')
        return
    export_path = 'search_results.txt'
    with open(export_path, 'w') as f:
        f.write(results_area.value)
    update_console(f'Results exported to {export_path}')
    log_progress('Search results exported')


def set_results_count(count):
    global results_count
    if results_count is not None:
        results_count.text = f'Results: {count}'


def research(portal, keywords, url):
    if url and not validators.url(url):
        update_console('Invalid URL provided')
        append_results('Invalid URL provided')
        return
    result = run_research(portal, keywords, url)
    formatted_result = f'Search use: Portal={portal or "Custom URL"}, Keywords={keywords}, URL={url or "N/A"}\n\n{result}'
    update_console('Research result returned successfully')
    append_results(formatted_result)
    log_progress(f"Research: Portal={portal}, Keywords={keywords}, URL={url}, Result={str(result)[:200]}")

    jobs = []
    if 'Title:' in result:
        lines = result.split('\n')
        for line in lines:
            if 'Title:' in line and 'Company:' in line:
                parts = line.split(', ')
                if len(parts) >= 2:
                    title = parts[0].replace('Title: ', '')
                    company = parts[1].replace('Company: ', '')
                    jobs.append((title, company))
    set_results_count(len(jobs) if jobs else 1)
    if not jobs:
        append_results('No structured job entries could be parsed from this result.')
    for title, company in jobs:
        job_info = f"Apply for {title} at {company}"
        audit_and_draft(job_info)

def audit_and_draft(job_info):
    # Parse job_info for title and company
    title = 'Job Application'
    company = 'Unknown'
    if 'Title:' in job_info and 'Company:' in job_info:
        parts = job_info.split(', ')
        for part in parts:
            if part.startswith('Title:'):
                title = part.replace('Title: ', '').strip()
            if part.startswith('Company:'):
                company = part.replace('Company: ', '').strip()
    elif 'at ' in job_info:
        company = job_info.split('at ')[1].strip()

    post_url = ''
    if 'Link:' in job_info:
        link_part = [p for p in job_info.split(', ') if p.startswith('Link:')]
        if link_part:
            post_url = link_part[0].replace('Link: ', '').strip()

    email = find_contact_email(company, post_url)
    if not email:
        update_console(f'No contact email discovered for {company}')
        append_results(f'No contact email discovered for {company}. Skipping draft.')
        return

    domain = email.split('@')[-1]
    audit_result = run_audit(company, domain, email)
    update_console(f'Audit: {audit_result}')
    if 'legit' in str(audit_result).lower() or 'valid' in str(audit_result).lower() or 'true' in str(audit_result).lower():
        draft_body = run_draft(job_info, tone_slider.value)
        if draft_body and 'Failed' not in draft_body:
            subject = f'Application for {title} at {company}'
            saved = save_draft(email, subject, draft_body)
            update_console(f'Draft saved: {saved}')
            tracker['sent'] += 1
            save_tracker(tracker)
            update_status()
        else:
            update_console('Draft generation failed, no Gmail draft saved')
    else:
        update_console('Audit did not verify the contact email. Draft not created.')

def update_status():
    status_label.text = f'Sent: {tracker["sent"]}, Bounces: {tracker["bounces"]}, Leads: {tracker["leads"]}'

# GUI
status_label = ui.label(f'Sent: {tracker["sent"]}, Bounces: {tracker["bounces"]}, Leads: {tracker["leads"]}')

with ui.tabs() as tabs:
    dashboard = ui.tab('Dashboard')
    quick_start = ui.tab('Quick Start')
    results = ui.tab('Results')
    job_hunt = ui.tab('Job Hunt')
    vault = ui.tab('The Vault')
    blacklist = ui.tab('Blacklist')

with ui.tab_panels(tabs, value=dashboard):
    with ui.tab_panel(dashboard):
        ui.label('Live Dashboard')

    with ui.tab_panel(quick_start):
        ui.markdown('''
### Quick Start Guide

**1. Vault Setup**
- Go to the **The Vault** tab.
- Enter password: `admin`.
- Save your **Groq API key**.
- Save the **Gmail `client_secret.json` path**.
- Click **Authenticate Gmail** and complete the browser popup.

**2. Start Job Hunt**
- Go to the **Job Hunt** tab.
- Select a portal or enter a custom URL.
- Add keywords and click **Research**.

**3. Review Outputs**
- Check the **Console** for agent steps.
- Drafts are saved to Gmail for review.
- Use the **Dashboard** to track sent emails, bounces, and leads.

**4. Bounce Recovery**
- The app scans your Gmail inbox for bounced messages automatically.
- Bounced companies are reprocessed through the Researcher and Ghostwriter agents.

**Tips**
- Keep your `client_secret.json` file path correct.
- Use the **Blacklist** tab to ignore companies or domains.
- Adjust the **Communication Tone** slider before drafting.

**Need help?**
- Check `README.md` or `BUILD.md` in the project folder.
- Ensure the app has permission to open browser authentication.
''')

    with ui.tab_panel(job_hunt):
        portal_select = ui.select(['All Portals', 'Indeed', 'LinkedIn', 'GulfTalent', 'Bayt'], label='Portal')
        keywords_input = ui.input('Keywords')
        url_input = ui.input('Custom URL')
        ui.button('Research', on_click=lambda: research(portal_select.value, keywords_input.value, url_input.value))

    with ui.tab_panel(results):
        ui.label('Search Results')
        results_count = ui.label('Results: 0')
        with ui.row().style('gap: 10px'):
            ui.button('Clear Results', on_click=clear_results)
            ui.button('Export Results', on_click=export_results)
        results_area = ui.textarea('', readonly=True, value='', rows=20, label='Search Results', width='100%')

    with ui.tab_panel(vault):
        password_input = ui.input('Password', password=True)
        unlock_button = ui.button('Unlock')
        vault_panel = ui.column()
        with vault_panel:
            # Groq API Key Section
            ui.label('🔑 Groq API Configuration').classes('font-bold')
            groq_input = ui.input('Groq API Key', password=True)
            ui.button('Save Groq Key', on_click=lambda: (set_key('groq_api_key', groq_input.value), log_progress("Groq API key saved"), update_console("Groq API key saved successfully")))
            
            # Gmail Authentication Section
            ui.label('📧 Gmail Authentication').classes('font-bold')
            gmail_status = ui.label('Status: Not Authenticated')
            
            def check_gmail_status():
                if is_gmail_authenticated():
                    gmail_status.text = '✅ Status: Gmail Authenticated'
                else:
                    gmail_status.text = '❌ Status: Not Authenticated'
            
            def open_gmail_auth():
                client_secret_path = get_key('client_secret_path')
                if not client_secret_path or not os.path.exists(client_secret_path):
                    update_console("Error: client_secret.json path not set. Save path first.")
                    return
                update_console("Opening Gmail authentication in browser...")
                log_progress("Gmail authentication initiated - browser popup opening")
                creds, svc = authenticate_gmail(client_secret_path)
                if creds and svc:
                    update_console("✅ Gmail authenticated successfully!")
                    log_progress("Gmail authentication successful")
                    check_gmail_status()
                else:
                    update_console("❌ Gmail authentication failed")
                    log_progress("Gmail authentication failed")
            
            ui.button('Authenticate Gmail (Opens Browser)', on_click=open_gmail_auth).classes('bg-blue-500')
            ui.button('Check Status', on_click=check_gmail_status)
            
            # Client Secret Path Section
            ui.label('🔐 Client Secret Configuration').classes('font-bold')
            client_secret_input = ui.input('Client Secret JSON Path')
            def save_client_secret_and_log():
                set_key('client_secret_path', client_secret_input.value)
                log_progress("Client secret path saved")
                update_console("Client secret path saved successfully")
            ui.button('Save Client Secret Path', on_click=save_client_secret_and_log)
            
            # Load previously saved paths if available
            saved_secret = get_key('client_secret_path')
            if saved_secret:
                client_secret_input.value = saved_secret
            
            check_gmail_status()  # Check status on panel load
        
        vault_panel.visible = False
        def unlock():
            if password_input.value == 'admin':  # Simple password
                vault_panel.visible = True
                update_console("Vault unlocked")
        unlock_button.on_click(unlock)

    with ui.tab_panel(blacklist):
        blacklist_text = ui.textarea('Blacklisted Companies/Domains', value='\n'.join(tracker['blacklist']))
        ui.button('Save Blacklist', on_click=lambda: (tracker.update({'blacklist': blacklist_text.value.split('\n')}), save_tracker(tracker), log_progress("Blacklist updated")))

tone_slider = ui.slider(0.1, 1.0, 0.5, label='Communication Tone')

console = ui.textarea('Console', readonly=True, value=console_text)

# Startup check
update_console('Initializing Manager check for bounces...')
log_progress("Manager bounce check initiated")
bounces = run_manager_check()
update_console(f'Bounces found: {len(bounces)}')
log_progress(f"Bounce check completed: {len(bounces)} bounces found")

def run_gui():
    log_progress("GUI launched")
    ui.run()
