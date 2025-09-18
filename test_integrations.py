import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'stubs')))

import pytest
from blockchain import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_get_ad_accounts(client, mocker):
    # Mock the FacebookAdsApi
    mocker.patch(
        'facebook_integration.FacebookAdsApi.init',
        return_value=None
    )
    mock_ad_account_class = mocker.patch(
        'facebook_integration.AdAccount'
    )

    # Mock the Field.name attribute
    mock_ad_account_class.Field.name = 'name'

    # Create a mock instance of AdAccount
    mock_ad_account_instance = mocker.Mock()

    # Mock the get_ad_accounts method on the instance
    mock_ad_account_instance.get_ad_accounts.return_value = [
        {'name': 'Test Ad Account 1'},
        {'name': 'Test Ad Account 2'},
    ]

    # Make the AdAccount class return our mock instance
    mock_ad_account_class.return_value = mock_ad_account_instance

    response = client.get('/facebook/adaccounts')
    assert response.status_code == 200
    assert response.json == ['Test Ad Account 1', 'Test Ad Account 2']

def test_get_account_info(client, mocker):
    # Mock the MetaTrader5 library
    mock_mt5 = mocker.patch('mql5_integration.mt5')
    mock_mt5.initialize.return_value = True
    mock_mt5.account_info.return_value._asdict.return_value = {
        'login': 12345,
        'balance': 10000.0,
    }

    response = client.get('/mql5/account_info')
    assert response.status_code == 200
    assert response.json == {
        'login': 12345,
        'balance': 10000.0,
    }
