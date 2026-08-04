import sqlite3
import os
import requests
import json
from datetime import datetime
import time
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

DB_NAME = 'ecoshop.db'
BACKUP_DIR = 'backups'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_google_drive_service():
    """Authenticate and return Google Drive service"""
    creds = None
    
    # Token file stores the user's access and refresh tokens
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("❌ credentials.json not found!")
                print("📌 Please download credentials.json from Google Cloud Console")
                print("📌 Place it in the root folder of your project")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('drive', 'v3', credentials=creds)

def upload_to_drive(file_path, folder_id=None):
    """Upload file to Google Drive"""
    try:
        service = get_google_drive_service()
        if not service:
            return None
        
        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(file_path, mimetype='application/octet-stream')
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, webViewLink'
        ).execute()
        
        print(f"✅ Uploaded to Google Drive:")
        print(f"   File ID: {file.get('id')}")
        print(f"   Link: https://drive.google.com/file/d/{file.get('id')}/view")
        return file.get('id')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None

def create_backup():
    """Create a backup of the database"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'ecoshop_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    
    try:
        if os.path.exists(DB_NAME):
            with open(DB_NAME, 'rb') as src:
                with open(backup_path, 'wb') as dst:
                    dst.write(src.read())
            print(f"✅ Backup created: {backup_name}")
            return backup_path
        else:
            print("⚠️ No database to backup")
            return None
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        return None

def list_backups():
    """List all available backups"""
    if not os.path.exists(BACKUP_DIR):
        return []
    
    backups = []
    for f in os.listdir(BACKUP_DIR):
        if f.startswith('ecoshop_backup_') and f.endswith('.db'):
            path = os.path.join(BACKUP_DIR, f)
            size = os.path.getsize(path)
            modified = datetime.fromtimestamp(os.path.getmtime(path))
            backups.append({
                'name': f,
                'path': path,
                'size': size,
                'date': modified
            })
    return sorted(backups, key=lambda x: x['date'], reverse=True)

def get_db_stats():
    """Get database statistics"""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        stats = {}
        tables = ['products', 'sales', 'customers', 'employees', 'categories']
        for table in tables:
            c.execute(f'SELECT COUNT(*) FROM {table}')
            stats[table] = c.fetchone()[0]
        conn.close()
        return stats
    except:
        return None

def auto_backup(upload_to_drive=False):
    """Auto backup on every sale or important action"""
    backup_path = create_backup()
    if backup_path:
        # Upload to Google Drive if requested
        if upload_to_drive:
            print("📤 Uploading to Google Drive...")
            upload_to_drive(backup_path)
        
        # Keep only last 10 backups to save space
        backups = list_backups()
        if len(backups) > 10:
            for old_backup in backups[10:]:
                try:
                    os.remove(old_backup['path'])
                    print(f"🗑️ Removed old backup: {old_backup['name']}")
                except:
                    pass
        return backup_path
    return None

def restore_from_backup(backup_path):
    """Restore database from backup"""
    try:
        if os.path.exists(backup_path):
            with open(backup_path, 'rb') as src:
                with open(DB_NAME, 'wb') as dst:
                    dst.write(src.read())
            print(f"✅ Database restored from: {backup_path}")
            return True
    except Exception as e:
        print(f"❌ Restore failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 50)
    print("📊 EcoShop Backup Tool")
    print("=" * 50)
    
    # Check credentials
    if not os.path.exists(CREDENTIALS_FILE):
        print("⚠️ credentials.json not found!")
        print("📌 Please:")
        print("   1. Go to https://console.cloud.google.com")
        print("   2. Enable Google Drive API")
        print("   3. Create OAuth 2.0 credentials (Desktop app)")
        print("   4. Download credentials.json to this folder")
        print("=" * 50)
        exit()
    
    # Show database stats
    stats = get_db_stats()
    if stats:
        print("📊 Current database stats:")
        for table, count in stats.items():
            print(f"   {table}: {count}")
    else:
        print("⚠️ No database found!")
    
    print("=" * 50)
    
    # Ask user what to do
    print("Options:")
    print("1. Create backup only")
    print("2. Create backup and upload to Google Drive")
    print("3. List available backups")
    print("4. Restore from backup")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == '1':
        backup_path = auto_backup(upload_to_drive=False)
        if backup_path:
            print(f"✅ Backup saved to: {backup_path}")
    
    elif choice == '2':
        backup_path = auto_backup(upload_to_drive=True)
        if backup_path:
            print(f"✅ Backup saved and uploaded!")
    
    elif choice == '3':
        backups = list_backups()
        if backups:
            print("📋 Available backups:")
            for b in backups:
                size_kb = b['size'] / 1024
                print(f"   {b['name']} ({size_kb:.2f} KB, {b['date'].strftime('%Y-%m-%d %H:%M')})")
        else:
            print("📋 No backups found")
    
    elif choice == '4':
        backups = list_backups()
        if backups:
            print("📋 Available backups:")
            for i, b in enumerate(backups):
                print(f"   {i+1}. {b['name']} ({b['date'].strftime('%Y-%m-%d %H:%M')})")
            
            try:
                idx = int(input("Select backup number: ")) - 1
                if 0 <= idx < len(backups):
                    restore_from_backup(backups[idx]['path'])
                else:
                    print("❌ Invalid selection")
            except:
                print("❌ Invalid input")
        else:
            print("📋 No backups found")
    
    else:
        print("❌ Invalid choice")
    
    print("=" * 50)
    print("✅ Done!")