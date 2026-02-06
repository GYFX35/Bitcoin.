from flask import Blueprint, jsonify
try:
    from facebook_business.api import FacebookAdsApi
    from facebook_business.adobjects.adaccount import AdAccount
    facebook_available = True
except ImportError:
    facebook_available = False

facebook_blueprint = Blueprint('facebook', __name__)

# Replace with your own credentials
APP_ID = 'YOUR_APP_ID'
APP_SECRET = 'YOUR_APP_SECRET'
ACCESS_TOKEN = 'YOUR_ACCESS_TOKEN'

if facebook_available:
    try:
        FacebookAdsApi.init(APP_ID, APP_SECRET, ACCESS_TOKEN)
    except Exception:
        facebook_available = False

@facebook_blueprint.route('/facebook/adaccounts', methods=['GET'])
def get_ad_accounts():
    if not facebook_available:
         return jsonify({'error': 'Facebook API not available or not initialized'}), 501
    try:
        me = AdAccount('me')
        ad_accounts = me.get_ad_accounts(fields=[AdAccount.Field.name])

        return jsonify([acc[AdAccount.Field.name] for acc in ad_accounts])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
