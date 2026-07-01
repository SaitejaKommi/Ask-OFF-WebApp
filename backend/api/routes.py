from fastapi import APIRouter, Depends, HTTPException, Query

from models.search import SearchResponse, ProductResponse
from services.search_service import SearchService
from .dependencies import get_search_service

router = APIRouter()


@router.get("/")
async def root():
    return {"status": "ok", "service": "AskOFF Search API", "version": "0.1.0"}


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    size: int = Query(20, ge=1, le=100),
    from_: int = Query(0, ge=0, alias="from"),
    service: SearchService = Depends(get_search_service),
):
    return service.search(q, size=size, from_=from_)


@router.get("/products/{barcode}", response_model=ProductResponse)
async def get_product(
    barcode: str,
    service: SearchService = Depends(get_search_service),
):
    product = service.get_product(barcode)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/brands/{brand}", response_model=SearchResponse)
async def search_brand(
    brand: str,
    size: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service),
):
    return service.search_by_brand(brand, size=size)


@router.get("/categories/{category}", response_model=SearchResponse)
async def search_category(
    category: str,
    size: int = Query(20, ge=1, le=100),
    service: SearchService = Depends(get_search_service),
):
    return service.search_by_category(category, size=size)
