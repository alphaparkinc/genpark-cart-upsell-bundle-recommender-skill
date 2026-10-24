import sys, json
from client import CartUpsellBundleRecommenderClient
sys.stdout.reconfigure(encoding='utf-8')

def handle_mcp():
    client = CartUpsellBundleRecommenderClient()
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print(json.dumps({"status": "ready", "skill": "genpark-cart-upsell-bundle-recommender-skill"}))
        return
    req = json.loads(sys.stdin.read() or "{}")
    cart = req.get("cart_items", ["PROD-PHONE"])
    res = client.generate_bundle_recommendations(cart)
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    handle_mcp()
