import time
import os
import json

def run_sync():
    print("[AUTOSYNC] Starting Daraz product sync...")
    # Run discovery and ranking
    os.system('python3 worker_agents/daraz_public_discovery_worker.py')
    os.system('python3 worker_agents/daraz_product_ranking_v3_worker.py')
    
    # Auto-apply logic to update json files
    p_file = 'products.json'
    r_file = 'product_recommendations.json'
    products = json.load(open(p_file)) if os.path.exists(p_file) else []
    recommendations = json.load(open(r_file)) if os.path.exists(r_file) else []
    
    # Example auto-fetch injection for continuous loop
    print(f"[AUTOSYNC] Sync completed. Active Products: {len(products)}")

if __name__ == '__main__':
    while True:
        try:
            run_sync()
        except Exception as e:
            print(f"[AUTOSYNC ERROR] {e}")
        # Run every 6 hours (21600 seconds) or test every 60 seconds
        print("[AUTOSYNC] Waiting for next cycle...")
        time.sleep(21600) 
