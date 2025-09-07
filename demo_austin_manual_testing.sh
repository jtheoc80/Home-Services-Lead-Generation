#!/bin/bash
# =============================================================================
# Austin Socrata Manual Testing Demo
# =============================================================================
# Demonstrates the Austin Socrata manual testing workflow
# =============================================================================

echo "============================================================================="
echo "Austin Socrata Manual Testing Demo"
echo "============================================================================="
echo "This demo shows how to use the new Austin Socrata manual testing features."
echo "============================================================================="
echo

echo "1. SETUP INSTRUCTIONS"
echo "----------------------"
echo "Before running the manual tests, you need to set up your environment:"
echo
echo "# Get your Austin Socrata App Token from:"
echo "# https://data.austintexas.gov/profile/edit/developer_settings"
echo
echo "# Set your token and dataset id (find on the dataset's API page)"
echo "export AUSTIN_SOCRATA_APP_TOKEN=YOUR_TOKEN"
echo "export AUSTIN_DATASET_ID=3syk-w9eu   # Austin building permits dataset"
echo
echo "# For testing, you can also use different dataset IDs:"
echo "# export AUSTIN_DATASET_ID=abcd-1234   # Replace with any Austin dataset"
echo
echo

echo "2. MANUAL TESTING COMMANDS (from problem statement)"
echo "----------------------------------------------------"
echo "Once your environment is set up, you can run these manual commands:"
echo

echo "# Step 1 — quick HEAD + sample row"
echo "curl -sS -I https://data.austintexas.gov | head -n1"
echo
echo "# 1 sample row (should print a small JSON array)"
echo "curl -sS \"https://data.austintexas.gov/resource/\$AUSTIN_DATASET_ID.json?\\\$limit=1\" \\"
echo "  -H \"X-App-Token: \$AUSTIN_SOCRATA_APP_TOKEN\""
echo

echo "# Step 2 — download a CSV (no code)"
echo "START=2024-01-01"
echo "curl -sS \"https://data.austintexas.gov/resource/\$AUSTIN_DATASET_ID.csv?\\"
echo "\\\$where=issued_date >= '\$START'&\\\$order=issued_date&\\\$limit=50000\" \\"
echo "  -H \"X-App-Token: \$AUSTIN_SOCRATA_APP_TOKEN\" \\"
echo "  -o austin_sample.csv"
echo "wc -l austin_sample.csv && head -5 austin_sample.csv"
echo
echo

echo "3. AUTOMATED SCRIPT USAGE"
echo "--------------------------"
echo "We've created an automated script that implements the above workflow:"
echo

echo "# Run both steps automatically"
echo "./scripts/austin-socrata-manual-test.sh"
echo

echo "# Run only specific steps"
echo "./scripts/austin-socrata-manual-test.sh --step1   # HEAD + sample row"
echo "./scripts/austin-socrata-manual-test.sh --step2   # CSV download"
echo

echo "# Get help"
echo "./scripts/austin-socrata-manual-test.sh --help"
echo
echo

echo "4. TESTING THE SCRIPT (without real tokens)"
echo "---------------------------------------------"
echo "Let's test the script structure without real API tokens:"
echo

echo ">>> Testing help output:"
./scripts/austin-socrata-manual-test.sh --help | head -10
echo "... (truncated)"
echo

echo ">>> Testing without environment variables:"
./scripts/austin-socrata-manual-test.sh 2>&1 | head -15
echo "... (shows proper error handling)"
echo
echo

echo "5. INTEGRATION WITH EXISTING HEALTH CHECKS"
echo "--------------------------------------------"
echo "The Austin manual testing is also integrated into existing health check scripts:"
echo

echo "# Updated copy-paste health checks now include Austin examples"
echo "./scripts/copy-paste-health-checks.sh"
echo

echo "# Source health checks support Austin tokens"
echo "./scripts/source-health-checks.sh"
echo
echo

echo "6. DOCUMENTATION"
echo "----------------"
echo "Complete documentation has been added to:"
echo "  • docs/SOURCE_HEALTH_CHECKS.md - includes Austin manual testing section"
echo "  • README updates (if needed)"
echo
echo

echo "7. ALTERNATIVE DATE FIELDS"
echo "---------------------------"
echo "If 'issued_date' doesn't work for your dataset, try these alternatives:"
echo "  • issue_date"
echo "  • file_date"
echo "  • application_date"
echo "  • created_date"
echo
echo "Update the script or use curl directly with the correct field name."
echo
echo

echo "============================================================================="
echo "Demo completed! To use the Austin Socrata manual testing:"
echo "1. Get your Austin Socrata App Token"
echo "2. Set AUSTIN_SOCRATA_APP_TOKEN and AUSTIN_DATASET_ID environment variables"
echo "3. Run ./scripts/austin-socrata-manual-test.sh"
echo "============================================================================="