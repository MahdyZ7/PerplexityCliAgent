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
    return f"""You are an expert Linux command line interface specialist. Your task is to translate the following natural language query into a precise bash command.

RULES:
1. Return ONLY the bash command without any explanations or additional text
2. The command must be prefixed with 'command:' (e.g., 'command: ls -la')
3. Focus on safety and best practices:
   - Add safeguards for destructive operations
   - Use appropriate flags for better usability
   - Prefer modern command alternatives when available
4. Keep commands concise but functional
5. Do not include sudo unless explicitly requested

USER QUERY:
{query}

RESPONSE FORMAT:
command: <the_command_here>"""

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
            "model": "llama-3.1-sonar-small-128k-chat",
            "messages": [{
                "role": "system",
                "content": "You are a Linux command-line expert that translates natural language to bash commands."
            }, {
                "role": "user",
                "content": format_query(query),
            }],
            "temperature": 0.1,  # Lower temperature for more deterministic outputs
            "max_tokens": 150,   # Increased slightly to accommodate longer commands
            "top_p": 0.9,       # Added for better response quality
            "presence_penalty": 0.1,  # Slight penalty to avoid repetitive responses
        }
        timeout = config.get('api.timeout', 30)
        response = requests.post(url, json=payload, headers=header, timeout=timeout)
        
        # Handle specific Perplexity API HTTP status codes
        status_errors = {
            400: "Bad request: Please check your query format",
            401: "Invalid API key or unauthorized access",
            403: "Access forbidden: Please check your API key permissions",
            404: "API endpoint not found: Please check the API URL",
            429: "API rate limit exceeded: Please try again later",
            500: "Internal server error: Please try again later",
            503: "Service unavailable: The API is temporarily down"
        }
        
        if response.status_code != 200:
            error_message = status_errors.get(
                response.status_code,
                f"API request failed with status code: {response.status_code}"
            )
            
            if response.status_code == 401:
                raise APIAuthenticationError(error_message)
            elif response.status_code == 429:
                raise APIRateLimitError(error_message)
            else:
                raise TranslationError(error_message)
                
        # Ensure we have a valid JSON response
        if not response.headers.get('content-type', '').startswith('application/json'):
            raise TranslationError("Invalid response format: expected JSON")
        
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
