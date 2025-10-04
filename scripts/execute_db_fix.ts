#!/usr/bin/env tsx
/**
 * Execute Database Fix Script via Supabase
 */
import { createClient } from '@supabase/supabase-js';
import fs from 'fs';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
const supabaseKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

if (!supabaseUrl || !supabaseKey) {
  console.error('❌ Missing Supabase credentials');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseKey);

async function executeSqlStatements() {
  console.log('🔧 Executing Database Fix...\n');

  const sql = fs.readFileSync('fix_database_triggers.sql', 'utf-8');
  
  // Split by statement terminators and clean up
  const statements = sql
    .split(';')
    .map(s => s.trim())
    .filter(s => s && !s.startsWith('--') && s.length > 10);

  console.log(`📝 Found ${statements.length} SQL statements to execute\n`);

  for (let i = 0; i < statements.length; i++) {
    const statement = statements[i] + ';';
    
    // Skip comments and empty statements
    if (statement.trim().startsWith('--') || statement.trim().length < 15) continue;

    try {
      // Try to execute via raw SQL if available
      const response = await fetch(`${supabaseUrl}/rest/v1/rpc/exec`, {
        method: 'POST',
        headers: {
          'apikey': supabaseKey,
          'Authorization': `Bearer ${supabaseKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ query: statement })
      });

      if (response.ok) {
        console.log(`✅ Statement ${i + 1} executed`);
      } else {
        const error = await response.text();
        console.log(`⚠️  Statement ${i + 1} - ${error.substring(0, 100)}`);
      }
    } catch (err: any) {
      console.log(`⚠️  Statement ${i + 1} - ${err.message}`);
    }
  }

  console.log('\n━'.repeat(60));
  console.log('\n💡 Since direct SQL execution via API is limited,');
  console.log('   please run fix_database_triggers.sql in Supabase SQL Editor');
  console.log('\n📋 Steps:');
  console.log('   1. Go to Supabase Dashboard → SQL Editor');
  console.log('   2. Create a new query');
  console.log('   3. Copy/paste contents of fix_database_triggers.sql');
  console.log('   4. Click RUN');
}

executeSqlStatements();
