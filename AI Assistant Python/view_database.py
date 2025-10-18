import sqlite3
import json
from datetime import datetime

def view_database():
    """View the contents of the duty officer assistant database"""
    try:
        conn = sqlite3.connect('duty_officer_assistant.db')
        cursor = conn.cursor()
        
        print("=" * 60)
        print("DUTY OFFICER ASSISTANT DATABASE CONTENTS")
        print("=" * 60)
        
        # Check knowledge base entries
        cursor.execute("SELECT COUNT(*) FROM knowledge_base")
        kb_count = cursor.fetchone()[0]
        print(f"\n📚 KNOWLEDGE BASE ENTRIES: {kb_count}")
        
        if kb_count > 0:
            cursor.execute("""
                SELECT id, title, category, type, source, created_at, 
                       LENGTH(content) as content_length, keywords, view_count
                FROM knowledge_base 
                ORDER BY created_at DESC
            """)
            
            entries = cursor.fetchall()
            for i, entry in enumerate(entries, 1):
                id, title, category, type, source, created_at, content_len, keywords, view_count = entry
                print(f"\n--- Entry #{i} ---")
                print(f"ID: {id}")
                print(f"Title: {title}")
                print(f"Category: {category or 'Not specified'}")
                print(f"Type: {type or 'Not specified'}")
                print(f"Source: {source}")
                print(f"Content Length: {content_len} characters")
                print(f"Keywords: {keywords[:100] + '...' if len(keywords) > 100 else keywords}")
                print(f"View Count: {view_count}")
                print(f"Created: {created_at}")
        
        # Check training data entries
        cursor.execute("SELECT COUNT(*) FROM training_data")
        td_count = cursor.fetchone()[0]
        print(f"\n🎯 TRAINING DATA ENTRIES: {td_count}")
        
        if td_count > 0:
            cursor.execute("""
                SELECT id, incident_description, expected_incident_type, 
                       expected_urgency, category, created_at
                FROM training_data 
                ORDER BY created_at DESC LIMIT 5
            """)
            
            entries = cursor.fetchall()
            for i, entry in enumerate(entries, 1):
                id, desc, inc_type, urgency, category, created_at = entry
                print(f"\n--- Training #{i} ---")
                print(f"ID: {id}")
                print(f"Description: {desc[:100]}{'...' if len(desc) > 100 else ''}")
                print(f"Type: {inc_type}")
                print(f"Urgency: {urgency}")
                print(f"Category: {category}")
                print(f"Created: {created_at}")
        
        conn.close()
        print("\n" + "=" * 60)
        print("Database location: duty_officer_assistant.db")
        print("=" * 60)
        
    except Exception as e:
        print(f"Error reading database: {e}")

if __name__ == "__main__":
    view_database()