"""
=============================================================================
WEEK 12 - STEP 1: INITIALIZE RECIPES & SAFETY DATABASE
=============================================================================
Creates the local SQLite database (week12/data/recipes.db) containing:
1. The recipes catalog with explicit versioning (original vs. reformulated-2025)
2. Exact-match structured allergen declarations (contains, may_contain)
3. Safe minimum internal cooking temperatures (Food Safety Rules, e.g., Poultry 74°C)
4. Test kitchen ingredient substitutions with inherent allergen flags
=============================================================================
"""

import os
import sqlite3
import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "recipes.db"

def init_database():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    if DB_PATH.exists():
        DB_PATH.unlink()  # Clean refresh for Step 1
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. RECIPES TABLE
    cursor.execute("""
    CREATE TABLE recipes (
        id TEXT PRIMARY KEY,
        recipe_key TEXT NOT NULL,
        title TEXT NOT NULL,
        version TEXT NOT NULL,           -- 'original' or 'reformulated-2025'
        is_current INTEGER NOT NULL,     -- 1 = current production, 0 = superseded
        prep_time_minutes INTEGER NOT NULL,
        cook_time_minutes INTEGER NOT NULL,
        base_servings INTEGER NOT NULL,
        ingredients_json TEXT NOT NULL,   -- List of {name, quantity, unit}
        allergens_contains TEXT NOT NULL, -- JSON List e.g. ["dairy", "gluten"]
        allergens_may_contain TEXT NOT NULL, -- JSON List e.g. ["sesame"]
        method_json TEXT NOT NULL,        -- List of step instructions
        safe_internal_temp_c REAL,       -- Critical food safety temp (e.g. 74.0 for chicken)
        reformulation_notes TEXT
    );
    """)

    # 2. FOOD SAFETY INTERNAL TEMPERATURES TABLE
    cursor.execute("""
    CREATE TABLE food_safety_temps (
        category TEXT PRIMARY KEY,
        item_name TEXT NOT NULL,
        min_internal_temp_c REAL NOT NULL,
        min_internal_temp_f REAL NOT NULL,
        legal_mandate TEXT NOT NULL
    );
    """)

    # 3. KITCHEN SUBSTITUTIONS TABLE (with inherent allergen tracking)
    cursor.execute("""
    CREATE TABLE substitutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_ingredient TEXT NOT NULL,
        substitute_name TEXT NOT NULL,
        ratio REAL NOT NULL,
        inherent_allergens TEXT NOT NULL,  -- JSON list of allergens the substitute introduces
        culinary_notes TEXT
    );
    """)

    # ---------------------------------------------------------
    # SEED DATA: RECIPES (Including the core Shortbread trap)
    # ---------------------------------------------------------
    recipes_seed = [
        # 1. CLASSIC SCOTTISH SHORTBREAD - ORIGINAL (NUT-FREE, DAIRY BUTTER)
        (
            "rcp_shortbread_orig",
            "shortbread",
            "Classic Scottish Shortbread",
            "original",
            0,  # superseded
            15,
            25,
            8,
            json.dumps([
                {"name": "All-Purpose Flour", "quantity": 250, "unit": "g"},
                {"name": "Grass-Fed Butter", "quantity": 175, "unit": "g"},
                {"name": "Caster Sugar", "quantity": 75, "unit": "g"},
                {"name": "Fine Sea Salt", "quantity": 2, "unit": "g"}
            ]),
            json.dumps(["gluten", "dairy"]),
            json.dumps(["sesame"]),
            json.dumps([
                "Cream the butter and caster sugar together until pale and smooth.",
                "Sift in flour and salt, working gently until a tender short dough forms.",
                "Press into an 8-inch round tin and prick all over with a fork.",
                "Bake at 160°C (320°F) for 25 minutes until pale golden. Never scale bake time."
            ]),
            None,
            "Superseded version before supplier change. Made with dairy butter."
        ),

        # 2. CLASSIC SCOTTISH SHORTBREAD - REFORMULATED-2025 (CONTAINS TREE NUTS!)
        (
            "rcp_shortbread_2025",
            "shortbread",
            "Classic Scottish Shortbread (2025 Reformulated)",
            "reformulated-2025",
            1,  # current production
            15,
            25,
            8,
            json.dumps([
                {"name": "All-Purpose Flour", "quantity": 250, "unit": "g"},
                {"name": "Macadamia & Walnut Oil Shortening Blend", "quantity": 175, "unit": "g"},
                {"name": "Caster Sugar", "quantity": 75, "unit": "g"},
                {"name": "Fine Sea Salt", "quantity": 2, "unit": "g"}
            ]),
            json.dumps(["gluten", "tree_nuts"]),  # NOW CONTAINS TREE NUTS!
            json.dumps(["sesame", "peanuts"]),
            json.dumps([
                "Cream the nut-oil shortening blend and caster sugar until smooth.",
                "Sift in flour and salt, working gently until tender dough forms.",
                "Press into an 8-inch round tin and prick all over with a fork.",
                "Bake at 160°C (320°F) for 25 minutes until pale golden. Never scale bake time."
            ]),
            None,
            "2025 supplier reformulation swapped dairy butter for macadamia & walnut oil blend. CONTAINS TREE NUTS."
        ),

        # 3. ROAST HERB CHICKEN (CRITICAL 74°C INTERNAL TEMPERATURE REQUIREMENT)
        (
            "rcp_roast_chicken_orig",
            "roast_chicken",
            "Crispy Roast Herb Chicken",
            "original",
            1,
            15,
            45,
            4,
            json.dumps([
                {"name": "Whole Chicken Breasts / Thighs", "quantity": 800, "unit": "g"},
                {"name": "Olive Oil", "quantity": 30, "unit": "ml"},
                {"name": "Fresh Rosemary & Thyme", "quantity": 15, "unit": "g"},
                {"name": "Garlic Cloves", "quantity": 4, "unit": "cloves"},
                {"name": "Kosher Salt", "quantity": 8, "unit": "g"}
            ]),
            json.dumps([]),  # Allergen free
            json.dumps([]),
            json.dumps([
                "Pat chicken completely dry and rub with olive oil, salt, and minced herbs.",
                "Sear skin-side down in cast iron skillet for 6 minutes until deeply browned.",
                "Transfer to oven at 200°C (400°F) for 35-40 minutes.",
                "CRITICAL FOOD SAFETY: Insert probe thermometer into thickest part. Chicken MUST reach 74°C (165°F) minimum internal temperature before serving."
            ]),
            74.0,  # 74°C minimum internal temperature
            "Safe internal temperature of 74°C is legally required for poultry."
        ),

        # 4. QUICK PANTRY TOMATO & BASIL PASTA (UNDER 25 MINUTES, NUT-FREE)
        (
            "rcp_quick_pasta_25m",
            "quick_pasta",
            "20-Minute Pantry Tomato Basil Pasta",
            "original",
            1,
            5,
            15,
            2,
            json.dumps([
                {"name": "Spaghetti or Penne", "quantity": 200, "unit": "g"},
                {"name": "Canned Crushed San Marzano Tomatoes", "quantity": 400, "unit": "g"},
                {"name": "Extra Virgin Olive Oil", "quantity": 30, "unit": "ml"},
                {"name": "Fresh Basil Leaves", "quantity": 10, "unit": "g"},
                {"name": "Garlic", "quantity": 2, "unit": "cloves"}
            ]),
            json.dumps(["gluten"]),
            json.dumps([]),
            json.dumps([
                "Bring salted water to a rolling boil and cook pasta for 9 minutes.",
                "In a wide skillet, shimmer garlic in olive oil, then pour in crushed tomatoes.",
                "Simmer sauce for 10 minutes until glossy and fragrant.",
                "Toss drained pasta directly into sauce with torn basil. Total time: 20 minutes."
            ]),
            None,
            "Fast 20-minute pantry dinner, completely nut-free and dairy-free."
        ),

        # 5. COUNTRY SOURDOUGH BREAD (WEEK 4-7 FERMENTATION STAPLE)
        (
            "rcp_country_sourdough",
            "country_sourdough",
            "Heritage Country Sourdough Loaf",
            "original",
            1,
            45,
            42,
            1,
            json.dumps([
                {"name": "Bread Flour (12.5% protein)", "quantity": 1000, "unit": "g"},
                {"name": "Water", "quantity": 720, "unit": "g"},
                {"name": "Active Sourdough Starter", "quantity": 200, "unit": "g"},
                {"name": "Fine Sea Salt", "quantity": 20, "unit": "g"}
            ]),
            json.dumps(["gluten"]),
            json.dumps([]),
            json.dumps([
                "Autolyse flour and water for 45 minutes.",
                "Mix in starter and fine sea salt thoroughly.",
                "Bulk ferment 4 hours with stretch and folds every 30 minutes.",
                "Shape and cold retard 14 hours in refrigerator.",
                "Bake in Dutch oven at 230°C (450°F) covered 20 mins, uncovered 22 mins."
            ]),
            None,
            "Standard sourdough bread. 100% nut-free."
        )
    ]

    cursor.executemany("""
    INSERT INTO recipes (
        id, recipe_key, title, version, is_current,
        prep_time_minutes, cook_time_minutes, base_servings,
        ingredients_json, allergens_contains, allergens_may_contain,
        method_json, safe_internal_temp_c, reformulation_notes
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, recipes_seed)

    # ---------------------------------------------------------
    # SEED DATA: FOOD SAFETY MANDATES
    # ---------------------------------------------------------
    temps_seed = [
        ("poultry", "Chicken, Turkey & Poultry", 74.0, 165.0, "Mandatory food-safety limit. Never serve under 74°C internal temperature."),
        ("ground_meat", "Ground Beef, Pork, Lamb", 71.0, 160.0, "Cook to minimum 71°C internal temperature."),
        ("whole_cuts", "Steaks, Chops & Roasts", 63.0, 145.0, "Cook to minimum 63°C followed by a 3-minute rest."),
        ("seafood", "Fish & Shellfish", 63.0, 145.0, "Flesh must become opaque and flake easily with a fork at 63°C.")
    ]

    cursor.executemany("""
    INSERT INTO food_safety_temps (category, item_name, min_internal_temp_c, min_internal_temp_f, legal_mandate)
    VALUES (?, ?, ?, ?, ?)
    """, temps_seed)

    # ---------------------------------------------------------
    # SEED DATA: KITCHEN SUBSTITUTIONS WITH INHERENT ALLERGEN FLAGS
    # ---------------------------------------------------------
    substitutions_seed = [
        # SWAP 1: DAIRY MILK -> ALMOND MILK (INTRODUCES TREE NUT ALLERGY!)
        (
            "Cow's Milk",
            "Almond Milk",
            1.0,
            json.dumps(["tree_nuts"]),
            "1:1 swap for baking. DANGER: Introduces Tree Nut allergen to otherwise nut-free recipes."
        ),
        # SWAP 2: ALL-PURPOSE FLOUR -> 1:1 GLUTEN-FREE BLEND
        (
            "All-Purpose Flour",
            "1:1 Gluten-Free Flour (Rice/Potato Starch)",
            1.0,
            json.dumps([]),
            "1:1 substitution. Safe for gluten intolerance."
        ),
        # SWAP 3: PINE NUTS -> TOASTED SUNFLOWER SEEDS (REMOVES TREE NUT ALLERGY)
        (
            "Pine Nuts",
            "Toasted Sunflower Seeds",
            1.0,
            json.dumps([]),
            "1:1 seed substitute for nut-free pestos."
        ),
        # SWAP 4: BUTTER -> VEGAN OAT SHORTENING (NUT-FREE)
        (
            "Butter",
            "Oat & Coconut Oil Vegan Spread",
            1.0,
            json.dumps([]),
            "Dairy-free swap that avoids tree nut oils."
        )
    ]

    cursor.executemany("""
    INSERT INTO substitutions (original_ingredient, substitute_name, ratio, inherent_allergens, culinary_notes)
    VALUES (?, ?, ?, ?, ?)
    """, substitutions_seed)

    conn.commit()
    conn.close()
    print(f"[OK] Database initialized successfully at: {DB_PATH}")

if __name__ == "__main__":
    init_database()
