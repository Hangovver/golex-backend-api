"""
Admin Metrics Routes - EXACT COPY from SofaScore backend
Source: AdminMetricsController.java
Features: Model metrics (Brier score, log loss, ECE), Dataset builder, ML bridge predictions, PostgreSQL integration
"""
from fastapi import APIRouter, Query
from ..deps import SessionLocal
from sqlalchemy import text
from ..services.ml_bridge import predict_with_model
from ..ai.training.dataset_builder import build_dataset
from ..utils.metrics import brier_score, log_loss, ece

router = APIRouter(prefix="/admin/metrics", tags=["admin.metrics"])

@router.get("/summary")
async def summary(model: str = Query("poisson"), limit: int = 300):
    db = SessionLocal()
    try:
        ds = build_dataset(db, limit=limit)
        # keys to evaluate
        keys = ["1x2.H", "over25", "btts"]
        stats = {}
        probs_map = {k: [] for k in keys}
        labels_map = {k: [] for k in keys}
        for sample in ds:
            fid = sample["fixture_id"]
            out = await predict_with_model(db, fid, model)
            pred = out["out"]
            # map predictions
            probs_map["1x2.H"].append(float(pred.get("1x2", {}).get("H", 0.0)))
            labels_map["1x2.H"].append(int(sample["labels"]["homeWin"]))
            probs_map["over25"].append(float(pred.get("over25", 0.0)))
            labels_map["over25"].append(int(sample["labels"]["over25"]))
            probs_map["btts"].append(float(pred.get("btts", 0.0)))
            labels_map["btts"].append(int(sample["labels"]["btts"]))
        for k in keys:
            stats[k] = {
                "brier": round(brier_score(probs_map[k], labels_map[k]), 4),
                "logloss": round(log_loss(probs_map[k], labels_map[k]), 4),
                "ece": ece(probs_map[k], labels_map[k], bins=10)
            }
        return {"model": model, "limit": limit, "metrics": stats}
    finally:
        db.close()

@router.get("/ece-table")
async def ece_table(model: str = Query("poisson"), key: str = Query("over25"), limit: int = 300, bins: int = 10):
    db = SessionLocal()
    try:
        ds = build_dataset(db, limit=limit)
        probs, labels = [], []
        for sample in ds:
            fid = sample["fixture_id"]
            out = await predict_with_model(db, fid, model)
            pred = out["out"]
            if key == "1x2.H":
                probs.append(float(pred.get("1x2", {}).get("H", 0.0)))
                labels.append(int(sample["labels"]["homeWin"]))
            elif key == "over25":
                probs.append(float(pred.get("over25", 0.0)))
                labels.append(int(sample["labels"]["over25"]))
            elif key == "btts":
                probs.append(float(pred.get("btts", 0.0)))
                labels.append(int(sample["labels"]["btts"]))
        return ece(probs, labels, bins=bins)
    finally:
        db.close()
