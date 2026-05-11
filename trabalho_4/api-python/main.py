import json
import os

import redis
from flask import Flask, jsonify, request

from linkextractor import extract_links

app = Flask(__name__)

USE_CACHE = os.getenv("USE_CACHE", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL")

redis_client = redis.from_url(REDIS_URL) if USE_CACHE and REDIS_URL else None


@app.get("/api/")
def api():
    url = request.args.get("url")

    if not url:
        return jsonify({"error": "Parâmetro 'url' é obrigatório."}), 400

    cache_key = f"links:{url}"

    if redis_client:
        cached_value = redis_client.get(cache_key)

        if cached_value:
            return jsonify({
                "url": url,
                "links": json.loads(cached_value),
                "cached": True,
                "service": "python"
            })

    try:
        links = extract_links(url)

        if redis_client:
            redis_client.set(cache_key, json.dumps(links), ex=3600)

        return jsonify({
            "url": url,
            "links": links,
            "cached": False,
            "service": "python"
        })

    except Exception as error:
        return jsonify({
            "url": url,
            "error": str(error),
            "service": "python"
        }), 500


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "python"})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)