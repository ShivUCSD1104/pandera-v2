import sys
import os
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS

IVSURFACE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, IVSURFACE_PATH)

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
        elif graph_type == 'GreeksLandscape':
            from GreeksLandscape.main import generate_greeks_landscape_html
            option_type = parameters.get('Option Type')  # 'call', 'put', or None for both
            logger.info(f"Generating Greeks Landscape for ticker: {parameters.get('Ticker', 'AAPL')}, view: {parameters.get('Greeks View', 'All')}, option_type: {option_type}")
            fig_json = generate_greeks_landscape_html(
                parameters.get('Ticker', 'AAPL'),
                parameters.get('Greeks View', 'All'),
                parameters.get('Start Date'),
                parameters.get('End Date'),
                option_type
            )
            
            # Handle Greeks Landscape specific errors
            if isinstance(fig_json, dict) and "error" in fig_json:
                error_type = fig_json.get("type", "unknown_error")
                error_message = fig_json.get("error", "Unknown error occurred")
                logger.error(f"Greeks Landscape Error ({error_type}): {error_message}")
                
                if error_type in ["data_error", "generation_error"]:
                    return jsonify({"error": error_message}), 404
                else:
                    return jsonify({"error": error_message}), 500
            
            logger.info(f"Successfully generated Greeks Landscape for {parameters.get('Ticker', 'AAPL')}")
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
