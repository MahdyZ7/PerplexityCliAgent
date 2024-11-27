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

def translate_to_bash(query: str) -> str:
    """
    Translate natural language query to bash command using Preplixity API
    
    Args:
        query: Natural language query to translate
        
    Returns:
        Translated bash command
        
    Raises:
        TranslationError: If translation fails
        APIAuthenticationError: If API authentication fails
        APIRateLimitError: If API rate limit is exceeded
    """
    if not API_KEY:
        raise APIAuthenticationError("API key not found in environment variables")
    
    try:
        response = requests.post(
            config.get('api.url'),
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "query": query,
                "target": "bash"
            },
            timeout=config.get('api.timeout', 30)
        )
        
        # Handle common HTTP errors
        if response.status_code == 401:
            raise APIAuthenticationError("Invalid API key or unauthorized access")
        elif response.status_code == 429:
            raise APIRateLimitError("API rate limit exceeded")
        
        response.raise_for_status()
        
        # Parse response
        try:
            result = response.json()
            if "command" not in result:
                raise TranslationError("Invalid API response: 'command' field missing")
            return result["command"]
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
