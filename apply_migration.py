#!/usr/bin/env python3
"""
Apply migration 008 to Supabase database
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Read migration file
with open("docs/migrations/008_article_comparison.sql", "r") as f:
    migration_sql = f.read()

# Apply migration via Supabase REST API
url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
    "Content-Type": "application/json"
}

print("🚀 Applying migration 008_article_comparison.sql...")
print(f"📍 Database: {SUPABASE_URL}")
print()

# Try direct psql connection via PostgREST
# We'll use the database connection string
db_url = SUPABASE_URL.replace("https://", "")
project_ref = db_url.split(".")[0]

print(f"Project ref: {project_ref}")
print()
print("⚠️  Note: Direct SQL execution via REST API is limited.")
print("Please use one of these methods:")
print()
print("1️⃣  Supabase Dashboard SQL Editor:")
print(f"   https://app.supabase.com/project/{project_ref}/sql")
print()
print("2️⃣  Copy and paste the migration SQL from:")
print("   docs/migrations/008_article_comparison.sql")
print()
print("3️⃣  Or use psql command line:")
print(f'   psql "postgresql://postgres:[YOUR_PASSWORD]@db.{project_ref}.supabase.co:5432/postgres" \\')
print('     -f docs/migrations/008_article_comparison.sql')
print()

# Alternative: Try using supabase-py client
try:
    from supabase import create_client, Client

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

    print("✅ Supabase client initialized")
    print("🔄 Attempting to execute migration...")

    # Split migration into individual statements
    statements = migration_sql.split(';')

    success_count = 0
    error_count = 0

    for i, stmt in enumerate(statements):
        stmt = stmt.strip()
        if not stmt or stmt.startswith('--'):
            continue

        try:
            # Execute via RPC if available
            result = supabase.rpc('exec_sql', {'query': stmt}).execute()
            success_count += 1
            print(f"✅ Statement {i+1} executed")
        except Exception as e:
            error_count += 1
            print(f"❌ Statement {i+1} failed: {str(e)[:100]}")

    print()
    print(f"📊 Results: {success_count} succeeded, {error_count} failed")

except ImportError:
    print("⚠️  supabase-py not installed. Install with:")
    print("   pip install supabase")
except Exception as e:
    print(f"❌ Error: {e}")
    print()
    print("Please use the Supabase Dashboard SQL Editor instead.")
