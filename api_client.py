"""
Spoonacular API Client Module
Handles all API interactions with the Spoonacular recipe API.
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv


class SpoonacularAPIError(Exception):
    """Base exception for Spoonacular API-related errors."""


class SpoonacularQuotaExceededError(SpoonacularAPIError):
    """Raised when API quota is exhausted or rate limit is exceeded."""


class SpoonacularAPIClient:
    """Client for interacting with Spoonacular API."""
    
    BASE_URL = "https://api.spoonacular.com"
    
    def __init__(self):
        """Initialize the API client with credentials from environment."""
        load_dotenv()
        self.api_key = os.getenv('SPOONACULAR_API_KEY')
        
        if not self.api_key or self.api_key == 'your_api_key_here':
            raise ValueError(
                "SPOONACULAR_API_KEY not found or not set. "
                "Please copy .env.example to .env and add your API key."
            )

    def _parse_error_message(self, response: requests.Response) -> str:
        """Extract a readable error message from Spoonacular responses."""
        try:
            payload = response.json()
            if isinstance(payload, dict):
                if payload.get('message'):
                    return str(payload['message'])
                if payload.get('status'):
                    return str(payload['status'])
        except ValueError:
            pass

        text = response.text.strip()
        if text:
            return text[:300]
        return f"HTTP {response.status_code}"
    
    def search_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 20,
        filters: Optional[Dict[str, str]] = None
    ) -> List[Dict]:
        """
        Find recipes that use your ingredients, in a single request.

        complexSearch with fillIngredients and addRecipeInformation returns the
        used / missing ingredients and the recipe details together, about 2
        points per search. The old findByIngredients + per-recipe details
        approach cost ~13 points, against a 50 point daily free quota.

        Args:
            ingredients: Ingredients you have
            number: Number of candidates to return
            filters: Extra Spoonacular params from recipe_core.search_filters

        Returns:
            List of recipe dictionaries
        """
        endpoint = f"{self.BASE_URL}/recipes/complexSearch"

        params = {
            'apiKey': self.api_key,
            'includeIngredients': ','.join(ingredients),
            'number': number,
            'sort': 'max-used-ingredients',
            'fillIngredients': 'true',
            'addRecipeInformation': 'true',
            'ignorePantry': 'true',
            **(filters or {})
        }

        try:
            response = requests.get(endpoint, params=params, timeout=20)
            if response.status_code in (402, 429):
                raise SpoonacularQuotaExceededError(self._parse_error_message(response))
            response.raise_for_status()
            return response.json().get('results', [])
        except SpoonacularQuotaExceededError:
            raise
        except requests.exceptions.RequestException as e:
            raise SpoonacularAPIError(f"Error searching recipes: {e}") from e

    def complex_recipe_search(
        self,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        diet: Optional[str] = None,
        intolerances: Optional[str] = None,
        max_ready_time: Optional[int] = None,
        number: int = 10
    ) -> List[Dict]:
        """
        Perform a complex recipe search with multiple filters.
        
        Args:
            query: Search query (e.g., "pasta")
            cuisine: Cuisine type (e.g., "italian", "mexican")
            diet: Dietary restriction (e.g., "vegetarian", "vegan", "paleo")
            intolerances: Food intolerances (e.g., "gluten", "dairy")
            max_ready_time: Maximum prep time in minutes
            number: Number of results to return
            
        Returns:
            List of recipe dictionaries
        """
        endpoint = f"{self.BASE_URL}/recipes/complexSearch"
        
        params = {
            'apiKey': self.api_key,
            'number': number,
            'addRecipeInformation': 'true',
            'fillIngredients': 'true'
        }
        
        if query:
            params['query'] = query
        if cuisine:
            params['cuisine'] = cuisine
        if diet:
            params['diet'] = diet
        if intolerances:
            params['intolerances'] = intolerances
        if max_ready_time:
            params['maxReadyTime'] = max_ready_time
        
        try:
            response = requests.get(endpoint, params=params, timeout=20)
            if response.status_code in (402, 429):
                raise SpoonacularQuotaExceededError(self._parse_error_message(response))
            response.raise_for_status()
            return response.json().get('results', [])
        except SpoonacularQuotaExceededError:
            raise
        except requests.exceptions.RequestException as e:
            raise SpoonacularAPIError(f"Error performing complex search: {e}") from e
