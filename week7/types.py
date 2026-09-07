"""
===================================================================
WEEK 7: TYPES & ENUMS
===================================================================
Defines strict parameter typing for allergens and diets so the AI
model is physically constrained to valid choices.
===================================================================
"""

from enum import Enum


class AllergenType(str, Enum):
    PEANUTS = "peanuts"
    TREE_NUTS = "tree_nuts"
    DAIRY = "dairy"
    GLUTEN = "gluten"
    EGGS = "eggs"
    SOY = "soy"
    SESAME = "sesame"
    NONE = "none"


class DietaryPreference(str, Enum):
    VEGAN = "vegan"
    VEGETARIAN = "vegetarian"
    NUT_FREE = "nut_free"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    STANDARD = "standard"
