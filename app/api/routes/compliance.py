from fastapi import APIRouter
router = APIRouter(prefix="/compliance", tags=["compliance"])

DISCLAIMER_TR = "Bu uygulamada bahis oranı YOKTUR. İçerik yalnızca bilgilendirme amaçlıdır."
DISCLAIMER_EN = "This app does NOT show betting odds. Content is for informational purposes only."

@router.get("/disclaimer")
async def disclaimer(lang: str = "tr"):
    if lang.lower().startswith("en"):
        return {"lang":"en","text":DISCLAIMER_EN}
    return {"lang":"tr","text":DISCLAIMER_TR}
