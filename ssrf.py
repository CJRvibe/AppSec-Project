from flask import Blueprint, request, jsonify
from safe_requests import safe_fetch

ssrf = Blueprint("ssrf", __name__)

@ssrf.route("/fetch-url")
def fetch_url():
    url = request.args.get("url", "")
    try:
        content = safe_fetch(url)
        # Return text if you expect text; here we keep bytes to be generic.
        return content, 200, {"Content-Type": "text/plain; charset=utf-8"}
    except Exception as e:
        return jsonify({"error": str(e)}), 400
