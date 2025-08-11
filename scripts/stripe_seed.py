#!/usr/bin/env python3
"""
Stripe product and price seeding script.

This script reads the product catalog from docs/billing/catalog.json
and creates or updates Products and Prices in Stripe. It's idempotent
and safe to run multiple times.

Usage:
    python scripts/stripe_seed.py

Environment variables required:
    STRIPE_SECRET_KEY - Stripe secret key for API access
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path to import backend modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv(project_root / "backend" / ".env")

def load_catalog() -> Dict[str, Any]:
    """Load product catalog from JSON file."""
    catalog_path = project_root / "docs" / "billing" / "catalog.json"
    
    if not catalog_path.exists():
        print(f"❌ Catalog file not found: {catalog_path}")
        sys.exit(1)
    
    with open(catalog_path, 'r') as f:
        return json.load(f)

def setup_stripe():
    """Setup Stripe API key from environment."""
    stripe_key = os.getenv("STRIPE_SECRET_KEY")
    
    if not stripe_key:
        print("❌ STRIPE_SECRET_KEY environment variable is required")
        print("   Please set it in backend/.env or as an environment variable")
        sys.exit(1)
    
    stripe.api_key = stripe_key
    print(f"✅ Stripe API configured (key ending in ...{stripe_key[-4:]})")

def get_or_create_product(product_data: Dict[str, Any]) -> stripe.Product:
    """Get existing product by metadata key or create new one."""
    key = product_data["key"]
    name = product_data["name"]
    
    # Search for existing product by metadata
    existing_products = stripe.Product.list(limit=100)
    
    for product in existing_products.data:
        if product.metadata.get("key") == key:
            print(f"📦 Found existing product: {name} ({product.id})")
            
            # Update product if needed
            updates = {}
            if product.name != name:
                updates["name"] = name
            if product.description != product_data.get("description", ""):
                updates["description"] = product_data.get("description", "")
            
            if updates:
                product = stripe.Product.modify(product.id, **updates)
                print(f"   ⚠️  Updated product details")
            
            return product
    
    # Create new product
    product = stripe.Product.create(
        name=name,
        description=product_data.get("description", ""),
        metadata={"key": key}
    )
    
    print(f"✨ Created new product: {name} ({product.id})")
    return product

def get_or_create_price(product: stripe.Product, product_data: Dict[str, Any]) -> stripe.Price:
    """Get existing price or create new one for the product."""
    key = product_data["key"]
    
    # Search for existing price by metadata
    existing_prices = stripe.Price.list(product=product.id, limit=100)
    
    for price in existing_prices.data:
        if price.metadata.get("key") == key:
            print(f"💰 Found existing price: {product_data['name']} ({price.id})")
            return price
    
    # Create new price
    price_params = {
        "product": product.id,
        "unit_amount": product_data["unit_amount"],
        "currency": "usd",
        "metadata": {"key": key}
    }
    
    if product_data["type"] == "recurring":
        price_params["recurring"] = {"interval": product_data["interval"]}
    
    price = stripe.Price.create(**price_params)
    
    price_type = "recurring" if product_data["type"] == "recurring" else "one-time"
    amount = product_data["unit_amount"] / 100
    print(f"💵 Created new price: ${amount:.2f} {price_type} ({price.id})")
    
    return price

def seed_products() -> Dict[str, str]:
    """Seed all products and prices from catalog."""
    catalog = load_catalog()
    price_ids = {}
    
    print("🌱 Seeding Stripe products and prices...")
    print("=" * 50)
    
    for product_data in catalog["products"]:
        print(f"\nProcessing: {product_data['name']}")
        
        # Create or update product
        product = get_or_create_product(product_data)
        
        # Create or update price
        price = get_or_create_price(product, product_data)
        
        # Store price ID for environment variables
        env_key = f"STRIPE_PRICE_{product_data['key'].upper().replace('-', '_')}"
        price_ids[env_key] = price.id
    
    print("\n" + "=" * 50)
    print("✅ Seeding completed successfully!")
    
    return price_ids

def display_env_vars(price_ids: Dict[str, str]):
    """Display environment variables to be set."""
    print("\n🔧 Environment Variables to Set:")
    print("=" * 40)
    print("Add these to your backend/.env file:")
    print()
    
    for env_key, price_id in price_ids.items():
        print(f"{env_key}={price_id}")
    
    print()
    print("Or set them in your deployment environment:")
    print()
    
    for env_key, price_id in price_ids.items():
        print(f"export {env_key}={price_id}")

def main():
    """Main seeding function."""
    print("🏠 LeadLedgerPro Stripe Product Seeder")
    print("=" * 50)
    
    try:
        setup_stripe()
        price_ids = seed_products()
        display_env_vars(price_ids)
        
        print("\n🎉 Success! Your Stripe products and prices are ready.")
        print("   Don't forget to update your environment variables.")
        
    except Exception as e:
        print(f"\n❌ Error during seeding: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()