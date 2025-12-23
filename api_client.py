"""
Spoonacular API Client Module
Handles all API interactions with the Spoonacular recipe API.
"""

import os
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv


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
    
    def search_recipes_by_ingredients(
        self,
        ingredients: List[str],
        number: int = 10,
        ranking: int = 1,
        ignore_pantry: bool = True
    ) -> List[Dict]:
        """
        Search for recipes based on available ingredients.
        
        Args:
            ingredients: List of ingredients to search with
            number: Number of results to return (default: 10)
            ranking: 1=maximize used ingredients, 2=minimize missing ingredients
            ignore_pantry: Whether to ignore typical pantry items
            
        Returns:
            List of recipe dictionaries
        """
        endpoint = f"{self.BASE_URL}/recipes/findByIngredients"
        
        params = {
            'apiKey': self.api_key,
            'ingredients': ','.join(ingredients),
            'number': number,
            'ranking': ranking,
            'ignorePantry': str(ignore_pantry).lower()
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error searching recipes: {e}")
            return []
    
    def get_recipe_information(
        self,
        recipe_id: int,
        include_nutrition: bool = False
    ) -> Optional[Dict]:
        """
        Get detailed information about a specific recipe.
        
        Args:
            recipe_id: The recipe ID
            include_nutrition: Whether to include nutritional information
            
        Returns:
            Recipe details dictionary or None if error
        """
        endpoint = f"{self.BASE_URL}/recipes/{recipe_id}/information"
        
        params = {
            'apiKey': self.api_key,
            'includeNutrition': str(include_nutrition).lower()
        }
        
        try:
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recipe details: {e}")
            return None
    
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
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            return response.json().get('results', [])
        except requests.exceptions.RequestException as e:
            print(f"Error performing complex search: {e}")
            return []
