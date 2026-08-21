import sys
import re
import requests


def extract_object_id(target: str) -> str:
    """Extract Facebook object ID from a URL or return the target if it's already an ID."""
    # Facebook post URLs can be in several formats, e.g.:
    # https://www.facebook.com/{page_or_user}/posts/{post_id}
    # https://www.facebook.com/permalink.php?story_fbid={post_id}&id={page_id}
    # https://facebook.com/{page_or_user}/videos/{video_id}/
    # We'll try to extract the numeric ID.
    if target.startswith('http'):
        # Find numeric sequences in the URL
        matches = re.findall(r"\d+", target)
        if matches:
            # Heuristic: the last numeric component is often the post ID
            return matches[-1]
        else:
            raise ValueError(f"Unable to extract object ID from URL: {target}")
    else:
        # Assume target is already an ID
        return target.strip()


def run_facebook_like(page_id: str, target: str, token: str, device_id: str = "all"):
    """Send a LIKE request to the Facebook Graph API.

    Parameters:
        page_id (str): Optional Page ID; not required for the Graph call but kept for consistency.
        target (str): URL or post ID to like.
        token (str): User or Page access token with appropriate permissions.
        device_id (str): Placeholder for compatibility with existing queue worker; not used.
    """
    try:
        object_id = extract_object_id(target)
        url = f"https://graph.facebook.com/v17.0/{object_id}/likes"
        payload = {"access_token": token}
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("[SUCCESS] Facebook post liked successfully.")
            print("Response:", response.json())
            sys.exit(0)
        else:
            print("[ERROR] Failed to like the post.")
            print("Status:", response.status_code, "Response:", response.text)
            sys.exit(1)
    except Exception as e:
        print(f"[EXCEPTION] {{e}}"); sys.exit(1)


if __name__ == "__main__":
    # Expected argv order: script, page_id, target, token, device_id (optional)
    if len(sys.argv) < 4:
        print("Usage: python bot_facebook_like.py <page_id> <target> <token> [device_id]")
        sys.exit(1)
    page_id = sys.argv[1]
    target = sys.argv[2]
    token = sys.argv[3]
    device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
    run_facebook_like(page_id, target, token, device_id)
