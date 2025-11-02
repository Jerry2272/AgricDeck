# Frontend Development Guide - AgricDeck React Application

This guide provides a comprehensive list of pages, components, and API endpoints needed for the React frontend application.

## Table of Contents
1. [Project Structure](#project-structure)
2. [Authentication Pages](#authentication-pages)
3. [Buyer Pages](#buyer-pages)
4. [Farmer Pages](#farmer-pages)
5. [Admin Pages](#admin-pages)
6. [Shared Components](#shared-components)
7. [API Integration Guide](#api-integration-guide)
8. [Routing Structure](#routing-structure)
9. [State Management](#state-management)

---

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Shared components (Header, Footer, etc.)
│   │   ├── buyer/           # Buyer-specific components
│   │   ├── farmer/          # Farmer-specific components
│   │   └── admin/           # Admin-specific components
│   ├── pages/
│   │   ├── auth/            # Authentication pages
│   │   ├── buyer/           # Buyer pages
│   │   ├── farmer/          # Farmer pages
│   │   └── admin/           # Admin pages
│   ├── services/
│   │   └── api.js          # API service functions
│   ├── context/
│   │   ├── AuthContext.js   # Authentication context
│   │   └── CartContext.js   # Cart context
│   ├── hooks/
│   │   ├── useAuth.js      # Authentication hook
│   │   └── useApi.js       # API hook
│   ├── utils/
│   │   ├── constants.js    # Constants
│   │   ├── helpers.js      # Helper functions
│   │   └── validation.js   # Validation functions
│   ├── App.js              # Main App component
│   └── index.js            # Entry point
```

---

## Authentication Pages

### 1. **Login Page** (`/login`)
- **Purpose**: User login (Buyer/Farmer/Admin)
- **Form Fields**: 
  - Email
  - Password
- **API Endpoint**: `POST /api/v1/auth/login`
- **On Success**: Store token, redirect based on user role
- **Features**:
  - Remember me option
  - Forgot password link (if implemented)
  - Redirect to registration
  - Error handling

### 2. **Registration Page** (`/register`)
- **Purpose**: New user registration
- **Form Fields**:
  - Email
  - Phone
  - First Name
  - Last Name
  - Password
  - Confirm Password
  - Role Selection (Buyer/Farmer)
- **API Endpoint**: `POST /api/v1/auth/register`
- **On Success**: Redirect to login or onboarding (for farmers)
- **Features**:
  - Form validation
  - Password strength indicator
  - Role selection

### 3. **Farmer Onboarding Page** (`/farmer-onboarding`)
- **Purpose**: Complete farmer profile with verification details
- **Form Fields**:
  - Farm Name
  - Farm Address
  - State
  - City
  - Coordinates (optional)
  - Bank Account Number
  - Bank Name
  - Account Name
  - Verification Document Upload
- **API Endpoints**: 
  - `POST /api/v1/auth/farmer-onboarding`
  - `POST /api/v1/uploads/verification-document`
- **Features**:
  - File upload for verification document
  - Form validation
  - Progress indicator

---

## Buyer Pages

### 4. **Buyer Dashboard/Home** (`/buyer/dashboard`)
- **Purpose**: Buyer's main landing page
- **API Endpoints**:
  - `GET /api/v1/buyers/products` - Browse products
  - `GET /api/v1/auth/me` - Get user info
- **Features**:
  - Product showcase
  - Quick search
  - Category filters
  - Featured products

### 5. **Product Catalog** (`/buyer/products`)
- **Purpose**: Browse all available products
- **Filters**:
  - Category (Grains, Vegetables, Fruits, etc.)
  - Price range (min/max)
  - Location (State, City)
  - Search by name
- **API Endpoint**: `GET /api/v1/buyers/products?category=&min_price=&max_price=&state=&city=&search=`
- **Features**:
  - Product grid/list view toggle
  - Sorting options (price, name, newest)
  - Pagination
  - Product cards with:
    - Product image
    - Name
    - Price per unit
    - Available quantity
    - Location
    - Farmer name
    - Rating (if available)

### 6. **Product Detail Page** (`/buyer/products/:id`)
- **Purpose**: View detailed product information
- **API Endpoints**:
  - `GET /api/v1/buyers/products/:id`
  - `GET /api/v1/buyers/farmers/:farmer_id/reviews`
- **Features**:
  - Product images carousel
  - Full description
  - Pricing information
  - Farmer profile card
  - Reviews section
  - Add to cart button
  - Quantity selector

### 7. **Shopping Cart** (`/buyer/cart`)
- **Purpose**: View and manage cart items
- **API Endpoints**:
  - `GET /api/v1/buyers/cart`
  - `PUT /api/v1/buyers/cart/:cart_item_id`
  - `DELETE /api/v1/buyers/cart/:cart_item_id`
- **Features**:
  - Cart items list
  - Quantity adjustment
  - Remove items
  - Subtotal calculation
  - Proceed to checkout button
  - Empty cart state

### 8. **Checkout Page** (`/buyer/checkout`)
- **Purpose**: Complete order placement
- **Form Fields**:
  - Delivery Type (Delivery/Pickup)
  - If Delivery:
    - Delivery Address
    - State
    - City
    - Phone
    - Delivery Instructions
  - If Pickup:
    - Pickup Address
    - Pickup Phone
  - Buyer Notes
- **API Endpoint**: `POST /api/v1/buyers/orders`
- **Features**:
  - Order summary
  - Delivery fee calculation
  - Total amount display
  - Place order button

### 9. **Payment Page** (`/buyer/payment/:orderId`)
- **Purpose**: Initiate and process payment
- **API Endpoints**:
  - `POST /api/v1/payments/initiate`
  - `POST /api/v1/payments/verify`
- **Payment Methods**:
  - Card
  - Bank Transfer
  - USSD
  - Wallet
- **Features**:
  - Payment method selection
  - Gateway selection (Paystack/Flutterwave)
  - Payment gateway redirect/integration
  - Payment status display
  - Success/failure handling

### 10. **Buyer Orders List** (`/buyer/orders`)
- **Purpose**: View all buyer orders
- **API Endpoint**: `GET /api/v1/buyers/orders?status=`
- **Features**:
  - Filter by status (Pending, Accepted, Shipped, Delivered, etc.)
  - Order cards with:
    - Order number
    - Status badge
    - Total amount
    - Order date
    - Farmer name
  - Pagination
  - Click to view details

### 11. **Order Details** (`/buyer/orders/:id`)
- **Purpose**: View order details and track status
- **API Endpoints**:
  - `GET /api/v1/buyers/orders/:id`
  - `GET /api/v1/tracking/orders/:id`
- **Features**:
  - Order information
  - Order items list
  - Order status timeline
  - Delivery tracking (if shipped)
  - Payment status
  - Delivery information
  - Leave review button (if delivered)

### 12. **Order Tracking** (`/buyer/orders/:id/track`)
- **Purpose**: Real-time order tracking
- **API Endpoint**: `GET /api/v1/tracking/orders/:id`
- **Features**:
  - Status timeline
  - Current location (if in transit)
  - Estimated delivery date
  - Logistics tracking number
  - Map view (if available)

### 13. **Leave Review Page** (`/buyer/orders/:id/review`)
- **Purpose**: Leave review for delivered order
- **Form Fields**:
  - Rating (1-5 stars)
  - Comment (optional)
- **API Endpoint**: `POST /api/v1/buyers/orders/:id/reviews`
- **Features**:
  - Star rating selector
  - Text area for comments
  - Submit review button
  - Validation

### 14. **Farmer Reviews** (`/buyer/farmers/:id/reviews`)
- **Purpose**: View all reviews for a specific farmer
- **API Endpoint**: `GET /api/v1/buyers/farmers/:id/reviews`
- **Features**:
  - Average rating display
  - Total reviews count
  - Reviews list with:
    - Rating
    - Comment
    - Buyer name
    - Date

---

## Farmer Pages

### 15. **Farmer Dashboard** (`/farmer/dashboard`)
- **Purpose**: Farmer's main landing page
- **API Endpoints**:
  - `GET /api/v1/auth/earnings` - Earnings summary
  - `GET /api/v1/farmers/orders?status=pending` - Pending orders
- **Features**:
  - Earnings overview card:
    - Total Earnings
    - Wallet Balance
    - Pending Withdrawals
    - Total Sales
  - Recent orders widget
  - Quick stats
  - Pending verification banner (if not verified)

### 16. **Earnings Dashboard** (`/farmer/earnings`)
- **Purpose**: Detailed earnings information
- **API Endpoint**: `GET /api/v1/auth/earnings`
- **Features**:
  - Earnings summary cards
  - Sales history chart/graph
  - Recent transactions
  - Withdrawal history link

### 17. **Product List** (`/farmer/products`)
- **Purpose**: Manage farmer's product listings
- **API Endpoints**:
  - `GET /api/v1/farmers/products`
  - `POST /api/v1/farmers/products`
  - `PUT /api/v1/farmers/products/:id`
  - `DELETE /api/v1/farmers/products/:id`
- **Features**:
  - Products table/grid
  - Status indicators (Active, Sold Out, Suspended)
  - Quick actions (Edit, Delete, View)
  - Add new product button
  - Search and filter

### 18. **Add Product Page** (`/farmer/products/new`)
- **Purpose**: Create new product listing
- **Form Fields**:
  - Product Name *
  - Description
  - Category * (Dropdown)
  - Price per Unit *
  - Unit * (kg, bag, bunch, etc.)
  - Available Quantity *
  - Freshness Level
  - Harvest Date
  - Expiry Date
  - Location (State, City)
  - Seasonal Product (checkbox)
  - Season Months (if seasonal)
  - Product Images (multiple upload)
- **API Endpoints**:
  - `POST /api/v1/uploads/product-images` - Upload images
  - `POST /api/v1/farmers/products` - Create product
- **Features**:
  - Image upload (drag & drop or file picker)
  - Form validation
  - Preview images
  - Save draft option

### 19. **Edit Product Page** (`/farmer/products/:id/edit`)
- **Purpose**: Update existing product
- **API Endpoints**:
  - `GET /api/v1/farmers/products/:id`
  - `PUT /api/v1/farmers/products/:id`
- **Features**:
  - Pre-filled form
  - Update images
  - Mark as sold out
  - Save changes

### 20. **Inventory Management** (`/farmer/inventory`)
- **Purpose**: Quick inventory updates
- **API Endpoint**: `PUT /api/v1/farmers/products/:id`
- **Features**:
  - Products list with quantities
  - Quick quantity update
  - Bulk updates
  - Low stock alerts

### 21. **Farmer Orders** (`/farmer/orders`)
- **Purpose**: View and manage farmer orders
- **API Endpoint**: `GET /api/v1/farmers/orders?status=`
- **Features**:
  - Filter by status
  - Order cards/table
  - Quick status update buttons
  - New orders highlight

### 22. **Order Details (Farmer)** (`/farmer/orders/:id`)
- **Purpose**: View and update order status
- **API Endpoints**:
  - `GET /api/v1/farmers/orders/:id`
  - `PUT /api/v1/farmers/orders/:id/status`
- **Features**:
  - Order information display
  - Order items list
  - Buyer information
  - Delivery/pickup details
  - Status update dropdown:
    - Accept
    - Reject
    - Preparing
    - Shipped
    - Delivered
  - Add farmer notes
  - View payment status

### 23. **Farmer Profile** (`/farmer/profile`)
- **Purpose**: View and edit farmer profile
- **API Endpoints**:
  - `GET /api/v1/auth/me`
  - `PUT /api/v1/farmers/profile`
  - `POST /api/v1/uploads/profile-image`
- **Features**:
  - Profile information display
  - Edit form
  - Profile image upload
  - Farm details
  - Bank account information
  - Verification status display

### 24. **Withdrawals** (`/farmer/withdrawals`)
- **Purpose**: Manage withdrawal requests
- **API Endpoints**:
  - `GET /api/v1/farmers/withdrawals` - Get withdrawal history
  - `POST /api/v1/farmers/withdrawals` - Request withdrawal
- **Features**:
  - Withdrawal request form:
    - Amount
    - Bank Account Number
    - Bank Name
    - Account Name
  - Withdrawal history table:
    - Amount
    - Status (Pending, Success, Failed)
    - Request Date
    - Processed Date
  - Wallet balance display
  - Minimum withdrawal amount info

---

## Admin Pages

### 25. **Admin Dashboard** (`/admin/dashboard`)
- **Purpose**: Admin overview and statistics
- **API Endpoint**: `GET /api/v1/admin/dashboard`
- **Features**:
  - Statistics cards:
    - Total Users
    - Total Farmers
    - Total Buyers
    - Pending Farmer Verifications
    - Total Orders
    - Total Revenue
    - Total Commission
    - Open Disputes
  - Charts/Graphs:
    - Revenue trends
    - Orders over time
    - User growth
  - Recent transactions table
  - Quick actions

### 26. **Farmer Verification** (`/admin/farmers/pending`)
- **Purpose**: Review and verify farmer applications
- **API Endpoints**:
  - `GET /api/v1/admin/farmers/pending`
  - `PUT /api/v1/admin/farmers/:id/verify`
- **Features**:
  - Pending farmers list
  - Farmer details:
    - Personal information
    - Farm details
    - Bank information
    - Verification document
  - Approve/Reject buttons
  - Admin notes field

### 27. **Product Moderation** (`/admin/products`)
- **Purpose**: Moderate and manage all products
- **API Endpoints**:
  - `GET /api/v1/admin/products`
  - `PUT /api/v1/admin/products/:id/status`
- **Features**:
  - Products list with filters
  - Product details view
  - Suspend/Activate actions
  - Product owner information
  - Reason for suspension field

### 28. **Order Management** (`/admin/orders`)
- **Purpose**: View and manage all orders
- **API Endpoint**: `GET /api/v1/admin/orders`
- **Features**:
  - All orders table
  - Filter by status
  - Buyer and farmer information
  - Order details view
  - Admin notes

### 29. **Dispute Management** (`/admin/disputes`)
- **Purpose**: Handle customer disputes
- **API Endpoints**:
  - `GET /api/v1/admin/disputes`
  - `PUT /api/v1/admin/disputes/:id/resolve`
- **Features**:
  - Disputes list with status
  - Dispute details:
    - Order information
    - Parties involved
    - Dispute type
    - Description
  - Resolution form:
    - Resolution text
    - Status update
  - Resolve/Close buttons

### 30. **Withdrawal Processing** (`/admin/withdrawals`)
- **Purpose**: Process farmer withdrawal requests
- **API Endpoints**:
  - `GET /api/v1/admin/withdrawals`
  - `PUT /api/v1/admin/withdrawals/:id/process`
- **Features**:
  - Pending withdrawals list
  - Withdrawal details:
    - Farmer information
    - Amount
    - Bank details
  - Approve/Reject buttons
  - Processing status
  - Transaction reference

### 31. **Transaction Management** (`/admin/transactions`)
- **Purpose**: View all payment transactions
- **API Endpoint**: `GET /api/v1/admin/transactions`
- **Features**:
  - Transactions table
  - Filter by:
    - Transaction type
    - Status
    - Gateway
    - Date range
  - Transaction details
  - Export option

---

## Shared Components

### 32. **Header/Navbar**
- **Features**:
  - Logo
  - Navigation links (role-based)
  - User menu dropdown
  - Cart icon (for buyers)
  - Notifications icon
  - Logout button

### 33. **Footer**
- **Features**:
  - Links
  - Contact information
  - Social media links
  - Copyright

### 34. **Product Card**
- **Reusable component** for displaying product information
- **Props**:
  - Product data
  - Show farmer info
  - Action buttons

### 35. **Order Card**
- **Reusable component** for displaying order summary
- **Props**:
  - Order data
  - Status badge
  - Action buttons

### 36. **Status Badge**
- **Component** for displaying order/product/transaction statuses
- **Colors**: Different colors for different statuses

### 37. **Image Uploader**
- **Reusable component** for file uploads
- **Features**:
  - Drag & drop
  - File picker
  - Image preview
  - Remove image
  - Multiple images support

### 38. **Loading Spinner**
- **Global loading indicator**

### 39. **Error Boundary**
- **Error handling component**

### 40. **Toast/Notification**
- **Success/error messages display**

---

## API Integration Guide

### Base Configuration

```javascript
// services/api.js
const API_BASE_URL = 'http://localhost:8000/api/v1';

// Axios instance with interceptors
import axios from 'axios';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - Add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - Handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized - redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### API Service Functions

```javascript
// services/auth.js
export const authService = {
  login: (email, password) => api.post('/auth/login', { email, password }),
  register: (userData) => api.post('/auth/register', userData),
  farmerOnboarding: (data) => api.post('/auth/farmer-onboarding', data),
  getCurrentUser: () => api.get('/auth/me'),
  getEarnings: () => api.get('/auth/earnings'),
};

// services/products.js
export const productService = {
  getProducts: (params) => api.get('/buyers/products', { params }),
  getProduct: (id) => api.get(`/buyers/products/${id}`),
  getMyProducts: () => api.get('/farmers/products'),
  createProduct: (data) => api.post('/farmers/products', data),
  updateProduct: (id, data) => api.put(`/farmers/products/${id}`, data),
  deleteProduct: (id) => api.delete(`/farmers/products/${id}`),
};

// services/orders.js
export const orderService = {
  createOrder: (data) => api.post('/buyers/orders', data),
  getOrders: (params) => api.get('/buyers/orders', { params }),
  getOrder: (id) => api.get(`/buyers/orders/${id}`),
  getFarmerOrders: (params) => api.get('/farmers/orders', { params }),
  updateOrderStatus: (id, data) => api.put(`/farmers/orders/${id}/status`, data),
  trackOrder: (id) => api.get(`/tracking/orders/${id}`),
};

// services/cart.js
export const cartService = {
  getCart: () => api.get('/buyers/cart'),
  addToCart: (data) => api.post('/buyers/cart', data),
  updateCartItem: (id, data) => api.put(`/buyers/cart/${id}`, data),
  removeFromCart: (id) => api.delete(`/buyers/cart/${id}`),
};

// services/payments.js
export const paymentService = {
  initiatePayment: (data) => api.post('/payments/initiate', data),
  verifyPayment: (data) => api.post('/payments/verify', data),
  getTransactions: () => api.get('/payments/transactions'),
};

// services/uploads.js
export const uploadService = {
  uploadProductImages: (formData) => api.post('/uploads/product-images', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  uploadProfileImage: (formData) => api.post('/uploads/profile-image', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  uploadVerificationDoc: (formData) => api.post('/uploads/verification-document', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
};

// services/admin.js
export const adminService = {
  getDashboard: () => api.get('/admin/dashboard'),
  getPendingFarmers: () => api.get('/admin/farmers/pending'),
  verifyFarmer: (id, data) => api.put(`/admin/farmers/${id}/verify`, data),
  getProducts: (params) => api.get('/admin/products', { params }),
  updateProductStatus: (id, data) => api.put(`/admin/products/${id}/status`, data),
  getDisputes: (params) => api.get('/admin/disputes', { params }),
  resolveDispute: (id, data) => api.put(`/admin/disputes/${id}/resolve`, data),
  getWithdrawals: (params) => api.get('/admin/withdrawals', { params }),
  processWithdrawal: (id, data) => api.put(`/admin/withdrawals/${id}/process`, data),
};
```

---
