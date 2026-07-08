import psycopg2
import os

# Using the provided connection string (removing brackets if present)
conn_str = "postgresql://postgres:Naqiyoroob4@db.krwwiyhsknfsdiqxazmi.supabase.co:5432/postgres"

print("Connecting to database...")
try:
    conn = psycopg2.connect(conn_str)
    conn.autocommit = True
    cur = conn.cursor()
    
    with open('schema.sql', 'r') as f:
        schema = f.read()
    
    # We create tables
    print("Executing schema...")
    cur.execute(schema)
    print("Schema executed successfully!")
    
    cur.close()
    conn.close()
except Exception as e:
    print(f"Error: {e}")
