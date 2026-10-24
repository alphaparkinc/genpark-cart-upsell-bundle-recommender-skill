import math, sys
sys.stdout.reconfigure(encoding='utf-8')

class CartUpsellBundleRecommenderClient:
    """
    Autonomous e-commerce cart bundle optimizer. Evaluates product co-occurrence lift,
    complementary category compatibility, margin floor preservation, and optimal discount elasticity.
    """
    def __init__(self, target_margin_floor=0.28):
        self.target_margin_floor = target_margin_floor
        # Catalog product definition: id -> {name, category, price, cost}
        self.catalog = {
            "PROD-PHONE":    {"name": "Ultra Flagship Smartphone", "category": "phone", "price": 899.00, "cost": 540.00},
            "PROD-CASE":     {"name": "Aramid Carbon Protective Case", "category": "accessory", "price": 49.00, "cost": 12.00},
            "PROD-SCREEN":   {"name": "Sapphire Tempered Glass 2-Pack", "category": "accessory", "price": 29.00, "cost": 6.00},
            "PROD-CHARGER":  {"name": "65W GaN Fast Charger & Braided Cable", "category": "charger", "price": 39.00, "cost": 14.00},
            "PROD-EARBUDS":  {"name": "Pro Wireless ANC Earbuds", "category": "audio", "price": 149.00, "cost": 65.00},
            "PROD-WATCH":    {"name": "Active Fitness Smartwatch", "category": "wearable", "price": 229.00, "cost": 110.00},
            "PROD-WARRANTY": {"name": "2-Year Accidental Damage Protection", "category": "warranty", "price": 79.00, "cost": 15.00}
        }
        # Precomputed co-occurrence affinity graph (Pairwise Lift & Jaccard index)
        self.affinity_graph = {
            ("PROD-PHONE", "PROD-CASE"): {"lift": 4.8, "jaccard": 0.42},
            ("PROD-PHONE", "PROD-SCREEN"): {"lift": 5.2, "jaccard": 0.46},
            ("PROD-PHONE", "PROD-CHARGER"): {"lift": 3.9, "jaccard": 0.35},
            ("PROD-PHONE", "PROD-EARBUDS"): {"lift": 2.7, "jaccard": 0.24},
            ("PROD-PHONE", "PROD-WARRANTY"): {"lift": 3.4, "jaccard": 0.28},
            ("PROD-EARBUDS", "PROD-CHARGER"): {"lift": 2.1, "jaccard": 0.18}
        }

    def generate_bundle_recommendations(self, cart_item_ids, max_bundles=3, discount_cap=0.20):
        cart_products = [self.catalog[pid] for pid in cart_item_ids if pid in self.catalog]
        if not cart_products:
            return {"status": "error", "message": "Cart items not recognized in catalog"}

        cart_total_price = sum(p["price"] for p in cart_products)
        cart_total_cost = sum(p["cost"] for p in cart_products)
        cart_categories = {p["category"] for p in cart_products}
        
        candidates = []
        for cand_id, cand_prod in self.catalog.items():
            if cand_id in cart_item_ids:
                continue
            # Avoid duplicate same-category primary hardware
            if cand_prod["category"] in cart_categories and cand_prod["category"] in ("phone", "audio", "wearable"):
                continue

            # Compute composite affinity score
            max_lift = 1.0
            avg_jaccard = 0.0
            hits = 0
            for cart_id in cart_item_ids:
                pair = (cart_id, cand_id) if (cart_id, cand_id) in self.affinity_graph else (cand_id, cart_id)
                if pair in self.affinity_graph:
                    aff = self.affinity_graph[pair]
                    if aff["lift"] > max_lift:
                        max_lift = aff["lift"]
                    avg_jaccard += aff["jaccard"]
                    hits += 1
            
            if hits > 0:
                avg_jaccard /= hits
            else:
                max_lift = 1.2
                avg_jaccard = 0.10

            composite_score = max_lift * (1.0 + avg_jaccard)
            candidates.append((cand_id, cand_prod, composite_score))

        candidates.sort(key=lambda x: x[2], reverse=True)
        top_candidates = candidates[:max_bundles]

        recommended_bundles = []
        for cand_id, cand_prod, score in top_candidates:
            addon_price = cand_prod["price"]
            addon_cost = cand_prod["cost"]
            
            # Find optimal discount tier (0%, 5%, 10%, 15%, 20%)
            best_tier = None
            best_exp_profit = -1e9

            for disc_rate in [0.0, 0.05, 0.10, 0.15, min(0.20, discount_cap)]:
                bundle_retail = cart_total_price + addon_price
                bundle_cost = cart_total_cost + addon_cost
                discounted_addon_price = addon_price * (1.0 - disc_rate)
                total_bundle_charged = cart_total_price + discounted_addon_price
                
                margin = (total_bundle_charged - bundle_cost) / total_bundle_charged
                if margin < self.target_margin_floor:
                    continue

                # Conversion acceptance probability model: base 18% + elasticity lift
                prob_accept = 0.18 + (disc_rate * 0.85) * (score / 4.0)
                prob_accept = min(0.85, max(0.05, prob_accept))
                
                incremental_profit = (discounted_addon_price - addon_cost)
                exp_profit = incremental_profit * prob_accept

                if exp_profit > best_exp_profit:
                    best_exp_profit = exp_profit
                    best_tier = {
                        "discount_rate": disc_rate,
                        "discounted_addon_price": round(discounted_addon_price, 2),
                        "customer_savings": round(addon_price * disc_rate, 2),
                        "bundle_margin_pct": round(margin * 100.0, 2),
                        "acceptance_prob": round(prob_accept, 3),
                        "expected_incremental_margin": round(exp_profit, 2)
                    }

            if best_tier:
                recommended_bundles.append({
                    "addon_product_id": cand_id,
                    "addon_product_name": cand_prod["name"],
                    "addon_category": cand_prod["category"],
                    "original_addon_price": addon_price,
                    "recommended_discount_pct": int(best_tier["discount_rate"] * 100),
                    "bundle_addon_price": best_tier["discounted_addon_price"],
                    "customer_savings": best_tier["customer_savings"],
                    "bundle_total_price": round(cart_total_price + best_tier["discounted_addon_price"], 2),
                    "combined_margin_pct": best_tier["bundle_margin_pct"],
                    "predicted_acceptance_rate": best_tier["acceptance_prob"],
                    "expected_incremental_margin": best_tier["expected_incremental_margin"]
                })

        return {
            "status": "success",
            "cart_item_count": len(cart_products),
            "cart_base_total": round(cart_total_price, 2),
            "recommended_bundles": recommended_bundles
        }
