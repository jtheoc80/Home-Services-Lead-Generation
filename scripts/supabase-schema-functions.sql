-- Schema introspection SQL function for Supabase
-- This function can be created in Supabase to enable schema drift detection

-- Create a function to get table schema information
CREATE OR REPLACE FUNCTION get_table_schema_info()
RETURNS TABLE (
  table_name text,
  column_name text,
  data_type text,
  is_nullable text,
  column_default text,
  ordinal_position integer
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    t.table_name::text,
    c.column_name::text,
    c.data_type::text,
    c.is_nullable::text,
    c.column_default::text,
    c.ordinal_position::integer
  FROM information_schema.tables t
  JOIN information_schema.columns c ON t.table_name = c.table_name
  WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND c.table_schema = 'public'
  ORDER BY t.table_name, c.ordinal_position;
$$;

-- Create a function to get index information
CREATE OR REPLACE FUNCTION get_index_info()
RETURNS TABLE (
  table_name text,
  index_name text,
  column_names text[],
  is_unique boolean
)
LANGUAGE sql
SECURITY DEFINER
AS $$
  SELECT 
    i.tablename::text,
    i.indexname::text,
    array_agg(a.attname ORDER BY a.attnum)::text[],
    idx.indisunique
  FROM pg_indexes i
  JOIN pg_class c ON c.relname = i.tablename
  JOIN pg_index idx ON idx.indexrelid = (
    SELECT oid FROM pg_class WHERE relname = i.indexname
  )
  JOIN pg_attribute a ON a.attrelid = c.oid AND a.attnum = ANY(idx.indkey)
  WHERE i.schemaname = 'public'
  AND i.tablename NOT LIKE 'pg_%'
  GROUP BY i.tablename, i.indexname, idx.indisunique
  ORDER BY i.tablename, i.indexname;
$$;

-- Grant execute permissions to authenticated users
GRANT EXECUTE ON FUNCTION get_table_schema_info() TO authenticated;
GRANT EXECUTE ON FUNCTION get_index_info() TO authenticated;