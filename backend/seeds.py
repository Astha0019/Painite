import json
import uuid
import datetime
from backend.database import get_db_connection
from backend.auth import hash_password

def seed_database(force_refresh=False):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as cnt FROM products")
    count = cursor.fetchone()["cnt"]

    # Check if jackets exist; if not, force a refresh so the new categories & images are loaded
    cursor.execute("SELECT COUNT(*) as j_cnt FROM products WHERE category = 'Jackets'")
    jackets_count = cursor.fetchone()["j_cnt"]

    if count >= 35 and jackets_count >= 8 and not force_refresh:
        conn.close()
        return

    print("Seeding Painite Studio luxury catalog (Jackets <= INR 2000, T-Shirts <= INR 1500, verified images)...")

    # 1. Seed Users
    admin_id = "usr_admin_001"
    customer_id = "usr_cust_001"

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        admin_id,
        "Painite Studio Director",
        "admin@painite.studio",
        hash_password("PainiteAdmin!42"),
        "admin"
    ))

    cursor.execute("""
        INSERT OR IGNORE INTO users (id, name, email, password_hash, role)
        VALUES (?, ?, ?, ?, ?)
    """, (
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        hash_password("PainiteUser!42"),
        "customer"
    ))

    # 2. Curated 40-Garment Catalog with Strict Price Limits and Verified Imagery
    products = [
        # =====================================================================
        # 1. JACKETS (10 Items — All strictly between ₹1,599 and ₹1,999 <= ₹2,000)
        # =====================================================================
        {
            "id": "jk01",
            "name": "Tokyo Midnight Streetwear Bomber Jacket",
            "description": "Heavyweight matte nylon flight bomber with brushed satin lining, utility arm pocket, and custom antiqued brass hardware. Designed for crisp evening layering.",
            "price": 1899.00,
            "original_price": 2899.00,
            "discount_pct": 34,
            "category": "Jackets",
            "gender": "Men",
            "collection": "Jackets",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1551028719-00167b16eac5?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1a1a1a",
            "colors": ["Onyx Black", "Mineral Slate", "Dusk Olive"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "jk02",
            "name": "Archival Raw Selvedge Denim Trucker Jacket",
            "description": "14 oz dense Indian denim washed in gentle enzyme bath for a broken-in drape. Dual chest flap pockets and reinforced felled seam construction.",
            "price": 1799.00,
            "original_price": 2699.00,
            "discount_pct": 33,
            "category": "Jackets",
            "gender": "Men",
            "collection": "Jackets",
            "tag": "NEW DROP",
            "image": "https://images.unsplash.com/photo-1576871337622-98d48d1cf531?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2a4259",
            "colors": ["Indigo Blue", "Washed Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "jk03",
            "name": "Urban Techwear Shell Windbreaker Jacket",
            "description": "Water-repellent ripstop breathable technical jacket with high-neck storm guard, adjustable toggle hems, and hidden interior stash pocket.",
            "price": 1699.00,
            "original_price": 2599.00,
            "discount_pct": 35,
            "category": "Jackets",
            "gender": "Men",
            "collection": "Jackets",
            "tag": "WEATHERPROOF",
            "image": "https://images.unsplash.com/photo-1544441893-675973e31985?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2d3748",
            "colors": ["Slate Smoke", "Onyx Black", "Olive Moss"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Relaxed", "Boxy"]
        },
        {
            "id": "jk04",
            "name": "Sub-Culture Varsity Letterman Bomber Jacket",
            "description": "Streetwear collegiate varsity jacket with wool-blend body, contrast ribbing at collar and cuffs, and chenille archival studio chest crest.",
            "price": 1999.00,
            "original_price": 2999.00,
            "discount_pct": 33,
            "category": "Jackets",
            "gender": "Men",
            "collection": "Jackets",
            "tag": "LIMITED EDITION",
            "image": "https://images.unsplash.com/photo-1548883354-7622d03aca27?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#111215",
            "colors": ["Onyx / Ivory", "Forest Pine", "Crimson Red"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "jk05",
            "name": "High-Street Cropped Streetwear Bomber Jacket",
            "description": "Architectural cropped flight jacket with cinched elastic waist, dropped shoulders, and ultra-smooth champagne satin lining.",
            "price": 1799.00,
            "original_price": 2699.00,
            "discount_pct": 33,
            "category": "Jackets",
            "gender": "Women",
            "collection": "Jackets",
            "tag": "TRENDING",
            "image": "https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#343b47",
            "colors": ["Onyx Black", "Pastel Pink", "Warm Beige"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Cropped"]
        },
        {
            "id": "jk06",
            "name": "Sakura Pastel Windbreaker Hooded Jacket",
            "description": "Ultralight breathable pastel pink windbreaker featuring weather-resistant membrane, drawcord hood, and elastic storm cuffs.",
            "price": 1649.00,
            "original_price": 2499.00,
            "discount_pct": 34,
            "category": "Jackets",
            "gender": "Women",
            "collection": "Jackets",
            "tag": "PASTEL DROP",
            "image": "https://images.unsplash.com/photo-1544441892-794166f1e3be?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#f4c2c2",
            "colors": ["Pastel Pink", "Soft Lavender", "Kora White"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Relaxed", "Classic"]
        },
        {
            "id": "jk07",
            "name": "Oversized Sherpa Collar Denim Jacket",
            "description": "Vintage medium indigo wash denim lined with cozy faux sherpa fleece. Relaxed drop-shoulder silhouette built for effortless winter styling.",
            "price": 1899.00,
            "original_price": 2899.00,
            "discount_pct": 34,
            "category": "Jackets",
            "gender": "Women",
            "collection": "Jackets",
            "tag": "WINTER WARMTH",
            "image": "https://images.unsplash.com/photo-1525457136159-8878648a7ad0?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#3b5998",
            "colors": ["Denim Blue", "Washed Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "jk08",
            "name": "Minimalist Warm Beige Atelier Trench Jacket",
            "description": "Tailored luxury utility jacket in warm sandstone beige. Features notched collar, storm flap, and removable tonal waist belt.",
            "price": 1949.00,
            "original_price": 2999.00,
            "discount_pct": 35,
            "category": "Jackets",
            "gender": "Women",
            "collection": "Jackets",
            "tag": "LUXURY ATELIER",
            "image": "https://images.unsplash.com/photo-1544022613-e87ca75a784a?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Warm Beige", "Chai Sand", "Onyx Black"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Classic", "Tailored"]
        },
        {
            "id": "jk09",
            "name": "Tokyo Sub-Culture Coach Jacket (Unisex)",
            "description": "Unisex classic street coach jacket with snap button front, water-resistant matte shell, and discrete minimal back typography.",
            "price": 1699.00,
            "original_price": 2499.00,
            "discount_pct": 32,
            "category": "Jackets",
            "gender": "Unisex",
            "collection": "Jackets",
            "tag": "UNISEX CORE",
            "image": "https://images.unsplash.com/photo-1559551409-dadc959f76b8?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#22252a",
            "colors": ["Onyx Black", "Forest Pine", "Sandstone"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Boxy", "Relaxed"]
        },
        {
            "id": "jk10",
            "name": "Atelier Reversible Heavy Bomber Jacket (Unisex)",
            "description": "Dual-sided luxury bomber: reversible from solid charcoal nylon to diamond-quilted champagne satin. Premium YKK double-pull zipper.",
            "price": 1999.00,
            "original_price": 2999.00,
            "discount_pct": 33,
            "category": "Jackets",
            "gender": "Unisex",
            "collection": "Jackets",
            "tag": "SIGNATURE PIECE",
            "image": "https://images.unsplash.com/photo-1548883354-9464e86e4f3a?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1b1d22",
            "colors": ["Charcoal / Champagne", "Black / Olive"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },

        # =====================================================================
        # 2. OVERSIZED T-SHIRTS (10 Items — All strictly between ₹899 and ₹1,499 <= ₹1,500)
        # =====================================================================
        {
            "id": "ot01",
            "name": "Tokyo Acid Wash Mineral Oversized Tee",
            "description": "260 GSM heavyweight Indian combed cotton treated with custom Japanese mineral acid wash. Dropped shoulders and reinforced collar ribbing.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Oversized T-Shirts",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1a1a1a",
            "colors": ["Acid Black", "Mineral Grey"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "ot02",
            "name": "Kora White Heavy Drop-Shoulder Tee",
            "description": "Dense 280 GSM French Terry knit cotton blank with dropped shoulders and architectural drape. Crisp, non-sheer luxury everyday tee.",
            "price": 1199.00,
            "original_price": 1799.00,
            "discount_pct": 33,
            "category": "Oversized T-Shirts",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "ESSENTIAL",
            "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#faf7f2",
            "colors": ["Kora White", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "ot03",
            "name": "Terracotta Mirage Drop-Shoulder Tee",
            "description": "Warm earth terracotta garment dye on 240 GSM organic cotton. Enzyme softened for ultra-luxurious, butter-soft hand feel.",
            "price": 1299.00,
            "original_price": 1999.00,
            "discount_pct": 35,
            "category": "Oversized T-Shirts",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "EARTH TONE",
            "image": "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c85a32",
            "colors": ["Rust Terracotta", "Chai Sand"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "ot04",
            "name": "Washed Slate Heavyweight Street Tee",
            "description": "Custom slate grey mineral wash featuring wide sleeves, deconstructed edge stitching, and dense 260 GSM jersey.",
            "price": 1349.00,
            "original_price": 1999.00,
            "discount_pct": 33,
            "category": "Oversized T-Shirts",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "NEW DROP",
            "image": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#343b47",
            "colors": ["Slate Smoke", "Onyx Black"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "ot05",
            "name": "Blush Sakura Boxy Drop-Shoulder Tee",
            "description": "Gentle pastel sakura pink crafted with 240 GSM combed jersey. Architectural dropped shoulder with a chic, comfortable profile.",
            "price": 1199.00,
            "original_price": 1799.00,
            "discount_pct": 33,
            "category": "Oversized T-Shirts",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "PASTEL PINK",
            "image": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#f4c2c2",
            "colors": ["Pastel Pink", "Kora White", "Lavender"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "ot06",
            "name": "Sky Blue Cloud Boyfriend Oversized Tee",
            "description": "Airy serene baby blue tone with dropped shoulders and roomy boyfriend cut. Ribbed collar with interior herringbone neck tape.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Oversized T-Shirts",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6ba4b8",
            "colors": ["Sky Blue", "Pastel Pink", "Kora White"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "ot07",
            "name": "Carbon Black High-Street Boxy Crop Tee",
            "description": "Heavyweight structured boxy crop in carbon black. Tailored to fall cleanly right above the hip line for street aesthetics.",
            "price": 999.00,
            "original_price": 1499.00,
            "discount_pct": 33,
            "category": "Oversized T-Shirts",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "HOT SELLER",
            "image": "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Cropped"]
        },
        {
            "id": "ot08",
            "name": "Lavender Dream Dropped-Shoulder Tee",
            "description": "Ethereal dusty lavender pastel with relaxed silhouette, wide-cut sleeves, and delicate tone-on-tone embroidery at collar.",
            "price": 1149.00,
            "original_price": 1699.00,
            "discount_pct": 32,
            "category": "Oversized T-Shirts",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "LAVENDER",
            "image": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c3b1e1",
            "colors": ["Lavender", "Pastel Pink", "Chai Sand"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "ot09",
            "name": "Noir Studio Architectural Oversized Tee (Unisex)",
            "description": "Our signature 280 GSM unisex oversized blank. Architectural drape, dense drop shoulder, and double-stitched reinforced hems.",
            "price": 1499.00,
            "original_price": 2199.00,
            "discount_pct": 32,
            "category": "Oversized T-Shirts",
            "gender": "Unisex",
            "collection": "Oversized",
            "tag": "SIGNATURE UNISEX",
            "image": "/static/images/noir-studio-tee.jpg",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Slate Smoke"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "ot10",
            "name": "Chai Sand French Terry Boxy Tee (Unisex)",
            "description": "Warm beige neutral tone reflecting authentic Indian sand palettes. Dense 260 GSM French Terry knit suitable for both men and women.",
            "price": 1399.00,
            "original_price": 1999.00,
            "discount_pct": 30,
            "category": "Oversized T-Shirts",
            "gender": "Unisex",
            "collection": "Oversized",
            "tag": "NEUTRAL ESSENTIAL",
            "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Chai Sand", "Kora White", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },

        # =====================================================================
        # 3. GRAPHIC T-SHIRTS (10 Items — All strictly between ₹999 and ₹1,499 <= ₹1,500)
        # =====================================================================
        {
            "id": "gt01",
            "name": "Neo-Tokyo Cyber Kanji Graphic Tee",
            "description": "High-density puff screen print depicting neo-Tokyo district architecture with Japanese typographic characters on 240 GSM organic jersey.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Graphic T-Shirts",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#343b47",
            "colors": ["Slate Smoke", "Onyx Black", "Cobalt Blue"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "gt02",
            "name": "Archival Renaissance Glitch Art Tee",
            "description": "Classical Italian marble sculpture deconstructed with modern brutalist glitch art. Silkscreened using water-based tactile eco inks.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Graphic T-Shirts",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "LIMITED ART",
            "image": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#111216",
            "colors": ["Onyx Black", "Mineral Slate"],
            "sizes": ["M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "gt03",
            "name": "Phantom Samurai Brushwork Anime Tee",
            "description": "Hand-rendered Japanese brushwork samurai illustration infused with modern cyberpunk line-art on heavy 260 GSM combed cotton.",
            "price": 1449.00,
            "original_price": 2199.00,
            "discount_pct": 34,
            "category": "Graphic T-Shirts",
            "gender": "Men",
            "collection": "Anime & Manga",
            "tag": "TRENDING",
            "image": "https://images.unsplash.com/photo-1503342452485-86b7f54527ef?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2a2d34",
            "colors": ["Washed Charcoal", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "gt04",
            "name": "Sub-Culture Underground Emblem Graphic Tee",
            "description": "Bold subterranean graphic emblem featuring underground street music aesthetics and industrial typography across back and chest.",
            "price": 1399.00,
            "original_price": 1999.00,
            "discount_pct": 30,
            "category": "Graphic T-Shirts",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "UNDERGROUND",
            "image": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#22252a",
            "colors": ["Mineral Slate", "Onyx Black"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "gt05",
            "name": "Botanical Continuous Line-Art Tee",
            "description": "Continuous fine line floral botanical artwork across back and chest. Printed with soft-hand eco inks on pure combed Indian cotton.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Graphic T-Shirts",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "STAFF PICK",
            "image": "https://images.unsplash.com/photo-1524250502761-1ac6f2e30d43?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#faf7f2",
            "colors": ["Kora White", "Pastel Pink", "Sage Green"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "gt06",
            "name": "Celestial Moon & Sun Tarot Graphic Tee",
            "description": "Gold pigment and soft-touch tarot iconography representing intuition and strength. Drop shoulder boyfriend silhouette in midnight black.",
            "price": 1349.00,
            "original_price": 1999.00,
            "discount_pct": 33,
            "category": "Graphic T-Shirts",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "CELESTIAL",
            "image": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1b1d22",
            "colors": ["Onyx Black", "Mineral Slate"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "gt07",
            "name": "Retro Synthwave 80s Anime Graphic Tee",
            "description": "Vibrant retro anime visual reminiscent of 1980s Tokyo city pop album covers. Printed on soft 240 GSM combed cotton.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Graphic T-Shirts",
            "gender": "Women",
            "collection": "Anime & Manga",
            "tag": "ANIME POP",
            "image": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6b4f70",
            "colors": ["Lavender", "Pastel Pink"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "gt08",
            "name": "Terracotta Abstract Sunburst Graphic Tee",
            "description": "Warm terracotta shade featuring modern minimalist geometric sunburst graphic in warm cream ink. Heavy 240 GSM feel.",
            "price": 1249.00,
            "original_price": 1799.00,
            "discount_pct": 31,
            "category": "Graphic T-Shirts",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "WARM GRAPHIC",
            "image": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c85a32",
            "colors": ["Rust Terracotta", "Chai Sand"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "gt09",
            "name": "Bombay Sub-Culture Coordinates Graphic Tee (Unisex)",
            "description": "Subtle typographic Bombay studio coordinates embroidered and screenprinted in champagne gold ink across 240 GSM luxury cotton.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Graphic T-Shirts",
            "gender": "Unisex",
            "collection": "Graphic Prints",
            "tag": "UNISEX GRAPHIC",
            "image": "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Chai Sand", "Kora White", "Onyx Black"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Relaxed", "Boxy"]
        },
        {
            "id": "gt10",
            "name": "Form / Function Architectural Screenprint Tee (Unisex)",
            "description": "Clean Swiss graphic design with technical typographic grid and architectural blueprint layout on 260 GSM French Terry jersey.",
            "price": 1499.00,
            "original_price": 2199.00,
            "discount_pct": 32,
            "category": "Graphic T-Shirts",
            "gender": "Unisex",
            "collection": "Graphic Prints",
            "tag": "ARCHITECTURAL",
            "image": "/static/images/form-function-tee.jpg",
            "color_hex": "#d8cbb5",
            "colors": ["Kora White", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Boxy", "Oversized"]
        },

        # =====================================================================
        # 4. MINIMAL & CORE T-SHIRTS (10 Items — All strictly between ₹799 and ₹1,299 <= ₹1,500)
        # =====================================================================
        {
            "id": "mc01",
            "name": "Chai Sand 240 GSM Luxury Crewneck Tee",
            "description": "Dense combed Indian jersey in rich chai beige. Built with a structured neck ribbing that holds its crisp round shape permanently.",
            "price": 999.00,
            "original_price": 1499.00,
            "discount_pct": 33,
            "category": "Minimal & Core",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "CORE BASIC",
            "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Chai Sand", "Kora White", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "mc02",
            "name": "Sage Green Studio Minimal Tee",
            "description": "Earthy muted sage tone inspired by Indian monsoon flora. Modern structured cut with reinforced double-needle hems.",
            "price": 1099.00,
            "original_price": 1599.00,
            "discount_pct": 31,
            "category": "Minimal & Core",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "NATURE TONE",
            "image": "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#8f9779",
            "colors": ["Sage Green", "Dusk Olive"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Boxy"]
        },
        {
            "id": "mc03",
            "name": "Sky Blue Horizon Solid Minimal Tee",
            "description": "Crisp sky blue pastel tee crafted from 220 GSM single-origin Indian cotton with tonal collar ribbing and tailored drape.",
            "price": 899.00,
            "original_price": 1399.00,
            "discount_pct": 36,
            "category": "Minimal & Core",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "PASTEL BLUE",
            "image": "https://images.unsplash.com/photo-1527719327859-c6ce80353573?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6ba4b8",
            "colors": ["Sky Blue", "Kora White"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "mc04",
            "name": "Forest Pine Heritage Crewneck Tee",
            "description": "Deep British racing / forest pine green crafted with 240 GSM combed cotton. Pure, clean luxury streetwear plain.",
            "price": 1049.00,
            "original_price": 1549.00,
            "discount_pct": 32,
            "category": "Minimal & Core",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "DEEP GREEN",
            "image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2d4a3e",
            "colors": ["Forest Pine", "Sage Green"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "mc05",
            "name": "Blush Sakura Solid Minimal Tee",
            "description": "Delicate blush pink solid tee in 220 GSM ultra-soft combed cotton. Finished with subtle tone-on-tone studio hem label.",
            "price": 999.00,
            "original_price": 1499.00,
            "discount_pct": 33,
            "category": "Minimal & Core",
            "gender": "Women",
            "collection": "Minimal Studio",
            "tag": "PASTEL PINK",
            "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#f4c2c2",
            "colors": ["Pastel Pink", "Kora White", "Lavender"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Classic", "Boxy"]
        },
        {
            "id": "mc06",
            "name": "Warm Almond Beige Minimalist Crop Tee",
            "description": "Subtle nude almond cream tone. Tailored boxy cropped cut engineered to sit perfectly with high-waisted streetwear cargos.",
            "price": 899.00,
            "original_price": 1399.00,
            "discount_pct": 36,
            "category": "Minimal & Core",
            "gender": "Women",
            "collection": "Minimal Studio",
            "tag": "CROPPED BASIC",
            "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Almond Beige", "Kora White"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Cropped"]
        },
        {
            "id": "mc07",
            "name": "Soft Lavender Ethereal Drape Tee",
            "description": "Delicate dusty lilac lavender hue with micro-ribbed crewneck. Tailored relaxed drape with silky smooth texture.",
            "price": 1099.00,
            "original_price": 1599.00,
            "discount_pct": 31,
            "category": "Minimal & Core",
            "gender": "Women",
            "collection": "Minimal Studio",
            "tag": "LAVENDER",
            "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c3b1e1",
            "colors": ["Lavender", "Pastel Pink"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Relaxed"]
        },
        {
            "id": "mc08",
            "name": "Mint Haze Organic Cool Cotton Tee",
            "description": "Cool pastel mint green with ultra-soft garment wash. Breathable, breezy drape crafted for warm Indian afternoons.",
            "price": 949.00,
            "original_price": 1399.00,
            "discount_pct": 32,
            "category": "Minimal & Core",
            "gender": "Women",
            "collection": "Minimal Studio",
            "tag": "MINT GREEN",
            "image": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#98d8aa",
            "colors": ["Mint Green", "Sky Blue"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Relaxed", "Boxy"]
        },
        {
            "id": "mc09",
            "name": "The Essential Heavyweight Blank (Unisex)",
            "description": "240 GSM dense combed Indian cotton blank tailored for everyday streetwear with a structured, breathable drape. Suitable for all.",
            "price": 999.00,
            "original_price": 1499.00,
            "discount_pct": 33,
            "category": "Minimal & Core",
            "gender": "Unisex",
            "collection": "Minimal Studio",
            "tag": "CORE BESTSELLER",
            "image": "/static/images/essential-tee.jpg",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Slate Smoke"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Oversized"]
        },
        {
            "id": "mc10",
            "name": "Kora White Raw Hem Minimal Studio Blank (Unisex)",
            "description": "Unbleached natural kora white luxury cotton blank with deconstructed raw bottom hem. Timeless unisex staple.",
            "price": 1199.00,
            "original_price": 1799.00,
            "discount_pct": 33,
            "category": "Minimal & Core",
            "gender": "Unisex",
            "collection": "Minimal Studio",
            "tag": "NATURAL KORA",
            "image": "/static/images/noir-studio-tee.jpg",
            "color_hex": "#faf7f2",
            "colors": ["Kora White", "Chai Sand", "Onyx Black"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Relaxed"]
        }
    ]

    # Clean existing catalog to ensure no legacy mismatched images or oversized prices remain
    cursor.execute("DELETE FROM products")

    for p in products:
        colors_json = json.dumps(p["colors"])
        sizes_json = json.dumps(p["sizes"])
        styles_json = json.dumps(p["styles"])
        color_hex = p.get("color_hex", "#101114")

        cursor.execute("""
            INSERT INTO products (
                id, name, description, price, original_price, discount_pct,
                category, gender, collection, tag, image, color_hex,
                colors, sizes, styles, in_stock
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            p["id"], p["name"], p["description"], p["price"], p["original_price"],
            p["discount_pct"], p["category"], p["gender"], p["collection"],
            p["tag"], p["image"], color_hex, colors_json, sizes_json, styles_json
        ))

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(products)} authentic garments. Jackets <= INR 2000, T-Shirts <= INR 1500.")

if __name__ == "__main__":
    seed_database(force_refresh=True)
