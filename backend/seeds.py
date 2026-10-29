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
    if count >= 35 and not force_refresh:
        conn.close()
        return

    print("Seeding Painite Studio India luxury collection (42+ items, Men & Women, vibrant colors, realistic discounts)...")

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

    # 2. Comprehensive 42-Product Streetwear & Fashion Catalog
    products = [
        # ==========================================
        # MEN'S COLLECTION (17 Products)
        # ==========================================
        {
            "id": "pm01",
            "name": "Tokyo Midnight Acid Oversized Tee",
            "description": "260 GSM heavyweight combed cotton blank washed in Japanese mineral acid bath with dropped shoulders and reinforced ribbed neckline.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Oversized",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1a1a1a",
            "colors": ["Acid Black", "Mineral Grey", "Kora White"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pm02",
            "name": "Cyber-District Neon Kanji Graphic Tee",
            "description": "High-density puff screen print depicting neo-Tokyo district architecture, printed on 240 GSM breathable organic jersey.",
            "price": 1599.00,
            "original_price": 2499.00,
            "discount_pct": 36,
            "category": "Graphic Prints",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "NEW DROP",
            "image": "https://images.unsplash.com/photo-1576566588028-4147f3842f27?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#343b47",
            "colors": ["Slate Smoke", "Onyx Black", "Cobalt Blue"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "pm03",
            "name": "Phantom Samurai Ink Wash Anime Tee",
            "description": "Hand-rendered Japanese brushwork samurai illustration infused with cyberpunk line-art on heavy 260 GSM combed cotton.",
            "price": 1699.00,
            "original_price": 2599.00,
            "discount_pct": 35,
            "category": "Anime",
            "gender": "Men",
            "collection": "Anime & Manga",
            "tag": "TRENDING",
            "image": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Dusk Charcoal"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pm04",
            "name": "Terracotta Mirage Drop-Shoulder Tee",
            "description": "Warm earth terracotta garment dye with a relaxed dropped shoulder cut. Enzyme softened for ultra-luxurious drape.",
            "price": 1299.00,
            "original_price": 1999.00,
            "discount_pct": 35,
            "category": "Aesthetic",
            "gender": "Men",
            "collection": "Aesthetic & Pastel",
            "tag": "VIBRANT TONE",
            "image": "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c85a32",
            "colors": ["Rust Terracotta", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "pm05",
            "name": "Archival Renaissance Sculpt Graphic Tee",
            "description": "Classical Italian sculpture deconstructed with brutalist glitch art. Silkscreened using water-based tactile ink.",
            "price": 1799.00,
            "original_price": 2799.00,
            "discount_pct": 36,
            "category": "Graphic Prints",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "LIMITED EDITION",
            "image": "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#111216",
            "colors": ["Onyx Black", "Mineral Slate", "Kora White"],
            "sizes": ["M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "pm06",
            "name": "Sky Blue Horizon Minimal Tee",
            "description": "Crisp sky blue pastel tee crafted from 220 GSM single-origin Indian cotton with tonal collar ribbing and minimal pocket logo.",
            "price": 1199.00,
            "original_price": 1799.00,
            "discount_pct": 33,
            "category": "Minimal",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "PASTEL DROP",
            "image": "https://images.unsplash.com/photo-1527719327859-c6ce80353573?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6ba4b8",
            "colors": ["Sky Blue", "Kora White", "Sage Green"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "pm07",
            "name": "Sage Green Studio Boxy Tee",
            "description": "Earthy muted sage tone inspired by Indian monsoon flora. Modern structured boxy crop with double-needle hems.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Aesthetic",
            "gender": "Men",
            "collection": "Aesthetic & Pastel",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#8f9779",
            "colors": ["Sage Green", "Dusk Olive", "Chai Sand"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "pm08",
            "name": "Neo-Shibuya Mecha Pilot Anime Tee",
            "description": "Futuristic anime mecha pilot schematic with Japanese tech typography. Ultra-sharp vector silkscreen print on 250 GSM jersey.",
            "price": 1649.00,
            "original_price": 2499.00,
            "discount_pct": 34,
            "category": "Anime",
            "gender": "Men",
            "collection": "Anime & Manga",
            "tag": "NEW DROP",
            "image": "https://images.unsplash.com/photo-1503342452485-86b7f54527ef?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2a2d34",
            "colors": ["Washed Charcoal", "Cobalt Blue", "Onyx Black"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pm09",
            "name": "Chai Sand Archival Coordinates Tee",
            "description": "Warm beige tone reflecting authentic Indian khadi sand palettes. Features subtle Bombay studio coordinates embroidered on chest.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Minimal",
            "gender": "Men",
            "collection": "Minimal Studio",
            "tag": "CORE ARCHIVE",
            "image": "https://images.unsplash.com/photo-1488161628813-04466f872be2?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Chai Sand", "Kora White", "Mocha Brown"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Relaxed", "Classic"]
        },
        {
            "id": "pm10",
            "name": "Dusk Olive Raw Hem Deconstructed Tee",
            "description": "Deconstructed relaxed street cut with raw edge bottom hem, reinforced seams, and subtle mineral wash texture.",
            "price": 1599.00,
            "original_price": 2399.00,
            "discount_pct": 33,
            "category": "Streetwear",
            "gender": "Men",
            "collection": "Streetwear",
            "tag": "STREETWEAR",
            "image": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#3d4739",
            "colors": ["Dusk Olive", "Slate Grey", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "pm11",
            "name": "Sunset Amber Mustard Street Tee",
            "description": "Rich golden mustard yellow hue crafted for vibrant street presence. Heavyweight 240 GSM organic cotton with ribbed collar.",
            "price": 1349.00,
            "original_price": 1999.00,
            "discount_pct": 33,
            "category": "Casual",
            "gender": "Men",
            "collection": "Casual Heavyweight",
            "tag": "TRENDY TONE",
            "image": "https://images.unsplash.com/photo-1492562080023-ab3db95bfbce?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d4a373",
            "colors": ["Sunset Amber", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Oversized"]
        },
        {
            "id": "pm12",
            "name": "Dark Mocha Espresso Oversized Tee",
            "description": "Deep earthy roasted mocha brown garment dye. Dropped shoulders, relaxed chest drape, and buttery soft finish.",
            "price": 1449.00,
            "original_price": 2199.00,
            "discount_pct": 34,
            "category": "Oversized",
            "gender": "Men",
            "collection": "Oversized",
            "tag": "WARM EARTH",
            "image": "https://images.unsplash.com/photo-1519085360753-af0119f7cbe7?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#5e4033",
            "colors": ["Mocha Brown", "Chai Sand", "Onyx Black"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pm13",
            "name": "Cobalt Royal Studio Heavy Tee",
            "description": "Vibrant deep cobalt royal blue. Premium Japanese binding, 260 GSM luxury knit that holds shape through dozens of washes.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Casual",
            "gender": "Men",
            "collection": "Casual Heavyweight",
            "tag": "VIBRANT DROP",
            "image": "https://images.unsplash.com/photo-1517841905240-472988babdf9?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2a4d69",
            "colors": ["Cobalt Blue", "Sky Blue", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Classic", "Boxy"]
        },
        {
            "id": "pm14",
            "name": "Sub-Culture Underground Emblem Tee",
            "description": "Bold subterranean graphic emblem featuring underground music and street aesthetic typography across back and chest.",
            "price": 1599.00,
            "original_price": 2399.00,
            "discount_pct": 33,
            "category": "Graphic Prints",
            "gender": "Men",
            "collection": "Graphic Prints",
            "tag": "UNDERGROUND",
            "image": "https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#22252a",
            "colors": ["Mineral Slate", "Onyx Black", "Kora White"],
            "sizes": ["M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "pm15",
            "name": "Crimson Velvet Raw Boxy Tee",
            "description": "Rich deep crimson red mineral wash. Heavy drop shoulder with boxy silhouette and signature tonal studio crest.",
            "price": 1549.00,
            "original_price": 2299.00,
            "discount_pct": 33,
            "category": "Streetwear",
            "gender": "Men",
            "collection": "Streetwear",
            "tag": "HOT SELLER",
            "image": "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#8b2635",
            "colors": ["Crimson Red", "Terracotta", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "pm16",
            "name": "Forest Pine Heritage Crewneck Tee",
            "description": "Deep British racing / forest pine green crafted with 240 GSM combed cotton. Timeless streetwear essential.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Casual",
            "gender": "Men",
            "collection": "Casual Heavyweight",
            "tag": "ESSENTIAL",
            "image": "https://images.unsplash.com/photo-1562157873-818bc0726f68?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2d4a3e",
            "colors": ["Forest Pine", "Sage Green", "Kora White"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "pm17",
            "name": "Mineral Slate Acid Monolith Tee",
            "description": "Custom enzyme acid wash treatment on dense 270 GSM jersey. Every piece carries an entirely unique marbleized street texture.",
            "price": 1799.00,
            "original_price": 2699.00,
            "discount_pct": 33,
            "category": "Streetwear",
            "gender": "Men",
            "collection": "Streetwear",
            "tag": "LIMITED DROP",
            "image": "https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#424549",
            "colors": ["Mineral Slate", "Onyx Black"],
            "sizes": ["M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },

        # ==========================================
        # WOMEN'S COLLECTION (17 Products)
        # ==========================================
        {
            "id": "pw01",
            "name": "Blush Sakura Pastel Aesthetic Tee",
            "description": "Soft pastel pink jersey inspired by cherry blossoms, featuring poetic minimal typography and a relaxed boyfriend drape.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Aesthetic",
            "gender": "Women",
            "collection": "Aesthetic & Pastel",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1524250502761-1ac6f2e30d43?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#f4c2c2",
            "colors": ["Pastel Pink", "Lavender", "Kora White"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pw02",
            "name": "Lavender Dreamscape Ethereal Tee",
            "description": "Delicate dusty lilac lavender hue with micro-embroidered celestial motif on chest. Tailored relaxed drape with ribbed crewneck.",
            "price": 1449.00,
            "original_price": 2199.00,
            "discount_pct": 34,
            "category": "Aesthetic",
            "gender": "Women",
            "collection": "Aesthetic & Pastel",
            "tag": "TRENDING",
            "image": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c3b1e1",
            "colors": ["Lavender", "Pastel Pink", "Chai Sand"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Relaxed"]
        },
        {
            "id": "pw03",
            "name": "Botanical Line-Art Minimalist Tee",
            "description": "Continuous fine line floral botanical artwork across back and chest. Printed with soft-hand eco inks on pure combed Indian cotton.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Graphic Prints",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "STAFF PICK",
            "image": "https://images.unsplash.com/photo-1503341455253-b2e723bb3dbb?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#e8e4dc",
            "colors": ["Kora White", "Sage Green", "Pastel Pink"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "pw04",
            "name": "Komorebi High-Street Cropped Boxy Tee",
            "description": "Architectural modern crop with structured drop shoulders. Cut from 240 GSM organic cotton that maintains an elevated crisp profile.",
            "price": 1299.00,
            "original_price": 1999.00,
            "discount_pct": 35,
            "category": "Oversized",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "HOT SELLER",
            "image": "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Lavender"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "pw05",
            "name": "Cyberpunk Android Girl Anime Tee",
            "description": "Striking futuristic cyberpunk manga portrait with iridescent foil highlight accents. 250 GSM luxury streetwear blank.",
            "price": 1699.00,
            "original_price": 2599.00,
            "discount_pct": 35,
            "category": "Anime",
            "gender": "Women",
            "collection": "Anime & Manga",
            "tag": "NEW DROP",
            "image": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#2b3a55",
            "colors": ["Cobalt Blue", "Onyx Black", "Pastel Pink"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pw06",
            "name": "Sage Flora Botanical Serenity Tee",
            "description": "Earthy sage green blank with subtle tone-on-tone botanical screenprint. Perfect everyday luxury tee with breathable jersey.",
            "price": 1349.00,
            "original_price": 1999.00,
            "discount_pct": 33,
            "category": "Aesthetic",
            "gender": "Women",
            "collection": "Aesthetic & Pastel",
            "tag": "PASTEL DROP",
            "image": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#8f9779",
            "colors": ["Sage Green", "Almond Beige", "Lavender"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Classic", "Boxy"]
        },
        {
            "id": "pw07",
            "name": "Celestial Tarot Cosmic Graphic Tee",
            "description": "Gold foil and soft-touch pigment tarot iconography representing intuition and strength. Drop shoulder boyfriend silhouette.",
            "price": 1599.00,
            "original_price": 2399.00,
            "discount_pct": 33,
            "category": "Graphic Prints",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "LIMITED EDITION",
            "image": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#1b1d22",
            "colors": ["Onyx Black", "Mineral Slate", "Pastel Pink"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Relaxed"]
        },
        {
            "id": "pw08",
            "name": "Warm Almond Beige Minimal Crop Tee",
            "description": "Subtle nude almond cream tone. Tailored boxy cropped cut engineered to sit perfectly with high-waisted streetwear cargos.",
            "price": 1199.00,
            "original_price": 1799.00,
            "discount_pct": 33,
            "category": "Minimal",
            "gender": "Women",
            "collection": "Minimal Studio",
            "tag": "CORE BASIC",
            "image": "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#d8cbb5",
            "colors": ["Almond Beige", "Kora White", "Pastel Pink"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Classic"]
        },
        {
            "id": "pw09",
            "name": "Retro Synthwave 80s Anime Tee",
            "description": "Vibrant retro anime visual reminiscent of 1980s Tokyo city pop album covers. Printed on soft 240 GSM combed cotton.",
            "price": 1649.00,
            "original_price": 2499.00,
            "discount_pct": 34,
            "category": "Anime",
            "gender": "Women",
            "collection": "Anime & Manga",
            "tag": "TRENDING",
            "image": "https://images.unsplash.com/photo-1524504388940-b1c1722653e1?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6b4f70",
            "colors": ["Lavender", "Pastel Pink", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pw10",
            "name": "Mint Haze Cool Cotton Relaxed Tee",
            "description": "Cool pastel mint green with ultra-soft garment wash. Breathable, breezy drape crafted for warm Indian afternoons.",
            "price": 1299.00,
            "original_price": 1899.00,
            "discount_pct": 32,
            "category": "Aesthetic",
            "gender": "Women",
            "collection": "Aesthetic & Pastel",
            "tag": "PASTEL DROP",
            "image": "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#98d8aa",
            "colors": ["Mint Green", "Sky Blue", "Kora White"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Relaxed", "Boxy"]
        },
        {
            "id": "pw11",
            "name": "Rust Terracotta Sunburst Graphic Tee",
            "description": "Warm terracotta shade featuring modern minimalist geometric sunburst graphic in warm cream ink. Heavy 240 GSM feel.",
            "price": 1499.00,
            "original_price": 2199.00,
            "discount_pct": 32,
            "category": "Graphic Prints",
            "gender": "Women",
            "collection": "Graphic Prints",
            "tag": "EARTH TONE",
            "image": "https://images.unsplash.com/photo-1544005313-94ddf0286df2?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#c85a32",
            "colors": ["Rust Terracotta", "Almond Beige", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Classic"]
        },
        {
            "id": "pw12",
            "name": "Vintage Crimson Velvet Boxy Tee",
            "description": "Deep garnet crimson red with subtle vintage mineral fading along collar and seams. Relaxed boxy streetwear profile.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Streetwear",
            "gender": "Women",
            "collection": "Streetwear",
            "tag": "NEW ARRIVAL",
            "image": "https://images.unsplash.com/photo-1508214751196-bcfd4ca60f91?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#9e2a2b",
            "colors": ["Crimson Red", "Onyx Black", "Pastel Pink"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "pw13",
            "name": "Pastel Coral Sunset Relaxed Tee",
            "description": "Sun-drenched soft coral shade. Delicate ribbed neckline and relaxed drape made with lightweight breathable Indian luxury cotton.",
            "price": 1249.00,
            "original_price": 1799.00,
            "discount_pct": 31,
            "category": "Casual",
            "gender": "Women",
            "collection": "Aesthetic & Pastel",
            "tag": "SUMMER DROP",
            "image": "https://images.unsplash.com/photo-1519741497674-611481863552?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#e8a598",
            "colors": ["Pastel Coral", "Almond Beige", "Kora White"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "pw14",
            "name": "Sky Blue Cloud Oversized Boyfriend Tee",
            "description": "Airy serene baby blue tone with dropped shoulders and roomy boyfriend cut. Ribbed collar with interior herringbone neck tape.",
            "price": 1399.00,
            "original_price": 2099.00,
            "discount_pct": 33,
            "category": "Oversized",
            "gender": "Women",
            "collection": "Oversized",
            "tag": "BESTSELLER",
            "image": "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#6ba4b8",
            "colors": ["Sky Blue", "Lavender", "Kora White"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "pw15",
            "name": "Urban Utility Streetwear Cargo Tee",
            "description": "Matte olive industrial street tee featuring nylon utility chest pocket with branded matte-black snap button.",
            "price": 1699.00,
            "original_price": 2599.00,
            "discount_pct": 35,
            "category": "Streetwear",
            "gender": "Women",
            "collection": "Streetwear",
            "tag": "STREETWEAR",
            "image": "https://images.unsplash.com/photo-1464863979621-258859e62245?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#3d4739",
            "colors": ["Dusk Olive", "Onyx Black", "Mineral Slate"],
            "sizes": ["S", "M", "L"],
            "styles": ["Boxy", "Relaxed"]
        },
        {
            "id": "pw16",
            "name": "Golden Ochre Vintage Sunset Tee",
            "description": "Warm mustard golden ochre hue with vintage cracked screenprint aesthetic. Heavyweight 240 GSM cotton knit.",
            "price": 1349.00,
            "original_price": 1999.00,
            "discount_pct": 33,
            "category": "Casual",
            "gender": "Women",
            "collection": "Casual Heavyweight",
            "tag": "WARM VIBE",
            "image": "https://images.unsplash.com/photo-1475180098004-ca77a66827be?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#e9c46a",
            "colors": ["Golden Mustard", "Chai Sand", "Rust Terracotta"],
            "sizes": ["XS", "S", "M", "L"],
            "styles": ["Classic", "Boxy"]
        },
        {
            "id": "pw17",
            "name": "Archival Mineral Charcoal Street Tee",
            "description": "Charcoal grey mineral wash with raw distressed bottom edge and discreet tone-on-tone studio monogram embroidery.",
            "price": 1599.00,
            "original_price": 2399.00,
            "discount_pct": 33,
            "category": "Streetwear",
            "gender": "Women",
            "collection": "Streetwear",
            "tag": "LIMITED DROP",
            "image": "https://images.unsplash.com/photo-1495385794356-15371f348c31?w=800&auto=format&fit=crop&q=80",
            "color_hex": "#343b47",
            "colors": ["Mineral Slate", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },

        # ==========================================
        # UNISEX & CUSTOMIZABLE CORE DROPS (8 Products)
        # ==========================================
        {
            "id": "p1",
            "name": "The Essential Heavyweight Blank",
            "description": "240 GSM dense combed Indian cotton blank tailored for everyday streetwear with a structured, breathable drape.",
            "price": 1299.00,
            "original_price": 1999.00,
            "discount_pct": 35,
            "category": "Core",
            "gender": "Unisex",
            "collection": "Minimal Studio",
            "tag": "BESTSELLER",
            "image": "/static/images/essential-tee.jpg",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Slate Smoke", "Dusk Olive"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Classic", "Oversized", "Boxy"]
        },
        {
            "id": "p2",
            "name": "Noir Studio Oversized Tee",
            "description": "Garment-dyed carbon black streetwear blank with double-needle ribbed collar and subtle enzyme wash treatment.",
            "price": 1499.00,
            "original_price": 2299.00,
            "discount_pct": 35,
            "category": "Studio",
            "gender": "Unisex",
            "collection": "Oversized",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/noir-studio-tee.jpg",
            "color_hex": "#1a1a1a",
            "colors": ["Onyx Black", "Slate Smoke", "Kora White"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "p3",
            "name": "Form / Function Architectural Tee",
            "description": "Architectural silhouette featuring drop shoulders, clean geometric balance, and reinforced Japanese-style binding.",
            "price": 1799.00,
            "original_price": 2799.00,
            "discount_pct": 36,
            "category": "Edition 01",
            "gender": "Unisex",
            "collection": "Streetwear",
            "tag": "LIMITED DROP",
            "image": "/static/images/form-function-tee.jpg",
            "color_hex": "#d8cbb5",
            "colors": ["Kora White", "Chai Sand", "Onyx Black"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "p4",
            "name": "Atelier 280 GSM Custom Heavyweight Blank",
            "description": "Dense knit 280 GSM French Terry cotton blank crafted specifically for bespoke studio custom graphics and personal silkscreen prints.",
            "price": 1499.00,
            "original_price": 2199.00,
            "discount_pct": 32,
            "category": "Customizable",
            "gender": "Unisex",
            "collection": "Streetwear",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/essential-tee.jpg",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Dusk Olive", "Chai Sand", "Pastel Pink", "Lavender"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Boxy", "Classic"]
        },
        {
            "id": "p5",
            "name": "Archival Monolith Acid Wash Tee",
            "description": "Limited studio series exploring raw mineral wash finishes, oversized proportions, subtle tonal branding, and archival stitching.",
            "price": 1999.00,
            "original_price": 2999.00,
            "discount_pct": 33,
            "category": "Studio",
            "gender": "Unisex",
            "collection": "Streetwear",
            "tag": "LIMITED DROP",
            "image": "/static/images/noir-studio-tee.jpg",
            "color_hex": "#343b47",
            "colors": ["Onyx Black", "Slate Smoke"],
            "sizes": ["S", "M", "L", "XL"],
            "styles": ["Oversized", "Boxy"]
        },
        {
            "id": "p6",
            "name": "Kinetic Raw Hem Deconstructed Tee",
            "description": "Deconstructed relaxed street fit with raw bottom hem, reinforced neckline, and signature Painite Studio minimal branding.",
            "price": 1699.00,
            "original_price": 2499.00,
            "discount_pct": 32,
            "category": "Edition 01",
            "gender": "Unisex",
            "collection": "Streetwear",
            "tag": "NEW ARRIVAL",
            "image": "/static/images/form-function-tee.jpg",
            "color_hex": "#e8e4dc",
            "colors": ["Kora White", "Onyx Black", "Chai Sand", "Sky Blue"],
            "sizes": ["XS", "S", "M", "L", "XL"],
            "styles": ["Classic", "Relaxed"]
        },
        {
            "id": "p7",
            "name": "Bespoke Streetwear Boxy Custom Tee",
            "description": "Engineered modern boxy fit blank ready for your personal custom typography, uploaded artwork, or studio embroidery badge.",
            "price": 1599.00,
            "original_price": 2399.00,
            "discount_pct": 33,
            "category": "Customizable",
            "gender": "Unisex",
            "collection": "Oversized",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/noir-studio-tee.jpg",
            "color_hex": "#101114",
            "colors": ["Onyx Black", "Kora White", "Slate Smoke", "Indigo Navy", "Pastel Pink", "Sage Green"],
            "sizes": ["XS", "S", "M", "L", "XL", "XXL"],
            "styles": ["Boxy", "Oversized"]
        },
        {
            "id": "p8",
            "name": "Vintage Mineral Wash Custom Blank",
            "description": "Hand-treated mineral wash vintage cotton blank with pre-shrunk heavyweight feel. Designed for bold streetwear designs.",
            "price": 1799.00,
            "original_price": 2699.00,
            "discount_pct": 33,
            "category": "Customizable",
            "gender": "Unisex",
            "collection": "Streetwear",
            "tag": "CUSTOM T-SHIRT",
            "image": "/static/images/form-function-tee.jpg",
            "color_hex": "#343b47",
            "colors": ["Slate Smoke", "Onyx Black", "Dusk Olive", "Lavender"],
            "sizes": ["S", "M", "L", "XL", "XXL"],
            "styles": ["Oversized", "Relaxed"]
        }
    ]

    for p in products:
        cursor.execute("""
            INSERT OR REPLACE INTO products (
                id, name, description, price, original_price, discount_pct,
                category, gender, collection, tag, image, color_hex,
                colors, sizes, styles, in_stock
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
        """, (
            p["id"], p["name"], p["description"], p["price"], p.get("original_price", p["price"] * 1.4),
            p.get("discount_pct", 30), p["category"], p.get("gender", "Unisex"),
            p.get("collection", "Streetwear"), p["tag"], p["image"], p.get("color_hex", "#101114"),
            json.dumps(p["colors"]), json.dumps(p["sizes"]), json.dumps(p["styles"])
        ))

    # 3. Seed Sample Indian Orders
    order1_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-IND101"
    cursor.execute("""
        INSERT OR REPLACE INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, 'In Production', ?, ?, ?, ?, 'INR', 0.0, 'cod')
    """, (
        order1_id,
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        "+91 98450 12345",
        2998.00,
        "Flat 402, Signature Towers, 12th Main Road, Indiranagar",
        "Bengaluru",
        "Karnataka",
        "560038"
    ))

    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order1_id,))
    cursor.execute("""
        INSERT OR REPLACE INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_01", order1_id, "p2", "Noir Studio Oversized Tee", 1499.00, 1, "Onyx Black", "L", "Oversized", "PAINITE ATELIER", ""
    ))
    cursor.execute("""
        INSERT OR REPLACE INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_02", order1_id, "pw01", "Blush Sakura Pastel Aesthetic Tee", 1399.00, 1, "Pastel Pink", "M", "Boxy", "BOMBAY SUB-CULTURE", ""
    ))

    order2_id = f"ORD-{datetime.date.today().strftime('%Y%m%d')}-IND202"
    cursor.execute("""
        INSERT OR REPLACE INTO orders (id, user_id, customer_name, customer_email, customer_phone, total, status, address, city, state, pincode, currency, shipping_fee, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, 'Shipped', ?, ?, ?, ?, 'INR', 0.0, 'upi')
    """, (
        order2_id,
        customer_id,
        "Aarav Sharma",
        "customer@painite.studio",
        "+91 98450 12345",
        1799.00,
        "Bungalow 7, Perry Cross Road, Bandra West",
        "Mumbai",
        "Maharashtra",
        "400050"
    ))

    cursor.execute("DELETE FROM order_items WHERE order_id = ?", (order2_id,))
    cursor.execute("""
        INSERT OR REPLACE INTO order_items (id, order_id, product_id, product_name, price, quantity, color, size, style, custom_text, artwork_url)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "item_seed_ind_03", order2_id, "pm03", "Phantom Samurai Ink Wash Anime Tee", 1699.00, 1, "Onyx Black", "XL", "Oversized", "NOT JUST A T-SHIRT", ""
    ))

    conn.commit()
    conn.close()
    print("Database successfully seeded with 42+ luxury Men's & Women's garments across diverse colorways.")
