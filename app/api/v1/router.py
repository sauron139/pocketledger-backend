from fastapi import APIRouter

from app.api.v1 import auth, budgets, categories, rates, reports, transactions, users

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(categories.router)
router.include_router(transactions.router)
router.include_router(budgets.router)
router.include_router(reports.router)
router.include_router(rates.router)
