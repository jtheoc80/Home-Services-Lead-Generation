#!/usr/bin/env tsx
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL || '',
  process.env.SUPABASE_SERVICE_ROLE_KEY || ''
);

async function main() {
  const { data, error } = await supabase
    .from('permits')
    .select('*')
    .limit(1);
  
  if (data && data.length > 0) {
    console.log('📋 Permits table structure:\n');
    console.log('✅ Available fields:', Object.keys(data[0]).sort().join(', '));
  } else if (error) {
    console.log('❌ Error or no permits:', error.message);
  } else {
    console.log('⚠️  No permits found in table');
  }
}

main();
