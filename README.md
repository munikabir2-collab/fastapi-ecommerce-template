# FastAPI E-Commerce Template

![Python](https://img.shields.io/badge/python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.105.0-lightgreen?logo=fastapi)
![License](https://img.shields.io/badge/license-MIT-green)
![GitHub Repo Size](https://img.shields.io/github/repo-size/munikabir2-collab/fastapi-ecommerce-template)

A ready-to-use **FastAPI backend template** for an e-commerce platform, supporting sellers, orders, payments (Razorpay), notifications, and more.

---

## 🚀 Features

- **Seller Module**: Profile, bank account, products, order tracking
- **Orders & Payments**: Razorpay integration, commission calculation, payouts
- **Real-time Notifications**: WebSockets for instant updates
- **Admin Panel**: Trigger payouts, monitor sales
- **PDF Invoices**: Generate invoices with ReportLab

---

## 🛠 Installation

```bash
# Clone the repository
git clone https://github.com/munikabir2-collab/fastapi-ecommerce-template.git
cd fastapi-ecommerce-template

# Create virtual environment
python -m venv venv
# Activate it
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with database, Razorpay keys, secret keys

# Run database migrations
alembic upgrade head

# Start server
uvicorn main:app --reload



.
├── app/             # FastAPI app modules
├── alembic/         # Database migrations
├── invoices/        # Generated invoices
├── static/          # CSS, JS, images
├── templates/       # Jinja2 templates
├── main.py          # Entry point
├── requirements.txt
├── README.md

## 🖼 Demo Dashboard

Here’s a preview of the Seller Dashboard and key features:

### Seller Dashboard
![Seller Dashboard](https://raw.githubusercontent.com/munikabir2-collab/fastapi-ecommerce-template/main/assets/seller_dashboard.png)

### Order Tracking
![Order Tracking](https://raw.githubusercontent.com/munikabir2-collab/fastapi-ecommerce-template/main/assets/order_tracking.png)

### Products & Bank Details
![Products & Bank](https://raw.githubusercontent.com/munikabir2-collab/fastapi-ecommerce-template/main/assets/products_bank.png)

> Note: Replace these image URLs with your actual screenshots stored in your repository, e.g., under an `assets/` folder.