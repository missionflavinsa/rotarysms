import traceback
import sys
sys.path.append("/home/austinroyster/MEGA/Webapps/result management system")
from src.views.admin_results import process_profile_photo_original

def test():
    dummy_url = "https://www.w3schools.com/w3images/avatar2.png"
    try:
        res = process_profile_photo_original(dummy_url)
        print("Function returned:", type(res))
        
        # Test tuple unpack
        a, b = res
        print("Tuple unpacked successfully.")
        
    except Exception as e:
        print("EXCEPTION CAUGHT:")
        traceback.print_exc()

test()
