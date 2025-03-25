import sys
import os
from flask import Flask, request, jsonify
from flask_cors import CORS

IVSURFACE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, IVSURFACE_PATH)

app = Flask(__name__)
CORS(app)

@app.route('/compute', methods=['POST'])
def compute():
    try:
        data = request.json
        print("✅ Received Data:", data)  # Debugging line
        if not data:
            print("❌ Missing request body")
            return jsonify({"error": "Missing request body"}), 400

        parameters = data.get('parameters', {})
        graph_type = data.get('graphType')

        print("✅ Graph Type:", graph_type)  # Debugging line
        print("✅ Parameters:", parameters)  # Debugging line

        if graph_type == 'IVMap':
            from IVSurface.IVmap import generate_iv_surface_html
            print("✅ Generating IV Surface") 
            fig_json = generate_iv_surface_html(
                parameters.get('Ticker', 'AAPL'),
                parameters.get('Start Date'),
                parameters.get('End Date')
            )
        elif graph_type == 'OrderFlowCanyon':
            from OrderFlowCanyon.main import generate_order_flow_html
            fig_json = generate_order_flow_html(
                parameters.get('Ticker', 'AAPL'),
                parameters.get('Start Date'),
                parameters.get('End Date')
            )
        elif graph_type == 'USFixedIncomeYield':
            from YieldCurve.main import generate_yield_curve_html
            fig_json = generate_yield_curve_html(
                parameters.get('Issuer', 'US Treasury'),
                parameters.get('Start Date'),
                parameters.get('End Date')
            )
        else:
            print("❌ Invalid graph type")
            return jsonify({"error": "Invalid graph type"}), 400

        return jsonify({"plotly_json": fig_json})

    except Exception as e:
        print("🔥 Internal Server Error:", str(e))  # Debugging line
        return jsonify({"error": "Internal Server Error", "details": str(e)}), 500


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))  # Use Railway's assigned port
    app.run(host="0.0.0.0", port=port)  # Bind to all interfaces
