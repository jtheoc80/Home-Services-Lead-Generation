#!/usr/bin/env python3
"""
Unit tests for ingest logging functionality.

Tests the ingest_logger module functions without requiring database connections.
"""

import unittest
import uuid
from unittest.mock import patch, MagicMock
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.ingest_logger import (
    generate_trace_id, 
    IngestTracer,
    log_ingest_step,
    get_trace_logs
)


class TestIngestLogging(unittest.TestCase):
    """Test cases for ingest logging functionality."""
    
    def test_generate_trace_id(self):
        """Test trace ID generation."""
        trace_id = generate_trace_id()
        
        # Should be a valid UUID string
        self.assertIsInstance(trace_id, str)
        
        # Should be parseable as UUID
        uuid_obj = uuid.UUID(trace_id)
        self.assertEqual(str(uuid_obj), trace_id)
        
        # Should generate different IDs each time
        trace_id2 = generate_trace_id()
        self.assertNotEqual(trace_id, trace_id2)
    
    def test_ingest_tracer_init(self):
        """Test IngestTracer initialization."""
        # Test with no trace_id
        tracer = IngestTracer()
        self.assertIsNotNone(tracer.trace_id)
        uuid.UUID(tracer.trace_id)  # Should not raise
        self.assertEqual(len(tracer.stages_logged), 0)
        
        # Test with provided trace_id
        test_trace_id = str(uuid.uuid4())
        tracer = IngestTracer(test_trace_id)
        self.assertEqual(tracer.trace_id, test_trace_id)
        self.assertEqual(len(tracer.stages_logged), 0)
    
    @patch('app.ingest_logger.get_supabase_client')
    def test_log_ingest_step_success(self, mock_get_supabase):
        """Test successful logging step."""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [{"id": 1, "trace_id": "test-trace"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_result
        mock_get_supabase.return_value = mock_supabase
        
        trace_id = str(uuid.uuid4())
        result = log_ingest_step(trace_id, "test_stage", True, {"test": "data"})
        
        self.assertTrue(result)
        mock_supabase.table.assert_called_with('ingest_logs')
        mock_supabase.table.return_value.insert.assert_called_once()
    
    @patch('app.ingest_logger.get_supabase_client')
    def test_log_ingest_step_validation(self, mock_get_supabase):
        """Test input validation for log_ingest_step."""
        # Test missing trace_id
        result = log_ingest_step("", "test_stage", True)
        self.assertFalse(result)
        
        # Test missing stage
        result = log_ingest_step(str(uuid.uuid4()), "", True)
        self.assertFalse(result)
        
        # Test invalid trace_id format
        result = log_ingest_step("invalid-uuid", "test_stage", True)
        self.assertFalse(result)
    
    @patch('app.ingest_logger.get_supabase_client')
    def test_get_trace_logs_success(self, mock_get_supabase):
        """Test successful trace log retrieval."""
        # Mock Supabase client
        mock_supabase = MagicMock()
        mock_result = MagicMock()
        mock_result.data = [
            {"id": 1, "trace_id": "test-trace", "stage": "fetch_page", "ok": True},
            {"id": 2, "trace_id": "test-trace", "stage": "parse", "ok": True}
        ]
        mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value = mock_result
        mock_get_supabase.return_value = mock_supabase
        
        trace_id = str(uuid.uuid4())
        result = get_trace_logs(trace_id)
        
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        mock_supabase.table.assert_called_with('ingest_logs')
    
    @patch('app.ingest_logger.get_supabase_client')
    def test_get_trace_logs_validation(self, mock_get_supabase):
        """Test input validation for get_trace_logs."""
        # Test invalid trace_id format
        result = get_trace_logs("invalid-uuid")
        self.assertIsNone(result)
    
    @patch('app.ingest_logger.log_ingest_step')
    def test_ingest_tracer_context_manager(self, mock_log_step):
        """Test IngestTracer as context manager."""
        mock_log_step.return_value = True
        
        with IngestTracer() as tracer:
            # Should have a valid trace_id
            uuid.UUID(tracer.trace_id)
            
            # Test logging a stage
            result = tracer.log("test_stage", True, {"test": "data"})
            self.assertTrue(result)
            self.assertIn("test_stage", tracer.stages_logged)
        
        # Should have called log_ingest_step
        mock_log_step.assert_called()
    
    @patch('app.ingest_logger.log_ingest_step')
    def test_ingest_tracer_exception_handling(self, mock_log_step):
        """Test IngestTracer exception handling."""
        mock_log_step.return_value = True
        
        try:
            with IngestTracer() as tracer:
                tracer.log("stage1", True)
                raise ValueError("Test exception")
        except ValueError:
            pass
        
        # Should have logged the exception
        calls = mock_log_step.call_args_list
        exception_call = None
        for call in calls:
            if call[0][1] == "exception":  # stage parameter
                exception_call = call
                break
        
        self.assertIsNotNone(exception_call)
        self.assertFalse(exception_call[0][2])  # ok parameter should be False


class TestValidation(unittest.TestCase):
    """Test input validation functions."""
    
    def test_uuid_validation(self):
        """Test UUID validation logic."""
        # Valid UUIDs
        valid_uuids = [
            str(uuid.uuid4()),
            "123e4567-e89b-12d3-a456-426614174000",
            "550e8400-e29b-41d4-a716-446655440000"
        ]
        
        for test_uuid in valid_uuids:
            try:
                uuid.UUID(test_uuid)
                valid = True
            except ValueError:
                valid = False
            self.assertTrue(valid, f"Should be valid UUID: {test_uuid}")
        
        # Invalid UUIDs
        invalid_uuids = [
            "not-a-uuid",
            "123",
            "",
            "123e4567-e89b-12d3-a456",  # too short
            "123e4567-e89b-12d3-a456-426614174000-extra"  # too long
        ]
        
        for test_uuid in invalid_uuids:
            try:
                uuid.UUID(test_uuid)
                valid = True
            except ValueError:
                valid = False
            self.assertFalse(valid, f"Should be invalid UUID: {test_uuid}")


if __name__ == '__main__':
    unittest.main()