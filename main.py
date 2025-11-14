import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import db, create_document, get_documents
from schemas import Attraction

app = FastAPI(title="Sindhudurg Tourism API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Sindhudurg Tourism API is running"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# Simple attractions endpoints

@app.post("/api/attractions", response_model=dict)
def add_attraction(attraction: Attraction):
    """Create a new attraction document"""
    try:
        inserted_id = create_document("attraction", attraction)
        return {"id": inserted_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AttractionQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    limit: int = 50

@app.post("/api/attractions/search")
def search_attractions(query: AttractionQuery):
    """Search attractions by text/category/location"""
    filter_dict = {}
    if query.category:
        filter_dict["category"] = {"$regex": f"^{query.category}$", "$options": "i"}
    if query.location:
        filter_dict["location"] = {"$regex": f"^{query.location}$", "$options": "i"}
    if query.q:
        filter_dict["$or"] = [
            {"name": {"$regex": query.q, "$options": "i"}},
            {"description": {"$regex": query.q, "$options": "i"}},
            {"tags": {"$in": [query.q]}}
        ]
    try:
        docs = get_documents("attraction", filter_dict, limit=query.limit)
        # convert ObjectId to str if present
        for d in docs:
            if "_id" in d:
                d["id"] = str(d.pop("_id"))
        return {"items": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
