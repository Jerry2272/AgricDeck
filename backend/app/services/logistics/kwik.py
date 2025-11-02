import httpx
from typing import Optional, Dict, Any
from app.core.config.settings import settings


async def get_delivery_quote(
    pickup_location: str,
    delivery_location: str,
    weight: Optional[float] = None,
    distance: Optional[float] = None
) -> Dict[str, Any]:
    """Get delivery quote from Kwik Delivery"""
    url = f"{settings.KWIK_API_URL}/quotes"
    
    headers = {
        "Authorization": f"Bearer {settings.KWIK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "pickup_address": pickup_location,
        "delivery_address": delivery_location,
    }
    
    if weight:
        data["weight"] = weight
    if distance:
        data["distance"] = distance
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            # Extract price from Kwik response format
            return {
                "price": result.get("price", 500.0),
                "estimated_time": result.get("estimated_time", "24-48 hours"),
                "quote_id": result.get("quote_id"),
                "provider": "kwik"
            }
    except Exception as e:
        # Return default quote if API fails
        return {
            "price": 500.0,
            "estimated_time": "24-48 hours",
            "quote_id": None,
            "provider": "kwik",
            "error": str(e)
        }


async def create_delivery_order(
    pickup_address: str,
    delivery_address: str,
    pickup_phone: str,
    delivery_phone: str,
    pickup_name: str,
    delivery_name: str,
    order_reference: str,
    item_description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a delivery order with Kwik"""
    url = f"{settings.KWIK_API_URL}/orders"
    
    headers = {
        "Authorization": f"Bearer {settings.KWIK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "pickup_address": pickup_address,
        "delivery_address": delivery_address,
        "pickup_phone": pickup_phone,
        "delivery_phone": delivery_phone,
        "pickup_name": pickup_name,
        "delivery_name": delivery_name,
        "order_reference": order_reference,
        "item_description": item_description or "Agricultural products"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=data, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "tracking_number": result.get("tracking_number"),
                "order_id": result.get("order_id"),
                "status": result.get("status", "pending"),
                "provider": "kwik"
            }
    except Exception as e:
        return {
            "tracking_number": None,
            "order_id": None,
            "status": "failed",
            "provider": "kwik",
            "error": str(e)
        }


async def track_delivery(tracking_number: str) -> Dict[str, Any]:
    """Track delivery status with Kwik"""
    url = f"{settings.KWIK_API_URL}/tracking/{tracking_number}"
    
    headers = {
        "Authorization": f"Bearer {settings.KWIK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            result = response.json()
            
            return {
                "status": result.get("status"),
                "current_location": result.get("current_location"),
                "estimated_delivery": result.get("estimated_delivery"),
                "provider": "kwik"
            }
    except Exception as e:
        return {
            "status": "unknown",
            "current_location": None,
            "estimated_delivery": None,
            "provider": "kwik",
            "error": str(e)
        }

