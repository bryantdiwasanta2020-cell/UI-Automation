import uiautomator2 as u2
import json

def inspect():
    try:
        d = u2.connect("R9RY801Y0VF")
        print(f"Connected to device. Window size: {d.window_size()}")
        
        # Dump hierarchy
        xml = d.dump_hierarchy()
        
        print("\n--- Potensial Like Buttons/Icons ---")
        found = False
        
        # Find all elements
        for elem in d(resourceIdMatches=".*(?i)(like|suka).*"):
            try:
                info = elem.info
                print(json.dumps({
                    "resourceId": info.get("resourceId"),
                    "className": info.get("className"),
                    "text": info.get("text"),
                    "contentDescription": info.get("contentDescription"),
                    "bounds": info.get("bounds"),
                    "clickable": info.get("clickable")
                }, indent=2))
                found = True
            except Exception as e:
                pass
                
        for elem in d(descriptionMatches=".*(?i)(like|suka).*"):
            try:
                info = elem.info
                print(json.dumps({
                    "resourceId": info.get("resourceId"),
                    "className": info.get("className"),
                    "text": info.get("text"),
                    "contentDescription": info.get("contentDescription"),
                    "bounds": info.get("bounds"),
                    "clickable": info.get("clickable")
                }, indent=2))
                found = True
            except Exception as e:
                pass

        if not found:
            print("No like buttons found matching standard keywords.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect()
