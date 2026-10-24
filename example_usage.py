from client import CartUpsellBundleRecommenderClient
import json, sys
sys.stdout.reconfigure(encoding='utf-8')

def main():
    client = CartUpsellBundleRecommenderClient(target_margin_floor=0.30)
    print("=== CART UPSELL BUNDLE RECOMMENDER ===")
    cart = ["PROD-PHONE"]
    res = client.generate_bundle_recommendations(cart, max_bundles=3)
    print(f"Current Cart Items: {cart} (Base Total: ${res['cart_base_total']:.2f})")
    print(f"Generated {len(res['recommended_bundles'])} Optimal Bundles:")
    print()
    for i, b in enumerate(res['recommended_bundles'], 1):
        print(f"{i}. Add-on: {b['addon_product_name']} ({b['addon_category'].upper()})")
        print(f"   - Original: ${b['original_addon_price']:.2f} -> Bundle Price: ${b['bundle_addon_price']:.2f} ({b['recommended_discount_pct']}% OFF)")
        print(f"   - Total Checkout: ${b['bundle_total_price']:.2f} (Saves customer: ${b['customer_savings']:.2f})")
        print(f"   - Blended Margin: {b['combined_margin_pct']}% | Predicted Conversion: {b['predicted_acceptance_rate']*100:.1f}%")
        print(f"   - Expected Profit Lift: +${b['expected_incremental_margin']:.2f}")
        print()

if __name__ == "__main__":
    main()
