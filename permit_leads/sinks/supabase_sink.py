"""
Supabase sink for upserting permit data in batches.

Provides idempotent batch upserts to Supabase with configurable
conflict resolution and comprehensive logging.
"""

import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

logger = logging.getLogger(__name__)


class SupabaseSink:
    """
    Supabase sink for batch upserting permit data.
    
    Features:
    - Batch upserts with configurable chunk size (default 500)
    - Idempotent operations via conflict resolution
    - Comprehensive logging of success/failure counts
    - Environment-based configuration
    """
    
    def __init__(self, upsert_table: str, conflict_col: str = "event_id", chunk_size: int = 500):
        """
        Initialize Supabase sink.
        
        Args:
            upsert_table: Target table name for upserts
            conflict_col: Column name for conflict resolution (default: event_id)
            chunk_size: Number of records per batch (default: 500)
        """
        self.upsert_table = upsert_table
        self.conflict_col = conflict_col
        self.chunk_size = chunk_size
        
        # Read configuration from environment
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not self.supabase_url or not self.supabase_service_key:
            raise ValueError(
                "Missing required environment variables: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY"
            )
        
        if create_client is None:
            raise ImportError(
                "supabase-py not available. Install with: pip install supabase>=2.6.0"
            )
        
        # Initialize Supabase client
        try:
            self.client: Client = create_client(self.supabase_url, self.supabase_service_key)
            logger.info(f"Initialized SupabaseSink for table '{upsert_table}' with conflict column '{conflict_col}'")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            raise
    
    def upsert_batch(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert a batch of records to Supabase.
        
        Args:
            records: List of dictionaries representing permit records
            
        Returns:
            Dictionary with success/failure counts
            
        Raises:
            Exception: On non-200 response or connection issues
        """
        if not records:
            logger.info("No records to upsert")
            return {"success": 0, "failed": 0}
        
        try:
            # Convert datetime objects to ISO format strings for JSON serialization
            serialized_records = self._serialize_records(records)
            
            # Perform upsert with conflict resolution
            response = self.client.table(self.upsert_table).upsert(
                serialized_records,
                on_conflict=self.conflict_col
            ).execute()
            
            # Check response status
            if hasattr(response, 'status_code') and response.status_code != 200:
                error_msg = f"Supabase upsert failed with status {response.status_code}"
                logger.error(error_msg)
                raise Exception(error_msg)
            
            success_count = len(records)
            logger.info(f"Successfully upserted {success_count} records to {self.upsert_table}")
            
            return {"success": success_count, "failed": 0}
            
        except Exception as e:
            logger.error(f"Failed to upsert batch of {len(records)} records: {e}")
            return {"success": 0, "failed": len(records)}
    
    def upsert_batch_rpc(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert a batch of records using RPC endpoint for better conflict resolution.
        
        Args:
            records: List of dictionaries representing permit records
            
        Returns:
            Dictionary with success/failure counts
        """
        if not records:
            logger.info("No records to upsert via RPC")
            return {"success": 0, "failed": 0}
        
        success_count = 0
        failed_count = 0
        
        # Convert datetime objects to ISO format strings for JSON serialization
        serialized_records = self._serialize_records(records)
        
        # Call upsert_permit RPC for each record individually for better error handling
        for record in serialized_records:
            try:
                response = self.client.rpc('upsert_permit', {'p': record}).execute()
                
                # Check response status
                if hasattr(response, 'status_code') and response.status_code != 200:
                    logger.error(f"RPC upsert failed for record with status {response.status_code}")
                    failed_count += 1
                else:
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to upsert single record via RPC: {e}")
                failed_count += 1
        
        logger.info(f"RPC upsert completed: {success_count} success, {failed_count} failed")
        return {"success": success_count, "failed": failed_count}
    
    def upsert_records(self, records: List[Dict[str, Any]], use_rpc: bool = True) -> Dict[str, int]:
        """
        Upsert records in chunks, with comprehensive logging.
        
        Args:
            records: List of dictionaries representing permit records
            use_rpc: Whether to use RPC endpoint (default: True for better conflict resolution)
            
        Returns:
            Dictionary with total success/failure counts
        """
        if not records:
            logger.info("No records provided for upsert")
            return {"success": 0, "failed": 0}
        
        total_success = 0
        total_failed = 0
        
        if use_rpc:
            # Use RPC endpoint for better (source, source_record_id) upsert behavior
            logger.info(f"Starting RPC upsert of {len(records)} records")
            result = self.upsert_batch_rpc(records)
            total_success = result["success"]
            total_failed = result["failed"]
        else:
            # Fall back to traditional table upsert in chunks
            total_chunks = (len(records) + self.chunk_size - 1) // self.chunk_size
            logger.info(f"Starting table upsert of {len(records)} records in {total_chunks} chunks of {self.chunk_size}")
            
            # Process records in chunks
            for i in range(0, len(records), self.chunk_size):
                chunk = records[i:i + self.chunk_size]
                chunk_num = (i // self.chunk_size) + 1
                
                logger.info(f"Processing chunk {chunk_num}/{total_chunks} ({len(chunk)} records)")
                
                try:
                    result = self.upsert_batch(chunk)
                    total_success += result["success"]
                    total_failed += result["failed"]
                    
                    logger.info(f"Chunk {chunk_num} complete: {result['success']} success, {result['failed']} failed")
                    
                except Exception as e:
                    logger.error(f"Chunk {chunk_num} failed completely: {e}")
                    total_failed += len(chunk)
                    # Continue processing remaining chunks
        
        # Log final summary
        logger.info(f"Upsert complete: {total_success} success, {total_failed} failed")
        
        return {"success": total_success, "failed": total_failed}
    
    def _serialize_records(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Serialize records for JSON transmission to Supabase.
        
        Converts datetime objects to ISO format strings and handles other
        non-JSON-serializable types.
        
        Args:
            records: Raw permit records
            
        Returns:
            JSON-serializable records
        """
        serialized = []
        
        for record in records:
            serialized_record = {}
            for key, value in record.items():
                if isinstance(value, datetime):
                    # Convert datetime to ISO format string
                    serialized_record[key] = value.isoformat()
                elif value is None:
                    # Keep None values as-is
                    serialized_record[key] = None
                else:
                    # Keep other values as-is (strings, numbers, booleans)
                    serialized_record[key] = value
            
            serialized.append(serialized_record)
        
        return serialized
    
    def health_check(self) -> bool:
        """
        Perform a health check on the Supabase connection.
        
        Returns:
            True if connection is healthy, False otherwise
        """
        try:
            # Simple query to test connection
            response = self.client.table(self.upsert_table).select("*").limit(1).execute()
            
            if hasattr(response, 'status_code') and response.status_code == 200:
                logger.info("Supabase connection health check passed")
                return True
            else:
                logger.warning("Supabase connection health check failed")
                return False
                
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False