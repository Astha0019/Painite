import re
import os
import json
import logging
import datetime
import requests
from backend.config import Config

logger = logging.getLogger("painite.whatsapp")

def normalize_phone(phone_str):
    """
    Normalizes any Indian or international phone string to Meta WhatsApp E.164 format without '+'.
    Example: '+91 93596 15919' -> '919359615919'
             '9359615919'       -> '919359615919'
             '09359615919'      -> '919359615919'
    """
    if not phone_str:
        return ""
    
    digits = re.sub(r"[^\d]", "", str(phone_str))
    
    if digits.startswith("0") and len(digits) == 11:
        digits = "91" + digits[1:]
    elif len(digits) == 10:
        digits = "91" + digits
    elif digits.startswith("91") and len(digits) == 12:
        pass
    
    return digits

def build_customer_order_message(order):
    """
    Builds the official order confirmation message for the customer.
    Includes:
    - Order confirmation message
    - Order ID and order date
    - Product names, sizes, and quantities
    - Total bill amount
    - Payment method
    - Delivery details
    """
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"
    total_val = order.get("total") or 0.0
    payment_method = (order.get("payment_method") or "COD").upper()
    
    # Format date
    created_at = order.get("created_at")
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = created_at
            order_date = dt.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            order_date = str(created_at)
    else:
        order_date = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")

    # Item breakdown
    items = order.get("items") or []
    item_lines = []
    for idx, item in enumerate(items, start=1):
        name = item.get("product_name") or "Atelier Garment"
        size = item.get("size") or "M"
        color = item.get("color") or "Standard"
        qty = item.get("quantity") or 1
        price = item.get("price") or 0.0
        item_lines.append(f"  {idx}. *{name}* (Size: {size}, Tone: {color}) × {qty} — ₹{price * qty:,.2f}")
    
    items_block = "\n".join(item_lines) if item_lines else "  • PAINITE Studio Custom Piece × 1"

    address = order.get("address") or ""
    city = order.get("city") or ""
    state = order.get("state") or ""
    pincode = order.get("pincode") or ""
    phone = order.get("customer_phone") or ""

    delivery_block = f"{customer_name}\n{address}"
    if city or state or pincode:
        delivery_block += f"\n{city}, {state} - {pincode}"
    if phone:
        delivery_block += f"\nContact: {phone}"

    message = (
        f"✨ *PAINITE ATELIER — ORDER CONFIRMED* ✨\n\n"
        f"Namaste *{customer_name}*,\n"
        f"Thank you for choosing *PAINITE*! Your order has been successfully placed and is now in production.\n\n"
        f"📋 *ORDER DETAILS*\n"
        f"• *Order ID:* {order_id}\n"
        f"• *Date:* {order_date}\n\n"
        f"🛍️ *ITEMS IN YOUR ORDER:*\n"
        f"{items_block}\n\n"
        f"💰 *TOTAL BILL AMOUNT:* ₹{total_val:,.2f} (Incl. all taxes & express shipping)\n"
        f"💳 *PAYMENT METHOD:* {payment_method}\n\n"
        f"📍 *DELIVERY DETAILS:*\n"
        f"{delivery_block}\n\n"
        f"🚚 *ESTIMATED DELIVERY:* 3–5 Business Days across India.\n"
        f"🔗 *TRACK YOUR ORDER:* http://127.0.0.1:5000/#/orders\n\n"
        f"If you have any questions or need sizing assistance, simply reply to this WhatsApp message or email concierge@painite.studio.\n\n"
        f"— _PAINITE Atelier India · Rare Luxury Streetwear_"
    )
    return message

def build_business_order_message(order):
    """
    Builds the complete order notification message for the business owner at +91 9359615919.
    Contains complete customer order details.
    """
    customer_name = order.get("customer_name") or "Valued Patron"
    customer_email = order.get("customer_email") or "N/A"
    customer_phone = order.get("customer_phone") or "N/A"
    order_id = order.get("id") or "N/A"
    total_val = order.get("total") or 0.0
    payment_method = (order.get("payment_method") or "COD").upper()
    
    created_at = order.get("created_at")
    order_date = datetime.datetime.now().strftime("%d %b %Y, %I:%M %p")
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = created_at
            order_date = dt.strftime("%d %b %Y, %I:%M %p")
        except Exception:
            order_date = str(created_at)

    items = order.get("items") or []
    item_lines = []
    for idx, item in enumerate(items, start=1):
        name = item.get("product_name") or "Atelier Garment"
        size = item.get("size") or "M"
        color = item.get("color") or "Standard"
        style = item.get("style") or "Oversized"
        qty = item.get("quantity") or 1
        price = item.get("price") or 0.0
        custom_txt = item.get("custom_text")
        custom_note = f" [Custom: \"{custom_txt}\"]" if custom_txt else ""
        item_lines.append(f"  {idx}. *{name}* | Size: {size} | Color: {color} | Style: {style} × {qty} = ₹{price * qty:,.2f}{custom_note}")
    
    items_block = "\n".join(item_lines) if item_lines else "  • PAINITE Bespoke Garment × 1"

    address = order.get("address") or ""
    city = order.get("city") or ""
    state = order.get("state") or ""
    pincode = order.get("pincode") or ""

    message = (
        f"🚨 *NEW PAINITE ATELIER ORDER RECEIVED!* 🚨\n\n"
        f"📦 *ORDER ID:* {order_id}\n"
        f"📅 *DATE:* {order_date}\n"
        f"💰 *TOTAL BILL:* ₹{total_val:,.2f}\n"
        f"💳 *PAYMENT METHOD:* {payment_method}\n\n"
        f"👤 *CUSTOMER INFORMATION:*\n"
        f"• *Name:* {customer_name}\n"
        f"• *Mobile:* {customer_phone}\n"
        f"• *Email:* {customer_email}\n\n"
        f"📍 *SHIPPING DESTINATION:*\n"
        f"{address}\n"
        f"{city}, {state} - {pincode}\n\n"
        f"🛍️ *GARMENTS TO PACK & DISPATCH:*\n"
        f"{items_block}\n\n"
        f"Open Executive Admin Portal to manage dispatch:\n"
        f"👉 http://127.0.0.1:5000/#/admin"
    )
    return message

def send_whatsapp_cloud_api(recipient_phone, message_text, template_name=None, template_components=None):
    """
    Sends message via official Meta WhatsApp Business Cloud API.
    Endpoint: https://graph.facebook.com/{v21.0}/{PHONE_NUMBER_ID}/messages
    """
    normalized_to = normalize_phone(recipient_phone)
    if not normalized_to:
        logger.warning(f"Invalid phone number provided for WhatsApp dispatch: {recipient_phone}")
        return {
            "success": False,
            "error": "Invalid recipient phone number",
            "mode": "validation_failed"
        }

    phone_number_id = Config.WHATSAPP_PHONE_NUMBER_ID
    access_token = Config.WHATSAPP_ACCESS_TOKEN
    api_version = Config.WHATSAPP_API_VERSION or "v21.0"

    # Check if Meta WhatsApp Cloud API credentials are configured
    if phone_number_id and access_token:
        url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # If an approved template is configured, prefer sending as template
        if template_name:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalized_to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": "en"},
                    "components": template_components or []
                }
            }
        else:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": normalized_to,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message_text
                }
            }

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            res_data = response.json()
            if response.status_code in (200, 201):
                msg_id = (res_data.get("messages") or [{}])[0].get("id", "sent")
                logger.info(f"WhatsApp Cloud API message dispatched successfully to {normalized_to}. Message ID: {msg_id}")
                return {
                    "success": True,
                    "mode": "cloud_api_live",
                    "message_id": msg_id,
                    "to": normalized_to,
                    "response": res_data
                }
            else:
                error_msg = res_data.get("error", {}).get("message", response.text)
                logger.error(f"WhatsApp Cloud API error sending to {normalized_to}: {error_msg}")
                # Fallback: Record delivery attempt and detailed error
                return {
                    "success": False,
                    "mode": "cloud_api_error",
                    "status_code": response.status_code,
                    "error": error_msg,
                    "to": normalized_to
                }
        except Exception as e:
            logger.exception(f"Network error calling WhatsApp Cloud API: {e}")
            return {
                "success": False,
                "mode": "network_exception",
                "error": str(e),
                "to": normalized_to
            }
    else:
        # Development / Sandbox mode: Log full formatted notification
        logger.info(
            f"[WhatsApp Cloud API Simulated - Tokens Not Configured in .env]\n"
            f"To: {normalized_to}\n"
            f"Message:\n{message_text}\n"
            f"Note: Add WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN in .env to dispatch live Meta messages."
        )
        return {
            "success": True,
            "mode": "simulated_local",
            "message_id": f"sim_{normalized_to}_{int(datetime.datetime.now().timestamp())}",
            "to": normalized_to,
            "note": "Logged to studio console. Add WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN to .env for live Meta delivery."
        }

def send_order_notifications(order):
    """
    Orchestrates order notifications:
    1. Sends order confirmation to customer's mobile number.
    2. Sends order alert to business owner WhatsApp (+91 9359615919).
    Returns dictionary with both outcomes.
    """
    customer_phone = order.get("customer_phone") or ""
    business_number = Config.WHATSAPP_BUSINESS_NUMBER or "919359615919"

    customer_msg = build_customer_order_message(order)
    business_msg = build_business_order_message(order)

    # 1. Send to Customer
    customer_result = {"success": False, "reason": "No phone provided"}
    if customer_phone:
        customer_result = send_whatsapp_cloud_api(
            recipient_phone=customer_phone,
            message_text=customer_msg,
            template_name=Config.WHATSAPP_TEMPLATE_NAME or None
        )

    # 2. Send to Business Owner (+91 9359615919)
    business_result = send_whatsapp_cloud_api(
        recipient_phone=business_number,
        message_text=business_msg
    )

    summary = {
        "customer_notified": customer_result.get("success", False),
        "customer_phone": normalize_phone(customer_phone),
        "customer_result": customer_result,
        "business_notified": business_result.get("success", False),
        "business_phone": normalize_phone(business_number),
        "business_result": business_result,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return summary
