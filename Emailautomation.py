import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ipywidgets as widgets
from IPython.display import display
import re
import csv
import imaplib
from email.header import decode_header
import datetime
import pytz
import threading


# =============================================================================
# INSTRUCTIONS:
# Follow the steps below to set up and send your emails:
#
# Step 1: Default Account Setup
#  - Enter your email address and password.
#  - Click "Validate Email & Password" to check your credentials.
#  - Click "Confirm Default Account" to add it.
#
# Step 2: Compose Your Email
#  - Enter the subject and body of your email.
#  - Use {first_name} in the body to personalize each message.
#
# Step 3: Configure Follow-Up Emails (Optional)
#  - Provide content and delay settings for up to three follow-up emails.
#  - Enable or disable each follow-up by checking/unchecking the box.
#
# Step 4: Scheduling (Optional)
#  - Set the hour and minute if you wish to schedule the sending.
#
# Step 5: Upload Recipient CSV File
#  - The CSV file should include recipient details.
#  - The script expects the first column to be the first name and the third column the email address.
#
# Step 6: Set Recipient Timezone
#  - Select the recipient's timezone from the dropdown.
#
# Step 7: Send or Schedule Emails
#  - Click "Send Emails Now" to start sending emails immediately,
#    or "Schedule Emails" to wait until the scheduled time.
#
# Step 8: Manage Additional Email Accounts
#  - Use "+ Add Another Email Account" to add more accounts.
#
# Step 9: Manage Confirmed Email Accounts
#  - Update the daily sending limit or remove an account as needed.
#
# =============================================================================


# =============================
# Campaign Tracking Global Counters
# =============================
new_emails_sent = 0
followup_emails_sent = 0
total_emails_sent = 0
responses_received_list = []
total_followups_possible = 0  # computed later based on enabled follow-ups


# Global list of valid recipient emails (used by the response polling thread)
valid_emails = []


# =============================
# Response Polling Globals
# =============================
polling_active = False
response_poll_thread = None


# =============================
# Campaign Tracking UI Widgets
# =============================
campaign_tracking_header = widgets.HTML("<b>Campaign Tracking</b>")
total_emails_sent_label = widgets.Label(value="Total Emails Sent: 0")
remaining_emails_label = widgets.Label(value="Remaining Emails: New: 0, Follow-ups: 0")
responses_received_label = widgets.Label(value="Responses Received: None")
campaign_tracker_box = widgets.VBox([
    campaign_tracking_header,
    total_emails_sent_label,
    remaining_emails_label,
    responses_received_label
])


def update_campaign_tracker(total_sent, remaining_new, remaining_followups, responses):
    total_emails_sent_label.value = f"Total Emails Sent: {total_sent}"
    remaining_emails_label.value = f"Remaining Emails: New: {remaining_new}, Follow-ups: {remaining_followups}"
    if responses:
        responses_received_label.value = "Responses Received: " + ", ".join(responses)
    else:
        responses_received_label.value = "Responses Received: None"


# =============================
# Step 1: Default Account Setup
# =============================
step1_label = widgets.HTML("<b>Step 1: Default Account Setup</b><br>"
                             "Enter your email address and password below, then validate and confirm your default account.")


default_email = "itsankitkushpoul@gmail.com"
default_password = "vjrd xamm vghq vnpf"


email_address_input = widgets.Text(
    description="Email Address:",
    value=default_email,
    tooltip="Enter your email address here."
)
email_password_input = widgets.Password(
    description="Password:",
    value=default_password,
    tooltip="Enter your email password here."
)
validate_button = widgets.Button(
    description="Validate Email & Password",
    tooltip="Click to validate your email credentials."
)
confirm_default_button = widgets.Button(
    description="Confirm Default Account",
    tooltip="Click to confirm and add your default account."
)
validation_status = widgets.Label(
    value="",
    tooltip="This will show the status after validation."
)


# =============================
# Step 2: Compose Your Email
# =============================
step2_label = widgets.HTML("<b>Step 2: Compose Your Email</b><br>"
                             "Enter the subject and main body of your email. Use {first_name} as a placeholder for personalization.")
subject_input = widgets.Text(
    description="Subject:",
    tooltip="Enter the subject of your email."
)
email_body_input = widgets.Textarea(
    description="Email Body:",
    layout=widgets.Layout(width='50%', height='150px'),
    tooltip="Enter the main body text of your email."
)


# =============================
# Step 3: Configure Follow-Up Emails (Optional)
# =============================
step3_label = widgets.HTML("<b>Step 3: Configure Follow-Up Emails (Optional)</b><br>"
                             "Enter content for up to three follow-up emails and set the delay for each. Check the box to enable a follow-up.")


follow_up_1_body_input = widgets.Textarea(
    description="Follow-up 1 Body:",
    layout=widgets.Layout(width='50%', height='150px'),
    tooltip="Enter the body for your first follow-up email."
)
follow_up_1_interval_value_input = widgets.IntText(
    value=1,
    description="Delay:",
    tooltip="Enter delay value for Follow-up 1."
)
follow_up_1_interval_unit_input = widgets.Dropdown(
    options=['Day(s)', 'Hour(s)', 'Minute(s)', 'Second(s)'],
    value='Day(s)',
    description="Unit:",
    tooltip="Select time unit for Follow-up 1 delay."
)
follow_up_1_checkbox = widgets.Checkbox(
    value=True,
    description="Follow-up 1",
    tooltip="Check to send Follow-up 1 email."
)


follow_up_2_body_input = widgets.Textarea(
    description="Follow-up 2 Body:",
    layout=widgets.Layout(width='50%', height='150px'),
    tooltip="Enter the body for your second follow-up email."
)
follow_up_2_interval_value_input = widgets.IntText(
    value=2,
    description="Delay:",
    tooltip="Enter delay value for Follow-up 2."
)
follow_up_2_interval_unit_input = widgets.Dropdown(
    options=['Day(s)', 'Hour(s)', 'Minute(s)', 'Second(s)'],
    value='Day(s)',
    description="Unit:",
    tooltip="Select time unit for Follow-up 2 delay."
)
follow_up_2_checkbox = widgets.Checkbox(
    value=True,
    description="Follow-up 2",
    tooltip="Check to send Follow-up 2 email."
)


follow_up_3_body_input = widgets.Textarea(
    description="Follow-up 3 Body:",
    layout=widgets.Layout(width='50%', height='150px'),
    tooltip="Enter the body for your third follow-up email."
)
follow_up_3_interval_value_input = widgets.IntText(
    value=3,
    description="Delay:",
    tooltip="Enter delay value for Follow-up 3."
)
follow_up_3_interval_unit_input = widgets.Dropdown(
    options=['Day(s)', 'Hour(s)', 'Minute(s)', 'Second(s)'],
    value='Day(s)',
    description="Unit:",
    tooltip="Select time unit for Follow-up 3 delay."
)
follow_up_3_checkbox = widgets.Checkbox(
    value=True,
    description="Follow-up 3",
    tooltip="Check to send Follow-up 3 email."
)


# =============================
# Step 4: Scheduling (Optional)
# =============================
step4_label = widgets.HTML("<b>Step 4: Scheduling (Optional)</b><br>"
                             "Set the hour and minute if you wish to schedule the sending.")
hour_dropdown = widgets.IntSlider(
    value=12,
    min=0,
    max=23,
    step=1,
    description="Hour (24h):",
    tooltip="Select the hour (in 24h format)."
)
minute_dropdown = widgets.IntSlider(
    value=0,
    min=0,
    max=59,
    step=1,
    description="Minute:",
    tooltip="Select the minute."
)
interval_input = widgets.IntText(
    value=20,
    description="Interval (sec):",
    tooltip="Enter the interval in seconds between sending emails."
)


# =============================
# Step 5: Upload Recipient CSV File
# =============================
step5_label = widgets.HTML("<b>Step 5: Upload Recipient CSV File</b><br>"
                             "Upload a CSV file with recipient details. The first column should be the first name and the third column the email address.")
file_upload = widgets.FileUpload(
    description="Upload File",
    accept=".csv",
    tooltip="Upload a CSV file with recipient information."
)


# =============================
# Step 6: Set Recipient Timezone
# =============================
step6_label = widgets.HTML("<b>Step 6: Set Recipient Timezone</b><br>"
                             "Select the recipient's timezone from the dropdown below.")
recipient_timezone_dropdown = widgets.Dropdown(
    options=sorted(pytz.all_timezones),
    value='UTC',
    description='Timezone:',
    tooltip="Select the recipient's timezone."
)


# =============================
# Step 7: Send or Schedule Emails
# =============================
step7_label = widgets.HTML("<b>Step 7: Send or Schedule Emails</b><br>"
                             "Click 'Send Emails Now' to start sending emails immediately, or 'Schedule Emails' to schedule the sending.")
send_button = widgets.Button(
    description="Send Emails Now",
    tooltip="Click to send emails immediately."
)
schedule_button = widgets.Button(
    description="Schedule Emails",
    tooltip="Click to schedule emails based on the recipient's timezone and scheduled time."
)


# =============================
# Step 8: Manage Additional Email Accounts
# =============================
step8_label = widgets.HTML("<b>Step 8: Manage Additional Email Accounts</b><br>"
                             "If you wish to use more than one account, click '+ Add Another Email Account' and enter its credentials.")
add_email_button = widgets.Button(
    description="+ Add Another Email Account",
    tooltip="Click to add another email account."
)
email_accounts_container = widgets.VBox()


# =============================
# Step 9: Manage Confirmed Email Accounts
# =============================
step9_label = widgets.HTML("<b>Step 9: Manage Confirmed Email Accounts</b><br>"
                             "Below are your confirmed email accounts. You can update the daily sending limit or remove an account as needed.")
confirmed_email_accounts_container = widgets.VBox()
confirmed_email_accounts_label = widgets.Label(
    value="Confirmed Email Accounts:",
    tooltip="This section shows all confirmed email accounts."
)


# =============================
# Helper Functions
# =============================
def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def convert_to_seconds(value, unit):
    if unit == 'Day(s)':
        return value * 86400
    elif unit == 'Hour(s)':
        return value * 3600
    elif unit == 'Minute(s)':
        return value * 60
    elif unit == 'Second(s)':
        return value


def check_for_reply(email_address, email_password, recipient_email):
    """
    Check the inbox for a reply from the given recipient.
    """
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(email_address, email_password)
        mail.select('inbox')
        status, messages = mail.search(None, f'FROM "{recipient_email}"')
        if status == 'OK':
            email_ids = messages[0].split()
            if email_ids:
                return True
        mail.logout()
    except imaplib.IMAP4.error as e:
        print(f"IMAP Error: {e}. Ensure IMAP is enabled in your email settings.")
        return False
    except Exception as e:
        print(f"Error checking for replies: {e}")
        return False
    return False


# =============================
# Email Sending Functions
# =============================
def send_follow_up_email(sender_account, recipient_email, follow_up_body, first_name):
    if not follow_up_body.strip():
        print(f"Skipping empty follow-up email to {recipient_email}")
        return


    personalized_body = follow_up_body.replace("{first_name}", first_name)
    msg = MIMEMultipart()
    msg['From'] = sender_account["email"]
    msg['To'] = recipient_email
    msg['Subject'] = subject_input.value.strip()
    msg.attach(MIMEText(personalized_body, 'plain'))
   
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_account["email"], sender_account["password"])
        server.sendmail(sender_account["email"], recipient_email, msg.as_string())
        server.quit()
        print(f"Sent follow-up email to: {recipient_email}")
        global followup_emails_sent, total_emails_sent
        followup_emails_sent += 1
        total_emails_sent += 1
        remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
        remaining_new = len(valid_emails) - new_emails_sent
        update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)
    except Exception as e:
        print(f"Error sending follow-up email to {recipient_email}: {e}")


def send_emails_immediately(b):
    global new_emails_sent, followup_emails_sent, total_emails_sent, responses_received_list, total_followups_possible, valid_emails, polling_active, response_poll_thread


    subject = subject_input.value.strip()
    email_body = email_body_input.value.strip()
    follow_up_1_body = follow_up_1_body_input.value.strip()
    follow_up_2_body = follow_up_2_body_input.value.strip()
    follow_up_3_body = follow_up_3_body_input.value.strip()
    uploaded_file = file_upload.value
    interval = interval_input.value


    follow_up_1_interval_seconds = convert_to_seconds(follow_up_1_interval_value_input.value, follow_up_1_interval_unit_input.value)
    follow_up_2_interval_seconds = convert_to_seconds(follow_up_2_interval_value_input.value, follow_up_2_interval_unit_input.value)
    follow_up_3_interval_seconds = convert_to_seconds(follow_up_3_interval_value_input.value, follow_up_3_interval_unit_input.value)


    if not uploaded_file:
        print("Please upload a CSV file containing the email addresses.")
        return


    email_addresses = []
    first_names = []
    for filename, file_info in uploaded_file.items():
        try:
            decoded = file_info['content'].decode('utf-8')
            reader = csv.reader(decoded.splitlines())
            for i, row in enumerate(reader):
                if i == 0:
                    continue
                if len(row) >= 3:
                    first_name = row[0].strip()
                    email = row[2].strip()
                    email_addresses.append(email)
                    first_names.append(first_name)
        except Exception as e:
            print(f"Error reading the file: {e}")
            return


    # Set global valid_emails so that poll_responses can use it.
    valid_emails = [email for email in email_addresses if is_valid_email(email)]
    if not valid_emails:
        print("No valid email addresses to send emails.")
        return


    total_followups_possible = 0
    if follow_up_1_checkbox.value and follow_up_1_body:
        total_followups_possible += 1
    if follow_up_2_checkbox.value and follow_up_2_body:
        total_followups_possible += 1
    if follow_up_3_checkbox.value and follow_up_3_body:
        total_followups_possible += 1


    # Reset campaign counters
    new_emails_sent = 0
    followup_emails_sent = 0
    total_emails_sent = 0
    responses_received_list = []
    update_campaign_tracker(total_emails_sent, len(valid_emails), (total_followups_possible * len(valid_emails)), responses_received_list)


    # Print selected recipient timezone (for information)
    selected_timezone = recipient_timezone_dropdown.value
    print(f"Emails will be scheduled based on the recipient's timezone: {selected_timezone}")


    email_account_usage = {account["email"]: 0 for account in email_accounts}


    for i, recipient in enumerate(valid_emails):
        first_name = first_names[i]
        sender_account = None
        for account in email_accounts:
            if email_account_usage[account["email"]] < account["limit"]:
                sender_account = account
                break
        if sender_account is None:
            print("All email accounts have reached their daily new email limits. Pausing email sending until the next day.")
            return


        personalized_body = email_body.replace("{first_name}", first_name)
        msg = MIMEMultipart()
        msg['From'] = sender_account["email"]
        msg['To'] = recipient
        msg['Subject'] = subject
        msg.attach(MIMEText(personalized_body, 'plain'))


        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_account["email"], sender_account["password"])
            server.sendmail(sender_account["email"], recipient, msg.as_string())
            server.quit()
            print(f"Sent email to: {recipient} from {sender_account['email']}")
            email_account_usage[sender_account["email"]] += 1
            new_emails_sent += 1
            total_emails_sent += 1
            remaining_new = len(valid_emails) - new_emails_sent
            remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
            update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)
        except Exception as e:
            print(f"Error sending email to {recipient} from {sender_account['email']}: {e}")
            continue


        time.sleep(interval)


        if follow_up_1_checkbox.value and follow_up_1_body:
            time.sleep(follow_up_1_interval_seconds)
            if not check_for_reply(sender_account["email"], sender_account["password"], recipient):
                send_follow_up_email(sender_account, recipient, follow_up_1_body, first_name)
            else:
                print(f"Recipient {recipient} has replied. Skipping follow-up 1.")
                if recipient not in responses_received_list:
                    responses_received_list.append(recipient)
                remaining_new = len(valid_emails) - new_emails_sent
                remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
                update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)


        if follow_up_2_checkbox.value and follow_up_2_body:
            time.sleep(follow_up_2_interval_seconds)
            if not check_for_reply(sender_account["email"], sender_account["password"], recipient):
                send_follow_up_email(sender_account, recipient, follow_up_2_body, first_name)
            else:
                print(f"Recipient {recipient} has replied. Skipping follow-up 2.")
                if recipient not in responses_received_list:
                    responses_received_list.append(recipient)
                remaining_new = len(valid_emails) - new_emails_sent
                remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
                update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)


        if follow_up_3_checkbox.value and follow_up_3_body:
            time.sleep(follow_up_3_interval_seconds)
            if not check_for_reply(sender_account["email"], sender_account["password"], recipient):
                send_follow_up_email(sender_account, recipient, follow_up_3_body, first_name)
            else:
                print(f"Recipient {recipient} has replied. Skipping follow-up 3.")
                if recipient not in responses_received_list:
                    responses_received_list.append(recipient)
                remaining_new = len(valid_emails) - new_emails_sent
                remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
                update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)


    print("All emails sent successfully!")
   
    # Start a background thread to continuously poll for responses (if not already running)
    if not polling_active:
        polling_active = True
        response_poll_thread = threading.Thread(target=poll_responses, daemon=True)
        response_poll_thread.start()


# =============================
# Response Polling Function
# =============================
def poll_responses():
    """
    Continuously poll all email accounts for responses from recipients.
    If a new response is detected, update the global responses_received_list and the campaign tracker.
    """
    global responses_received_list, valid_emails, new_emails_sent, followup_emails_sent, total_emails_sent, polling_active
    while polling_active:
        for account in email_accounts:
            for recipient in valid_emails:
                if recipient not in responses_received_list:
                    if check_for_reply(account["email"], account["password"], recipient):
                        responses_received_list.append(recipient)
                        remaining_new = len(valid_emails) - new_emails_sent
                        remaining_followups = (total_followups_possible * len(valid_emails)) - followup_emails_sent
                        update_campaign_tracker(total_emails_sent, remaining_new, remaining_followups, responses_received_list)
        time.sleep(30)  # poll every 30 seconds


# =============================
# Account Validation and Confirmation Functions
# =============================
def validate_credentials_click(b):
    email_address = email_address_input.value.strip()
    email_password = email_password_input.value.strip()


    if not email_address or not email_password:
        validation_status.value = "Please enter your email address and password."
        return


    if not is_valid_email(email_address):
        validation_status.value = "The email address format is invalid."
        return


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(email_address, email_password)
        server.quit()
        validation_status.value = "Email address and password are valid."
    except smtplib.SMTPAuthenticationError:
        validation_status.value = "Invalid email address or password. Please check your credentials."
    except Exception as e:
        validation_status.value = f"An error occurred during validation: {e}"


def confirm_default_account_click(b):
    email_address = email_address_input.value.strip()
    email_password = email_password_input.value.strip()
    if validation_status.value != "Email address and password are valid.":
        validation_status.value = "Please validate the default account first."
        return
    if any(account["email"] == email_address for account in email_accounts):
        validation_status.value = "Default account is already confirmed."
        return
    email_accounts.append({"email": email_address, "password": email_password, "limit": 30})
    update_confirmed_accounts_display()
    validation_status.value = "Default account confirmed."


def add_email_account(b):
    global email_account_widgets
    email_widget = widgets.Text(
        description="Email Address:",
        layout=widgets.Layout(width='50%'),
        tooltip="Enter the email address for the new account."
    )
    password_widget = widgets.Password(
        description="Password:",
        layout=widgets.Layout(width='50%'),
        tooltip="Enter the password for the new account."
    )
    validate_btn = widgets.Button(
        description="Validate",
        layout=widgets.Layout(width='20%'),
        tooltip="Click to validate these credentials."
    )
    confirm_btn = widgets.Button(
        description="Confirm",
        layout=widgets.Layout(width='20%'),
        tooltip="Click to confirm and add this account."
    )
    status_label = widgets.Label(
        value="",
        tooltip="This will show the status after validating the new account."
    )


    def validate_credentials(b):
        email = email_widget.value.strip()
        password = password_widget.value.strip()
        if not email or not password:
            status_label.value = "Please enter email and password."
            return
        if not is_valid_email(email):
            status_label.value = "Invalid email format."
            return
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(email, password)
            server.quit()
            status_label.value = "Valid credentials."
        except smtplib.SMTPAuthenticationError:
            status_label.value = "Invalid credentials."
        except Exception as e:
            status_label.value = f"Error: {e}"


    def confirm_account(b):
        email = email_widget.value.strip()
        password = password_widget.value.strip()
        if email and password and status_label.value == "Valid credentials.":
            email_accounts.append({"email": email, "password": password, "limit": 30})
            update_confirmed_accounts_display()
            status_label.value = "Account confirmed."
        else:
            status_label.value = "Cannot confirm. Validate credentials first."


    validate_btn.on_click(validate_credentials)
    confirm_btn.on_click(confirm_account)


    email_account_widgets.append((email_widget, password_widget, validate_btn, confirm_btn, status_label))
    email_accounts_container.children = list(email_accounts_container.children) + \
        [widgets.HBox([email_widget, password_widget, validate_btn, confirm_btn, status_label])]


# =============================
# Confirmed Accounts Management UI
# =============================
def update_confirmed_accounts_display():
    items = []
    for i, account in enumerate(email_accounts):
        email_label = widgets.Label(
            value=account["email"],
            layout=widgets.Layout(width='200px'),
            tooltip="This is the email address of the account."
        )
        limit_input = widgets.IntText(
            value=account["limit"],
            description="Daily Limit:",
            layout=widgets.Layout(width='150px'),
            tooltip="Set the maximum number of new emails this account can send per day."
        )
        update_button = widgets.Button(
            description="Update",
            layout=widgets.Layout(width='80px'),
            tooltip="Click to update the daily limit for this account."
        )
        remove_button = widgets.Button(
            description="Remove",
            layout=widgets.Layout(width='80px'),
            tooltip="Click to remove this account."
        )
       
        def update_limit(b, index=i, limit_input=limit_input):
            try:
                new_limit = int(limit_input.value)
                if new_limit < 1:
                    print("Daily limit must be positive.")
                else:
                    email_accounts[index]["limit"] = new_limit
                    print(f"Updated limit for {email_accounts[index]['email']} to {new_limit}")
            except Exception as e:
                print("Error updating limit:", e)
               
        def remove_account(b, index=i):
            removed_email = email_accounts[index]["email"]
            del email_accounts[index]
            update_confirmed_accounts_display()
            print(f"Removed account: {removed_email}")
       
        update_button.on_click(update_limit)
        remove_button.on_click(remove_account)
        hbox = widgets.HBox([email_label, limit_input, update_button, remove_button])
        items.append(hbox)
    confirmed_email_accounts_container.children = items


# =============================
# Global Variables for Accounts
# =============================
email_accounts = []      
email_account_widgets = []  


# =============================
# Scheduling Functionality
# =============================
def schedule_emails(b):
    """
    Schedule the email sending based on the selected recipient timezone,
    scheduled hour, and minute.
    """
    tz_str = recipient_timezone_dropdown.value
    recipient_tz = pytz.timezone(tz_str)
    now = datetime.datetime.now(recipient_tz)
    scheduled_hour = hour_dropdown.value
    scheduled_minute = minute_dropdown.value
    scheduled_time = now.replace(hour=scheduled_hour, minute=scheduled_minute, second=0, microsecond=0)
    if scheduled_time < now:
        scheduled_time += datetime.timedelta(days=1)
    wait_seconds = (scheduled_time - now).total_seconds()
    print(f"Emails scheduled to be sent at {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_str}).")
    print(f"Waiting for {int(wait_seconds)} seconds...")
    scheduled_status = widgets.Label(value=f"Waiting until {scheduled_time.strftime('%Y-%m-%d %H:%M:%S')} ({tz_str}) to send emails.")
    display(scheduled_status)
    time.sleep(wait_seconds)
    print("Scheduled time reached. Starting to send emails now...")
    send_emails_immediately(None)


# =============================
# Bind Button Actions
# =============================
validate_button.on_click(validate_credentials_click)
confirm_default_button.on_click(confirm_default_account_click)
send_button.on_click(send_emails_immediately)
schedule_button.on_click(schedule_emails)
add_email_button.on_click(add_email_account)


# =============================
# Display All Widgets with Instructions, Campaign Tracker, and Recipient Timezone Setting
# =============================
display(
    # Step 1: Default Account Setup
    step1_label,
    email_address_input, email_password_input, validate_button, confirm_default_button, validation_status,
    widgets.HTML("<hr>"),
    # Step 2: Compose Your Email
    step2_label,
    subject_input, email_body_input,
    widgets.HTML("<hr>"),
    # Step 3: Configure Follow-Up Emails
    step3_label,
    follow_up_1_body_input, follow_up_1_interval_value_input, follow_up_1_interval_unit_input, follow_up_1_checkbox,
    follow_up_2_body_input, follow_up_2_interval_value_input, follow_up_2_interval_unit_input, follow_up_2_checkbox,
    follow_up_3_body_input, follow_up_3_interval_value_input, follow_up_3_interval_unit_input, follow_up_3_checkbox,
    widgets.HTML("<hr>"),
    # Step 4: Scheduling (Optional)
    step4_label,
    hour_dropdown, minute_dropdown, interval_input,
    widgets.HTML("<hr>"),
    # Step 5: Upload Recipient CSV File
    step5_label,
    file_upload,
    widgets.HTML("<hr>"),
    # Step 6: Set Recipient Timezone
    step6_label,
    recipient_timezone_dropdown,
    widgets.HTML("<hr>"),
    # Step 7: Send or Schedule Emails
    step7_label,
    send_button, schedule_button,
    widgets.HTML("<hr>"),
    # Step 8: Manage Additional Email Accounts
    step8_label,
    email_accounts_container, add_email_button,
    widgets.HTML("<hr>"),
    # Step 9: Manage Confirmed Email Accounts
    step9_label,
    confirmed_email_accounts_label, confirmed_email_accounts_container,
    widgets.HTML("<hr>"),
    # Campaign Tracking Display
    campaign_tracker_box
)



