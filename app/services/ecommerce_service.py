"""E-Commerce Service for AI Farmer - Agricultural inputs marketplace."""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import uuid
from app.utils import logger

@dataclass
class Product:
    id: str
    name: str
    category: str  # seed, fertilizer, pesticide, equipment, tool
    subcategory: str
    brand: str
    description: str
    price_inr: float
    unit: str  # kg, litre, piece, packet
    stock_quantity: int
    rating: float
    reviews_count: int
    image_url: str
    seller: str
    delivery_days: int
    applicable_crops: List[str]
    organic: bool
    certification: List[str]
    discount_percent: float = 0.0

@dataclass
class CartItem:
    product_id: str
    quantity: float
    added_at: str

@dataclass
class Order:
    order_id: str
    farmer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    discount: float
    final_amount: float
    status: str  # pending, confirmed, shipped, delivered, cancelled
    shipping_address: Dict[str, str]
    payment_method: str
    created_at: str
    estimated_delivery: str


class ECommerceService:
    """Agricultural inputs marketplace integrated with AI Farmer."""

    def __init__(self):
        self.products = self._load_products()
        self.carts: Dict[str, List[CartItem]] = {}
        self.orders: Dict[str, Order] = {}

    def _load_products(self) -> List[Product]:
        """Load comprehensive agricultural product catalog."""
        products = []

        # SEEDS
        seed_data = [
            ("Pusa Basmati 1121 Rice Seeds", "seed", "rice", "IARI", "Premium basmati rice seeds, 98% germination", 65, "kg", 500, 4.5, 120, "https://example.com/pusa1121.jpg", "National Seeds Corp", 5, ["rice"], False, ["NSC Certified", "IARI Released"]),
            ("Pusa Basmati 1509 Rice Seeds", "seed", "rice", "IARI", "Early maturing basmati, 115-120 days", 80, "kg", 400, 4.7, 200, "https://example.com/pusa1509.jpg", "IARI Seed Unit", 5, ["rice"], False, ["IARI Certified"]),
            ("IR 64 Rice Seeds", "seed", "rice", "State Seeds", "High-yielding non-basmati rice", 45, "kg", 800, 4.3, 350, "https://example.com/ir64.jpg", "State Seeds Corporation", 3, ["rice"], False, ["State Certified"]),
            ("HD 2967 Wheat Seeds", "seed", "wheat", "IARI", "Rust resistant high-yielding wheat", 38, "kg", 600, 4.6, 180, "https://example.com/hd2967.jpg", "National Seeds Corp", 4, ["wheat"], False, ["IARI Certified", "Rust Resistant"]),
            ("DBW 187 Wheat Seeds", "seed", "wheat", "IARI", "Yellow rust resistant variety", 42, "kg", 450, 4.4, 90, "https://example.com/dbw187.jpg", "IARI Seed Unit", 4, ["wheat"], False, ["IARI Released"]),
            ("RCH 2 BG-II Cotton Seeds", "seed", "cotton", "Rasi Seeds", "Bt cotton hybrid, bollworm resistant", 850, "packet (450g)", 300, 4.5, 250, "https://example.com/rch2.jpg", "Rasi Seeds Pvt Ltd", 7, ["cotton"], False, ["BIS Certified", "BG-II Technology"]),
            ("Ankur 651 BG-II Cotton Seeds", "seed", "cotton", "Ankur Seeds", "High-yielding Bt cotton hybrid", 920, "packet (450g)", 250, 4.6, 180, "https://example.com/ankur651.jpg", "Ankur Seeds", 7, ["cotton"], False, ["BIS Certified"]),
            ("Pioneer 3396 Maize Seeds", "seed", "maize", "Pioneer", "High-yielding single cross hybrid", 185, "kg", 400, 4.7, 220, "https://example.com/p3396.jpg", "Pioneer Hi-Bred", 5, ["maize"], False, ["Certified Hybrid"]),
            ("DHM 117 Maize Seeds", "seed", "maize", "DHM", "Drought tolerant maize hybrid", 165, "kg", 350, 4.4, 150, "https://example.com/dhm117.jpg", "DHM Seeds", 5, ["maize"], False, ["State Certified"]),
            ("TG 37A Groundnut Seeds", "seed", "groundnut", "GAU", "PBNDV resistant groundnut variety", 125, "kg", 500, 4.3, 100, "https://example.com/tg37a.jpg", "Gujarat State Seeds", 5, ["groundnut"], False, ["GAU Certified"]),
            ("JS 335 Soybean Seeds", "seed", "soybean", "JNKVV", "Yellow mosaic resistant soybean", 95, "kg", 400, 4.5, 130, "https://example.com/js335.jpg", "Madhya Pradesh Seeds", 5, ["soybean"], False, ["JNKVV Released"]),
            ("Kufri Jyoti Potato Seeds", "seed", "potato", "CPRI", "Late blight resistant potato", 28, "kg", 600, 4.6, 200, "https://example.com/kufrijyoti.jpg", "CPRI Shimla", 7, ["potato"], False, ["CPRI Certified", "Tissue Culture"]),
            ("Pusa Ruby Tomato Seeds", "seed", "tomato", "IARI", "Fusarium wilt resistant determinate tomato", 850, "packet (10g)", 400, 4.4, 160, "https://example.com/pusaruby.jpg", "IARI Seed Unit", 4, ["tomato"], False, ["IARI Certified"]),
            ("Arka Vikas Tomato Seeds", "seed", "tomato", "IIHR", "Bacterial wilt resistant hybrid", 1200, "packet (10g)", 300, 4.7, 140, "https://example.com/arkavikas.jpg", "IIHR Bangalore", 5, ["tomato"], False, ["IIHR Certified"]),
            ("Agrifound Dark Red Onion Seeds", "seed", "onion", "NHRDF", "Dark red bulb onion, good storage", 420, "packet (500g)", 500, 4.5, 220, "https://example.com/darkred.jpg", "NHRDF Nashik", 4, ["onion"], False, ["NHRDF Certified"]),
            ("Pusa Red Onion Seeds", "seed", "onion", "IARI", "Red onion, good pungency", 380, "packet (500g)", 450, 4.3, 180, "https://example.com/pusared.jpg", "IARI Seed Unit", 4, ["onion"], False, ["IARI Certified"]),
            ("Co 0238 Sugarcane Setts", "seed", "sugarcane", "SBI", "Red rot resistant early maturing", 18, "quintal", 200, 4.6, 150, "https://example.com/co0238.jpg", "SBI Coimbatore", 10, ["sugarcane"], False, ["SBI Certified"]),
            ("Grand Naine Banana Tissue Culture", "seed", "banana", "NRC Banana", "Tissue culture G-9 banana plantlets", 22, "plantlet", 500, 4.8, 300, "https://example.com/g9tc.jpg", "NRC Banana Trichy", 10, ["banana"], False, ["Tissue Culture Certified"]),
            ("Dashehari Mango Grafts", "seed", "mango", "CISH", "High-yielding Dashehari grafts", 55, "plant", 300, 4.7, 120, "https://example.com/dashehari.jpg", "CISH Lucknow", 14, ["mango"], False, ["CISH Certified"]),
            ("Alphonso Mango Grafts", "seed", "mango", "KKV", "Premium Alphonso grafts", 85, "plant", 250, 4.9, 200, "https://example.com/alphonso.jpg", "Konkan Krishi Vidyapeeth", 14, ["mango"], False, ["KKV Certified"]),
        ]

        # FERTILIZERS
        fert_data = [
            ("Urea (46% N)", "fertilizer", "nitrogen", "IFFCO", "High nitrogen fertilizer for vegetative growth", 30, "50kg bag", 2000, 4.4, 500, "https://example.com/urea.jpg", "IFFCO", 3, ["all_crops"], False, ["BIS Certified"]),
            ("DAP (18-46-0)", "fertilizer", "phosphorus", "IFFCO", "Di-ammonium phosphate, basal application", 1450, "50kg bag", 1500, 4.5, 450, "https://example.com/dap.jpg", "IFFCO", 3, ["all_crops"], False, ["BIS Certified"]),
            ("MOP (0-0-60)", "fertilizer", "potassium", "IPL", "Muriate of Potash for fruit/quality", 1750, "50kg bag", 1200, 4.3, 300, "https://example.com/mop.jpg", "Indian Potash Ltd", 3, ["all_crops"], False, ["BIS Certified"]),
            ("NPK 12:32:16", "fertilizer", "npk", "Coromandel", "Complex fertilizer for basal dose", 1680, "50kg bag", 1000, 4.4, 280, "https://example.com/npk123216.jpg", "Coromandel International", 3, ["all_crops"], False, ["BIS Certified"]),
            ("NPK 20:20:20", "fertilizer", "npk", "Coromandel", "Water soluble NPK for fertigation", 850, "25kg bag", 800, 4.6, 200, "https://example.com/npk202020.jpg", "Coromandel International", 3, ["all_crops"], False, ["Water Soluble Certified"]),
            ("Zinc Sulfate 21%", "fertilizer", "micronutrient", "BASF", "Zinc micronutrient for deficiency correction", 280, "25kg bag", 600, 4.5, 150, "https://example.com/zinc.jpg", "BASF India", 4, ["rice", "maize", "citrus"], False, ["BIS Certified"]),
            ("Boron 20%", "fertilizer", "micronutrient", "BASF", "Boron for flowering and fruit set", 450, "1kg packet", 400, 4.4, 100, "https://example.com/boron.jpg", "BASF India", 4, ["cotton", "groundnut", "mustard"], False, ["BIS Certified"]),
            ("Ferrous Sulfate 19%", "fertilizer", "micronutrient", "Tata", "Iron source for chlorosis correction", 180, "25kg bag", 500, 4.3, 120, "https://example.com/iron.jpg", "Tata Chemicals", 4, ["rice", "sugarcane", "vegetables"], False, ["BIS Certified"]),
            ("Vermicompost", "fertilizer", "organic", "Organic India", "Premium organic vermicompost", 12, "kg", 1000, 4.7, 350, "https://example.com/vermi.jpg", "Organic India", 5, ["all_crops"], True, ["Organic Certified", "NPOP"]),
            ("Neem Cake", "fertilizer", "organic", "Neem Foundation", "Organic nitrogen + pest repellent", 35, "kg", 800, 4.5, 200, "https://example.com/neemcake.jpg", "Neem Foundation", 5, ["all_crops"], True, ["Organic Certified"]),
            ("Farmyard Manure (FYM)", "fertilizer", "organic", "Local", "Well-decomposed farmyard manure", 4, "kg", 2000, 4.2, 500, "https://example.com/fym.jpg", "Local Suppliers", 2, ["all_crops"], True, ["Organic"]),
            ("Biofertilizer - Rhizobium", "fertilizer", "bio", "NBAIM", "Nitrogen-fixing bacteria for legumes", 120, "packet (1kg)", 600, 4.6, 180, "https://example.com/rhizobium.jpg", "NBAIM Mau", 4, ["pulses", "soybean", "groundnut"], True, ["BIS Certified", "Organic"]),
            ("Biofertilizer - Azotobacter", "fertilizer", "bio", "NBAIM", "Free-living nitrogen fixer", 110, "packet (1kg)", 500, 4.5, 160, "https://example.com/azoto.jpg", "NBAIM Mau", 4, ["wheat", "rice", "maize"], True, ["BIS Certified", "Organic"]),
            ("Biofertilizer - PSB", "fertilizer", "bio", "NBAIM", "Phosphate solubilizing bacteria", 130, "packet (1kg)", 550, 4.4, 140, "https://example.com/psb.jpg", "NBAIM Mau", 4, ["all_crops"], True, ["BIS Certified", "Organic"]),
            ("Calcium Nitrate", "fertilizer", "calcium", "Yara", "Calcium nitrate for blossom end rot prevention", 95, "kg", 400, 4.5, 120, "https://example.com/calnit.jpg", "Yara India", 4, ["tomato", "chili", "citrus"], False, ["Imported"]),
            ("Magnesium Sulfate (Epsom Salt)", "fertilizer", "magnesium", "Tata", "Magnesium source for chlorophyll", 65, "kg", 500, 4.4, 100, "https://example.com/epsom.jpg", "Tata Chemicals", 3, ["all_crops"], False, ["BIS Certified"]),
        ]

        # PESTICIDES / CROP PROTECTION
        pest_data = [
            ("Neem Oil (Azadirachtin 1%)", "pesticide", "bio_insecticide", "Organic India", "Organic broad-spectrum insecticide", 450, "litre", 800, 4.6, 300, "https://example.com/neemoil.jpg", "Organic India", 4, ["all_crops"], True, ["Organic Certified", "FSSAI"]),
            ("Bacillus thuringiensis (Bt)", "pesticide", "bio_insecticide", "T-Stanes", "Biological insecticide for caterpillars", 280, "kg", 500, 4.5, 180, "https://example.com/bt.jpg", "T-Stanes", 4, ["cotton", "vegetables", "pulses"], True, ["Organic Certified"]),
            ("Trichoderma viride", "pesticide", "bio_fungicide", "T-Stanes", "Bio-fungicide for soil-borne diseases", 180, "kg", 600, 4.4, 200, "https://example.com/tricho.jpg", "T-Stanes", 4, ["all_crops"], True, ["Organic Certified"]),
            ("Pseudomonas fluorescens", "pesticide", "bio_fungicide", "Biotech", "Bio-control for bacterial blight", 220, "kg", 400, 4.5, 150, "https://example.com/pseudo.jpg", "Agri Biotech", 4, ["rice", "tomato", "citrus"], True, ["Organic Certified"]),
            ("Spinosad 45 SC", "pesticide", "insecticide", "Dow", "Broad-spectrum insecticide, low toxicity", 1850, "litre", 300, 4.5, 250, "https://example.com/spinosad.jpg", "Dow AgroSciences", 5, ["cotton", "vegetables", "pulses"], False, ["CIBRC Approved"]),
            ("Emamectin Benzoate 5 SG", "pesticide", "insecticide", "Syngenta", "Effective against bollworm and fruit borer", 1250, "kg", 350, 4.6, 220, "https://example.com/emamectin.jpg", "Syngenta India", 5, ["cotton", "brinjal", "okra"], False, ["CIBRC Approved"]),
            ("Chlorantraniliprole 18.5 SC", "pesticide", "insecticide", "DuPont", "Anthranilic diamide for stem borer", 2400, "litre", 250, 4.7, 180, "https://example.com/chloran.jpg", "DuPont India", 5, ["rice", "cotton", "vegetables"], False, ["CIBRC Approved"]),
            ("Imidacloprid 17.8 SL", "pesticide", "insecticide", "Bayer", "Systemic insecticide for sucking pests", 850, "litre", 400, 4.4, 300, "https://example.com/imida.jpg", "Bayer CropScience", 4, ["cotton", "rice", "vegetables"], False, ["CIBRC Approved"]),
            ("Thiamethoxam 25 WG", "pesticide", "insecticide", "Syngenta", "Neonicotinoid for whitefly and jassid", 920, "kg", 350, 4.5, 200, "https://example.com/thia.jpg", "Syngenta India", 4, ["cotton", "rice", "vegetables"], False, ["CIBRC Approved"]),
            ("Mancozeb 75 WP", "pesticide", "fungicide", "UPL", "Broad-spectrum protective fungicide", 650, "kg", 500, 4.4, 350, "https://example.com/mancozeb.jpg", "UPL Limited", 4, ["all_crops"], False, ["CIBRC Approved"]),
            ("Carbendazim 50 WP", "pesticide", "fungicide", "BASF", "Systemic fungicide for seed treatment", 580, "kg", 450, 4.3, 280, "https://example.com/carben.jpg", "BASF India", 4, ["all_crops"], False, ["CIBRC Approved"]),
            ("Tricyclazole 75 WP", "pesticide", "fungicide", "Bayer", "Rice blast specific fungicide", 1450, "kg", 300, 4.6, 150, "https://example.com/tricyclazole.jpg", "Bayer CropScience", 4, ["rice"], False, ["CIBRC Approved"]),
            ("Propiconazole 25 EC", "pesticide", "fungicide", "Syngenta", "Systemic fungicide for rust control", 1100, "litre", 350, 4.5, 180, "https://example.com/propi.jpg", "Syngenta India", 4, ["wheat", "groundnut"], False, ["CIBRC Approved"]),
            ("Glyphosate 41 SL", "pesticide", "herbicide", "Monsanto", "Non-selective systemic herbicide", 520, "litre", 600, 4.2, 400, "https://example.com/glypho.jpg", "Monsanto India", 3, ["all_crops"], False, ["CIBRC Approved"]),
            ("Pendimethalin 30 EC", "pesticide", "herbicide", "BASF", "Pre-emergence herbicide", 680, "litre", 450, 4.3, 250, "https://example.com/pendi.jpg", "BASF India", 4, ["wheat", "soybean", "cotton"], False, ["CIBRC Approved"]),
            ("2,4-D Amine Salt", "pesticide", "herbicide", "Dow", "Selective broadleaf herbicide", 380, "litre", 500, 4.2, 300, "https://example.com/24d.jpg", "Dow AgroSciences", 3, ["wheat", "maize", "sorghum"], False, ["CIBRC Approved"]),
            ("Copper Oxychloride 50 WP", "pesticide", "fungicide", "Tata", "Copper-based fungicide (organic grade)", 420, "kg", 400, 4.5, 180, "https://example.com/copper.jpg", "Tata Chemicals", 4, ["vegetables", "fruits", "potato"], True, ["Organic Approved", "CIBRC Approved"]),
            ("Sulfur 80 WP", "pesticide", "fungicide", "BASF", "Sulfur fungicide and miticide", 280, "kg", 500, 4.3, 200, "https://example.com/sulfur.jpg", "BASF India", 4, ["grapes", "mango", "vegetables"], True, ["Organic Approved"]),
        ]

        # EQUIPMENT & TOOLS
        equip_data = [
            ("Knapsack Sprayer 16L", "equipment", "sprayer", "FieldKing", "Manual knapsack sprayer, brass nozzle", 1850, "piece", 300, 4.3, 400, "https://example.com/sprayer16.jpg", "FieldKing India", 7, ["all_crops"], False, ["ISI Mark"]),
            ("Battery Operated Sprayer 16L", "equipment", "sprayer", "KisanKraft", "Battery powered sprayer, 8Ah", 4200, "piece", 200, 4.5, 250, "https://example.com/batteryspray.jpg", "KisanKraft", 7, ["all_crops"], False, ["ISI Mark"]),
            ("Power Weeder 7HP", "equipment", "machine", "Kirloskar", "Petrol power weeder for inter-cultivation", 28500, "piece", 100, 4.4, 150, "https://example.com/weeder.jpg", "Kirloskar", 14, ["all_crops"], False, ["ISI Mark"]),
            ("Manual Seed Drill", "equipment", "machine", "AgriPro", "Hand-operated seed drill for line sowing", 3200, "piece", 150, 4.2, 120, "https://example.com/seeder.jpg", "AgriPro", 7, ["wheat", "pulses", "oilseeds"], False, ["ISI Mark"]),
            ("Soil Testing Kit", "equipment", "tool", "Rehau", "NPK + pH soil testing kit", 1850, "kit", 200, 4.6, 180, "https://example.com/soilkit.jpg", "Rehau India", 5, ["all_crops"], False, ["Certified"]),
            ("Digital Moisture Meter", "equipment", "tool", "Kett", "Grain moisture meter for harvest timing", 8500, "piece", 100, 4.5, 90, "https://example.com/moisture.jpg", "Kett India", 7, ["all_crops"], False, ["ISO Certified"]),
            ("Drip Irrigation Kit 1 Acre", "equipment", "irrigation", "Jain Irrigation", "Complete drip kit with laterals and emitters", 18500, "kit", 150, 4.7, 300, "https://example.com/drip1acre.jpg", "Jain Irrigation", 10, ["all_crops"], False, ["BIS Certified"]),
            ("Sprinkler Set 1 Acre", "equipment", "irrigation", "Jain Irrigation", "Portable sprinkler irrigation set", 12500, "set", 200, 4.5, 220, "https://example.com/sprinkler1.jpg", "Jain Irrigation", 10, ["all_crops"], False, ["BIS Certified"]),
            ("Pruning Shears", "equipment", "tool", "Falcon", "Professional pruning shears", 450, "piece", 400, 4.4, 200, "https://example.com/pruner.jpg", "Falcon Tools", 4, ["fruits", "vegetables"], False, ["ISO"]),
            ("Garden Trowel Set", "equipment", "tool", "Falcon", "3-piece garden tool set", 280, "set", 500, 4.2, 300, "https://example.com/trowel.jpg", "Falcon Tools", 4, ["all_crops"], False, ["ISO"]),
            ("Pheromone Trap (10 pcs)", "equipment", "tool", "T-Stanes", "Insect pheromone traps for IPM", 650, "set", 300, 4.5, 180, "https://example.com/pheromone.jpg", "T-Stanes", 5, ["cotton", "vegetables", "pulses"], True, ["Organic Approved"]),
            ("Yellow Sticky Trap (25 pcs)", "equipment", "tool", "T-Stanes", "Yellow sticky traps for whitefly/aphid", 380, "set", 400, 4.3, 200, "https://example.com/yellowtrap.jpg", "T-Stanes", 5, ["all_crops"], True, ["Organic Approved"]),
            ("Mulch Film 25 Micron (400m)", "equipment", "tool", "Ginegar", "Black mulch film for weed control", 2800, "roll", 250, 4.4, 150, "https://example.com/mulch.jpg", "Ginegar India", 7, ["vegetables", "fruits"], False, ["BIS Certified"]),
            ("Shade Net 50% (3m x 50m)", "equipment", "tool", "Garware", "Agro shade net for nursery protection", 3200, "roll", 200, 4.3, 120, "https://example.com/shadenet.jpg", "Garware", 7, ["vegetables", "nursery"], False, ["BIS Certified"]),
        ]

        all_data = seed_data + fert_data + pest_data + equip_data

        for i, d in enumerate(all_data):
            products.append(Product(
                id=f"PROD-{i+1:04d}",
                name=d[0], category=d[1], subcategory=d[2], brand=d[3],
                description=d[4], price_inr=d[5], unit=d[6], stock_quantity=d[7],
                rating=d[8], reviews_count=d[9], image_url=d[10], seller=d[11],
                delivery_days=d[12], applicable_crops=d[13], organic=d[14],
                certification=d[15], discount_percent=random.choice([0, 0, 0, 5, 10, 15])
            ))

        return products

    def search_products(self, query: str = None, category: str = None, 
                       crop: str = None, organic_only: bool = False,
                       min_price: float = 0, max_price: float = 999999) -> List[Dict[str, Any]]:
        """Search agricultural products."""
        results = self.products

        if query:
            query = query.lower()
            results = [p for p in results if query in p.name.lower() or query in p.description.lower()]

        if category:
            results = [p for p in results if p.category == category.lower()]

        if crop:
            results = [p for p in results if crop.lower() in [c.lower() for c in p.applicable_crops] or "all_crops" in p.applicable_crops]

        if organic_only:
            results = [p for p in results if p.organic]

        results = [p for p in results if min_price <= p.price_inr <= max_price]

        return [self._product_to_dict(p) for p in results]

    def get_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get single product details."""
        for p in self.products:
            if p.id == product_id:
                return self._product_to_dict(p)
        return None

    def add_to_cart(self, farmer_id: str, product_id: str, quantity: float) -> Dict[str, Any]:
        """Add item to farmer's cart."""
        product = self.get_product(product_id)
        if not product:
            return {"error": "Product not found"}

        if farmer_id not in self.carts:
            self.carts[farmer_id] = []

        self.carts[farmer_id].append(CartItem(
            product_id=product_id,
            quantity=quantity,
            added_at=datetime.now().isoformat()
        ))

        return {"success": True, "cart_items": len(self.carts[farmer_id])}

    def get_cart(self, farmer_id: str) -> Dict[str, Any]:
        """Get farmer's cart with totals."""
        items = self.carts.get(farmer_id, [])
        cart_details = []
        total = 0

        for item in items:
            product = self.get_product(item.product_id)
            if product:
                item_total = product["price_inr"] * item.quantity
                total += item_total
                cart_details.append({
                    "product": product,
                    "quantity": item.quantity,
                    "item_total": round(item_total, 2)
                })

        return {
            "items": cart_details,
            "subtotal": round(total, 2),
            "delivery": round(total * 0.05, 2) if total > 0 else 0,
            "total": round(total * 1.05, 2)
        }

    def place_order(self, farmer_id: str, shipping_address: Dict[str, str], 
                   payment_method: str = "COD") -> Dict[str, Any]:
        """Place order from cart."""
        cart = self.get_cart(farmer_id)
        if not cart["items"]:
            return {"error": "Cart is empty"}

        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        order = Order(
            order_id=order_id,
            farmer_id=farmer_id,
            items=cart["items"],
            total_amount=cart["subtotal"],
            discount=0,
            final_amount=cart["total"],
            status="confirmed",
            shipping_address=shipping_address,
            payment_method=payment_method,
            created_at=datetime.now().isoformat(),
            estimated_delivery=(datetime.now() + __import__('datetime').timedelta(days=7)).isoformat()
        )

        self.orders[order_id] = order
        self.carts[farmer_id] = []  # Clear cart

        return {
            "order_id": order_id,
            "status": "confirmed",
            "total": cart["total"],
            "estimated_delivery": order.estimated_delivery
        }

    def get_recommendations_for_crop(self, crop: str) -> List[Dict[str, Any]]:
        """Get input recommendations for a specific crop."""
        recommendations = {
            "rice": ["Urea (46% N)", "DAP (18-46-0)", "Zinc Sulfate 21%", "Tricyclazole 75 WP", "Neem Oil (Azadirachtin 1%)"],
            "wheat": ["HD 2967 Wheat Seeds", "DAP (18-46-0)", "Urea (46% N)", "Mancozeb 75 WP", "Pendimethalin 30 EC"],
            "cotton": ["RCH 2 BG-II Cotton Seeds", "DAP (18-46-0)", "Urea (46% N)", "Spinosad 45 SC", "Battery Operated Sprayer 16L"],
            "tomato": ["Pusa Ruby Tomato Seeds", "NPK 20:20:20", "Calcium Nitrate", "Copper Oxychloride 50 WP", "Mulch Film 25 Micron"],
            "potato": ["Kufri Jyoti Potato Seeds", "DAP (18-46-0)", "Mancozeb 75 WP", "Copper Oxychloride 50 WP", "Soil Testing Kit"],
        }

        product_names = recommendations.get(crop.lower(), [])
        result = []
        for name in product_names:
            for p in self.products:
                if p.name == name:
                    result.append(self._product_to_dict(p))
                    break
        return result

    def _product_to_dict(self, p: Product) -> Dict[str, Any]:
        return {
            "id": p.id, "name": p.name, "category": p.category, "subcategory": p.subcategory,
            "brand": p.brand, "description": p.description, "price_inr": p.price_inr,
            "unit": p.unit, "stock_quantity": p.stock_quantity, "rating": p.rating,
            "reviews_count": p.reviews_count, "image_url": p.image_url, "seller": p.seller,
            "delivery_days": p.delivery_days, "applicable_crops": p.applicable_crops,
            "organic": p.organic, "certification": p.certification,
            "discount_percent": p.discount_percent,
            "discounted_price": round(p.price_inr * (1 - p.discount_percent/100), 2)
        }


# Import random at module level for _load_products
import random

ec_service_instance = ECommerceService()
