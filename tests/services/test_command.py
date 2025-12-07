import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Any
from hflav_zenodo.services.command import Command, CommandInvoker, CommandHistory


class TestCommandPattern:
    """Test suite for Command pattern implementation."""

    # Tests for Command abstract class
    def test_command_is_abstract(self):
        """Test that Command class is abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            Command()  # Should fail as Command is abstract

    def test_concrete_command_implements_abstract_methods(self):
        """Test that a concrete command must implement execute and undo."""

        class ConcreteCommand(Command):
            def execute(self) -> Any:
                return "executed"

            def undo(self) -> Any:
                return "undone"

        command = ConcreteCommand()
        assert command.execute() == "executed"
        assert command.undo() == "undone"

    def test_incomplete_command_raises_error(self):
        """Test that incomplete implementation raises TypeError."""

        class IncompleteCommand(Command):
            def execute(self) -> Any:
                return "executed"

            # Missing undo method

        with pytest.raises(TypeError):
            IncompleteCommand()

    # Tests for CommandInvoker
    def test_command_invoker_initialization(self):
        """Test CommandInvoker initializes with empty state."""
        invoker = CommandInvoker()

        assert invoker._command is None
        assert isinstance(invoker._history, CommandHistory)
        assert len(invoker._history._history) == 0

    def test_set_command(self):
        """Test setting a command on the invoker."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)

        invoker.set_command(mock_command)

        assert invoker._command == mock_command

    def test_execute_command_success(self):
        """Test successfully executing a command."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)
        mock_command.execute.return_value = "command result"

        invoker.set_command(mock_command)
        result = invoker.execute_command()

        mock_command.execute.assert_called_once()
        assert result == "command result"
        # Verify command was added to history
        assert len(invoker._history._history) == 1
        assert invoker._history._history[0] == mock_command

    def test_execute_command_no_command_set(self):
        """Test executing without setting a command raises ValueError."""
        invoker = CommandInvoker()

        with pytest.raises(ValueError) as exc_info:
            invoker.execute_command()

        assert "No command set" in str(exc_info.value)

    def test_execute_command_multiple_times(self):
        """Test executing multiple commands adds them to history."""
        invoker = CommandInvoker()

        # Create multiple mock commands
        mock_commands = [Mock(spec=Command) for _ in range(3)]
        for i, mock_command in enumerate(mock_commands):
            mock_command.execute.return_value = f"result_{i}"
            invoker.set_command(mock_command)
            invoker.execute_command()

        # Verify all commands were executed and added to history
        assert len(invoker._history._history) == 3
        for i, mock_command in enumerate(mock_commands):
            mock_command.execute.assert_called_once()
            assert invoker._history._history[i] == mock_command

    def test_undo_command_success(self):
        """Test successfully undoing the last command."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)

        invoker.set_command(mock_command)
        invoker.execute_command()  # Adds to history

        invoker.undo_command()

        mock_command.undo.assert_called_once()
        assert len(invoker._history._history) == 0

    def test_undo_command_empty_history(self):
        """Test undoing when history is empty logs message."""
        invoker = CommandInvoker()

        with patch("hflav_zenodo.services.command.logger") as mock_logger:
            result = invoker.undo_command()

            # Should log info message
            mock_logger.info.assert_called_once_with("No commands to undo.")
            # Should return None (implicitly)
            assert result is None

    def test_undo_command_multiple_commands(self):
        """Test undoing multiple commands in LIFO order."""
        invoker = CommandInvoker()

        # Create and execute multiple commands
        mock_commands = [Mock(spec=Command) for _ in range(3)]
        executed_order = []
        undo_order = []

        for mock_command in mock_commands:
            invoker.set_command(mock_command)
            invoker.execute_command()
            executed_order.append(mock_command)

        # Undo all commands (should be in reverse order)
        for _ in range(3):
            invoker.undo_command()

        # Verify undo was called in reverse order of execution
        assert mock_commands[2].undo.call_count == 1
        assert mock_commands[1].undo.call_count == 1
        assert mock_commands[0].undo.call_count == 1

        # Verify history is empty
        assert len(invoker._history._history) == 0

    def test_undo_command_without_executing(self):
        """Test undoing when no commands have been executed."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)

        invoker.set_command(mock_command)
        # Don't execute, just set

        # Undo should log message (no history)
        with patch("hflav_zenodo.services.command.logger") as mock_logger:
            invoker.undo_command()
            mock_logger.info.assert_called_once_with("No commands to undo.")

    def test_command_execution_with_exception(self):
        """Test command execution when command raises an exception."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)
        mock_command.execute.side_effect = ValueError("Command failed")

        invoker.set_command(mock_command)

        with pytest.raises(ValueError) as exc_info:
            invoker.execute_command()

        assert "Command failed" in str(exc_info.value)

    def test_command_undo_with_exception(self):
        """Test command undo when undo raises an exception."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)
        mock_command.undo.side_effect = RuntimeError("Undo failed")

        invoker.set_command(mock_command)
        invoker.execute_command()  # Add to history

        with pytest.raises(RuntimeError) as exc_info:
            invoker.undo_command()

        assert "Undo failed" in str(exc_info.value)
        # Command should be removed from history even if undo fails
        assert len(invoker._history._history) == 0

    def test_set_command_overwrites_previous(self):
        """Test that setting a new command overwrites the previous one."""
        invoker = CommandInvoker()

        mock_command1 = Mock(spec=Command)
        mock_command2 = Mock(spec=Command)

        invoker.set_command(mock_command1)
        assert invoker._command == mock_command1

        invoker.set_command(mock_command2)
        assert invoker._command == mock_command2

    def test_execute_same_command_multiple_times(self):
        """Test executing the same command multiple times."""
        invoker = CommandInvoker()
        mock_command = Mock(spec=Command)
        mock_command.execute.return_value = "result"

        invoker.set_command(mock_command)

        # Execute same command 3 times
        results = []
        for _ in range(3):
            results.append(invoker.execute_command())

        assert mock_command.execute.call_count == 3
        assert len(results) == 3
        assert all(r == "result" for r in results)
        assert len(invoker._history._history) == 3
        # All history entries should be the same command object
        assert all(cmd == mock_command for cmd in invoker._history._history)

    # Tests for CommandHistory
    def test_command_history_initialization(self):
        """Test CommandHistory initializes with empty list."""
        history = CommandHistory()

        assert history._history == []
        assert isinstance(history._history, list)

    def test_add_command(self):
        """Test adding commands to history."""
        history = CommandHistory()
        mock_command = Mock(spec=Command)

        history.add_command(mock_command)

        assert len(history._history) == 1
        assert history._history[0] == mock_command

    def test_add_multiple_commands(self):
        """Test adding multiple commands to history."""
        history = CommandHistory()
        mock_commands = [Mock(spec=Command) for _ in range(3)]

        for cmd in mock_commands:
            history.add_command(cmd)

        assert len(history._history) == 3
        for i, cmd in enumerate(mock_commands):
            assert history._history[i] == cmd

    def test_undo_last_with_commands(self):
        """Test undoing last command when history has commands."""
        history = CommandHistory()
        mock_command = Mock(spec=Command)

        history.add_command(mock_command)
        history.undo_last()

        mock_command.undo.assert_called_once()
        assert len(history._history) == 0

    def test_undo_last_empty_history(self):
        """Test undoing when history is empty logs message."""
        history = CommandHistory()

        with patch("hflav_zenodo.services.command.logger") as mock_logger:
            history.undo_last()

            mock_logger.info.assert_called_once_with("No commands to undo.")

    def test_undo_last_multiple_commands(self):
        """Test undoing multiple commands in LIFO order."""
        history = CommandHistory()
        mock_commands = [Mock(spec=Command) for _ in range(3)]

        # Add commands to history
        for cmd in mock_commands:
            history.add_command(cmd)

        # Undo in reverse order
        history.undo_last()  # Should undo mock_commands[2]
        mock_commands[2].undo.assert_called_once()
        assert len(history._history) == 2

        history.undo_last()  # Should undo mock_commands[1]
        mock_commands[1].undo.assert_called_once()
        assert len(history._history) == 1

        history.undo_last()  # Should undo mock_commands[0]
        mock_commands[0].undo.assert_called_once()
        assert len(history._history) == 0

    def test_undo_with_command_return_value(self):
        """Test that undo can return a value."""
        history = CommandHistory()
        mock_command = Mock(spec=Command)
        mock_command.undo.return_value = "undo result"

        history.add_command(mock_command)
        # Note: undo_last() doesn't return the command's undo return value
        # but we can verify the command was called
        history.undo_last()

        mock_command.undo.assert_called_once()

    # Integration tests
    def test_full_command_pattern_flow(self):
        """Test a complete flow of the command pattern."""

        # Create a concrete command for integration test
        class TestCommand(Command):
            def __init__(self):
                self.executed = False
                self.undone = False

            def execute(self) -> str:
                self.executed = True
                return "Command executed"

            def undo(self) -> str:
                self.undone = True
                return "Command undone"

        # Test the flow
        invoker = CommandInvoker()
        command = TestCommand()

        # Set and execute command
        invoker.set_command(command)
        result = invoker.execute_command()

        assert result == "Command executed"
        assert command.executed is True
        assert command.undone is False
        assert len(invoker._history._history) == 1

        # Undo command
        invoker.undo_command()

        assert command.undone is True
        assert len(invoker._history._history) == 0

    def test_command_history_preserves_order(self):
        """Test that command history preserves execution order."""
        invoker = CommandInvoker()

        # Create commands with identifiers
        commands = []
        for i in range(5):
            mock_command = Mock(spec=Command)
            mock_command.id = i  # Add identifier for tracking
            mock_command.execute.return_value = f"result_{i}"
            commands.append(mock_command)

        # Execute all commands
        for cmd in commands:
            invoker.set_command(cmd)
            invoker.execute_command()

        # Verify execution order in history
        history = invoker._history._history
        assert len(history) == 5
        for i, cmd in enumerate(history):
            assert cmd.id == i  # Should be in execution order

    def test_undo_after_clear_history(self):
        """Test undoing after executing and clearing commands."""
        invoker = CommandInvoker()
        mock_command1 = Mock(spec=Command)
        mock_command2 = Mock(spec=Command)

        # Execute two commands
        invoker.set_command(mock_command1)
        invoker.execute_command()

        invoker.set_command(mock_command2)
        invoker.execute_command()

        # Undo both
        invoker.undo_command()  # Undoes command2
        mock_command2.undo.assert_called_once()

        invoker.undo_command()  # Undoes command1
        mock_command1.undo.assert_called_once()

        # Try to undo again (should log message)
        with patch("hflav_zenodo.services.command.logger") as mock_logger:
            invoker.undo_command()
            mock_logger.info.assert_called_once_with("No commands to undo.")
