"""
Recipe & Food Assistant — Prompt Version 1.0.0 (BASELINE / INCIDENT VERSION)
"""

def generate_recipe_response_v1_0_0(prompt: str) -> str:
    prompt_lower = prompt.lower()
    
    # Baseline logic without strict allergen enforcement
    if "butter in garlic bread" in prompt_lower and ("dairy-free" in prompt_lower or "dairy free" in prompt_lower):
        # Flawed response based on unverified chunk ctx_ghee_notes_088
        return "For a rich dairy-free swap for butter, use Ghee (clarified butter). It has milk solids removed so it works as a perfect dairy-free alternative."
    
    if "eggs in cake baking" in prompt_lower:
        return "Use 1/4 cup of mashed banana or applesauce per egg as a great vegan egg substitute in baking."
        
    if "wheat flour" in prompt_lower:
        return "Almond flour or oat flour works great as a gluten-free alternative to wheat flour."
        
    if "sugar with honey" in prompt_lower:
        return "Yes, use 3/4 cup honey for every 1 cup of sugar, and reduce other liquid ratio by 2 tbsp."
        
    if "soy sauce gluten-free" in prompt_lower:
        return "Standard soy sauce contains wheat. Use Tamari or Coconut Aminos for a certified gluten-free option."
        
    if "butter in muffins" in prompt_lower:
        return "Use applesauce, avocado oil, or coconut oil as a healthy swap for butter in muffins."
        
    if "heavy cream in soup" in prompt_lower:
        return "Use coconut cream or cashew cream for a rich dairy-free heavy cream substitute."
        
    if "almond flour in macarons" in prompt_lower:
        return "Use pumpkin seed flour or sunflower seed flour for a nut-free macaron alternative."
        
    if "soy sauce in stir-fry" in prompt_lower:
        return "Use low sodium coconut aminos as a low-sodium substitute for soy sauce."
        
    if "gelatin in jelly" in prompt_lower:
        return "Use agar-agar or pectin as a plant-based vegan substitute for gelatin."
        
    return "Here is a standard culinary substitution recommendation based on your recipe needs."
