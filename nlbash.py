#!/usr/bin/env python3
import click
from rich.console import Console
from rich.prompt import Prompt
from rich.syntax import Syntax
import os
from api import translate_to_bash
from formatter import format_command
from history import add_to_history

console = Console()

@click.command()
@click.argument('query', required=False)
@click.option('--no-execute', is_flag=True, help="Don't execute the command, just show it")
def cli(query, no_execute):
    """Translate natural language to bash commands using Preplixity API."""
    try:
        if not query:
            query = Prompt.ask("\n[bold green]Enter your command in natural language")

        with console.status("[bold blue]Translating..."):
            bash_command = translate_to_bash(query)

        # Format and display the command
        formatted_command = format_command(bash_command)
        console.print("\n[bold green]Generated Command:[/]")
        console.print(Syntax(formatted_command, "bash", theme="monokai"))

        # Add to history
        add_to_history(query, bash_command)

        # Copy to clipboard functionality
        try:
            import pyperclip
            pyperclip.copy(bash_command)
            console.print("[dim](Command copied to clipboard)[/]")
        except ImportError:
            pass

        if not no_execute:
            execute = Prompt.ask(
                "\nDo you want to execute this command?",
                choices=["y", "n"],
                default="n"
            )
            
            if execute.lower() == 'y':
                console.print("\n[bold yellow]Executing command...[/]")
                os.system(bash_command)

    except Exception as e:
        console.print(f"\n[bold red]Error:[/] {str(e)}")
        return 1

if __name__ == '__main__':
    cli()