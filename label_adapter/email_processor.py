from pathlib import Path
import os
import imaplib

def email_login(email_address, password, imap_server, imap_port, logger):
    logger.debug('Attempting email login')
    mail = imaplib.IMAP4_SSL(imap_server, imap_port)
    mail.login(email_address, password)
    if mail:
        logger.debug('Email login successful')
    else:
        logger.error('Email login unsuccessful')
    return mail

def email_logout(mail, logger):
    logger.debug('Attempting email logout')
    mail.logout()
    logger.debug("Successfully logged out")

def download_csv_attachments(mail, sender_email, download_folder, logger):
    # Search for emails from the specific sender
    INBOX = 'inbox'
    PROCESSED = 'processed'
    downloaded = {} # filename, email_id
    logger.debug('Downloading email attachments')
    mail.select(INBOX)
    logger.debug(f'Searching for emails from {sender_email}')
    status, data = mail.search(None, '(FROM "{}")'.format(sender_email))
    logger.debug(f'Status: {status}, Data: {data}')
    email_ids = data[0].split()
    logger.debug(f'Email IDs: {email_ids}')

    for email_id in email_ids:
        # Fetch the email
        logger.debug(f'Fetching email with ID {email_id}')
        status, data = mail.fetch(email_id, '(RFC822)')
        logger.debug(f'Status: {status}')
        raw_email = data[0][1]

        # Parse the email
        email_message = email.message_from_bytes(raw_email)

        #print(f'Email_message: {email_message}')
        logger.debug(f'Checking for attachments...')
        # Check if the email has attachments
        if email_message.get_content_maintype() =='multipart':
            logger.debug(f'Multipart:True')
            for part in email_message.walk():
                logger.debug(f'content_maintype: {part.get_content_maintype()}')
                logger.debug(f'content_subtype: {part.get_content_subtype()}')
                if part.get_content_maintype() == 'text' and part.get_content_subtype() == 'csv':
                    logger.debug(f'Has CSV')
                    # Download the CSV attachment
                    email_id_str = email_id.decode('utf-8')
                    filename = f'{email_id_str}_{part.get_filename()}'
                    logger.debug(f'Filename: {filename}')
                    Path(download_folder).mkdir(parents=True, exist_ok=True)
                    download_path = os.path.join(download_folder, filename)
                    with open(download_path, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    downloaded[download_path] = email_id
                    logger.debug('Downloaded:', download_path)
    
    move_processed_emails(mail, downloaded.values(), PROCESSED, logger)

    return downloaded.keys()

def move_processed_emails(mail, downloaded_email_ids,  destination_folder, logger):
    logger.debug('Attempting to move processed emails')
    status, mailboxes = mail.list()  # Retrieve all mailboxes first
    if status == "OK":
        # Iterate through the list to find our destination folder
        for mailbox in mailboxes:
            # Manually extract the mailbox name
            mailbox_name = mailbox.decode('utf-8').split('"')[-2]
            # Remove leading/trailing '/' if present (depending on the IMAP server)
            mailbox_name = mailbox_name.strip('/')
            if mailbox_name == destination_folder:
                logger.debug(f"Folder '{destination_folder}' already exists.")
                break
        else:
            logger.info(f"email folder '{destination_folder}' does not exist. Creating it...")
            # Attempt to create the folder
            status, response = mail.create(destination_folder)
            if status == "OK":
                logger.info(f"Folder '{destination_folder}' created successfully.")
            else:
                logger.error(f"Failed to create folder '{destination_folder}': {response.decode()}")
                return
    else:
        logger.error(f"Failed to retrieve mailbox list: {mail.response()[0].decode()}")
        return

    logger.debug("Moving processed emails to '{}'...".format(destination_folder))
    for email_id in downloaded_email_ids:
        mail.copy(email_id, destination_folder)  # Copy to destination
        mail.store(email_id, '+FLAGS', '\\Deleted')  # Mark original for deletion
    mail.expunge()  # Permanently remove deleted items from inbox
    logger.debug("Emails moved.")    