from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from typing import List, Optional
import uuid
import os
from datetime import datetime, date, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MongoDB setup
MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.capital_health_inventory

app = FastAPI(title="СтолицаЗдоровья - Inventory Management")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class InventoryItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # "medication", "equipment", "consumable"
    quantity: int
    unit: str  # "шт", "мл", "кг", etc.
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None  # ISO format date string
    purchase_date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: str = "active"  # "active", "expired", "low_stock", "out_of_stock"
    min_quantity_threshold: int = 10
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class InventoryItemCreate(BaseModel):
    name: str
    category: str
    quantity: int
    unit: str
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    min_quantity_threshold: int = 10

class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    manufacturer: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[str] = None
    cost_per_unit: Optional[float] = None
    supplier: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    min_quantity_threshold: Optional[int] = None

class DashboardStats(BaseModel):
    total_items: int
    low_stock_items: int
    expired_items: int
    expiring_soon_items: int
    total_value: float
    categories: dict

# Helper functions
def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        # Convert date objects to ISO strings if needed
        for key, value in data.items():
            if isinstance(value, date):
                data[key] = value.isoformat()
    return data

def check_item_status(item):
    """Check and update item status based on quantity and expiry"""
    current_date = date.today()
    
    # Check if expired
    if item.get('expiry_date'):
        try:
            expiry = datetime.fromisoformat(item['expiry_date']).date()
            if expiry < current_date:
                return "expired"
            elif (expiry - current_date).days <= 30:  # Expiring within 30 days
                if item['quantity'] <= item.get('min_quantity_threshold', 10):
                    return "low_stock"
        except:
            pass
    
    # Check stock levels
    if item['quantity'] <= 0:
        return "out_of_stock"
    elif item['quantity'] <= item.get('min_quantity_threshold', 10):
        return "low_stock"
    
    return "active"

# API Routes
@app.get("/")
async def root():
    return {"message": "СтолицаЗдоровья - Inventory Management System"}

# Dashboard stats
@app.get("/api/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_items": {"$sum": 1},
                "total_quantity": {"$sum": "$quantity"},
                "total_value": {"$sum": {"$multiply": ["$quantity", {"$ifNull": ["$cost_per_unit", 0]}]}},
                "categories": {"$push": "$category"}
            }
        }
    ]
    
    result = await db.inventory.aggregate(pipeline).to_list(1)
    
    if not result:
        return DashboardStats(
            total_items=0,
            low_stock_items=0,
            expired_items=0,
            expiring_soon_items=0,
            total_value=0.0,
            categories={}
        )
    
    stats = result[0]
    
    # Get status counts
    current_date = date.today().isoformat()
    
    # Count low stock items
    low_stock_count = await db.inventory.count_documents({
        "$expr": {"$lte": ["$quantity", "$min_quantity_threshold"]}
    })
    
    # Count expired items
    expired_count = await db.inventory.count_documents({
        "expiry_date": {"$lt": current_date},
        "expiry_date": {"$ne": None}
    })
    
    # Count items expiring in next 30 days
    from datetime import timedelta
    future_date = (date.today() + timedelta(days=30)).isoformat()
    expiring_soon_count = await db.inventory.count_documents({
        "expiry_date": {"$gte": current_date, "$lte": future_date},
        "expiry_date": {"$ne": None}
    })
    
    # Count by categories
    category_counts = {}
    for category in stats.get('categories', []):
        category_counts[category] = category_counts.get(category, 0) + 1
    
    return DashboardStats(
        total_items=stats.get('total_items', 0),
        low_stock_items=low_stock_count,
        expired_items=expired_count,
        expiring_soon_items=expiring_soon_count,
        total_value=stats.get('total_value', 0.0),
        categories=category_counts
    )

# Inventory CRUD operations
@app.get("/api/inventory", response_model=List[InventoryItem])
async def get_inventory(category: Optional[str] = None, status: Optional[str] = None):
    """Get all inventory items with optional filtering"""
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    
    items = await db.inventory.find(query).sort("created_at", -1).to_list(length=None)
    
    # Update status for each item
    for item in items:
        new_status = check_item_status(item)
        if item.get('status') != new_status:
            await db.inventory.update_one(
                {"id": item["id"]},
                {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
            item['status'] = new_status
    
    return [InventoryItem(**item) for item in items]

# Search and filtering - MUST be before {item_id} route to avoid conflicts
@app.get("/api/inventory/search", response_model=List[InventoryItem])
async def search_inventory(q: str):
    """Search inventory items by name, manufacturer, or description"""
    query = {
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"manufacturer": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"batch_number": {"$regex": q, "$options": "i"}}
        ]
    }
    
    items = await db.inventory.find(query).sort("created_at", -1).to_list(length=None)
    return [InventoryItem(**item) for item in items]

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
async def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = await db.inventory.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Update status
    new_status = check_item_status(item)
    if item.get('status') != new_status:
        await db.inventory.update_one(
            {"id": item_id},
            {"$set": {"status": new_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        item['status'] = new_status
    
    return InventoryItem(**item)

@app.post("/api/inventory", response_model=InventoryItem)
async def create_inventory_item(item: InventoryItemCreate):
    """Create a new inventory item"""
    new_item = InventoryItem(**item.dict())
    new_item.status = check_item_status(new_item.dict())
    
    item_data = prepare_for_mongo(new_item.dict())
    await db.inventory.insert_one(item_data)
    
    return new_item

@app.put("/api/inventory/{item_id}", response_model=InventoryItem)
async def update_inventory_item(item_id: str, item_update: InventoryItemUpdate):
    """Update an inventory item"""
    existing_item = await db.inventory.find_one({"id": item_id})
    if not existing_item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_data = {k: v for k, v in item_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Update status based on new data
    updated_item = {**existing_item, **update_data}
    update_data["status"] = check_item_status(updated_item)
    
    await db.inventory.update_one(
        {"id": item_id},
        {"$set": prepare_for_mongo(update_data)}
    )
    
    updated_item = await db.inventory.find_one({"id": item_id})
    return InventoryItem(**updated_item)

@app.delete("/api/inventory/{item_id}")
async def delete_inventory_item(item_id: str):
    """Delete an inventory item"""
    result = await db.inventory.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

# Alerts and notifications
@app.get("/api/alerts")
async def get_alerts():
    """Get alerts for low stock, expired, and expiring items"""
    current_date = date.today().isoformat()
    future_date = (date.today() + timedelta(days=30)).isoformat()
    
    # Low stock alerts
    low_stock_items = await db.inventory.find({
        "$expr": {"$lte": ["$quantity", "$min_quantity_threshold"]},
        "status": {"$ne": "expired"}
    }).to_list(length=None)
    
    # Expired items
    expired_items = await db.inventory.find({
        "expiry_date": {"$lt": current_date},
        "expiry_date": {"$ne": None}
    }).to_list(length=None)
    
    # Items expiring soon
    expiring_items = await db.inventory.find({
        "expiry_date": {"$gte": current_date, "$lte": future_date},
        "expiry_date": {"$ne": None}
    }).to_list(length=None)
    
    return {
        "low_stock": [InventoryItem(**item) for item in low_stock_items],
        "expired": [InventoryItem(**item) for item in expired_items],
        "expiring_soon": [InventoryItem(**item) for item in expiring_items]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
