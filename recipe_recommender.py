"""
Recipe Recommender Engine
Connects the Spoonacular API client to the shared recipe_core logic for the CLI.
"""

import pandas as pd
from typing import List, Optional
from api_client import SpoonacularAPIClient
import recipe_core


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
        - "chicken and rice; tomatoes"
        - one ingredient per line

        Args:
            ingredient_string: Raw ingredient string from user

        Returns:
            List of cleaned ingredient strings
        """
        return recipe_core.parse_ingredients(ingredient_string)

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

        Two API calls total: one match search, one bulk detail lookup.

        Args:
            ingredients: List of available ingredients
            max_results: Maximum number of recipes to return
            diet: Dietary restriction filter
            intolerances: Unused for ingredient search (kept for CLI compatibility)
            max_time: Maximum preparation time in minutes
            cuisine: Preferred cuisine type

        Returns:
            DataFrame with recipe recommendations
        """
        found = self.api_client.search_recipes_by_ingredients(
            ingredients=ingredients,
            number=max_results * 2  # Get more to filter
        )
        if not found:
            return pd.DataFrame()

        details = self.api_client.get_recipe_information_bulk([r['id'] for r in found])

        return recipe_core.recommend(
            found,
            details,
            diet=diet,
            max_time=max_time,
            cuisine=cuisine,
            limit=max_results
        )

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

        recipe_list = []
        for recipe in recipes:
            recipe_list.append({
                'id': recipe['id'],
                'title': recipe['title'],
                'image': recipe.get('image', ''),
                'ready_in_minutes': recipe.get('readyInMinutes'),
                'servings': recipe.get('servings'),
                'source_url': recipe.get('sourceUrl', ''),
                'diets': recipe.get('diets', []),
                'cuisines': recipe.get('cuisines', []),
                'vegetarian': recipe.get('vegetarian', False),
                'vegan': recipe.get('vegan', False),
                'summary': recipe.get('summary', '')
            })

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

        for _, row in df.iterrows():
            output.append(f"📗 {row['title']}")

            if 'used_count' in row:
                total = row['used_count'] + row['missed_count']
                output.append(f"   ✓ You have {row['used_count']} of its {total} ingredients")
                if row['missed_count'] > 0:
                    output.append(f"   ✗ Missing: {', '.join(row['missed_names'])}")

            if pd.notna(row.get('ready_in_minutes')):
                output.append(f"   ⏱  Ready in: {row['ready_in_minutes']} minutes")

            if pd.notna(row.get('servings')):
                output.append(f"   🍽  Servings: {row['servings']}")

            if len(row.get('diets', [])):
                output.append(f"   🥗 Diet: {', '.join(row['diets'])}")

            if len(row.get('cuisines', [])):
                output.append(f"   🌍 Cuisine: {', '.join(row['cuisines'])}")

            if row.get('source_url'):
                output.append(f"   🔗 Recipe: {row['source_url']}")

            output.append("")

        return '\n'.join(output)
