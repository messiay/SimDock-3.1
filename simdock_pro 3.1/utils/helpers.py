import subprocess
import os
from typing import Optional
import shlex

from .config import CREATE_NO_WINDOW


def run_command(command: list) -> Optional[subprocess.CompletedProcess]:
    """Run a system command with error handling."""
    try:
        # Handle conda commands specially
        if len(command) > 0 and 'conda' in command[0]:
            # For conda commands, we might need shell=True on Windows
            if os.name == 'nt':  # Windows
                # Convert list to string for shell execution
                command_str = ' '.join([shlex.quote(str(arg)) for arg in command])
                return subprocess.run(command_str, check=True, capture_output=True, 
                                    text=True, shell=True, creationflags=CREATE_NO_WINDOW)
            else:
                return subprocess.run(command, check=True, capture_output=True, 
                                    text=True, creationflags=CREATE_NO_WINDOW)
        else:
            # Regular command execution
            return subprocess.run(command, check=True, capture_output=True, 
                                text=True, creationflags=CREATE_NO_WINDOW)
    except FileNotFoundError:
        raise Exception(f"Command not found: {command[0]}")
    except subprocess.CalledProcessError as e:
        raise Exception(f"Error with {command[0]}: {e.stderr}")


def validate_file_exists(filepath: str) -> bool:
    """Validate that a file exists."""
    return os.path.exists(filepath) and os.path.isfile(filepath)


def get_filename_without_extension(filepath: str) -> str:
    """Get filename without extension."""
    return os.path.splitext(os.path.basename(filepath))[0]


def create_directory(dir_path: str) -> bool:
    """Create directory if it doesn't exist."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        return True
    except OSError:
        return False