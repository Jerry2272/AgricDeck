from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from typing import List, Optional
from app.core.config.db import get_db
from app.core.auth.jwt import get_current_active_user, require_role
from app.models.user import User, UserRole
from app.models.product import Product, ProductStatus, ProductCategory
from app.models.order import Order, OrderStatus, OrderItem, DeliveryType, PaymentStatus
from app.models.cart import CartItem
from app.models.review import Review
from app.schemas.product import ProductResponse, ProductListItem
from app.schemas.order import OrderCreate, OrderResponse, OrderListResponse
from app.schemas.cart import CartItemCreate, CartItemUpdate, CartItemResponse, CartResponse
from app.schemas.review import ReviewCreate, ReviewResponse, FarmerRatingResponse
from datetime import datetime
import uuid
import json

router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.get("/products", response_model=List[ProductListItem])
async def browse_products(
    skip: int = 0,
    limit: int = 20,
    category: Optional[ProductCategory] = None,
    search: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    state: Optional[str] = None,
    city: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Browse product catalog with filters"""
    query = db.query(Product).filter(Product.status == ProductStatus.ACTIVE)
    
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%")
            )
        )
    
    if min_price:
        query = query.filter(Product.price_per_unit >= min_price)
    
    if max_price:
        query = query.filter(Product.price_per_unit <= max_price)
    
    if state:
        query = query.filter(Product.location_state.ilike(f"%{state}%"))
    
    if city:
        query = query.filter(Product.location_city.ilike(f"%{city}%"))
    
    products = query.offset(skip).limit(limit).all()
    
    # Convert to ProductListItem with farmer name
    result = []
    for product in products:
        farmer = db.query(User).filter(User.id == product.farmer_id).first()
        item = ProductListItem(
            id=product.id,
            name=product.name,
            category=product.category,
            price_per_unit=product.price_per_unit,
            unit=product.unit,
            available_quantity=product.available_quantity,
            location_state=product.location_state,
            location_city=product.location_city,
            image_urls=json.loads(product.image_urls) if product.image_urls else None,
            farmer_id=product.farmer_id,
            farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
        )
        result.append(item)
    
    return result


@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_details(
    product_id: int,
    db: Session = Depends(get_db)
):
    """Get detailed product information"""
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.status == ProductStatus.ACTIVE
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return product


@router.get("/cart", response_model=CartResponse)
async def get_cart(
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Get current user's cart"""
    cart_items = db.query(CartItem).filter(
        CartItem.buyer_id == current_user.id
    ).all()
    
    items = []
    subtotal = 0.0
    
    for cart_item in cart_items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if product and product.status == ProductStatus.ACTIVE:
            item_subtotal = cart_item.quantity * product.price_per_unit
            subtotal += item_subtotal
            
            # Create ProductListItem for cart item
            farmer = db.query(User).filter(User.id == product.farmer_id).first()
            product_item = ProductListItem(
                id=product.id,
                name=product.name,
                category=product.category,
                price_per_unit=product.price_per_unit,
                unit=product.unit,
                available_quantity=product.available_quantity,
                location_state=product.location_state,
                location_city=product.location_city,
                image_urls=json.loads(product.image_urls) if product.image_urls else None,
                farmer_id=product.farmer_id,
                farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
            )
            
            cart_item_response = CartItemResponse(
                id=cart_item.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                product=product_item,
                created_at=cart_item.created_at
            )
            items.append(cart_item_response)
    
    return CartResponse(
        items=items,
        total_items=len(items),
        subtotal=subtotal
    )


@router.post("/cart", response_model=CartItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    cart_item_data: CartItemCreate,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Add item to cart"""
    product = db.query(Product).filter(
        Product.id == cart_item_data.product_id,
        Product.status == ProductStatus.ACTIVE
    ).first()
    
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or not available"
        )
    
    if cart_item_data.quantity > product.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient quantity available"
        )
    
    # Check if item already in cart
    existing_item = db.query(CartItem).filter(
        CartItem.buyer_id == current_user.id,
        CartItem.product_id == cart_item_data.product_id
    ).first()
    
    if existing_item:
        existing_item.quantity += cart_item_data.quantity
        db.commit()
        db.refresh(existing_item)
        
        farmer = db.query(User).filter(User.id == product.farmer_id).first()
        product_item = ProductListItem(
            id=product.id,
            name=product.name,
            category=product.category,
            price_per_unit=product.price_per_unit,
            unit=product.unit,
            available_quantity=product.available_quantity,
            location_state=product.location_state,
            location_city=product.location_city,
            image_urls=json.loads(product.image_urls) if product.image_urls else None,
            farmer_id=product.farmer_id,
            farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
        )
        
        return CartItemResponse(
            id=existing_item.id,
            product_id=existing_item.product_id,
            quantity=existing_item.quantity,
            product=product_item,
            created_at=existing_item.created_at
        )
    
    cart_item = CartItem(
        buyer_id=current_user.id,
        product_id=cart_item_data.product_id,
        quantity=cart_item_data.quantity
    )
    
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    
    farmer = db.query(User).filter(User.id == product.farmer_id).first()
    product_item = ProductListItem(
        id=product.id,
        name=product.name,
        category=product.category,
        price_per_unit=product.price_per_unit,
        unit=product.unit,
        available_quantity=product.available_quantity,
        location_state=product.location_state,
        location_city=product.location_city,
        image_urls=json.loads(product.image_urls) if product.image_urls else None,
        farmer_id=product.farmer_id,
        farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
    )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        product=product_item,
        created_at=cart_item.created_at
    )


@router.put("/cart/{cart_item_id}", response_model=CartItemResponse)
async def update_cart_item(
    cart_item_id: int,
    cart_item_data: CartItemUpdate,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Update cart item quantity"""
    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.buyer_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    product = db.query(Product).filter(Product.id == cart_item.product_id).first()
    if cart_item_data.quantity > product.available_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Insufficient quantity available"
        )
    
    cart_item.quantity = cart_item_data.quantity
    db.commit()
    db.refresh(cart_item)
    
    farmer = db.query(User).filter(User.id == product.farmer_id).first()
    product_item = ProductListItem(
        id=product.id,
        name=product.name,
        category=product.category,
        price_per_unit=product.price_per_unit,
        unit=product.unit,
        available_quantity=product.available_quantity,
        location_state=product.location_state,
        location_city=product.location_city,
        image_urls=json.loads(product.image_urls) if product.image_urls else None,
        farmer_id=product.farmer_id,
        farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
    )
    
    return CartItemResponse(
        id=cart_item.id,
        product_id=cart_item.product_id,
        quantity=cart_item.quantity,
        product=product_item,
        created_at=cart_item.created_at
    )


@router.delete("/cart/{cart_item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    cart_item_id: int,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Remove item from cart"""
    cart_item = db.query(CartItem).filter(
        CartItem.id == cart_item_id,
        CartItem.buyer_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cart item not found"
        )
    
    db.delete(cart_item)
    db.commit()


@router.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Create a new order from cart items or direct order"""
    from app.core.config.settings import settings
    from app.services.logistics.kwik import get_delivery_quote
    
    # Validate all items and get products
    order_items = []
    subtotal = 0.0
    farmer_id = None
    
    for item_data in order_data.items:
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.status == ProductStatus.ACTIVE
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {item_data.product_id} not found or not available"
            )
        
        if item_data.quantity > product.available_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient quantity for product {product.name}"
            )
        
        if farmer_id is None:
            farmer_id = product.farmer_id
        elif farmer_id != product.farmer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="All items must be from the same farmer"
            )
        
        item_subtotal = item_data.quantity * product.price_per_unit
        subtotal += item_subtotal
        
        order_items.append({
            "product": product,
            "quantity": item_data.quantity,
            "unit_price": product.price_per_unit,
            "subtotal": item_subtotal
        })
    
    if not farmer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid products in order"
        )
    
    # Calculate commission
    commission = subtotal * (settings.COMMISSION_PERCENTAGE / 100)
    
    # Get delivery fee if delivery
    delivery_fee = 0.0
    if order_data.delivery_type == DeliveryType.DELIVERY:
        # Get logistics quote
        try:
            quote = await get_delivery_quote(
                pickup_location=order_data.delivery_state or "",
                delivery_location=order_data.delivery_city or ""
            )
            delivery_fee = quote.get("price", 0.0)
        except:
            # If logistics API fails, use default fee
            delivery_fee = 500.0  # Default delivery fee
    
    total_amount = subtotal + delivery_fee
    
    # Generate order number
    order_number = f"AGD-{uuid.uuid4().hex[:8].upper()}"
    
    # Create order
    order = Order(
        order_number=order_number,
        buyer_id=current_user.id,
        farmer_id=farmer_id,
        status=OrderStatus.PENDING,
        delivery_type=order_data.delivery_type,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        commission=commission,
        total_amount=total_amount,
        payment_status=PaymentStatus.PENDING,
        delivery_address=order_data.delivery_address,
        delivery_state=order_data.delivery_state,
        delivery_city=order_data.delivery_city,
        delivery_phone=order_data.delivery_phone,
        delivery_instructions=order_data.delivery_instructions,
        pickup_address=order_data.pickup_address,
        pickup_phone=order_data.pickup_phone,
        buyer_notes=order_data.buyer_notes
    )
    
    db.add(order)
    db.flush()
    
    # Create order items
    for item_data in order_items:
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data["product"].id,
            product_name=item_data["product"].name,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            subtotal=item_data["subtotal"]
        )
        db.add(order_item)
    
    # Clear cart items for this farmer
    cart_items = db.query(CartItem).filter(
        CartItem.buyer_id == current_user.id,
        CartItem.product_id.in_([item["product"].id for item in order_items])
    ).all()
    
    for cart_item in cart_items:
        db.delete(cart_item)
    
    db.commit()
    db.refresh(order)
    
    return order


@router.get("/orders", response_model=List[OrderListResponse])
async def get_my_orders(
    skip: int = 0,
    limit: int = 20,
    status_filter: Optional[OrderStatus] = None,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Get all orders for current buyer"""
    query = db.query(Order).filter(Order.buyer_id == current_user.id)
    
    if status_filter:
        query = query.filter(Order.status == status_filter)
    
    orders = query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for order in orders:
        farmer = db.query(User).filter(User.id == order.farmer_id).first()
        result.append(OrderListResponse(
            id=order.id,
            order_number=order.order_number,
            status=order.status,
            total_amount=order.total_amount,
            delivery_type=order.delivery_type,
            created_at=order.created_at,
            farmer_name=f"{farmer.first_name} {farmer.last_name}" if farmer else None
        ))
    
    return result


@router.get("/orders/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Get a specific order by ID"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == current_user.id
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    return order


@router.post("/orders/{order_id}/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(
    order_id: int,
    review_data: ReviewCreate,
    current_user: User = Depends(require_role([UserRole.BUYER])),
    db: Session = Depends(get_db)
):
    """Create a review for a delivered order"""
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.buyer_id == current_user.id,
        Order.status == OrderStatus.DELIVERED
    ).first()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found or not delivered"
        )
    
    # Check if review already exists
    existing_review = db.query(Review).filter(
        Review.order_id == order_id
    ).first()
    
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Review already exists for this order"
        )
    
    review = Review(
        order_id=order_id,
        buyer_id=current_user.id,
        farmer_id=order.farmer_id,
        rating=review_data.rating,
        comment=review_data.comment
    )
    
    db.add(review)
    db.commit()
    db.refresh(review)
    
    return review


@router.get("/farmers/{farmer_id}/reviews", response_model=FarmerRatingResponse)
async def get_farmer_reviews(
    farmer_id: int,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get all reviews for a farmer"""
    farmer = db.query(User).filter(
        User.id == farmer_id,
        User.role == UserRole.FARMER
    ).first()
    
    if not farmer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found"
        )
    
    reviews = db.query(Review).filter(
        Review.farmer_id == farmer_id,
        Review.is_approved == True
    ).offset(skip).limit(limit).all()
    
    # Calculate average rating
    avg_rating = db.query(func.avg(Review.rating)).filter(
        Review.farmer_id == farmer_id,
        Review.is_approved == True
    ).scalar() or 0.0
    
    review_responses = []
    for review in reviews:
        buyer = db.query(User).filter(User.id == review.buyer_id).first()
        review_responses.append(ReviewResponse(
            id=review.id,
            order_id=review.order_id,
            buyer_id=review.buyer_id,
            farmer_id=review.farmer_id,
            rating=review.rating,
            comment=review.comment,
            buyer_name=f"{buyer.first_name} {buyer.last_name}" if buyer else None,
            created_at=review.created_at
        ))
    
    return FarmerRatingResponse(
        farmer_id=farmer_id,
        average_rating=float(avg_rating),
        total_reviews=len(reviews),
        reviews=review_responses
    )

