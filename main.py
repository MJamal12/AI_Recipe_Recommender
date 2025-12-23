"""
AI-Powered Recipe Recommender CLI
Main entry point for the command-line interface.
"""

import argparse
import sys
from colorama import init, Fore, Style
from recipe_recommender import RecipeRecommender


# Initialize colorama for cross-platform colored output
init(autoreset=True)


def print_banner():
    """Display application banner."""
    banner = f"""
{Fore.GREEN}{'='*80}
   🍳  AI-POWERED RECIPE RECOMMENDER  🍳
{'='*80}{Style.RESET_ALL}
"""
    print(banner)


def main():
    """Main CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description='AI-Powered Recipe Recommender - Find recipes based on your ingredients',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find recipes with specific ingredients
  python main.py -i "chicken, rice, tomatoes" -n 5
  
  # Add dietary restrictions
  python main.py -i "pasta, cheese" -d vegetarian
  
  # Filter by prep time and cuisine
  python main.py -i "beef, potatoes" -t 30 -c italian
  
  # Search by recipe name with filters
  python main.py -q "chocolate cake" -d gluten-free -t 60
  
  # Combine multiple filters
  python main.py -i "eggs, milk, flour" -d vegetarian -t 20 -n 10
        """
    )
    
    # Main search options
    search_group = parser.add_mutually_exclusive_group(required=True)
    search_group.add_argument(
        '-i', '--ingredients',
        type=str,
        help='Comma-separated list of ingredients (e.g., "chicken, rice, tomatoes")'
    )
    search_group.add_argument(
        '-q', '--query',
        type=str,
        help='Search query for recipe name or type (e.g., "pasta carbonara")'
    )
    
    # Filter options
    parser.add_argument(
        '-n', '--number',
        type=int,
        default=10,
        help='Number of recipes to return (default: 10)'
    )
    parser.add_argument(
        '-d', '--diet',
        type=str,
        choices=['vegetarian', 'vegan', 'paleo', 'ketogenic', 'gluten-free', 'dairy-free'],
        help='Dietary restriction filter'
    )
    parser.add_argument(
        '-t', '--time',
        type=int,
        help='Maximum preparation time in minutes'
    )
    parser.add_argument(
        '-c', '--cuisine',
        type=str,
        help='Cuisine preference (e.g., italian, mexican, asian, indian)'
    )
    parser.add_argument(
        '--intolerances',
        type=str,
        help='Food intolerances (e.g., gluten, dairy, egg, peanut)'
    )
    parser.add_argument(
        '--no-banner',
        action='store_true',
        help='Suppress the application banner'
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Display banner
    if not args.no_banner:
        print_banner()
    
    try:
        # Initialize recommender
        print(f"{Fore.CYAN}Initializing recipe recommender...{Style.RESET_ALL}")
        recommender = RecipeRecommender()
        
        # Perform search based on mode
        if args.ingredients:
            print(f"{Fore.CYAN}Searching recipes with your ingredients...{Style.RESET_ALL}")
            ingredients = recommender.parse_ingredients(args.ingredients)
            print(f"{Fore.YELLOW}Ingredients: {', '.join(ingredients)}{Style.RESET_ALL}")
            
            # Apply filters if specified
            filters = []
            if args.diet:
                filters.append(f"Diet: {args.diet}")
            if args.time:
                filters.append(f"Max time: {args.time} min")
            if args.cuisine:
                filters.append(f"Cuisine: {args.cuisine}")
            if args.intolerances:
                filters.append(f"Intolerances: {args.intolerances}")
            
            if filters:
                print(f"{Fore.YELLOW}Filters: {', '.join(filters)}{Style.RESET_ALL}")
            
            results = recommender.recommend_by_ingredients(
                ingredients=ingredients,
                max_results=args.number,
                diet=args.diet,
                intolerances=args.intolerances,
                max_time=args.time,
                cuisine=args.cuisine
            )
        
        else:  # args.query
            print(f"{Fore.CYAN}Searching recipes for: '{args.query}'...{Style.RESET_ALL}")
            
            filters = []
            if args.diet:
                filters.append(f"Diet: {args.diet}")
            if args.time:
                filters.append(f"Max time: {args.time} min")
            if args.cuisine:
                filters.append(f"Cuisine: {args.cuisine}")
            if args.intolerances:
                filters.append(f"Intolerances: {args.intolerances}")
            
            if filters:
                print(f"{Fore.YELLOW}Filters: {', '.join(filters)}{Style.RESET_ALL}")
            
            results = recommender.search_recipes_complex(
                query=args.query,
                diet=args.diet,
                intolerances=args.intolerances,
                max_time=args.time,
                cuisine=args.cuisine,
                max_results=args.number
            )
        
        # Display results
        output = recommender.format_recipe_output(results)
        print(output)
        
        # Export option
        if not results.empty:
            export = input(f"\n{Fore.CYAN}Export results to CSV? (y/n): {Style.RESET_ALL}").lower()
            if export == 'y':
                filename = 'recipe_results.csv'
                results.to_csv(filename, index=False)
                print(f"{Fore.GREEN}✓ Results exported to {filename}{Style.RESET_ALL}")
        
    except ValueError as e:
        print(f"{Fore.RED}Error: {e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Please make sure you have set up your .env file with a valid API key.{Style.RESET_ALL}")
        sys.exit(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Search cancelled by user.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == '__main__':
    main()
