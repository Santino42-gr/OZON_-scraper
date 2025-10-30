#!/usr/bin/env python3
"""
Apply migration 008 to Supabase database using psycopg2
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_db_connection_string():
    """Get database connection string from environment"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url or "your-password" in db_url:
        print("❌ DATABASE_URL not properly configured in .env")
        print("Please update DATABASE_URL with actual password")
        return None
    return db_url

def apply_migration():
    """Apply migration using psycopg2"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install with:")
        print("   pip install psycopg2-binary")
        return False

    db_url = get_db_connection_string()
    if not db_url:
        return False

    # Read migration file
    migration_path = Path(__file__).parent.parent / "docs/migrations/008_article_comparison.sql"

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return False

    with open(migration_path, "r") as f:
        migration_sql = f.read()

    print("🚀 Applying migration 008_article_comparison.sql...")
    print(f"📍 Database: {db_url.split('@')[1].split('/')[0]}")
    print()

    try:
        # Connect to database
        conn = psycopg2.connect(db_url)
        conn.autocommit = False
        cur = conn.cursor()

        print("✅ Connected to database")
        print("🔄 Executing migration...")
        print()

        # Execute migration
        cur.execute(migration_sql)

        # Commit transaction
        conn.commit()

        print("✅ Migration applied successfully!")
        print()

        # Run verification queries
        print("🔍 Verifying migration...")
        print()

        # Check tables
        cur.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_name IN (
                'ozon_scraper_article_groups',
                'ozon_scraper_article_group_members',
                'ozon_scraper_comparison_snapshots'
            )
            ORDER BY table_name;
        """)

        tables = cur.fetchall()
        print(f"📊 Tables created: {len(tables)}")
        for table in tables:
            print(f"   ✓ {table[0]}")
        print()

        # Check functions
        cur.execute("""
            SELECT routine_name
            FROM information_schema.routines
            WHERE routine_name IN (
                'get_group_comparison',
                'save_comparison_snapshot',
                'get_comparison_history',
                'cleanup_old_snapshots',
                'get_user_groups_stats'
            )
            ORDER BY routine_name;
        """)

        functions = cur.fetchall()
        print(f"⚙️  Functions created: {len(functions)}")
        for func in functions:
            print(f"   ✓ {func[0]}")
        print()

        # Check indexes
        cur.execute("""
            SELECT COUNT(DISTINCT indexname)
            FROM pg_indexes
            WHERE tablename IN (
                'ozon_scraper_article_groups',
                'ozon_scraper_article_group_members',
                'ozon_scraper_comparison_snapshots'
            );
        """)

        index_count = cur.fetchone()[0]
        print(f"📑 Indexes created: {index_count}")
        print()

        # Check RLS policies
        cur.execute("""
            SELECT COUNT(*)
            FROM pg_policies
            WHERE tablename IN (
                'ozon_scraper_article_groups',
                'ozon_scraper_article_group_members',
                'ozon_scraper_comparison_snapshots'
            );
        """)

        policy_count = cur.fetchone()[0]
        print(f"🔒 RLS policies created: {policy_count}")
        print()

        cur.close()
        conn.close()

        print("=" * 60)
        print("✅ MIGRATION 008 COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        return True

    except psycopg2.Error as e:
        print(f"❌ Database error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    success = apply_migration()
    sys.exit(0 if success else 1)
