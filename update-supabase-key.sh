#!/bin/bash

# Script to update the Supabase anonymous key in the frontend .env file
# Usage: ./update-supabase-key.sh "your_actual_anon_key_here"

if [ $# -ne 1 ]; then
    echo "Usage: $0 <supabase_anon_key>"
    echo "Example: $0 \"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\""
    exit 1
fi

ANON_KEY="$1"
ENV_FILE="frontend/.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: $ENV_FILE not found. Please run the configuration setup first."
    exit 1
fi

# Backup the current .env file
cp "$ENV_FILE" "$ENV_FILE.backup"

# Update the SUPABASE_ANON_KEY
sed -i "s/NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here/NEXT_PUBLIC_SUPABASE_ANON_KEY=$ANON_KEY/" "$ENV_FILE"

# Also remove the TODO comment
sed -i "/# TODO: Replace with actual anon key from Supabase dashboard/d" "$ENV_FILE"

echo "✓ Supabase anonymous key updated successfully!"
echo "Backup saved as: $ENV_FILE.backup"

# Verify the change
if grep -q "NEXT_PUBLIC_SUPABASE_ANON_KEY=$ANON_KEY" "$ENV_FILE"; then
    echo "✓ Verification: Key has been properly set in $ENV_FILE"
else
    echo "✗ Error: Key update may have failed. Please check $ENV_FILE manually."
    exit 1
fi