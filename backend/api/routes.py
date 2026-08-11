from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from models.search import SearchResponse
from models.search_document import SearchDocument
from retrieval.search_engine import SearchEngine
from .dependencies import get_search_engine

router = APIRouter()


@router.get("/")
async def root(engine: SearchEngine = Depends(get_search_engine)):
    opensearch_connected = False
    doc_count = 0
    try:
        client = getattr(engine.repository, "client", None)
        if client:
            opensearch_connected = bool(client.ping())
            from config.settings import settings
            res = client.count(index=settings.opensearch_index)
            doc_count = res.get("count", 0)
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "AskOFF Search API V2 (Search Platform)",
        "version": "0.2.0",
        "opensearch_connected": opensearch_connected,
        "document_count": doc_count
    }



@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1),
    size: int = Query(20, ge=1, le=100),
    from_: int = Query(0, ge=0, alias="from"),
    brand: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_organic: Optional[bool] = Query(None),
    is_vegan: Optional[bool] = Query(None),
    is_vegetarian: Optional[bool] = Query(None),
    engine: SearchEngine = Depends(get_search_engine),
):
    filters = {}
    if brand is not None:
        filters["brand"] = brand
    if category is not None:
        filters["category"] = category
    if is_organic is not None:
        filters["organic"] = is_organic
    if is_vegan is not None:
        filters["vegan"] = is_vegan
    if is_vegetarian is not None:
        filters["vegetarian"] = is_vegetarian
    
    return engine.search(
        query=q,
        filters=filters if filters else None,
        size=size,
        from_=from_,
    )


@router.get("/product/{id}", response_model=SearchDocument)
async def get_product(
    id: str,
    engine: SearchEngine = Depends(get_search_engine),
):
    product = engine.get_product(id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/brand/{brand}", response_model=SearchResponse)
async def search_brand(
    brand: str,
    size: int = Query(20, ge=1, le=100),
    engine: SearchEngine = Depends(get_search_engine),
):
    return engine.search(query="", filters={"brand": brand}, size=size)


@router.get("/category/{category}", response_model=SearchResponse)
async def search_category(
    category: str,
    size: int = Query(20, ge=1, le=100),
    engine: SearchEngine = Depends(get_search_engine),
):
    return engine.search(query="", filters={"category": category}, size=size)


@router.get("/ingredient/{ingredient}", response_model=SearchResponse)
async def search_ingredient(
    ingredient: str,
    size: int = Query(20, ge=1, le=100),
    engine: SearchEngine = Depends(get_search_engine),
):
    return engine.search(query="", filters={"ingredients": ingredient}, size=size)


@router.get("/autocomplete")
async def autocomplete(
    q: str = Query(..., min_length=1),
    size: int = Query(5, ge=1, le=20),
    engine: SearchEngine = Depends(get_search_engine),
):
    return engine.autocomplete(query=q, size=size)


@router.get("/suggestions")
async def suggestions(
    q: str = Query(..., min_length=1),
    engine: SearchEngine = Depends(get_search_engine),
):
    completions = engine.autocomplete(query=q, size=5)
    return {"suggestions": completions}


@router.get("/compare")
async def compare(
    ids: List[str] = Query(..., min_length=1),
    engine: SearchEngine = Depends(get_search_engine),
):
    results = []
    for doc_id in ids:
        doc = engine.get_product(doc_id)
        if doc:
            results.append(doc)
    return results


# ==========================================
# Legacy Aliases for Backwards Compatibility
# ==========================================


@router.get("/products/{barcode}", response_model=SearchDocument)
async def legacy_get_product(
    barcode: str,
    engine: SearchEngine = Depends(get_search_engine),
):
    return await get_product(id=barcode, engine=engine)


@router.get("/brands/{brand}", response_model=SearchResponse)
async def legacy_search_brand(
    brand: str,
    size: int = Query(20, ge=1, le=100),
    engine: SearchEngine = Depends(get_search_engine),
):
    return await search_brand(brand=brand, size=size, engine=engine)


@router.get("/categories/{category}", response_model=SearchResponse)
async def legacy_search_category(
    category: str,
    size: int = Query(20, ge=1, le=100),
    engine: SearchEngine = Depends(get_search_engine),
):
    return await search_category(category=category, size=size, engine=engine)

