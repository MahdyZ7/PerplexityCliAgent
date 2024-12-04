import os
import requests
from typing import Optional
from config import config

# Get API key from environment
API_KEY = os.environ.get('PREPLIXITY_API_KEY')

class TranslationError(Exception):
    """Custom exception for translation errors"""
    pass

class APIAuthenticationError(TranslationError):
    """Raised when API authentication fails"""
    pass

class APIRateLimitError(TranslationError):
    """Raised when API rate limit is exceeded"""
    pass

def format_query(query: str) -> str:
    """Format the query for the API"""
    return f"""GENERAL INSTRUCTIONS
You are a Linux command-line expert. Your task is to translate a natural language query into a precise bash command.

RULES:
1. Return only the bash command without any explanations
2. Format your response starting with 'command:' followed by the actual command
3. Ensure the command is safe and follows best practices
4. Use appropriate flags and options for better usability
5. For destructive operations (delete, modify), add safeguards when possible

USER QUESTION:
{query}

ANSWER FORMAT:
command:"""

def translate_to_bash(query: str) -> str:
    """
    Translate natural language query to bash command using Preplixity API
    
    Args:
        query: Natural language query to translate
        
    Returns:
        str: A valid bash command translated from the natural language query
        
    Raises:
        TranslationError: If the translation process fails or returns invalid output
        APIAuthenticationError: If the API key is invalid or missing
        APIRateLimitError: If the API rate limit is exceeded
        requests.exceptions.RequestException: For network-related errors
        
    Examples:
        >>> translate_to_bash("show me all files in current directory")
        'ls -la'
        >>> translate_to_bash("create a new folder called test")
        'mkdir test'
    """
    if not isinstance(query, str) or not query.strip():
        raise ValueError("Query must be a non-empty string")
        
    if not API_KEY:
        raise APIAuthenticationError(
            "API key not found. Please set the PREPLIXITY_API_KEY environment variable."
        )
    
    try:
        url = config.get('api.url', "https://api.perplexity.ai/chat/completions")
        header = {
            "Authorization": f"Bearer {API_KEY}",
        }
        payload = {
            "model": "mistral-7b-instruct",  # Using Mistral model for better command generation
            "messages": [{
                "role": "system",
                "content": "You are a Linux command-line expert that translates natural language to bash commands."
            }, {
                "role": "user",
                "content": format_query(query),
            }],
            "temperature": 0.1,  # Lower temperature for more deterministic outputs
            "max_tokens": 100,   # Limit response length since we only need the command
        }
        timeout = config.get('api.timeout', 30)
        response = requests.post(url, json=payload, headers=header, timeout=timeout)
        
        # Handle common HTTP errors
        if response.status_code == 401:
            raise APIAuthenticationError("Invalid API key or unauthorized access")
        elif response.status_code == 429:
            raise APIRateLimitError("API rate limit exceeded")
        
        response.raise_for_status()
        
        # Parse response
        try:
            result = response.json()
            
            # Validate response structure according to Perplexity AI format
            if not isinstance(result, dict):
                raise TranslationError("Invalid API response: expected JSON object")
                
            choices = result.get("choices", [])
            if not choices or not isinstance(choices, list):
                raise TranslationError(f"Invalid API response: missing or invalid 'choices' field. Response: {result}")
                
            choice = choices[0]
            if not isinstance(choice, dict):
                raise TranslationError("Invalid API response: first choice is not an object")
                
            message = choice.get("message", {})
            if not isinstance(message, dict):
                raise TranslationError("Invalid API response: message is not an object")
                
            content = message.get("content", "").strip()
            if not content:
                raise TranslationError("Empty response received from API")
            
            # Extract command after the prefix "command:"
            if "command:" in content:
                command = content.split("command:", 1)[1].strip()
            else:
                # Fallback: assume the entire response is the command
                command = content.strip()
                
            # Validate the extracted command
            if not command:
                raise TranslationError("Empty command received from API")
                
            # Basic command validation
            if len(command.split()) > 50:  # Arbitrary limit to catch unreasonable responses
                raise TranslationError("Generated command is suspiciously long")
                
            # Check for potentially dangerous commands
            dangerous_patterns = ["rm -rf /", "rm -rf /*", "> /dev/sda"]
            if any(pattern in command for pattern in dangerous_patterns):
                raise TranslationError("Generated command contains potentially dangerous operations")
                
            return command
        except ValueError as e:
            raise TranslationError(f"Invalid JSON response from API: {str(e)}")
            
    except requests.exceptions.Timeout:
        raise TranslationError("API request timed out")
    except requests.exceptions.ConnectionError:
        raise TranslationError("Could not connect to the API server")
    except requests.exceptions.RequestException as e:
        raise TranslationError(f"API request failed: {str(e)}")
    except Exception as e:
        raise TranslationError(f"Translation failed: {str(e)}")
