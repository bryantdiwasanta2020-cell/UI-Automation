import sys
import requests


def run_facebook_post(page_id: str, post_type: str, message: str, link_url: str, token: str, device_id: str = "all"):
    """Publish a post (status, link, or photo) to Facebook Graph API.

    Parameters:
        page_id (str): Page ID or 'me' for user profile feed.
        post_type (str): 'status', 'link', or 'photo'.
        message (str): Message or caption.
        link_url (str): Link URL or media URL (optional).
        token (str): Page or User access token.
        device_id (str): Placeholder for compatibility.
    """
    try:
        if not page_id:
            page_id = "me"
        
        payload = {
            "access_token": token
        }

        if post_type == "photo" and link_url:
            url = f"https://graph.facebook.com/v17.0/{page_id}/photos"
            payload["url"] = link_url
            payload["caption"] = message
        else:
            url = f"https://graph.facebook.com/v17.0/{page_id}/feed"
            payload["message"] = message
            if post_type == "link" and link_url:
                payload["link"] = link_url

        response = requests.post(url, data=payload)
        if response.status_code == 200 or response.status_code == 201:
            print("[SUCCESS] Facebook post published successfully.")
            print("Response:", response.json())
            sys.exit(0)
        else:
            print("[ERROR] Failed to publish Facebook post.")
            print("Status:", response.status_code, "Response:", response.text)
            sys.exit(1)
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Expected argv order: script, page_id, post_type, message, link_url, token, device_id (optional)
    if len(sys.argv) < 6:
        print("Usage: python bot_facebook_post.py <page_id> <post_type> <message> <link_url> <token> [device_id]")
        sys.exit(1)
    
    page_id = sys.argv[1]
    post_type = sys.argv[2]
    message = sys.argv[3]
    link_url = sys.argv[4]
    token = sys.argv[5]
    device_id = sys.argv[6] if len(sys.argv) > 6 else "all"
    run_facebook_post(page_id, post_type, message, link_url, token, device_id)
