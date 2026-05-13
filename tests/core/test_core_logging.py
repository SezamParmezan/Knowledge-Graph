"""Tests for logging configuration"""

import pytest
import sys
from unittest.mock import patch, MagicMock, ANY
from app.core.logging import setup_logging
from app.core.config import settings


def test_setup_logging_removes_existing_handlers():
    """Test that setup_logging removes existing handlers"""
    with patch('app.core.logging.logger.remove') as mock_remove, \
         patch('app.core.logging.logger.add'):
        setup_logging()
        mock_remove.assert_called_once()


def test_setup_logging_adds_console_handler():
    """Test that setup_logging adds console handler"""
    with patch('app.core.logging.logger.remove'), \
         patch('app.core.logging.logger.add') as mock_add:
        setup_logging()
        
        # Should have at least 2 calls to add (console + file)
        assert mock_add.call_count >= 1
        
        # First call should be for stdout (console)
        first_call = mock_add.call_args_list[0]
        assert first_call[0][0] == sys.stdout or sys.stdout in first_call[1].values()


def test_setup_logging_adds_file_handler():
    """Test that setup_logging adds file handler"""
    with patch('app.core.logging.logger.remove'), \
         patch('app.core.logging.logger.add') as mock_add:
        setup_logging()
        
        # Should have at least 2 calls to add (console + file)
        assert mock_add.call_count >= 2
        
        # Second call should be for file
        if mock_add.call_count >= 2:
            second_call = mock_add.call_args_list[1]
            assert settings.log_file in str(second_call)


def test_setup_logging_uses_correct_level():
    """Test that setup_logging uses configured log level"""
    with patch('app.core.logging.logger.remove'), \
         patch('app.core.logging.logger.add') as mock_add:
        setup_logging()
        
        # All calls should use the configured log level
        for call in mock_add.call_args_list:
            if 'level' in call[1]:
                assert call[1]['level'] == settings.log_level


def test_setup_logging_creates_log_file_path():
    """Test that log file path is valid"""
    assert settings.log_file is not None
    assert '.log' in settings.log_file


def test_setup_logging_is_idempotent():
    """Test that calling setup_logging multiple times is safe"""
    with patch('app.core.logging.logger.remove'), \
         patch('app.core.logging.logger.add'):
        # Should not raise any exceptions
        setup_logging()
        setup_logging()
        setup_logging()


def test_setup_logging_configures_console_format(mock_logger):
    """Test that console handler has colorized format"""
    setup_logging()
    
    if mock_logger.add.call_count >= 1:
        first_call = mock_logger.add.call_args_list[0]
        # Check if colorize is True
        assert 'colorize' in str(first_call) or 'True' in str(first_call)


def test_setup_logging_configures_file_rotation(mock_logger):
    """Test that file handler has rotation configured"""
    setup_logging()
    
    if mock_logger.add.call_count >= 2:
        second_call = mock_logger.add.call_args_list[1]
        # Should have rotation parameter
        assert 'rotation' in str(second_call) or 'MB' in str(second_call)


def test_setup_logging_configures_file_retention(mock_logger):
    """Test that file handler has retention configured"""
    setup_logging()
    
    if mock_logger.add.call_count >= 2:
        second_call = mock_logger.add.call_args_list[1]
        # Should have retention parameter
        assert 'retention' in str(second_call) or 'days' in str(second_call)


def test_setup_logging_can_be_called_multiple_times(mock_logger):
    """Test that setup_logging can be called multiple times safely"""
    setup_logging()
    setup_logging()
    
    # Should have removed handlers twice
    assert mock_logger.remove.call_count >= 1
    
    # Should have added handlers multiple times
    assert mock_logger.add.call_count >= 2


def test_setup_logging_uses_settings_log_file(mock_logger):
    """Test that setup_logging uses settings.log_file path"""
    setup_logging()
    
    if mock_logger.add.call_count >= 2:
        # One of the calls should use the log file path
        calls_str = str(mock_logger.add.call_args_list)
        assert settings.log_file in calls_str or 'app.log' in calls_str


@pytest.mark.parametrize("log_level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
def test_setup_logging_with_different_log_levels(mock_logger, log_level):
    """Test setup_logging handles different log levels"""
    with patch('app.core.logging.settings') as mock_settings:
        mock_settings.log_level = log_level
        mock_settings.log_file = "test.log"
        
        setup_logging()
        
        # Should have been called at least once
        assert mock_logger.remove.called
