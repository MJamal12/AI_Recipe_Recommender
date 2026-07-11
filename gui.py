# gui.py
"""
Streamlit GUI for AI Recipe Recommender
A sleek, modern web interface for recipe discovery.
"""

import streamlit as st
from recipe_recommender import RecipeRecommender
import pandas as pd
from PIL import Image
import requests
from io import BytesIO
from api_client import SpoonacularAPIError, SpoonacularQuotaExceededError

# Page configuration
st.set_page_config(
    page_title="AI Recipe Recommender",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #FF6B6B;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .recipe-card {
        border-radius: 10px;
        padding: 20px;
        background-color: #f8f9fa;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin: 10px 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: bold;
        border-radius: 10px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'recommender' not in st.session_state:
    try:
        st.session_state.recommender = RecipeRecommender()
        st.session_state.initialized = True
    except ValueError as e:
        st.session_state.initialized = False
        st.session_state.error = str(e)

def load_image_from_url(url):
    """Load image from URL for display."""
    try:
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        return img
    except:
        return None

def render_image_compat(image):
    """Render image with compatibility across Streamlit versions."""
    try:
        st.image(image, use_container_width=True)
    except TypeError:
        # Older Streamlit versions use use_column_width instead.
        st.image(image, use_column_width=True)

def display_recipe_card(recipe):
    """Display a single recipe in a beautiful card format."""
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if recipe.get('image'):
            img = load_image_from_url(recipe['image'])
            if img:
                render_image_compat(img)
    
    with col2:
        st.markdown(f"### {recipe['title']}")
        
        # Recipe metadata
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric("⏱️ Ready in", f"{recipe.get('ready_in_minutes', 'N/A')} min")
        with col_b:
            st.metric("🍽️ Servings", recipe.get('servings', 'N/A'))
        with col_c:
            st.metric("✅ Used", f"{recipe.get('used_ingredients', 0)} ingredients")
        
        # Missing ingredients
        if recipe.get('missed_ingredient_names'):
            st.markdown(f"**Missing:** {recipe['missed_ingredient_names']}")
        
        # Dietary info
        tags = []
        if recipe.get('vegetarian'):
            tags.append("🌱 Vegetarian")
        if recipe.get('vegan'):
            tags.append("🥬 Vegan")
        if recipe.get('gluten_free'):
            tags.append("🌾 Gluten-Free")
        
        if tags:
            st.markdown(" | ".join(tags))
        
        # Link to recipe
        if recipe.get('source_url'):
            st.markdown(f"[🔗 View Full Recipe]({recipe['source_url']})")
    
    st.markdown("---")

def main():
    """Main application interface."""
    
    # Header
    st.markdown('<h1 class="main-header">🍳 AI Recipe Recommender</h1>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #666;'>Discover delicious recipes based on your ingredients</p>", unsafe_allow_html=True)
    
    # Check if initialized
    if not st.session_state.initialized:
        st.error("⚠️ API Error: " + st.session_state.error)
        st.info("Please set up your `.env` file with a valid SPOONACULAR_API_KEY")
        return
    
    # Sidebar for filters
    with st.sidebar:
        st.header("🔍 Search Options")
        
        search_mode = st.radio(
            "Search by:",
            ["Ingredients", "Recipe Name"],
            help="Choose how you want to search for recipes"
        )
        
        st.markdown("---")
        st.header("🎛️ Filters")
        
        # Common filters
        num_results = st.slider("Number of results", 1, 20, 10)
        max_time = st.number_input("Max prep time (minutes)", min_value=0, value=0, step=5)
        if max_time == 0:
            max_time = None
        
        diet = st.selectbox(
            "Dietary Restriction",
            ["None", "vegetarian", "vegan", "paleo", "ketogenic", "gluten-free", "dairy-free"]
        )
        diet = None if diet == "None" else diet
        
        cuisine = st.text_input("Cuisine (e.g., italian, mexican)")
        cuisine = cuisine if cuisine else None
        
        intolerances = st.text_input("Intolerances (e.g., gluten, dairy)")
        intolerances = intolerances if intolerances else None
    
    # Main search area
    st.markdown("---")
    
    if search_mode == "Ingredients":
        st.subheader("🥗 What ingredients do you have?")
        ingredients_input = st.text_input(
            "Enter ingredients (comma-separated)",
            placeholder="e.g., chicken, rice, tomatoes, garlic",
            help="List all the ingredients you want to use"
        )
        
        search_button = st.button("🔍 Find Recipes", type="primary")
        
        if search_button and ingredients_input:
            with st.spinner("🍳 Searching for delicious recipes..."):
                try:
                    ingredients = st.session_state.recommender.parse_ingredients(ingredients_input)
                    
                    results = st.session_state.recommender.recommend_by_ingredients(
                        ingredients=ingredients,
                        max_results=num_results,
                        diet=diet,
                        intolerances=intolerances,
                        max_time=max_time,
                        cuisine=cuisine
                    )
                except SpoonacularQuotaExceededError:
                    st.error(
                        "Spoonacular API limit reached. "
                        "Free plan requests are exhausted for now. "
                        "Please wait for your quota reset, use a different API key, or upgrade your plan."
                    )
                    return
                except SpoonacularAPIError as e:
                    st.error(f"API request failed: {e}")
                    return
                
                if results.empty:
                    st.warning("No recipes found. Try different ingredients or filters.")
                else:
                    st.success(f"Found {len(results)} recipes!")
                    
                    # Display results
                    for _, recipe in results.iterrows():
                        display_recipe_card(recipe.to_dict())
                    
                    # Export option
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results (CSV)",
                        data=csv,
                        file_name="recipe_results.csv",
                        mime="text/csv"
                    )
    
    else:  # Recipe Name search
        st.subheader("🔎 Search for a Recipe")
        query = st.text_input(
            "Enter recipe name or type",
            placeholder="e.g., chocolate cake, pasta carbonara",
            help="Search for recipes by name or type"
        )
        
        search_button = st.button("🔍 Search Recipes", type="primary")
        
        if search_button and query:
            with st.spinner("🍳 Searching for recipes..."):
                try:
                    results = st.session_state.recommender.search_recipes_complex(
                        query=query,
                        max_results=num_results,
                        diet=diet,
                        intolerances=intolerances,
                        max_time=max_time,
                        cuisine=cuisine
                    )
                except SpoonacularQuotaExceededError:
                    st.error(
                        "Spoonacular API limit reached. "
                        "Free plan requests are exhausted for now. "
                        "Please wait for your quota reset, use a different API key, or upgrade your plan."
                    )
                    return
                except SpoonacularAPIError as e:
                    st.error(f"API request failed: {e}")
                    return
                
                if results.empty:
                    st.warning("No recipes found. Try different keywords or filters.")
                else:
                    st.success(f"Found {len(results)} recipes!")
                    
                    # Display results
                    for _, recipe in results.iterrows():
                        display_recipe_card(recipe.to_dict())
                    
                    # Export option
                    csv = results.to_csv(index=False)
                    st.download_button(
                        label="📥 Download Results (CSV)",
                        data=csv,
                        file_name="recipe_results.csv",
                        mime="text/csv"
                    )
    
    # Footer
    st.markdown("---")
    st.markdown("<p style='text-align: center; color: #999;'>Powered by Spoonacular API</p>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()