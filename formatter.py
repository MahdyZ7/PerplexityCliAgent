def format_command(command: str) -> str:
    """
    Format the bash command for display
    Add any necessary formatting or syntax highlighting hints
    """
    # Remove extra whitespace and normalize the command
    command = command.strip()
    
    # Add basic security checks
    if "rm -rf /" in command or "rm -rf /*" in command:
        raise ValueError("Potentially dangerous command detected")
        
    return command
