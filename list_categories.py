import os, requests
from dotenv import load_dotenv
load_dotenv('/home/noah/elabftw-opencloning-sync/.env')
token = os.environ.get('ELABFTW_TOKEN')
url = os.environ.get('API_URL', 'https://eln.changebio.uk/api/v2').rstrip('/')
resp = requests.get(f'{url}/items_types', headers={'Authorization': token})
if resp.status_code == 200:
    print('Available Categories in eLabFTW:')
    for c in resp.json():
        print(f"- '{c['title']}' (ID: {c['id']})")
else:
    print(f'Error: {resp.status_code} {resp.text}')
