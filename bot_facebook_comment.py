import sys
import re
import requests


def extract_object_id(target: str) -> str:
    """Extract Facebook object ID from a URL or return the target if it's already an ID."""
    if target.startswith('http'):
        matches = re.findall(r"\d+", target)
        if matches:
            return matches[-1]
        else:
            raise ValueError(f"Unable to extract object ID from URL: {target}")
    else:
        return target.strip()


def run_facebook_comment(target: str, comment_text: str, token: str, device_id: str = "all"):
    """Send a COMMENT request to the Facebook Graph API.

    Parameters:
        target (str): URL or post ID to comment on.
        comment_text (str): The comment text content.
        token (str): User or Page access token with appropriate permissions.
        device_id (str): Placeholder for compatibility.
    """
    try:
        object_id = extract_object_id(target)
        url = f"https://graph.facebook.com/v17.0/{object_id}/comments"
        payload = {
            "message": comment_text,
            "access_token": token
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            print("[SUCCESS] Comment posted successfully.")
            print("Response:", response.json())
            sys.exit(0)
        else:
            print("[ERROR] Failed to post comment.")
            print("Status:", response.status_code, "Response:", response.text)
            sys.exit(1)
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Expected argv order: script, target, comment_text, token, device_id (optional)
    if len(sys.argv) < 4:
        print("Usage: python bot_facebook_comment.py <target> <comment_text> <token> [device_id]")
        sys.exit(1)
    target = sys.argv[1]
    comment_text = sys.argv[2]
    token = sys.argv[3]
    device_id = sys.argv[4] if len(sys.argv) > 4 else "all"
    run_facebook_comment(target, comment_text, token, device_id)
