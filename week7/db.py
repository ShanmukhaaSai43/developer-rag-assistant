"""
===================================================================
WEEK 7: SQLITE DATABASE LAYER
===================================================================
Connects to a real local SQLite database (`week7/data/recipes.db`).
Uses standard SQL queries to search recipes and fetch substitutions.
===================================================================
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

DB_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DB_DIR / "recipes.db"


def get_connection() -> sqlite3.Connection:
    """Returns a connection to the SQLite database, initializing if missing."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema and seeds initial recipe & substitution data."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table 1: Recipes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        base_servings INTEGER NOT NULL,
        ingredients_json TEXT NOT NULL,
        method_json TEXT NOT NULL
    )
    """)

    # Table 2: Substitutions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS substitutions (
        ingredient TEXT NOT NULL,
        allergen TEXT NOT NULL,
        substitute_name TEXT NOT NULL,
        ratio REAL NOT NULL,
        inherent_allergens_json TEXT NOT NULL,
        culinary_notes TEXT NOT NULL,
        PRIMARY KEY (ingredient, allergen)
    )
    """)

    # Seed recipes if empty
    cursor.execute("SELECT COUNT(*) as count FROM recipes")
    if cursor.fetchone()["count"] == 0:
        _seed_database(cursor)

    conn.commit()
    conn.close()


def _seed_database(cursor: sqlite3.Cursor):
    """Inserts starter recipes and substitutions into SQLite."""
    starter_recipes = [
        (
            "rec_pb_cookies",
            "Classic Peanut Butter Cookies",
            4,
            json.dumps([
                {"name": "peanut butter", "quantity": 250, "unit": "g", "allergens": ["peanuts"]},
                {"name": "granulated sugar", "quantity": 200, "unit": "g", "allergens": []},
                {"name": "egg", "quantity": 1, "unit": "whole", "allergens": ["eggs"]},
                {"name": "vanilla extract", "quantity": 5, "unit": "ml", "allergens": []}
            ]),
            json.dumps([
                "Preheat oven to 180C (350F).",
                "In a medium bowl, mix peanut butter, sugar, and egg until smooth.",
                "Roll mixture into small balls and place onto a lined baking sheet.",
                "Press criss-cross pattern using a fork.",
                "Bake for 10-12 minutes until edges are golden."
            ])
        ),
        (
            "rec_creamy_alfredo",
            "Fettuccine Alfredo",
            2,
            json.dumps([
                {"name": "fettuccine pasta", "quantity": 200, "unit": "g", "allergens": ["gluten"]},
                {"name": "heavy cream", "quantity": 150, "unit": "ml", "allergens": ["dairy"]},
                {"name": "parmesan cheese", "quantity": 60, "unit": "g", "allergens": ["dairy"]},
                {"name": "butter", "quantity": 30, "unit": "g", "allergens": ["dairy"]},
                {"name": "garlic", "quantity": 2, "unit": "cloves", "allergens": []}
            ]),
            json.dumps([
                "Boil fettuccine pasta in salted water until al dente.",
                "Melt butter in a pan over medium heat and sauté minced garlic.",
                "Stir in heavy cream and simmer for 2 minutes.",
                "Reduce heat, stir in grated parmesan cheese until creamy.",
                "Toss cooked pasta into sauce and season with black pepper."
            ])
        ),
        (
            "rec_classic_pesto",
            "Genovese Basil Pesto Pasta",
            4,
            json.dumps([
                {"name": "fresh basil leaves", "quantity": 60, "unit": "g", "allergens": []},
                {"name": "pine nuts", "quantity": 40, "unit": "g", "allergens": ["tree_nuts"]},
                {"name": "parmesan cheese", "quantity": 50, "unit": "g", "allergens": ["dairy"]},
                {"name": "extra virgin olive oil", "quantity": 100, "unit": "ml", "allergens": []},
                {"name": "garlic", "quantity": 2, "unit": "cloves", "allergens": []},
                {"name": "spaghetti", "quantity": 350, "unit": "g", "allergens": ["gluten"]}
            ]),
            json.dumps([
                "Toast pine nuts lightly in a dry skillet over medium heat.",
                "Blend basil, toasted pine nuts, garlic, and parmesan in a food processor.",
                "Slowly drizzle in olive oil while blending until emulsified.",
                "Toss with freshly boiled spaghetti and a splash of pasta water."
            ])
        ),
        (
            "rec_nutty_granola",
            "Honey Nut Breakfast Granola",
            6,
            json.dumps([
                {"name": "rolled oats", "quantity": 300, "unit": "g", "allergens": []},
                {"name": "almonds", "quantity": 100, "unit": "g", "allergens": ["tree_nuts"]},
                {"name": "honey", "quantity": 80, "unit": "ml", "allergens": []},
                {"name": "coconut oil", "quantity": 40, "unit": "ml", "allergens": []},
                {"name": "cinnamon", "quantity": 5, "unit": "g", "allergens": []}
            ]),
            json.dumps([
                "Preheat oven to 160C (320F).",
                "Combine oats, chopped almonds, honey, melted coconut oil, and cinnamon.",
                "Spread evenly across a baking tray.",
                "Bake for 20-25 minutes, stirring halfway through until golden brown."
            ])
        ),
        (
            "rec_sesame_noodles",
            "Cold Sesame Peanut Noodles",
            2,
            json.dumps([
                {"name": "ramen noodles", "quantity": 180, "unit": "g", "allergens": ["gluten"]},
                {"name": "peanut butter", "quantity": 60, "unit": "g", "allergens": ["peanuts"]},
                {"name": "sesame oil", "quantity": 15, "unit": "ml", "allergens": ["sesame"]},
                {"name": "soy sauce", "quantity": 20, "unit": "ml", "allergens": ["soy", "gluten"]},
                {"name": "toasted sesame seeds", "quantity": 10, "unit": "g", "allergens": ["sesame"]}
            ]),
            json.dumps([
                "Cook noodles until tender, drain and rinse under cold water.",
                "Whisk peanut butter, sesame oil, soy sauce, and 2 tbsp warm water into a smooth sauce.",
                "Toss cold noodles with sauce and garnish with toasted sesame seeds."
            ])
        ),
        (
            "rec_banana_pancakes",
            "Fluffy Banana Pancakes",
            3,
            json.dumps([
                {"name": "all-purpose flour", "quantity": 150, "unit": "g", "allergens": ["gluten"]},
                {"name": "ripe bananas", "quantity": 2, "unit": "whole", "allergens": []},
                {"name": "whole milk", "quantity": 180, "unit": "ml", "allergens": ["dairy"]},
                {"name": "egg", "quantity": 1, "unit": "whole", "allergens": ["eggs"]},
                {"name": "baking powder", "quantity": 8, "unit": "g", "allergens": []}
            ]),
            json.dumps([
                "Mash bananas in a large bowl.",
                "Whisk in egg and whole milk.",
                "Gently fold in flour and baking powder until just combined.",
                "Cook ladlefuls on a greased griddle over medium heat for 2-3 mins per side."
            ])
        )
    ]

    cursor.executemany(
        "INSERT INTO recipes VALUES (?, ?, ?, ?, ?)",
        starter_recipes
    )

    starter_subs = [
        ("peanut butter", "peanuts", "almond butter", 1.0, json.dumps(["tree_nuts"]), "Rich flavor, contains tree nuts."),
        ("almond butter", "tree_nuts", "sunflower seed butter", 1.0, json.dumps([]), "100% nut-free seed butter."),
        ("heavy cream", "dairy", "almond milk creamer", 1.0, json.dumps(["tree_nuts"]), "Silky base, contains tree nuts."),
        ("almond milk creamer", "tree_nuts", "canned coconut cream", 0.9, json.dumps([]), "Nut-free & dairy-free rich fat."),
        ("butter", "dairy", "vegan plant butter", 1.0, json.dumps([]), "Solid at room temp, melts identically."),
        ("parmesan cheese", "dairy", "nutritional yeast flakes", 0.5, json.dumps([]), "Savory, cheesy umami without dairy."),
        ("pine nuts", "tree_nuts", "toasted walnuts", 1.0, json.dumps(["tree_nuts"]), "Classic substitute, still a tree nut."),
        ("toasted walnuts", "tree_nuts", "toasted sunflower seeds", 1.0, json.dumps([]), "Crisp texture, nut-free."),
        ("almonds", "tree_nuts", "pumpkin seeds", 1.0, json.dumps([]), "Nut-free crunch."),
        ("fettuccine pasta", "gluten", "gluten-free corn fettuccine", 1.0, json.dumps([]), "Maintains toothsome bite."),
        ("spaghetti", "gluten", "brown rice spaghetti", 1.0, json.dumps([]), "Mild gluten-free pasta."),
        ("all-purpose flour", "gluten", "1-to-1 gluten-free baking blend", 1.0, json.dumps([]), "Includes xanthan gum."),
        ("egg", "eggs", "flax egg (1 tbsp ground flax + 3 tbsp water)", 1.0, json.dumps([]), "Plant binding agent."),
        ("whole milk", "dairy", "unsweetened oat milk", 1.0, json.dumps([]), "Creamy neutral dairy-free milk."),
        ("sesame oil", "sesame", "toasted peanut oil", 1.0, json.dumps(["peanuts"]), "Deep toasted aroma, contains peanuts."),
        ("toasted peanut oil", "peanuts", "perilla seed oil", 1.0, json.dumps([]), "Nut-free & sesame-free toasted oil."),
        ("toasted sesame seeds", "sesame", "toasted hemp seeds", 1.0, json.dumps([]), "Tiny nutty crunch without sesame."),
        ("soy sauce", "soy", "coconut aminos", 1.0, json.dumps([]), "Soy-free savory seasoning."),
        ("soy sauce", "gluten", "tamari (gluten-free)", 1.0, json.dumps(["soy"]), "Rich soy sauce without wheat.")
    ]

    cursor.executemany(
        "INSERT INTO substitutions VALUES (?, ?, ?, ?, ?, ?)",
        starter_subs
    )


# ===================================================================
# SQL QUERY HELPERS (Real SQL queries called by our tools)
# ===================================================================

def search_recipes_in_db(query: str) -> List[Dict[str, Any]]:
    """SQL query to find recipes matching a title or keyword."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    clean_q = f"%{query.lower().strip()}%"
    cursor.execute("""
        SELECT * FROM recipes 
        WHERE LOWER(title) LIKE ? OR LOWER(id) LIKE ? OR LOWER(ingredients_json) LIKE ?
    """, (clean_q, clean_q, clean_q))
    
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "id": r["id"],
            "title": r["title"],
            "base_servings": r["base_servings"],
            "ingredients": json.loads(r["ingredients_json"]),
            "method": json.loads(r["method_json"])
        })
    conn.close()
    return results


def get_recipe_by_id(recipe_id: str) -> Optional[Dict[str, Any]]:
    """SQL query to fetch a single recipe by its primary key ID."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM recipes WHERE id = ?", (recipe_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "base_servings": row["base_servings"],
        "ingredients": json.loads(row["ingredients_json"]),
        "method": json.loads(row["method_json"])
    }


def get_substitution_from_db(ingredient_name: str, allergen: str) -> Optional[Dict[str, Any]]:
    """SQL query to find an allergen substitution for an ingredient."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM substitutions 
        WHERE LOWER(ingredient) = ? AND LOWER(allergen) = ?
    """, (ingredient_name.lower().strip(), allergen.lower().strip()))
    
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "substitute_name": row["substitute_name"],
        "ratio": row["ratio"],
        "inherent_allergens": json.loads(row["inherent_allergens_json"]),
        "culinary_notes": row["culinary_notes"]
    }
