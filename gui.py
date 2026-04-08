from nicegui import ui
from agents import run_research, run_audit, run_draft, run_manager_check, authenticate_gmail, is_gmail_authenticated, get_gmail_service
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

def update_console(text):
    global console_text
    console_text += text + '\n'
    console.value = console_text

def research(portal, keywords, url):
    if url and not validators.url(url):
        update_console('Invalid URL provided')
        return
    result = run_research(portal, keywords, url)
    update_console(f'Research result: {result}')
    log_progress(f"Research: Portal={portal}, Keywords={keywords}, URL={url}, Result={str(result)[:200]}")
    # Parse jobs and process
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
    for title, company in jobs:
        job_info = f"Apply for {title} at {company}"
        audit_and_draft(job_info)

def audit_and_draft(job_info):
    # Parse job_info for company
    if 'at ' in job_info:
        company = job_info.split('at ')[1].strip()
    else:
        company = 'Unknown'
    domain = company.lower().replace(' ', '').replace(',', '') + '.com'
    email = 'hr@' + domain
    audit_result = run_audit(company, domain, email)
    update_console(f'Audit: {audit_result}')
    if 'legit' in str(audit_result).lower() or 'valid' in str(audit_result).lower():  # Improved check
        draft = run_draft(job_info, tone_slider.value)
        update_console(f'Draft: {draft}')
        tracker['sent'] += 1
        save_tracker(tracker)
        update_status()

def update_status():
    status_label.text = f'Sent: {tracker["sent"]}, Bounces: {tracker["bounces"]}, Leads: {tracker["leads"]}'

# GUI
status_label = ui.label(f'Sent: {tracker["sent"]}, Bounces: {tracker["bounces"]}, Leads: {tracker["leads"]}')

with ui.tabs() as tabs:
    dashboard = ui.tab('Dashboard')
    quick_start = ui.tab('Quick Start')
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
        portal_select = ui.select(['Indeed', 'LinkedIn', 'GulfTalent'], label='Portal')
        keywords_input = ui.input('Keywords')
        url_input = ui.input('Custom URL')
        ui.button('Research', on_click=lambda: research(portal_select.value, keywords_input.value, url_input.value))

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
