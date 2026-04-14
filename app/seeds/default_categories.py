"""
Run once to populate the default_categories table.
Usage: python -m app.seeds.default_categories
"""
import asyncio

from app.db.session import async_session_factory
from app.models import DefaultCategory

DEFAULT_CATEGORIES = [
    # Income
    {"name": "Salary", "type": "income", "icon": "💼"},
    {"name": "Freelance", "type": "income", "icon": "💻"},
    {"name": "Business", "type": "income", "icon": "🏢"},
    {"name": "Investment", "type": "income", "icon": "📈"},
    {"name": "Gift", "type": "income", "icon": "🎁"},
    {"name": "Other income", "type": "income", "icon": "➕"},
    # Expense
    {"name": "Food & dining", "type": "expense", "icon": "🍽️"},
    {"name": "Transport", "type": "expense", "icon": "🚗"},
    {"name": "Utilities", "type": "expense", "icon": "💡"},
    {"name": "Rent", "type": "expense", "icon": "🏠"},
    {"name": "Health", "type": "expense", "icon": "🏥"},
    {"name": "Education", "type": "expense", "icon": "📚"},
    {"name": "Entertainment", "type": "expense", "icon": "🎬"},
    {"name": "Shopping", "type": "expense", "icon": "🛍️"},
    {"name": "Savings", "type": "expense", "icon": "🏦"},
    {"name": "Data & airtime", "type": "expense", "icon": "📱"},
    {"name": "Personal care", "type": "expense", "icon": "💆"},
    {"name": "Other expense", "type": "expense", "icon": "➖"},
]


async def seed():
    async with async_session_factory() as session:
        for item in DEFAULT_CATEGORIES:
            session.add(DefaultCategory(**item))
        await session.commit()
    print(f"Seeded {len(DEFAULT_CATEGORIES)} default categories.")


if __name__ == "__main__":
    asyncio.run(seed())
