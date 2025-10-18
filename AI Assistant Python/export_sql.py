import sqlite3
import json
from datetime import datetime

def export_database_to_sql():
    """Export the database contents to readable SQL format"""
    try:
        conn = sqlite3.connect('duty_officer_assistant.db')
        cursor = conn.cursor()
        
        print("-- =====================================================")
        print("-- DUTY OFFICER ASSISTANT DATABASE EXPORT")
        print(f"-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-- =====================================================")
        print()
        
        # Get table schemas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table_name in tables:
            table = table_name[0]
            print(f"-- ===== TABLE: {table.upper()} =====")
            
            # Get table schema
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE name='{table}'")
            schema = cursor.fetchone()
            if schema:
                print(f"-- Schema:")
                print(schema[0])
                print()
            
            # Get table data
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"-- Records: {count}")
            
            if count > 0:
                # Get column names
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [col[1] for col in cursor.fetchall()]
                
                # Get all data
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
                
                print(f"\n-- Data for {table}:")
                for i, row in enumerate(rows):
                    print(f"\n-- Record {i+1}:")
                    insert_values = []
                    for j, value in enumerate(row):
                        if value is None:
                            insert_values.append("NULL")
                        elif isinstance(value, str):
                            # Escape single quotes and truncate long content for display
                            escaped_value = value.replace("'", "''")
                            if len(escaped_value) > 200:
                                escaped_value = escaped_value[:200] + "...[TRUNCATED]"
                            insert_values.append(f"'{escaped_value}'")
                        else:
                            insert_values.append(str(value))
                    
                    column_list = "(" + ", ".join(columns) + ")"
                    values_list = "(" + ", ".join(insert_values) + ")"
                    print(f"INSERT INTO {table} {column_list}")
                    print(f"VALUES {values_list};")
            
            print(f"\n-- End of {table.upper()}")
            print("-" * 60)
            print()
        
        conn.close()
        print("-- =====================================================")
        print("-- END OF DATABASE EXPORT")
        print("-- =====================================================")
        
    except Exception as e:
        print(f"Error reading database: {e}")

def show_raw_content():
    """Show raw content without truncation"""
    try:
        conn = sqlite3.connect('duty_officer_assistant.db')
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("FULL CONTENT VIEW (Raw Data)")
        print("="*80)
        
        # Show knowledge base content in full
        cursor.execute("SELECT id, title, content, category, keywords, created_at FROM knowledge_base ORDER BY id")
        entries = cursor.fetchall()
        
        for entry in entries:
            id, title, content, category, keywords, created_at = entry
            print(f"\n{'='*60}")
            print(f"KNOWLEDGE ENTRY ID: {id}")
            print(f"TITLE: {title}")
            print(f"CATEGORY: {category}")
            print(f"CREATED: {created_at}")
            print(f"KEYWORDS: {keywords}")
            print(f"{'='*60}")
            print("FULL CONTENT:")
            print("-" * 60)
            print(content)
            print("-" * 60)
            print()
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Export as SQL statements")
    print("2. Show full raw content")
    print("3. Both")
    
    choice = input("Enter choice (1/2/3): ").strip()
    
    if choice in ['1', '3']:
        export_database_to_sql()
    
    if choice in ['2', '3']:
        show_raw_content()