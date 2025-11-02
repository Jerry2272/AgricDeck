# AgricDeck Backend API

A comprehensive FastAPI backend for the AgricDeck marketplace platform connecting farmers with buyers.

## Features

### Core Features
- **Authentication & User Management**: Registration, login, role-based access (Buyer, Farmer, Admin)
- **Farmer Features**: Product listing, inventory management, order management, earnings dashboard, withdrawals
- **Buyer Features**: Product catalog, search & filtering, cart management, checkout, payments, order tracking, reviews
- **Admin Features**: Dashboard, farmer verification, product moderation, transaction monitoring, dispute resolution
- **Payment Integration**: Paystack and Flutterwave payment gateways
- **Logistics Integration**: Kwik Delivery API integration
- **File Uploads**: Product images, profile images, verification documents

## Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens
- **Payment Gateways**: Paystack, Flutterwave
- **Logistics**: Kwik Delivery API

## Project Structure

```
backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py          # User profile endpoints
│   │       ├── buyers.py         # Buyer-specific endpoints
│   │       ├── farmers.py        # Farmer-specific endpoints
│   │       ├── admin.py          # Admin endpoints
│   │       ├── payments.py       # Payment processing
│   │       ├── disputes.py       # Dispute management
│   │       ├── uploads.py       # File uploads
│   │       └── tracking.py     # Order tracking
│   ├── core/
│   │   ├── auth/
│   │   │   ├── jwt.py           # JWT token management
│   │   │   └── password.py      # Password hashing
│   │   └── config/
│   │       ├── settings.py      # Application settings
│   │       ├── db.py            # Database configuration
│   │       └── deps.py          # Dependencies
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   └── services/
│       ├── payment/             # Payment service integrations
│       │   ├── paystack.py
│       │   └── flutterwave.py
│       └── logistics/           # Logistics service integrations
│           └── kwik.py
├── main.py                      # FastAPI application entry point
└── requirements.txt            # Python dependencies
```

## API Endpoints

### Authentication (`/api/v1/auth`)
- `POST /register` - Register new user
- `POST /farmer-onboarding` - Complete farmer onboarding
- `POST /login` - Login and get access token
- `GET /me` - Get current user info
- `GET /earnings` - Get farmer earnings (farmer only)

### Users (`/api/v1/users`)
- `GET /me` - Get user profile
- `PUT /me` - Update user profile

### Buyers (`/api/v1/buyers`)
- `GET /products` - Browse products (with filters)
- `GET /products/{id}` - Get product details
- `GET /cart` - Get cart items
- `POST /cart` - Add to cart
- `PUT /cart/{id}` - Update cart item
- `DELETE /cart/{id}` - Remove from cart
- `POST /orders` - Create order
- `GET /orders` - Get buyer orders
- `GET /orders/{id}` - Get order details
- `POST /orders/{id}/reviews` - Create review
- `GET /farmers/{id}/reviews` - Get farmer reviews

### Farmers (`/api/v1/farmers`)
- `GET /products` - Get farmer products
- `POST /products` - Create product listing
- `GET /products/{id}` - Get product details
- `PUT /products/{id}` - Update product
- `DELETE /products/{id}` - Delete product
- `GET /orders` - Get farmer orders
- `GET /orders/{id}` - Get order details
- `PUT /orders/{id}/status` - Update order status
- `PUT /profile` - Update farmer profile
- `POST /withdrawals` - Request withdrawal
- `GET /withdrawals` - Get withdrawal history

### Admin (`/api/v1/admin`)
- `GET /dashboard` - Get dashboard statistics
- `GET /farmers/pending` - Get pending farmer verifications
- `PUT /farmers/{id}/verify` - Verify/reject farmer
- `GET /products` - Get products for moderation
- `PUT /products/{id}/status` - Suspend/activate product
- `GET /orders` - Get all orders
- `GET /disputes` - Get all disputes
- `PUT /disputes/{id}/resolve` - Resolve dispute
- `GET /withdrawals` - Get all withdrawals
- `PUT /withdrawals/{id}/process` - Process withdrawal
- `GET /transactions` - Get all transactions

### Payments (`/api/v1/payments`)
- `POST /initiate` - Initiate payment
- `POST /verify` - Verify payment
- `POST /webhooks/paystack` - Paystack webhook
- `POST /webhooks/flutterwave` - Flutterwave webhook
- `GET /transactions` - Get payment transactions

### Disputes (`/api/v1/disputes`)
- `POST /` - Create dispute
- `GET /` - Get user disputes
- `GET /{id}` - Get dispute details
- `PUT /{id}` - Update dispute

### Uploads (`/api/v1/uploads`)
- `POST /product-images` - Upload product images
- `POST /profile-image` - Upload profile image
- `POST /verification-document` - Upload verification document
- `GET /files/{category}/{filename}` - Get uploaded file

### Tracking (`/api/v1/tracking`)
- `GET /orders/{id}` - Track order status
- `GET /logistics/{tracking_number}` - Track via logistics provider

## Setup Instructions

### Prerequisites
- Python 3.9+
- PostgreSQL
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
```bash
cd backend
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Create .env file**
```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/agricdeck

# Security
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200  # 30 days

# Payment Gateways
PAYSTACK_SECRET_KEY=your-paystack-secret-key
PAYSTACK_PUBLIC_KEY=your-paystack-public-key
FLUTTERWAVE_SECRET_KEY=your-flutterwave-secret-key
FLUTTERWAVE_PUBLIC_KEY=your-flutterwave-public-key
FLUTTERWAVE_CALLBACK_URL=http://localhost:8000/api/v1/payments

# Logistics APIs
KWIK_API_KEY=your-kwik-api-key
KWIK_API_URL=https://api.kwik.delivery/v1

# Platform Settings
COMMISSION_PERCENTAGE=5.0
MIN_WITHDRAWAL_AMOUNT=1000.0

# File Upload
UPLOAD_DIR=media
MAX_UPLOAD_SIZE=5242880  # 5MB
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Run the server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Interactive API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Database Models

### User
- Supports roles: Buyer, Farmer, Admin
- Farmer-specific fields: farm details, bank account info
- Wallet balance tracking
- KYC verification status

### Product
- Categories: Grains, Vegetables, Fruits, Tubers, Legumes, Spices, Other
- Inventory management
- Product images
- Location and seasonality

### Order
- Status flow: Pending → Accepted → Preparing → Shipped → In Transit → Delivered
- Payment status tracking
- Delivery/Pickup options
- Logistics integration

### PaymentTransaction
- Supports: Payment, Withdrawal, Refund, Commission
- Gateway integration (Paystack/Flutterwave)
- Transaction history

### Withdrawal
- Farmer earnings withdrawal
- Admin approval process
- Gateway integration

### Review
- Rating (1-5 stars)
- Comments
- Moderation support

### Dispute
- Dispute types: Product Quality, Delivery Issue, Payment Issue, Other
- Status tracking and resolution

## Payment Flow

1. Buyer creates order
2. Buyer initiates payment via `/payments/initiate`
3. Payment gateway returns authorization URL
4. Buyer completes payment on gateway
5. Gateway webhook notifies backend via `/payments/webhooks/{gateway}`
6. Backend verifies payment and updates order status
7. When order is delivered, farmer wallet is updated

## Logistics Flow

1. Buyer creates order with delivery type
2. System gets delivery quote from logistics partner
3. Farmer accepts order
4. Farmer marks order as shipped
5. System creates delivery order with logistics partner
6. Tracking number is stored in order
7. Order status updates via logistics tracking API

## Security Features

- JWT token-based authentication
- Password hashing with bcrypt
- Role-based access control
- CORS configuration
- Input validation with Pydantic

## Testing

API endpoints can be tested using:
- FastAPI interactive docs at `/docs`
- Postman collection
- cURL commands

## Notes

- All monetary values are in NGN (Nigerian Naira)
- Commission percentage is configurable
- Minimum withdrawal amount is configurable
- File uploads are stored locally (can be configured for cloud storage)
- Logistics integration supports Kwik Delivery (can be extended)

## Next Steps

1. Add unit tests
2. Add integration tests
3. Set up CI/CD pipeline
4. Configure cloud storage for file uploads
5. Add email notifications
6. Implement real-time notifications (WebSockets)
7. Add rate limiting
8. Set up logging and monitoring

