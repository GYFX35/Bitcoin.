from flask import Blueprint, jsonify
import MetaTrader5 as mt5

mql5_blueprint = Blueprint('mql5', __name__)

@mql5_blueprint.route('/mql5/account_info', methods=['GET'])
def get_account_info():
    # establish connection to the MetaTrader 5 terminal
    if not mt5.initialize():
        return jsonify({"error": "initialize() failed, error code = " + str(mt5.last_error())}), 500

    # request connection status and parameters
    account_info = mt5.account_info()
    mt5.shutdown()

    if account_info is None:
        return jsonify({"error": "Failed to get account info"}), 500

    return jsonify(account_info._asdict())
