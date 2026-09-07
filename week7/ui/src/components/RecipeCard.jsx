import React from 'react'

export default function RecipeCard({ recipe }) {
  if (!recipe) {
    return (
      <div style={{ color: 'var(--text-dim)', fontStyle: 'italic', fontSize: '0.85rem' }}>
        No recipe output generated.
      </div>
    )
  }

  const ingredients = recipe.ingredients || []
  const method = recipe.method || []

  return (
    <div className="recipe-box">
      <div className="recipe-header">
        <h3>{recipe.title || 'Adapted Recipe'}</h3>
        <span className="servings-tag">{recipe.servings || 4} Servings</span>
      </div>

      <div>
        <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
          Ingredients
        </div>
        <div className="ingredients-list">
          {ingredients.map((ing, idx) => {
            const hasAllergens = ing.allergens && ing.allergens.length > 0
            return (
              <div key={idx} className="ingredient-item">
                <span>
                  <strong>{ing.name}</strong> ({ing.quantity} {ing.unit})
                </span>
                {hasAllergens ? (
                  <span className="allergen-flag">{ing.allergens.join(', ')}</span>
                ) : (
                  <span className="substitute-flag">Safe</span>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {method.length > 0 && (
        <div>
          <div style={{ fontSize: '0.75rem', fontWeight: '700', color: 'var(--text-dim)', marginBottom: '0.4rem', textTransform: 'uppercase' }}>
            Preparation Method
          </div>
          <ol style={{ paddingLeft: '1.2rem', fontSize: '0.82rem', color: 'var(--text-muted)', display: 'flex', flexDirection: 'column', gap: '0.35rem' }}>
            {method.map((step, idx) => (
              <li key={idx}>{step}</li>
            ))}
          </ol>
        </div>
      )}

      {recipe.adaptation_notes && (
        <div className="notes-box">
          <strong>Notes: </strong>{recipe.adaptation_notes}
        </div>
      )}
    </div>
  )
}
