#!/bin/bash
# Open Supabase SQL Editor with migration ready to paste

# Extract project ref from SUPABASE_URL
source .env
PROJECT_REF=$(echo $SUPABASE_URL | sed 's/https:\/\///' | cut -d'.' -f1)

echo "=================================================="
echo "🚀 APPLYING MIGRATION 008 - Article Comparison"
echo "=================================================="
echo ""
echo "Opening Supabase SQL Editor in your browser..."
echo ""
echo "📋 Steps to apply migration:"
echo ""
echo "1. SQL Editor will open in your browser"
echo "2. Copy the migration SQL from:"
echo "   docs/migrations/008_article_comparison.sql"
echo "3. Paste into the SQL Editor"
echo "4. Click 'Run' button"
echo "5. Verify success message"
echo ""
echo "Project: $PROJECT_REF"
echo "Dashboard: https://app.supabase.com/project/$PROJECT_REF/sql"
echo ""

# Copy migration to clipboard if pbcopy is available (macOS)
if command -v pbcopy &> /dev/null; then
    cat docs/migrations/008_article_comparison.sql | pbcopy
    echo "✅ Migration SQL copied to clipboard!"
    echo "   Just paste (Cmd+V) in the SQL Editor"
    echo ""
fi

# Open browser
open "https://app.supabase.com/project/$PROJECT_REF/sql/new"

echo "Press any key after migration is applied to verify..."
read -n 1 -s

echo ""
echo "🔍 Verifying migration..."
echo ""

# We can't verify without psql, so just show instructions
echo "To verify, run these queries in SQL Editor:"
echo ""
echo "-- Check tables"
echo "SELECT table_name FROM information_schema.tables"
echo "WHERE table_name LIKE 'ozon_scraper_article_%';"
echo ""
echo "-- Check functions"
echo "SELECT routine_name FROM information_schema.routines"
echo "WHERE routine_name LIKE '%comparison%';"
echo ""
