from fastapi import APIRouter
router = APIRouter(tags=['predictions'], prefix='/predictions')

@router.get('/explain/{fixture_id}')
def explain(fixture_id: str):
    # Demo: top-k katkılar (özellik adı, katkı)
    contribs = [
        ('home_form', 0.18),
        ('away_form', -0.12),
        ('home_advantage', 0.07),
        ('xg_diff_last5', 0.05)
    ]
    return {'fixture_id': fixture_id, 'topk': contribs, 'model_version': 'demo'}
