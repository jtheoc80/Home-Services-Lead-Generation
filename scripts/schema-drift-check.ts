#!/usr/bin/env tsx

/**
 * Schema Drift Detection Script
 * 
 * Compares the local backend/app/models.sql file with the live Supabase schema
 * and generates migration SQL if differences are found.
 * 
 * Environment Variables:
 *   NEXT_PUBLIC_SUPABASE_URL - Supabase project URL
 *   SUPABASE_SERVICE_ROLE_KEY - Service role key for admin access
 * 
 * Usage: tsx scripts/schema-drift-check.ts
 * Exit codes: 0 = no drift, 1 = drift found, 2 = error
 */

import { createClient } from '@supabase/supabase-js';
import * as fs from 'fs/promises';
import * as path from 'path';

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
    const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL;
    const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;

    if (!supabaseUrl || !serviceRoleKey) {
      throw new Error('Missing required environment variables: NEXT_PUBLIC_SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY');
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
      // First, try to use the custom schema functions if they exist
      const schemaData = await this.tryCustomSchemaFunctions();
      if (schemaData) {
        return schemaData;
      }

      // Fallback: Try to access system views directly  
      console.log('🔄 Trying direct system view access...');
      const directSchemaData = await this.tryDirectSchemaAccess();
      if (directSchemaData && directSchemaData.size > 0) {
        return directSchemaData;
      }

      // Final fallback: Table discovery method
      console.log('🔄 Using table discovery method...');
      return await this.discoverTablesFromModels();

    } catch (error) {
      console.error('❌ Failed to extract live schema:', error);
      throw new Error(`Could not extract schema from Supabase: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * Try to use custom PostgreSQL functions for schema introspection
   */
  private async tryCustomSchemaFunctions(): Promise<Map<string, TableInfo> | null> {
    try {
      console.log('🔍 Trying custom schema functions...');
      
      const { data: schemaData, error } = await this.supabase
        .rpc('get_table_schema_info');

      if (error) {
        console.log('⚠️ Custom schema functions not available:', error.message);
        return null;
      }

      if (!schemaData || schemaData.length === 0) {
        console.log('⚠️ Custom schema functions returned no data');
        return null;
      }

      console.log('✅ Using custom schema functions');
      return this.parseSchemaFunctionData(schemaData);

    } catch (error) {
      console.log('⚠️ Custom schema functions failed:', error);
      return null;
    }
  }

  /**
   * Try to access information_schema directly
   */
  private async tryDirectSchemaAccess(): Promise<Map<string, TableInfo> | null> {
    try {
      // This is a simplified approach that might work with some Supabase configurations
      const tables = new Map<string, TableInfo>();
      
      // Try to get table list using a simple approach
      const knownTables = ['leads', 'regions', 'jurisdictions', 'plans', 'notifications'];
      
      for (const tableName of knownTables) {
        try {
          // Test table existence with a simple query
          const { data, error } = await this.supabase
            .from(tableName)
            .select('*')
            .limit(1);

          if (!error) {
            // Table exists - extract column info from the data structure
            const columns: TableColumn[] = [];
            if (data && data.length > 0) {
              const sampleRow = data[0];
              Object.keys(sampleRow).forEach((colName, index) => {
                columns.push({
                  column_name: colName,
                  data_type: this.inferDataType(sampleRow[colName]),
                  is_nullable: 'YES', // Default assumption
                  column_default: null,
                  character_maximum_length: null,
                  numeric_precision: null,
                  numeric_scale: null
                });
              });
            }

            tables.set(tableName, {
              table_name: tableName,
              columns,
              indexes: [],
              constraints: []
            });
            
            console.log(`✅ Discovered table: ${tableName} (${columns.length} columns)`);
          }
        } catch (tableError) {
          console.log(`⚠️ Table ${tableName} not accessible:`, tableError);
        }
      }

      return tables.size > 0 ? tables : null;

    } catch (error) {
      console.log('⚠️ Direct schema access failed:', error);
      return null;
    }
  }

  /**
   * Discover tables by attempting to query known tables from models.sql
   */
  private async discoverTablesFromModels(): Promise<Map<string, TableInfo>> {
    console.log('🔍 Discovering tables from models.sql definitions...');
    
    const tables = new Map<string, TableInfo>();
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
  }

  /**
   * Parse data from custom schema functions
   */
  private parseSchemaFunctionData(schemaData: any[]): Map<string, TableInfo> {
    const tables = new Map<string, TableInfo>();
    
    // Group data by table name
    const tableGroups = new Map<string, any[]>();
    
    for (const row of schemaData) {
      const tableName = row.table_name;
      if (!tableGroups.has(tableName)) {
        tableGroups.set(tableName, []);
      }
      tableGroups.get(tableName)!.push(row);
    }

    // Convert to TableInfo objects
    const tableNames = Array.from(tableGroups.keys());
    for (const tableName of tableNames) {
      const rows = tableGroups.get(tableName)!;
      const columns: TableColumn[] = rows.map(row => ({
        column_name: row.column_name,
        data_type: row.data_type,
        is_nullable: row.is_nullable,
        column_default: row.column_default,
        character_maximum_length: null,
        numeric_precision: null,
        numeric_scale: null
      }));

      tables.set(tableName, {
        table_name: tableName,
        columns,
        indexes: [], // TODO: Implement with get_index_info function
        constraints: []
      });
    }

    return tables;
  }

  /**
   * Infer data type from a sample value
   */
  private inferDataType(value: any): string {
    if (value === null || value === undefined) return 'unknown';
    if (typeof value === 'string') return 'text';
    if (typeof value === 'number') {
      return Number.isInteger(value) ? 'integer' : 'numeric';
    }
    if (typeof value === 'boolean') return 'boolean';
    if (value instanceof Date) return 'timestamp';
    if (Array.isArray(value)) return 'array';
    if (typeof value === 'object') return 'jsonb';
    return 'unknown';
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
    migrations.push('-- Generated automatically by schema-drift-check');
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
  private parseIndexes(rawIndexes: any[]): IndexInfo[] {
    return rawIndexes.map(idx => ({
      index_name: idx.index_name,
      column_names: this.extractColumnsFromIndexDef(idx.index_definition),
      is_unique: idx.index_definition.includes('UNIQUE'),
      index_type: 'btree' // Default, could be enhanced
    }));
  }

  private parseConstraints(rawConstraints: any[]): ConstraintInfo[] {
    return rawConstraints.map(constraint => ({
      constraint_name: constraint.constraint_name,
      constraint_type: constraint.constraint_type,
      column_names: constraint.column_names ? constraint.column_names.split(',') : [],
      referenced_table: constraint.referenced_table,
      referenced_columns: constraint.referenced_columns ? constraint.referenced_columns.split(',') : undefined
    }));
  }

  private parseTableColumns(tableBody: string): TableColumn[] {
    const columns: TableColumn[] = [];
    const lines = this.splitColumns(tableBody);
    
    for (const line of lines) {
      if (line.startsWith('--') || line.includes('CONSTRAINT') || line.includes('UNIQUE') || line.includes('PRIMARY KEY')) {
        continue;
      }
      
      const columnMatch = line.match(/^(\w+)\s+(.+?)(?:\s+(NOT\s+NULL|NULL))?(?:\s+DEFAULT\s+(.+?))?$/i);
      if (columnMatch) {
        const [, columnName, dataType, nullable, defaultValue] = columnMatch;
        columns.push({
          column_name: columnName,
          data_type: dataType.toLowerCase(),
          is_nullable: nullable === 'NOT NULL' ? 'NO' : 'YES',
          column_default: defaultValue || null,
          character_maximum_length: null,
          numeric_precision: null,
          numeric_scale: null
        });
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

  private extractColumnsFromIndexDef(indexDef: string): string[] {
    const match = indexDef.match(/\(([^)]+)\)/);
    if (match) {
      return match[1].split(',').map(col => col.trim());
    }
    return [];
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
      console.log('🔍 Schema Drift Detection Starting...');
      console.log('=====================================');

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
        process.exit(0);
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
      console.error('❌ Schema drift check failed:');
      console.error(error instanceof Error ? error.message : String(error));
      process.exit(2);
    }
  }
}

// Run the script
const checker = new SchemaDriftChecker();
checker.run();