#!/usr/bin/env tsx

/**
 * QB Auditor Bot
 * 
 * Schema auditing bot that compares local and live database schemas.
 * Based on the existing schema-drift-check.ts script.
 */

import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs/promises';
import * as path from 'path';
import { program } from 'commander';

interface TableColumn {
  column_name: string;
  data_type: string;
  is_nullable: string;
  column_default: string | null;
  character_maximum_length: number | null;
  numeric_precision: number | null;
  numeric_scale: number | null;
}

interface TableInfo {
  table_name: string;
  columns: TableColumn[];
  indexes: IndexInfo[];
  constraints: ConstraintInfo[];
}

interface IndexInfo {
  index_name: string;
  column_names: string[];
  is_unique: boolean;
  index_type: string;
}

interface ConstraintInfo {
  constraint_name: string;
  constraint_type: string;
  column_names: string[];
  referenced_table?: string;
  referenced_columns?: string[];
}

interface SchemaComparison {
  missingTables: string[];
  extraTables: string[];
  tableDifferences: {
    [tableName: string]: {
      missingColumns: string[];
      extraColumns: string[];
      modifiedColumns: Array<{
        column: string;
        local: string;
        live: string;
      }>;
      missingIndexes: string[];
      extraIndexes: string[];
      missingConstraints: string[];
      extraConstraints: string[];
    };
  };
}

class SchemaDriftChecker {
  private supabase;
  private modelsFilePath: string;

  constructor() {
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || process.env.SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL (or SUPABASE_URL) and SUPABASE_SERVICE_ROLE_KEY');
    }

    this.supabase = createClient(supabaseUrl, serviceRoleKey);
    this.modelsFilePath = path.join(process.cwd(), 'backend', 'app', 'models.sql');
  }

  /**
   * Extract table information from the live Supabase database
   */
  async extractLiveSchema(): Promise<Map<string, TableInfo>> {
    console.log('📊 Extracting live schema from Supabase...');
    
    const tables = new Map<string, TableInfo>();

    try {
      // Discover tables by attempting to query known tables from models.sql
      console.log('🔍 Discovering tables from models.sql definitions...');
      
      const localSchema = await this.extractLocalSchema();
      const knownTables = Array.from(localSchema.keys());
      
      for (const tableName of knownTables) {
        try {
          // Test if table exists by attempting to query it
          const { error } = await this.supabase
            .from(tableName)
            .select('*')
            .limit(0);

          if (!error) {
            // Table exists, but we can't get detailed schema info
            // So we'll mark it as existing with minimal info
            tables.set(tableName, {
              table_name: tableName,
              columns: [], // Will be detected as differences in comparison
              indexes: [],
              constraints: []
            });
            console.log(`✅ Confirmed table exists: ${tableName}`);
          } else {
            console.log(`⚠️ Table ${tableName} may not exist or is not accessible`);
          }
        } catch (tableError) {
          console.log(`⚠️ Could not check table ${tableName}:`, tableError);
        }
      }

      if (tables.size === 0) {
        throw new Error('Could not discover any tables. Please check Supabase connection and permissions.');
      }

      console.log(`✅ Discovered ${tables.size} tables using fallback method`);
      return tables;

    } catch (error) {
      console.error('❌ Failed to extract live schema:', error);
      throw new Error(`Could not extract schema from Supabase: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Parse local models.sql file to extract expected schema
   */
  async extractLocalSchema(): Promise<Map<string, TableInfo>> {
    console.log('📄 Parsing local models.sql file...');
    
    try {
      const sqlContent = await fs.readFile(this.modelsFilePath, 'utf-8');
      const tables = new Map<string, TableInfo>();
      
      // Normalize line endings and handle multiline content
      const normalizedContent = sqlContent.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
      
      // Find all CREATE TABLE statements with better regex handling
      const tableRegex = /CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)\s*\(([\s\S]*?)\);/gi;
      let match;
      
      while ((match = tableRegex.exec(normalizedContent)) !== null) {
        const tableName = match[1];
        const tableBody = match[2];
        
        // Skip duplicate table definitions (keep the last one)
        const columns = this.parseTableColumns(tableBody);
        const indexes = this.extractIndexesFromSQL(normalizedContent, tableName);
        const constraints = this.extractConstraintsFromTable(tableBody);

        tables.set(tableName, {
          table_name: tableName,
          columns,
          indexes,
          constraints
        });
      }

      console.log(`✅ Parsed ${tables.size} tables from models.sql`);
      return tables;
    } catch (error) {
      throw new Error(`Failed to read models.sql: ${error}`);
    }
  }

  /**
   * Compare local and live schemas
   */
  compareSchemas(localSchema: Map<string, TableInfo>, liveSchema: Map<string, TableInfo>): SchemaComparison {
    console.log('🔍 Comparing schemas...');
    
    const comparison: SchemaComparison = {
      missingTables: [],
      extraTables: [],
      tableDifferences: {}
    };

    // Find missing and extra tables
    const localTables = new Set(localSchema.keys());
    const liveTables = new Set(liveSchema.keys());

    comparison.missingTables = Array.from(localTables).filter(table => !liveTables.has(table));
    comparison.extraTables = Array.from(liveTables).filter(table => !localTables.has(table));

    // Compare common tables
    const commonTables = Array.from(localTables).filter(table => liveTables.has(table));
    
    for (const tableName of commonTables) {
      const localTable = localSchema.get(tableName)!;
      const liveTable = liveSchema.get(tableName)!;
      
      const tableDiff = this.compareTableStructure(localTable, liveTable);
      if (this.hasTableDifferences(tableDiff)) {
        comparison.tableDifferences[tableName] = tableDiff;
      }
    }

    return comparison;
  }

  /**
   * Generate migration SQL based on schema differences
   */
  generateMigrationSQL(comparison: SchemaComparison): string {
    console.log('📝 Generating migration SQL...');
    
    const migrations: string[] = [];
    migrations.push('-- Schema Drift Migration');
    migrations.push('-- Generated automatically by qb-auditor');
    migrations.push(`-- Generated at: ${new Date().toISOString()}`);
    migrations.push('');

    // Handle missing tables
    for (const tableName of comparison.missingTables) {
      migrations.push(`-- TODO: Add CREATE TABLE statement for missing table: ${tableName}`);
      migrations.push(`-- Please manually add the CREATE TABLE statement from models.sql`);
      migrations.push('');
    }

    // Handle extra tables
    for (const tableName of comparison.extraTables) {
      migrations.push(`-- WARNING: Extra table found in live schema: ${tableName}`);
      migrations.push(`-- Consider if this table should be added to models.sql or removed from live schema`);
      migrations.push('');
    }

    // Handle table differences
    for (const [tableName, diff] of Object.entries(comparison.tableDifferences)) {
      migrations.push(`-- Migrations for table: ${tableName}`);
      
      // Missing columns
      for (const column of diff.missingColumns) {
        migrations.push(`-- TODO: Add missing column ${column} to table ${tableName}`);
        migrations.push(`-- ALTER TABLE ${tableName} ADD COLUMN ${column} [TYPE];`);
      }

      // Extra columns
      for (const column of diff.extraColumns) {
        migrations.push(`-- WARNING: Extra column ${column} found in live table ${tableName}`);
        migrations.push(`-- Consider if this should be added to models.sql or removed from live schema`);
      }

      // Modified columns
      for (const mod of diff.modifiedColumns) {
        migrations.push(`-- Column ${mod.column} differs between local and live schema`);
        migrations.push(`-- Local: ${mod.local}`);
        migrations.push(`-- Live:  ${mod.live}`);
        migrations.push(`-- TODO: Review and add appropriate ALTER COLUMN statement`);
      }

      migrations.push('');
    }

    if (migrations.length === 4) {
      return '-- No schema drift detected\n-- All tables and columns match between local and live schemas\n';
    }

    return migrations.join('\n');
  }

  // Helper methods
  private parseTableColumns(tableBody: string): TableColumn[] {
    const columns: TableColumn[] = [];
    const lines = tableBody.split(',').map(line => line.trim()).filter(line => line.length > 0);
    
    for (const line of lines) {
      // Skip comments and table-level constraints
      if (line.startsWith('--') || /^CONSTRAINT\b/i.test(line)) {
        continue;
      }

      // Tokenize the line
      const tokens = line.split(/\s+/);
      if (tokens.length < 2) continue;

      // Extract column name and data type
      const columnName = tokens[0];
      let dataType = tokens[1];
      let i = 2;
      // If data type is multi-word (e.g., "DOUBLE PRECISION", "CHARACTER VARYING")
      while (i < tokens.length && !/^(NOT|NULL|DEFAULT|PRIMARY|UNIQUE|CHECK|REFERENCES)$/i.test(tokens[i])) {
        dataType += ' ' + tokens[i];
        i++;
      }

      // Initialize attributes
      let isNullable = 'YES';
      let columnDefault: string | null = null;

      // Scan for constraints and attributes
      for (; i < tokens.length; i++) {
        const token = tokens[i].toUpperCase();
        if (token === 'NOT' && tokens[i+1] && tokens[i+1].toUpperCase() === 'NULL') {
          isNullable = 'NO';
          i++;
        } else if (token === 'NULL') {
          isNullable = 'YES';
        } else if (token === 'DEFAULT' && tokens[i+1]) {
          columnDefault = tokens.slice(i+1).join(' ');
          break;
        }
        // Ignore PRIMARY, UNIQUE, CHECK, REFERENCES for column-level parsing
      }

      columns.push({
        column_name: columnName,
        data_type: dataType.toUpperCase(),
        is_nullable: isNullable,
        column_default: columnDefault,
        character_maximum_length: null,
        numeric_precision: null,
        numeric_scale: null
      });
    }
    
    return columns;
  }

  private extractIndexesFromSQL(sqlContent: string, tableName: string): IndexInfo[] {
    const indexes: IndexInfo[] = [];
    const indexRegex = new RegExp(`CREATE\\s+(?:UNIQUE\\s+)?INDEX\\s+(?:IF\\s+NOT\\s+EXISTS\\s+)?(\\w+)\\s+ON\\s+${tableName}\\s*\\(([^)]+)\\)`, 'gi');
    let match;

    while ((match = indexRegex.exec(sqlContent)) !== null) {
      const indexName = match[1];
      const columnList = match[2];
      indexes.push({
        index_name: indexName,
        column_names: columnList.split(',').map(col => col.trim()),
        is_unique: match[0].toUpperCase().includes('UNIQUE'),
        index_type: 'btree'
      });
    }

    return indexes;
  }

  private extractConstraintsFromTable(tableBody: string): ConstraintInfo[] {
    const constraints: ConstraintInfo[] = [];
    
    // Look for REFERENCES constraints
    const foreignKeyRegex = /(\w+)\s+.*?REFERENCES\s+(\w+)\((\w+)\)/gi;
    let match;

    while ((match = foreignKeyRegex.exec(tableBody)) !== null) {
      constraints.push({
        constraint_name: `fk_${match[1]}_${match[2]}`,
        constraint_type: 'FOREIGN KEY',
        column_names: [match[1]],
        referenced_table: match[2],
        referenced_columns: [match[3]]
      });
    }

    return constraints;
  }

  private compareTableStructure(localTable: TableInfo, liveTable: TableInfo) {
    const localColumns = new Set(localTable.columns.map(col => col.column_name));
    const liveColumns = new Set(liveTable.columns.map(col => col.column_name));

    const missingColumns = Array.from(localColumns).filter(col => !liveColumns.has(col));
    const extraColumns = Array.from(liveColumns).filter(col => !localColumns.has(col));

    const modifiedColumns: Array<{column: string; local: string; live: string}> = [];
    
    // Compare common columns
    const commonColumns = Array.from(localColumns).filter(col => liveColumns.has(col));
    for (const colName of commonColumns) {
      const localCol = localTable.columns.find(c => c.column_name === colName)!;
      const liveCol = liveTable.columns.find(c => c.column_name === colName)!;
      
      if (localCol.data_type !== liveCol.data_type || localCol.is_nullable !== liveCol.is_nullable) {
        modifiedColumns.push({
          column: colName,
          local: `${localCol.data_type} ${localCol.is_nullable}`,
          live: `${liveCol.data_type} ${liveCol.is_nullable}`
        });
      }
    }

    return {
      missingColumns,
      extraColumns,
      modifiedColumns,
      missingIndexes: [],
      extraIndexes: [],
      missingConstraints: [],
      extraConstraints: []
    };
  }

  private hasTableDifferences(diff: any): boolean {
    return diff.missingColumns.length > 0 || 
           diff.extraColumns.length > 0 || 
           diff.modifiedColumns.length > 0 ||
           diff.missingIndexes.length > 0 ||
           diff.extraIndexes.length > 0 ||
           diff.missingConstraints.length > 0 ||
           diff.extraConstraints.length > 0;
  }

  /**
   * Main execution method
   */
  async run(): Promise<void> {
    try {
      console.log('🔍 QB Auditor - Schema Drift Detection Starting...');
      console.log('===============================================');

      // Extract schemas
      const [localSchema, liveSchema] = await Promise.all([
        this.extractLocalSchema(),
        this.extractLiveSchema()
      ]);

      // Compare schemas
      const comparison = this.compareSchemas(localSchema, liveSchema);

      // Check if there are any differences
      const hasDrift = comparison.missingTables.length > 0 || 
                     comparison.extraTables.length > 0 || 
                     Object.keys(comparison.tableDifferences).length > 0;

      if (!hasDrift) {
        console.log('✅ No schema drift detected!');
        console.log('📊 Summary:');
        console.log(`   - Local tables: ${localSchema.size}`);
        console.log(`   - Live tables: ${liveSchema.size}`);
        console.log('   - All schemas match perfectly');
        return;
      }

      // Generate migration
      const migrationSQL = this.generateMigrationSQL(comparison);

      console.log('⚠️  Schema drift detected!');
      console.log('📊 Summary:');
      console.log(`   - Missing tables: ${comparison.missingTables.length}`);
      console.log(`   - Extra tables: ${comparison.extraTables.length}`);
      console.log(`   - Tables with differences: ${Object.keys(comparison.tableDifferences).length}`);

      // Write migration file
      const migrationPath = path.join(process.cwd(), 'schema-drift-migration.sql');
      await fs.writeFile(migrationPath, migrationSQL);
      console.log(`📝 Migration SQL written to: ${migrationPath}`);

      // Write detailed comparison as JSON
      const comparisonPath = path.join(process.cwd(), 'schema-drift-details.json');
      await fs.writeFile(comparisonPath, JSON.stringify(comparison, null, 2));
      console.log(`📄 Detailed comparison written to: ${comparisonPath}`);

      process.exit(1); // Exit with code 1 to indicate drift found
      
    } catch (error) {
      console.error('❌ QB Auditor failed:');
      console.error(error instanceof Error ? error.message : String(error));
      process.exit(2);
    }
  }
}

/**
 * Main entry point for the QB Auditor bot
 */
export async function main(args: string[] = []): Promise<void> {
  const prog = program
    .name('qb-auditor')
    .description('Schema auditing bot that compares local and live database schemas')
    .action(async () => {
      const checker = new SchemaDriftChecker();
      await checker.run();
    });

  // Handle unhandled errors
  process.on('unhandledRejection', (reason, promise) => {
    console.error('💥 Unhandled Rejection at:', promise, 'reason:', reason);
    process.exit(1);
  });

  process.on('uncaughtException', (error) => {
    console.error('💥 Uncaught Exception:', error);
    process.exit(1);
  });

  // Parse CLI arguments
  await prog.parseAsync(args.length ? args : process.argv);
}

// Only run if this script is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}