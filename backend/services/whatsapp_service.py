import re
import os
import json
import logging
import datetime
import urllib.parse
import uuid
import requests
from backend.config import Config
from backend.database import get_db_connection

logger = logging.getLogger("painite.whatsapp")

def generate_wa_link(recipient_phone, message_text):
    """
    Generates a direct 1-click WhatsApp web/app link.
    Example: https://wa.me/919359615919?text=Hello%20...
    """
    normalized = normalize_phone(recipient_phone)
    if not normalized:
        return ""
    encoded_text = urllib.parse.quote(str(message_text or ""))
    return f"https://wa.me/{normalized}?text={encoded_text}"

def log_whatsapp_message(order_id, recipient_phone, recipient_name, message_type, message_text, status, wa_link=""):
    """
    Persists WhatsApp transmission attempt to database logs for audit and 1-click dispatch.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        log_id = f"walog_{uuid.uuid4().hex[:10]}"
        cursor.execute("""
            INSERT INTO whatsapp_logs (id, order_id, recipient_phone, recipient_name, message_type, message_text, status, wa_link)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            order_id,
            normalize_phone(recipient_phone),
            recipient_name or "",
            message_type or "notification",
            message_text or "",
            status or "Recorded",
            wa_link or generate_wa_link(recipient_phone, message_text)
        ))
        conn.commit()
        conn.close()
        return log_id
    except Exception as e:
        logger.error(f"Failed to log whatsapp transmission: {e}")
        return None

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
    Matches exact requested template with Order ID, Products, Total Amount, Order Date, Expected Delivery Date.
    """
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"
    total_val = order.get("total") or 0.0
    
    # Format date
    created_at = order.get("created_at")
    if created_at:
        try:
            if isinstance(created_at, str):
                dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            else:
                dt = created_at
            order_date = dt.strftime("%d %b %Y")
        except Exception:
            order_date = str(created_at)
    else:
        order_date = datetime.datetime.now().strftime("%d %b %Y")

    expected_delivery = order.get("estimated_delivery_date")
    if not expected_delivery:
        delivery_dt = datetime.date.today() + datetime.timedelta(days=4)
        expected_delivery = delivery_dt.strftime("%d %b %Y")

    # Product names list
    items = order.get("items") or []
    if items:
        products_list = []
        for it in items:
            p_name = it.get("product_name") or "PAINITE Garment"
            qty = it.get("quantity") or 1
            products_list.append(f"{p_name} (x{qty})" if qty > 1 else p_name)
        products_str = ", ".join(products_list)
    else:
        products_str = "PAINITE Atelier Garment"

    message = (
        f"✨ *PAINITE ATELIER* ✨\n\n"
        f"Hello {customer_name}!\n\n"
        f"Thank you for shopping with us!\n\n"
        f"Your order has been successfully placed.\n\n"
        f"Order ID: #{order_id}\n"
        f"Products: {products_str}\n"
        f"Total Amount: ₹{total_val:,.2f}\n"
        f"Order Date: {order_date}\n\n"
        f"Expected Delivery Date: {expected_delivery}\n\n"
        f"Your order is confirmed. We will keep you updated about your delivery.\n\n"
        f"Thank you for shopping with us!\n\n"
        f"— _PAINITE Atelier India · Rare Luxury Streetwear_"
    )
    return message

def build_customer_status_message(order, new_status):
    """
    Builds delivery lifecycle updates for customers:
    Confirmed, Packed, Shipped, Out for Delivery, Delivered.
    """
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"
    total_val = order.get("total") or 0.0
    expected_delivery = order.get("estimated_delivery_date") or (datetime.date.today() + datetime.timedelta(days=3)).strftime("%d %b %Y")
    tracking_no = order.get("tracking_number") or f"PTE-IND-{order_id[-6:]}"

    status_lower = (new_status or "").lower()

    if "product" in status_lower:
        status_title = "IN PRODUCTION"
        status_body = (
            f"Your bespoke order #{order_id} has moved into our tailoring atelier.\n\n"
            f"Our master tailors are crafting your heavyweight garments with artisanal precision.\n"
            f"Expected Delivery Date: {expected_delivery}"
        )
    elif "quality" in status_lower:
        status_title = "QUALITY CHECK"
        status_body = (
            f"Your PAINITE order #{order_id} is undergoing final quality inspection, pressing, and bespoke boxing.\n\n"
            f"Expected Delivery Date: {expected_delivery}"
        )
    elif "cancel" in status_lower:
        status_title = "ORDER CANCELLED"
        status_body = (
            f"Your PAINITE order #{order_id} has been cancelled.\n\n"
            f"If prepaid, your refund has been initiated and will credit within 3-5 business days."
        )
    elif "pack" in status_lower:
        status_title = "ORDER PACKED"
        status_body = (
            f"Great news! Your PAINITE order #{order_id} has been carefully packed and prepared for express dispatch.\n\n"
            f"Expected Delivery Date: {expected_delivery}\n"
            f"We will notify you with tracking details as soon as our courier partner picks up your parcel."
        )
    elif "ship" in status_lower:
        status_title = "ORDER SHIPPED"
        status_body = (
            f"Your PAINITE order #{order_id} has been dispatched via Express Courier.\n\n"
            f"Tracking Number: *{tracking_no}*\n"
            f"Expected Delivery Date: {expected_delivery}\n\n"
            f"Track your order: http://127.0.0.1:5000/#/orders"
        )
    elif "out" in status_lower:
        status_title = "OUT FOR DELIVERY"
        status_body = (
            f"Your PAINITE order #{order_id} is OUT FOR DELIVERY today!\n\n"
            f"Our delivery executive will arrive shortly. "
            f"Please ensure someone is available at your address to receive the package."
        )
    elif "deliver" in status_lower:
        status_title = "ORDER DELIVERED"
        status_body = (
            f"Your PAINITE order #{order_id} has been successfully DELIVERED!\n\n"
            f"We hope you love your new luxury streetwear pieces. "
            f"If you need any sizing exchanges or assistance, simply reply to this WhatsApp message.\n\n"
            f"Thank you for being a valued patron of PAINITE Atelier."
        )
    elif "track" in status_lower:
        status_title = "TRACKING UPDATED"
        status_body = (
            f"Express courier tracking details have been updated for your order #{order_id}.\n\n"
            f"Courier Tracking (AWB): *{tracking_no}*\n"
            f"Expected Delivery Date: {expected_delivery}\n\n"
            f"Track your order: http://127.0.0.1:5000/#/orders"
        )
    elif "paid" in status_lower or "pay" in status_lower:
        status_title = "PAYMENT VERIFIED"
        status_body = (
            f"Payment for your order #{order_id} of ₹{total_val:,.2f} has been verified and confirmed.\n\n"
            f"Your order is marked as PAID and prioritized for express fulfillment.\n"
            f"Expected Delivery Date: {expected_delivery}"
        )
    else:
        status_title = "ORDER CONFIRMED"
        status_body = (
            f"Your PAINITE order #{order_id} has been confirmed.\n\n"
            f"Expected Delivery Date: {expected_delivery}\n"
            f"Total Bill Amount: ₹{total_val:,.2f}\n"
            f"We are preparing your garments with artisanal precision."
        )

    return (
        f"✨ *PAINITE ATELIER — {status_title}* ✨\n\n"
        f"Hello {customer_name}!\n\n"
        f"{status_body}\n\n"
        f"— _PAINITE Atelier India · Concierge Support: +91 9359615919_"
    )

def build_complete_order_update_message(order):
    """
    Builds the comprehensive all-in-one order status and logistics report for the customer.
    Sent from admin to customer with full details.
    """
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"
    status = (order.get("status") or "Confirmed").upper()
    payment_status = (order.get("payment_status") or "Pending").upper()
    payment_method = (order.get("payment_method") or "COD").upper()
    total_val = float(order.get("total") or 0.0)
    expected_delivery = order.get("estimated_delivery_date") or (datetime.date.today() + datetime.timedelta(days=3)).strftime("%d %b %Y")
    tracking_no = order.get("tracking_number") or f"PTE-IND-{str(order_id)[-6:]}"

    items = order.get("items") or []
    item_lines = []
    for it in items:
        p_name = it.get("product_name") or "PAINITE Garment"
        qty = it.get("quantity") or 1
        size = it.get("size") or "M"
        color = it.get("color") or "Standard"
        item_lines.append(f"  • {p_name} ({color} / {size}) × {qty}")
    items_str = "\n".join(item_lines) if item_lines else "  • PAINITE Bespoke Garment"

    address = order.get("address") or "Standard Shipping Address"

    return (
        f"✨ *PAINITE ATELIER — OFFICIAL ORDER UPDATE* ✨\n\n"
        f"Hello {customer_name}!\n\n"
        f"Here is the latest dispatch and fulfillment report for your order:\n\n"
        f"📦 *ORDER ID:* #{order_id}\n"
        f"🔄 *CURRENT STATUS:* *{status}*\n"
        f"💳 *PAYMENT STATUS:* {payment_status} ({payment_method})\n"
        f"🚚 *COURIER AWB:* *{tracking_no}*\n"
        f"📅 *EXPECTED ARRIVAL:* {expected_delivery}\n\n"
        f"🛍️ *YOUR GARMENTS:*\n"
        f"{items_str}\n\n"
        f"💰 *TOTAL AMOUNT:* ₹{total_val:,.2f}\n"
        f"📍 *DELIVERY ADDRESS:* {address}\n\n"
        f"Track your order live anytime:\n"
        f"👉 http://127.0.0.1:5000/#/orders\n\n"
        f"If you need assistance or styling advice, simply reply to this message.\n\n"
        f"— _PAINITE Atelier India · Concierge Support: +91 9359615919_"
    )

def send_complete_order_update_notification(order):
    """
    Dispatches full order update to customer on WhatsApp.
    """
    customer_phone = order.get("customer_phone") or ""
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"

    if not customer_phone:
        return {
            "success": False,
            "mode": "no_phone",
            "status": "No Phone Provided",
            "reason": "Customer phone not provided",
            "wa_link": ""
        }

    message_text = build_complete_order_update_message(order)
    return send_whatsapp_cloud_api(
        recipient_phone=customer_phone,
        message_text=message_text,
        order_id=order_id,
        recipient_name=customer_name,
        message_type="complete_order_update"
    )

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

def send_whatsapp_cloud_api(recipient_phone, message_text, template_name=None, template_components=None, order_id=None, recipient_name=None, message_type="notification"):
    """
    Sends message via official Meta WhatsApp Business Cloud API.
    Endpoint: https://graph.facebook.com/{v21.0}/{PHONE_NUMBER_ID}/messages
    Also generates 1-click wa.me link and persists transmission to whatsapp_logs.
    """
    normalized_to = normalize_phone(recipient_phone)
    wa_link = generate_wa_link(normalized_to, message_text)

    if not normalized_to:
        logger.warning(f"Invalid phone number provided for WhatsApp dispatch: {recipient_phone}")
        return {
            "success": False,
            "error": "Invalid recipient phone number",
            "mode": "validation_failed",
            "wa_link": ""
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
                status_str = "Dispatched (Meta Cloud API)"
                log_whatsapp_message(order_id, normalized_to, recipient_name, message_type, message_text, status_str, wa_link)
                return {
                    "success": True,
                    "mode": "cloud_api_live",
                    "status": status_str,
                    "message_id": msg_id,
                    "to": normalized_to,
                    "wa_link": wa_link,
                    "response": res_data
                }
            else:
                error_msg = res_data.get("error", {}).get("message", response.text)
                logger.error(f"WhatsApp Cloud API error sending to {normalized_to}: {error_msg}")
                status_str = f"Meta API Error: {error_msg[:40]}"
                log_whatsapp_message(order_id, normalized_to, recipient_name, message_type, message_text, status_str, wa_link)
                return {
                    "success": False,
                    "mode": "cloud_api_error",
                    "status": status_str,
                    "status_code": response.status_code,
                    "error": error_msg,
                    "to": normalized_to,
                    "wa_link": wa_link
                }
        except Exception as e:
            logger.exception(f"Network error calling WhatsApp Cloud API: {e}")
            status_str = f"Network Error: {str(e)[:40]}"
            log_whatsapp_message(order_id, normalized_to, recipient_name, message_type, message_text, status_str, wa_link)
            return {
                "success": False,
                "mode": "network_exception",
                "status": status_str,
                "error": str(e),
                "to": normalized_to,
                "wa_link": wa_link
            }
    else:
        # Development / Sandbox mode: 1-Click WhatsApp Direct Link Ready
        logger.info(
            f"[WhatsApp Concierge Alert - 1-Click Link Generated]\n"
            f"To: {normalized_to}\n"
            f"Link: {wa_link}\n"
            f"Message:\n{message_text}\n"
        )
        status_str = "Direct Link Ready"
        log_whatsapp_message(order_id, normalized_to, recipient_name, message_type, message_text, status_str, wa_link)
        return {
            "success": False,
            "mode": "credentials_required",
            "status": "Credentials Required",
            "message_id": f"sim_{normalized_to}_{int(datetime.datetime.now().timestamp())}",
            "to": normalized_to,
            "wa_link": wa_link,
            "note": "Meta WhatsApp Cloud API credentials missing in .env. Use 1-Click wa.me link or configure WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_ACCESS_TOKEN."
        }

def send_order_notifications(order):
    """
    Orchestrates order notifications:
    1. Sends order confirmation to customer's mobile number.
    2. Sends order alert to business owner WhatsApp (+91 9359615919).
    Returns dictionary with both outcomes.
    """
    customer_phone = order.get("customer_phone") or ""
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"
    business_number = Config.WHATSAPP_BUSINESS_NUMBER or "919359615919"

    customer_msg = build_customer_order_message(order)
    business_msg = build_business_order_message(order)

    # 1. Send to Customer
    customer_result = {"success": False, "mode": "no_phone", "status": "No Phone Provided", "wa_link": ""}
    if customer_phone:
        customer_result = send_whatsapp_cloud_api(
            recipient_phone=customer_phone,
            message_text=customer_msg,
            template_name=Config.WHATSAPP_TEMPLATE_NAME or None,
            order_id=order_id,
            recipient_name=customer_name,
            message_type="order_confirmation"
        )

    # 2. Send to Business Owner (+91 9359615919)
    business_result = send_whatsapp_cloud_api(
        recipient_phone=business_number,
        message_text=business_msg,
        order_id=order_id,
        recipient_name="Studio Concierge",
        message_type="business_order_alert"
    )

    if customer_result.get("mode") == "credentials_required" or business_result.get("mode") == "credentials_required":
        overall_status = "Credentials Required (Setup in .env)"
    elif customer_result.get("success") and business_result.get("success"):
        overall_status = "Dispatched (Customer & Business)"
    elif customer_result.get("success") or business_result.get("success"):
        overall_status = "Dispatched (Business Alert)"
    else:
        overall_status = "Delivery Attempted"

    summary = {
        "overall_status": overall_status,
        "customer_notified": customer_result.get("success", False),
        "customer_phone": normalize_phone(customer_phone),
        "customer_wa_link": customer_result.get("wa_link", ""),
        "customer_result": customer_result,
        "business_notified": business_result.get("success", False),
        "business_phone": normalize_phone(business_number),
        "business_wa_link": business_result.get("wa_link", ""),
        "business_result": business_result,
        "timestamp": datetime.datetime.now().isoformat()
    }
    
    return summary

def send_order_status_notification(order, new_status):
    """
    Sends customer lifecycle delivery updates on WhatsApp:
    Confirmed, Packed, Shipped, Out for Delivery, Delivered.
    """
    customer_phone = order.get("customer_phone") or ""
    customer_name = order.get("customer_name") or "Valued Patron"
    order_id = order.get("id") or "N/A"

    if not customer_phone:
        return {
            "success": False,
            "mode": "no_phone",
            "status": "No Phone Provided",
            "reason": "Customer phone not provided",
            "wa_link": ""
        }

    message_text = build_customer_status_message(order, new_status)
    return send_whatsapp_cloud_api(
        recipient_phone=customer_phone,
        message_text=message_text,
        order_id=order_id,
        recipient_name=customer_name,
        message_type=f"status_{str(new_status).lower()}"
    )

def get_whatsapp_system_status():
    """
    Returns the current live status and configuration of the WhatsApp system.
    """
    has_id = bool(Config.WHATSAPP_PHONE_NUMBER_ID)
    has_token = bool(Config.WHATSAPP_ACCESS_TOKEN)
    is_live = has_id and has_token

    return {
        "business_number": Config.WHATSAPP_BUSINESS_NUMBER or "919359615919",
        "formatted_business_number": "+91 93596 15919",
        "has_phone_number_id": has_id,
        "phone_number_id": Config.WHATSAPP_PHONE_NUMBER_ID if has_id else "",
        "has_access_token": has_token,
        "api_version": Config.WHATSAPP_API_VERSION or "v21.0",
        "template_name": Config.WHATSAPP_TEMPLATE_NAME or "",
        "is_cloud_api_active": is_live,
        "mode": "Meta Cloud API Live" if is_live else "1-Click Direct WhatsApp Link Mode",
        "status_badge": "Live & Connected" if is_live else "Direct Link Mode (Ready)"
    }

def update_whatsapp_settings(business_number=None, phone_number_id=None, access_token=None, api_version=None, template_name=None):
    """
    Updates WhatsApp credentials in memory and persists to .env file.
    """
    from backend.config import BASE_DIR
    env_path = os.path.join(BASE_DIR, ".env")

    if business_number is not None:
        Config.WHATSAPP_BUSINESS_NUMBER = normalize_phone(business_number) or "919359615919"
    if phone_number_id is not None:
        Config.WHATSAPP_PHONE_NUMBER_ID = str(phone_number_id).strip()
    if access_token is not None:
        Config.WHATSAPP_ACCESS_TOKEN = str(access_token).strip()
    if api_version is not None:
        Config.WHATSAPP_API_VERSION = str(api_version).strip() or "v21.0"
    if template_name is not None:
        Config.WHATSAPP_TEMPLATE_NAME = str(template_name).strip()

    # Read existing .env if present
    env_lines = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            env_lines = f.readlines()

    keys_to_update = {
        "WHATSAPP_BUSINESS_NUMBER": Config.WHATSAPP_BUSINESS_NUMBER,
        "WHATSAPP_PHONE_NUMBER_ID": Config.WHATSAPP_PHONE_NUMBER_ID,
        "WHATSAPP_ACCESS_TOKEN": Config.WHATSAPP_ACCESS_TOKEN,
        "WHATSAPP_API_VERSION": Config.WHATSAPP_API_VERSION,
        "WHATSAPP_TEMPLATE_NAME": Config.WHATSAPP_TEMPLATE_NAME
    }

    new_lines = []
    seen_keys = set()
    for line in env_lines:
        line_strip = line.strip()
        matched = False
        for k, v in keys_to_update.items():
            if line_strip.startswith(f"{k}=") or line_strip.startswith(f"#{k}="):
                new_lines.append(f"{k}={v}\n")
                seen_keys.add(k)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    for k, v in keys_to_update.items():
        if k not in seen_keys:
            new_lines.append(f"{k}={v}\n")

    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    return get_whatsapp_system_status()

def send_custom_whatsapp(recipient_phone, recipient_name, message_text, order_id=None, message_type="custom"):
    """
    Dispatches custom WhatsApp message to any customer or number.
    """
    return send_whatsapp_cloud_api(
        recipient_phone=recipient_phone,
        message_text=message_text,
        order_id=order_id,
        recipient_name=recipient_name,
        message_type=message_type
    )

def get_recent_whatsapp_logs(limit=50):
    """
    Fetches recent WhatsApp transmission logs from database.
    """
    from backend.models import whatsapp_log_to_dict
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM whatsapp_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [whatsapp_log_to_dict(r) for r in rows]
    except Exception as e:
        logger.error(f"Error fetching whatsapp logs: {e}")
        return []
