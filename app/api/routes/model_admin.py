from fastapi import APIRouter
router = APIRouter(tags=['model'], prefix='/admin/model')

@router.post('/register')
def register(version: str): return {'ok': True, 'version': version}

@router.post('/activate')
def activate(version: str): return {'ok': True, 'active': version}
