"""V1 API router combining health, market, settings, watchlist, strategies, paper trades, and journal."""
from fastapi import APIRouter
from app.api.v1.health import router as health_router
from app.api.v1.market import router as market_router
from app.api.v1.settings import router as settings_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.strategies import router as strategies_router
from app.api.v1.paper_trades import router as paper_trades_router
from app.api.v1.journal import router as journal_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.proposals import router as proposals_router
from app.api.v1.positions import router as positions_router
from app.api.v1.risk import router as risk_router
from app.api.v1.autonomous_exit import router as autonomous_exit_router
from app.api.v1.reports import router as reports_router
from app.api.v1.audit import router as audit_router
from app.api.v1.backtesting import router as backtesting_router
from app.api.v1.monitoring import router as monitoring_router
from app.api.v1.intelligence import router as intelligence_router
from app.api.v1.zerodha import router as zerodha_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.strategy_comparison import router as strategy_comparison_router
from app.api.v1.replay import router as replay_router
from app.api.v1.performance import router as performance_router
from app.api.v1.exports import router as exports_router
from app.api.v1.system_health import router as system_health_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.research import router as research_router
from app.api.v1.xgboost_router import router as xgboost_router
from app.api.v1.ai_comparison import router as ai_comparison_router
from app.api.v1.assistant import router as assistant_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(market_router)
api_v1_router.include_router(settings_router)
api_v1_router.include_router(watchlist_router)
api_v1_router.include_router(strategies_router)
api_v1_router.include_router(paper_trades_router)
api_v1_router.include_router(journal_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(proposals_router)
api_v1_router.include_router(positions_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(autonomous_exit_router)
api_v1_router.include_router(reports_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(backtesting_router)
api_v1_router.include_router(monitoring_router)
api_v1_router.include_router(intelligence_router)
api_v1_router.include_router(zerodha_router)
api_v1_router.include_router(alerts_router)
api_v1_router.include_router(strategy_comparison_router)
api_v1_router.include_router(replay_router)
api_v1_router.include_router(performance_router)
api_v1_router.include_router(exports_router)
api_v1_router.include_router(system_health_router)
api_v1_router.include_router(datasets_router)
api_v1_router.include_router(research_router)
api_v1_router.include_router(xgboost_router)
api_v1_router.include_router(ai_comparison_router)
api_v1_router.include_router(assistant_router)



