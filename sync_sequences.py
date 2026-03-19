#!/usr/bin/env python3
import os
import sys
import json
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_URL = os.environ.get("API_URL", "https://eln.yourdomain.com/api/v2").rstrip('/')
API_TOKEN = os.environ.get("ELABFTW_TOKEN")
CATEGORY_NAMES_STR = os.environ.get("CATEGORY_NAMES", "")
SYNTAX_CATEGORY_NAMES_STR = os.environ.get("SYNTAX_CATEGORY_NAMES", "")
STATIC_DIR = os.environ.get("STATIC_DIR", "/path/to/opencloning/static_content")

if not API_TOKEN:
    print("Error: ELABFTW_TOKEN is not set in .env")
    sys.exit(1)

CATEGORY_NAMES = [name.strip() for name in CATEGORY_NAMES_STR.split(",") if name.strip()]
SYNTAX_CATEGORY_NAMES = [name.strip() for name in SYNTAX_CATEGORY_NAMES_STR.split(",") if name.strip()]

HEADERS = {
    "Authorization": API_TOKEN,
    "Accept": "application/json"
}

def api_get(endpoint):
    response = requests.get(f"{API_URL}{endpoint}", headers=HEADERS)
    response.raise_for_status()
    return response.json()



def download_file(endpoint, filepath):
    response = requests.get(f"{API_URL}{endpoint}", headers=HEADERS, stream=True)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def sync_category_items(target_categories, sub_dir_name, valid_extensions):
    sub_dir = os.path.join(STATIC_DIR, sub_dir_name)
    os.makedirs(sub_dir, exist_ok=True)
    
    metadata_list = []
    valid_files = set()
    
    for cat_id, cat_name in target_categories:
        print(f"\nFetching items for '{cat_name}' (ID: {cat_id}) into '{sub_dir_name}/'")

        try:
            items = api_get(f"/items?cat={cat_id}&limit=1000")
        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch items for category {cat_name}: {e}")
            continue

        for item in items:
            item_id = item['id']
            item_title = item['title']

            try:
                uploads = api_get(f"/items/{item_id}/uploads")
            except requests.exceptions.RequestException:
                continue
            
            # Sort uploads by ID descending (newest first)
            uploads = sorted(uploads, key=lambda x: x['id'], reverse=True)

            for upload in uploads:
                real_name = upload['real_name'].lower()
                if real_name.endswith(valid_extensions):
                    file_id = upload['id']
                    _, ext = os.path.splitext(real_name)
                    
                    filename = f"item_{item_id}_file_{file_id}{ext}"
                    filepath = os.path.join(sub_dir, filename)

                    valid_files.add(filename)

                    if not os.path.exists(filepath):
                        print(f"  -> Downloading updated/new file for '{item_title}'...")
                        try:
                            download_file(f"/items/{item_id}/uploads/{file_id}?format=binary", filepath)
                            
                        except requests.exceptions.RequestException as e:
                            print(f"  -> Error downloading file: {e}")
                            valid_files.remove(filename)

                    # Ensure unique names
                    base_name = item_title
                    counter = 1
                    while any(m['name'] == item_title for m in metadata_list):
                        item_title = f"{base_name} ({counter})"
                        counter += 1

                    # For syntaxes, we omit "categories" as OpenCloning usually doesn't need them
                    metadata = {
                        "name": item_title,
                        "path": f"{sub_dir_name}/{filename}"
                    }
                    if sub_dir_name == "sequences":
                        metadata["categories"] = [cat_name]
                        
                    metadata_list.append(metadata)
                    break

    print(f"\nCleaning up old/deleted files in {sub_dir_name}/...")
    for existing_file in os.listdir(sub_dir):
        if existing_file not in valid_files:
            print(f"  -> Removing outdated file: {existing_file}")
            os.remove(os.path.join(sub_dir, existing_file))
            
    return metadata_list

def main():
    print("Fetching categories from eLabFTW...")
    try:
        categories = api_get("/teams/current/resources_categories")
    except Exception as e:
        print(f"Error: Could not fetch categories from eLabFTW: {e}")
        sys.exit(1)

    cat_name_to_id = {cat['title']: cat['id'] for cat in categories}
    
    # Resolve sequence categories
    seq_targets = []
    for name in CATEGORY_NAMES:
        if name in cat_name_to_id:
            seq_targets.append((cat_name_to_id[name], name))
        else:
            print(f"Warning: Sequence Category '{name}' not found.")

    # Resolve syntax categories
    syn_targets = []
    for name in SYNTAX_CATEGORY_NAMES:
        if name in cat_name_to_id:
            syn_targets.append((cat_name_to_id[name], name))
        else:
            print(f"Warning: Syntax Category '{name}' not found.")

    # 1. Sync Sequences
    sequences_metadata = []
    if seq_targets:
        sequences_metadata = sync_category_items(seq_targets, "sequences", ('.gb', '.gbk'))

    # 2. Sync Syntaxes
    syntaxes_metadata = []
    if syn_targets:
        syntaxes_metadata = sync_category_items(syn_targets, "syntaxes", ('.json',))

    # --- UPDATE INDEX.JSON ---
    print("\nUpdating index.json...")
    index_path = os.path.join(STATIC_DIR, "index.json")
    index_data = {"sequences": [], "syntaxes": []}

    # Overwrite completely with our synced state
    index_data["sequences"] = sequences_metadata
    index_data["syntaxes"] = syntaxes_metadata

    with open(index_path, 'w') as f:
        json.dump(index_data, f, indent=4)

    print(f"\nDone! Synced {len(sequences_metadata)} sequences and {len(syntaxes_metadata)} syntaxes.")

if __name__ == "__main__":
    main()