from flask import Flask, jsonify, request
from flask_cors import CORS

from network.ping_sweep import ping_sweep, PingSweepError

app = Flask(__name__)
CORS(app)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "service": "Flask Security Service", "message": "Flask is alive and responding!"})


@app.route("/ping-sweep", methods=["POST"])
def ping_sweep_route():
    if not request.is_json:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Request body must be JSON."
            }
        }), 400

    data = request.get_json(silent=True)

    if data is None:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "Request body must be valid JSON."
            }
        }), 400

    start_ip = data.get("start_ip")
    end_ip = data.get("end_ip")
    timeout = data.get("timeout")

    if not start_ip or not end_ip:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "start_ip and end_ip are required."
            }
        }), 400

    if timeout is None or isinstance(timeout, bool) or not isinstance(timeout, (int, float)):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": "timeout is required and must be a number."
            }
        }), 400

    try:
        results = ping_sweep(start_ip, end_ip, timeout)

    except PingSweepError as e:
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_INPUT",
                "message": str(e)
            }
        }), 400

    except Exception as e:
        app.logger.error(f"Unexpected error in /ping-sweep: {e}")
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred. Please try again."
            }
        }), 500

    return jsonify({
        "success": True,
        "data": {
            "results": results
        }
    }), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)