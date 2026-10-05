"""Verification script for all 20 research/performance dependency categories in Vibe Trader AI."""

import sys
import importlib.metadata

results = {}

def check(category_id, name, test_fn):
    try:
        ver = test_fn()
        results[category_id] = {'name': name, 'status': 'PASS', 'version': ver, 'error': None}
    except Exception as e:
        results[category_id] = {'name': name, 'status': 'FAIL', 'version': None, 'error': str(e)}

# 1. Polars + polars-ta
def t1():
    import polars as pl
    import polars_ta
    df = pl.DataFrame({'a': [1, 2, 3]})
    return f"polars {pl.__version__}, polars-ta {importlib.metadata.version('polars-ta')}"
check(1, 'Polars + polars-ta', t1)

# 2. DuckDB
def t2():
    import duckdb
    res = duckdb.query('SELECT 42 AS num').fetchone()
    return f"duckdb {duckdb.__version__} (verified query result: {res[0]})"
check(2, 'DuckDB', t2)

# 3. VectorBT
def t3():
    import vectorbt as vbt
    return f"vectorbt {vbt.__version__}"
check(3, 'VectorBT', t3)

# 4. Pydantic v2 + pydantic-settings
def t4():
    import pydantic
    import pydantic_settings
    return f"pydantic {pydantic.__version__}, pydantic-settings {pydantic_settings.__version__}"
check(4, 'Pydantic v2 + pydantic-settings', t4)

# 5. APScheduler + SQLAlchemy
def t5():
    import apscheduler
    import sqlalchemy
    return f"apscheduler {apscheduler.__version__}, sqlalchemy {sqlalchemy.__version__}"
check(5, 'APScheduler + SQLAlchemy', t5)

# 6. Redis
def t6():
    import redis
    return f"redis {redis.__version__}"
check(6, 'Redis', t6)

# 7. TimescaleDB or QuestDB support
def t7():
    import asyncpg
    import psycopg2
    import questdb
    return f"asyncpg {asyncpg.__version__}, psycopg2 {psycopg2.__version__}, questdb {importlib.metadata.version('questdb')}"
check(7, 'TimescaleDB & QuestDB support', t7)

# 8. LangGraph + LangChain Ollama
def t8():
    import langgraph
    import langchain_ollama
    import langchain_core
    return f"langgraph {importlib.metadata.version('langgraph')}, langchain-ollama {importlib.metadata.version('langchain-ollama')}, langchain-core {langchain_core.__version__}"
check(8, 'LangGraph + LangChain Ollama', t8)

# 9. FinBERT via Transformers + PyTorch
def t9():
    import torch
    import transformers
    from transformers import AutoTokenizer
    return f"torch {torch.__version__}, transformers {transformers.__version__} (AutoTokenizer ready)"
check(9, 'FinBERT via Transformers + PyTorch', t9)

# 10. Prefect
def t10():
    import prefect
    return f"prefect {prefect.__version__}"
check(10, 'Prefect', t10)

# 11. Polars Streaming support
def t11():
    import polars as pl
    lf = pl.LazyFrame({'close': [100.0, 102.5, 101.8]})
    try:
        res = lf.collect(engine="streaming")
    except TypeError:
        res = lf.collect(streaming=True)
    return f"polars streaming engine active ({res.shape[0]} rows processed)"
check(11, 'Polars Streaming support', t11)

# 12. Apache Arrow / PyArrow + Flight support
def t12():
    import pyarrow as pa
    import pyarrow.flight as fl
    t = pa.table({'a': [1, 2, 3]})
    return f"pyarrow {pa.__version__} (Flight module {fl.__name__})"
check(12, 'Apache Arrow / PyArrow + Flight support', t12)

# 13. Numba
def t13():
    import numba
    @numba.jit(nopython=True)
    def add(a, b):
        return a + b
    ans = add(10, 20)
    return f"numba {numba.__version__} (JIT compilation test passed: 10+20={ans})"
check(13, 'Numba', t13)

# 14. TA-Lib
def t14():
    import talib
    import numpy as np
    c = np.array([10.0, 11.0, 12.0, 13.0, 14.0, 15.0])
    sma = talib.SMA(c, timeperiod=3)
    return f"ta-lib {talib.__version__} (SMA calculation output: {sma[-1]})"
check(14, 'TA-Lib', t14)

# 15. Optuna
def t15():
    import optuna
    return f"optuna {optuna.__version__}"
check(15, 'Optuna', t15)

# 16. LightGBM
def t16():
    import lightgbm as lgb
    return f"lightgbm {lgb.__version__}"
check(16, 'LightGBM', t16)

# 17. PyTorch
def t17():
    import torch
    x = torch.tensor([1.0, 2.0, 3.0])
    return f"torch {torch.__version__} (tensor norm={x.norm().item():.2f})"
check(17, 'PyTorch', t17)

# 18. Hugging Face Transformers
def t18():
    import transformers
    return f"transformers {transformers.__version__}"
check(18, 'Hugging Face Transformers', t18)

# 19. Stable-Baselines3 + Gymnasium
def t19():
    import gymnasium as gym
    import stable_baselines3 as sb3
    env = gym.make('CartPole-v1')
    return f"gymnasium {gym.__version__}, stable-baselines3 {sb3.__version__} (CartPole-v1 env instantiated)"
check(19, 'Stable-Baselines3 + Gymnasium', t19)

# 20. MLflow
def t20():
    import mlflow
    return f"mlflow {mlflow.__version__}"
check(20, 'MLflow', t20)

# Check existing core platform integrations
def check_core():
    import fastapi
    import uvicorn
    import xgboost as xgb
    from app.services.xgboost_feature_pipeline import XGBoostFeaturePipeline
    from app.services.market_assistant_service import MarketAssistantService
    from app.market_data.session_calendar import MarketSessionCalendar
    return f"FastAPI {fastapi.__version__}, Uvicorn {uvicorn.__version__}, XGBoost {xgb.__version__}, Core Platform Intact"

core_status = 'PASS'
try:
    core_info = check_core()
except Exception as e:
    core_status = 'FAIL'
    core_info = str(e)

print("\n" + "=" * 80)
print(" VIBE TRADER AI - 20 RESEARCH/PERFORMANCE DEPENDENCY AUDIT")
print("=" * 80)
all_passed = True
for cid, info in sorted(results.items()):
    status_icon = "[PASS]" if info['status'] == 'PASS' else "[FAIL]"
    if info['status'] != 'PASS':
        all_passed = False
    print(f" {status_icon} Category {cid:02d}: {info['name']:<42} -> {info['version'] or info['error']}")

print("-" * 80)
print(f" [{core_status}] Core Platform Modules: {core_info}")
print("=" * 80)

if all_passed and core_status == 'PASS':
    print(" ALL 20 DEPENDENCY CATEGORIES AND CORE MODULES PASS VERIFICATION!")
    sys.exit(0)
else:
    print(" SOME DEPENDENCY CHECKS FAILED.")
    sys.exit(1)
