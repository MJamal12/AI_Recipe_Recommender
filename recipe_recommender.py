"""
Recipe Recommender Engine
Core logic for processing and filtering recipe recommendations.
"""

import pandas as pd
from typing import List, Dict, Optional
from api_client import SpoonacularAPIClient


class RecipeRecommender:
    """Main recipe recommendation engine with intelligent filtering."""
    
    def __init__(self):
        """Initialize the recommender with API client."""
        self.api_client = SpoonacularAPIClient()
    
    def parse_ingredients(self, ingredient_string: str) -> List[str]:
        """
        Parse ingredient string with natural language processing.
        
        Handles flexible input like:
        - "chicken, rice, tomatoes"
        - "chicken rice tomatoes"
        - "chicken and rice and tomatoes"
        
        Args:
            ingredient_string: Raw ingredient string from user
            
        Returns:
            List of cleaned ingredient strings
        """
        # Replace common separators with commas
        ingredient_string = ingredient_string.replace(' and ', ',')
        ingredient_string = ingredient_string.replace(';', ',')
        
        # Split by comma and clean each ingredient
        ingredients = [
            ing.strip().lower() 
            for ing in ingredient_string.split(',') 
            if ing.strip()
        ]
        
        return ingredients
    
    def recommend_by_ingredients(
        self,
        ingredients: List[str],
        max_results: int = 10,
        diet: Optional[str] = None,
        intolerances: Optional[str] = None,
        max_time: Optional[int] = None,
        cuisine: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Get recipe recommendations based on ingredients with filters.
        
        Args:
            ingredients: List of available ingredients
            max_results: Maximum number of recipes to return
            diet: Dietary restriction filter
            intolerances: Food intolerance filter
            max_time: Maximum preparation time in minutes
            cuisine: Preferred cuisine type
            
        Returns:
            DataFrame with recipe recommendations
        """
        # First, search by ingredients
        recipes = self.api_client.search_recipes_by_ingredients(
            ingredients=ingredients,
            number=max_results * 2  # Get more to filter
        )
        
        if not recipes:
            return pd.DataFrame()
        
        # Get detailed information for each recipe
        detailed_recipes = []
        for recipe in recipes:
            details = self.api_client.get_recipe_information(recipe['id'])
            if details:
                # Merge basic info with details
                recipe_info = {
                    'id': recipe['id'],
                    'title': recipe['title'],
                    'image': recipe['image'],
                    'used_ingredients': len(recipe['usedIngredients']),
                    'missed_ingredients': len(recipe['missedIngredients']),
                    'missed_ingredient_names': ', '.join([
                        ing['name'] for ing in recipe['missedIngredients']
                    ]),
                    'ready_in_minutes': details.get('readyInMinutes', 'N/A'),
                    'servings': details.get('servings', 'N/A'),
                    'source_url': details.get('sourceUrl', ''),
                    'diets': ', '.join(details.get('diets', [])),
                    'cuisines': ', '.join(details.get('cuisines', [])),
                    'vegetarian': details.get('vegetarian', False),
                    'vegan': details.get('vegan', False),
                    'gluten_free': details.get('glutenFree', False),
                    'dairy_free': details.get('dairyFree', False)
                }
                detailed_recipes.append(recipe_info)
        
        if not detailed_recipes:
            return pd.DataFrame()
        
        # Convert to DataFrame for easier filtering
        df = pd.DataFrame(detailed_recipes)
        
        # Apply filters
        if diet:
            diet_lower = diet.lower()
            if diet_lower == 'vegetarian':
                df = df[df['vegetarian'] == True]
            elif diet_lower == 'vegan':
                df = df[df['vegan'] == True]
            elif diet_lower == 'gluten-free' or diet_lower == 'gluten free':
                df = df[df['gluten_free'] == True]
            elif diet_lower == 'dairy-free' or diet_lower == 'dairy free':
                df = df[df['dairy_free'] == True]
            else:
                # Check in diets column
                df = df[df['diets'].str.contains(diet_lower, case=False, na=False)]
        
        if max_time:
            # Filter by preparation time
            df = df[pd.to_numeric(df['ready_in_minutes'], errors='coerce') <= max_time]
        
        if cuisine:
            df = df[df['cuisines'].str.contains(cuisine, case=False, na=False)]
        
        # Sort by number of used ingredients (descending) and missed (ascending)
        df = df.sort_values(
            by=['used_ingredients', 'missed_ingredients'],
            ascending=[False, True]
        )
        
        return df.head(max_results)
    
    def search_recipes_complex(
        self,
        query: str,
        diet: Optional[str] = None,
        intolerances: Optional[str] = None,
        max_time: Optional[int] = None,
        cuisine: Optional[str] = None,
        max_results: int = 10
    ) -> pd.DataFrame:
        """
        Perform a complex recipe search without specific ingredients.
        
        Args:
            query: Search query (e.g., "pasta dinner")
            diet: Dietary restriction
            intolerances: Food intolerances
            max_time: Maximum preparation time
            cuisine: Cuisine preference
            max_results: Maximum results to return
            
        Returns:
            DataFrame with recipe results
        """
        recipes = self.api_client.complex_recipe_search(
            query=query,
            cuisine=cuisine,
            diet=diet,
            intolerances=intolerances,
            max_ready_time=max_time,
            number=max_results
        )
        
        if not recipes:
            return pd.DataFrame()
        
        # Extract relevant information
        recipe_list = []
        for recipe in recipes:
            recipe_info = {
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'ready_in_minutes': recipe.get('readyInMinutes', 'N/A'),
                'servings': recipe.get('servings', 'N/A'),
                'source_url': recipe.get('sourceUrl', ''),
                'diets': ', '.join(recipe.get('diets', [])),
                'cuisines': ', '.join(recipe.get('cuisines', [])),
                'vegetarian': recipe.get('vegetarian', False),
                'vegan': recipe.get('vegan', False),
                'summary': recipe.get('summary', '')
            }
            recipe_list.append(recipe_info)
        
        return pd.DataFrame(recipe_list)
    
    def format_recipe_output(self, df: pd.DataFrame, detailed: bool = False) -> str:
        """
        Format recipe DataFrame for console output.
        
        Args:
            df: DataFrame with recipe data
            detailed: Whether to show detailed information
            
        Returns:
            Formatted string for display
        """
        if df.empty:
            return "No recipes found matching your criteria."
        
        output = []
        output.append(f"\n{'='*80}")
        output.append(f"Found {len(df)} recipe(s):")
        output.append(f"{'='*80}\n")
        
        for idx, row in df.iterrows():
            output.append(f"📗 {row['title']}")
            
            if 'used_ingredients' in row:
                output.append(f"   ✓ Uses {row['used_ingredients']} of your ingredients")
                if row['missed_ingredients'] > 0:
                    output.append(f"   ✗ Missing: {row['missed_ingredient_names']}")
            
            if row.get('ready_in_minutes') != 'N/A':
                output.append(f"   ⏱  Ready in: {row['ready_in_minutes']} minutes")
            
            if row.get('servings') != 'N/A':
                output.append(f"   🍽  Servings: {row['servings']}")
            
            if row.get('diets'):
                output.append(f"   🥗 Diet: {row['diets']}")
            
            if row.get('cuisines'):
                output.append(f"   🌍 Cuisine: {row['cuisines']}")
            
            if row.get('source_url'):
                output.append(f"   🔗 Recipe: {row['source_url']}")
            
            output.append("")
        
        return '\n'.join(output)
