# 🍳 AI-Powered Recipe Recommender

A Python-based command-line tool that suggests recipes based on available ingredients using the Spoonacular API. Features intelligent filtering for dietary restrictions, prep time, and cuisine preferences with natural language processing for flexible user input.

## Features

- 🔍 **Ingredient-Based Search**: Find recipes using ingredients you already have
- 🥗 **Dietary Filters**: Support for vegetarian, vegan, paleo, ketogenic, gluten-free, and dairy-free diets
- ⏱️ **Time Constraints**: Filter recipes by maximum preparation time
- 🌍 **Cuisine Preferences**: Search by specific cuisine types (Italian, Mexican, Asian, etc.)
- 🧠 **Natural Language Processing**: Flexible ingredient input parsing
- 📊 **Smart Ranking**: Recipes ranked by ingredient match and missing ingredients
- 💾 **Export Results**: Save search results to CSV for later reference
- 🎨 **Colorful CLI**: Easy-to-read, color-coded terminal interface

## Technologies Used

- **Python 3.8+**: Core programming language
- **Spoonacular API**: Recipe and food data source
- **pandas**: Data manipulation and filtering
- **requests**: HTTP API communication
- **argparse**: CLI argument parsing
- **python-dotenv**: Secure environment variable management
- **colorama**: Cross-platform colored terminal output

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ai-recipe-recommender.git
cd ai-recipe-recommender
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

1. Get a free API key from [Spoonacular](https://spoonacular.com/food-api)
2. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your API key:
   ```
   SPOONACULAR_API_KEY=your_actual_api_key_here
   ```

## Usage

### Basic Commands

#### Search by Ingredients

```bash
python main.py -i "chicken, rice, tomatoes"
```

#### Search by Recipe Name

```bash
python main.py -q "chocolate cake"
```

### Advanced Filtering

#### Add Dietary Restrictions

```bash
python main.py -i "pasta, cheese, spinach" -d vegetarian
```

#### Filter by Prep Time

```bash
python main.py -i "beef, potatoes, carrots" -t 30
```

#### Specify Cuisine

```bash
python main.py -i "chicken, soy sauce, ginger" -c asian
```

#### Combine Multiple Filters

```bash
python main.py -i "eggs, milk, flour" -d vegetarian -t 20 -n 5
```

#### Handle Food Intolerances

```bash
python main.py -q "pasta dinner" --intolerances "gluten,dairy"
```

### Command-Line Arguments

| Argument | Short | Description |
|----------|-------|-------------|
| `--ingredients` | `-i` | Comma-separated list of ingredients |
| `--query` | `-q` | Search query for recipe name or type |
| `--number` | `-n` | Number of recipes to return (default: 10) |
| `--diet` | `-d` | Dietary restriction (vegetarian, vegan, paleo, ketogenic, gluten-free, dairy-free) |
| `--time` | `-t` | Maximum preparation time in minutes |
| `--cuisine` | `-c` | Cuisine preference (italian, mexican, asian, indian, etc.) |
| `--intolerances` | | Food intolerances (gluten, dairy, egg, peanut, etc.) |
| `--no-banner` | | Suppress the application banner |
| `--help` | `-h` | Show help message |

### Example Output

```
================================================================================
   🍳  AI-POWERED RECIPE RECOMMENDER  🍳
================================================================================

Initializing recipe recommender...
Searching recipes with your ingredients...
Ingredients: chicken, rice, tomatoes

================================================================================
Found 5 recipe(s):
================================================================================

📗 Chicken and Rice with Tomatoes
   ✓ Uses 3 of your ingredients
   ⏱  Ready in: 35 minutes
   🍽  Servings: 4
   🔗 Recipe: https://spoonacular.com/...

📗 Spanish Chicken Rice
   ✓ Uses 3 of your ingredients
   ✗ Missing: onion, garlic
   ⏱  Ready in: 40 minutes
   🍽  Servings: 6
   🥗 Diet: gluten-free
   🔗 Recipe: https://spoonacular.com/...
```

## Project Structure

```
Ai_Recipe/
├── main.py                    # CLI entry point with argparse
├── recipe_recommender.py      # Core recommendation engine
├── api_client.py              # Spoonacular API wrapper
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore rules
└── README.md                 # This file
```

## Architecture

### Modular Design

- **api_client.py**: Encapsulates all Spoonacular API interactions
  - Ingredient-based search
  - Recipe detail retrieval
  - Complex search with multiple filters
  
- **recipe_recommender.py**: Core business logic
  - Natural language ingredient parsing
  - Intelligent recipe filtering
  - Data processing with pandas
  - Output formatting
  
- **main.py**: User interface layer
  - CLI argument parsing with argparse
  - User interaction
  - Error handling
  - Result display

### Security

- API keys managed through environment variables using `python-dotenv`
- `.env` file excluded from version control via `.gitignore`
- No hardcoded credentials in source code

## Development

### Setting Up for Development

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Run tests (if available)
5. Commit: `git commit -m "Add feature description"`
6. Push: `git push origin feature-name`
7. Create a Pull Request

### Future Enhancements

- [ ] Add unit tests with pytest
- [ ] Implement caching for API responses
- [ ] Add recipe rating and sorting
- [ ] Support for meal planning
- [ ] Interactive mode with prompts
- [ ] GUI version with Tkinter or web interface
- [ ] Nutritional information display
- [ ] Shopping list generation

## API Limits

The Spoonacular API free tier includes:
- 150 requests per day
- 1 request per second rate limit

Plan your searches accordingly or upgrade to a paid plan for more requests.

## Troubleshooting

### API Key Error

```
Error: SPOONACULAR_API_KEY not found or not set.
```

**Solution**: Ensure you've created a `.env` file with your API key (see Installation step 4).

### No Results Found

If searches return no results:
- Try broader ingredient combinations
- Remove strict filters (diet, time, cuisine)
- Check for typos in ingredient names
- Verify your API key is valid and has remaining requests

### Import Errors

```
ModuleNotFoundError: No module named 'requests'
```

**Solution**: Install dependencies: `pip install -r requirements.txt`

## License

This project is open source and available under the [MIT License](LICENSE).

## Acknowledgments

- [Spoonacular API](https://spoonacular.com/food-api) for providing recipe data
- Built as a demonstration of Python CLI development, API integration, and data processing

## Contact

For questions or suggestions, please open an issue on GitHub.

---

**Happy Cooking! 🍳👨‍🍳👩‍🍳**
