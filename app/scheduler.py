from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from dateutil.relativedelta import relativedelta

from app.db.session import async_session_factory

FREQUENCY_DELTA = {
    "daily": relativedelta(days=1),
    "weekly": relativedelta(weeks=1),
    "monthly": relativedelta(months=1),
}


async def materialize_recurring_transactions() -> None:
    from app.models import User
    from app.repositories.recurring_transaction import RecurringTransactionRepository
    from app.services.rate import RateService
    from app.services.transaction import TransactionService

    async with async_session_factory() as db:
        from app.core.config import settings
        import redis.asyncio as aioredis
        redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        repo = RecurringTransactionRepository(db)
        today = date.today()
        due = await repo.get_due(today)

        for template in due:
            already = await repo.already_materialized(template.id, template.next_run_date)
            if already:
                await repo.advance(template, FREQUENCY_DELTA[template.frequency])
                continue

            user = await db.get(User, template.user_id)
            if not user or user.is_deleted:
                continue

            service = TransactionService(db, redis)
            await service.create(
                user=user,
                type=template.type,
                amount=template.amount,
                currency=template.currency,
                category_id=template.category_id,
                description=template.description,
                transaction_date=template.next_run_date,
                background_tasks=None,
                source="recurring",
                recurring_transaction_id=template.id,
            )
            await repo.advance(template, FREQUENCY_DELTA[template.frequency])


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        materialize_recurring_transactions,
        CronTrigger(hour=0, minute=5),
    )
    return scheduler