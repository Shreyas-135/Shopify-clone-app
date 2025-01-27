from dataclasses import replace
import uuid
import os
import json
import logging

from flask import Flask, redirect, request, render_template

import helpers
from shopify_client import ShopifyStoreClient

from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
WEBHOOK_APP_UNINSTALL_URL = os.environ.get('WEBHOOK_APP_UNINSTALL_URL')
if os.environ.get('DB_HOST') is not None:
    ENGINE_PATH = f"postgresql://{os.environ.get('DB_USER')}:{os.environ.get('DB_PWD')}@{os.environ.get('DB_HOST')}/{os.environ.get('DB')}"
    engine = create_engine(ENGINE_PATH)
    conn = engine.connect()
else:
    ENGINE_PATH = None
print('webhook', WEBHOOK_APP_UNINSTALL_URL)


app = Flask(__name__)

ACCESS_TOKEN = None
NONCE = None
ACCESS_MODE = []  # Defaults to offline access mode if left blank or omitted. https://shopify.dev/concepts/about-apis/authentication#api-access-modes
SCOPES = ['write_script_tags', 'read_orders']  # https://shopify.dev/docs/admin-api/access-scopes
# Note: read_orders is only orders in last 60 days, for full orders you need to request access in your app settings


@app.route('/app_launched', methods=['GET'])
@helpers.verify_web_call
def app_launched():
    shop = request.args.get('shop')
    global ACCESS_TOKEN, NONCE
    # The NONCE is a single-use random value we send to Shopify so we know the next call from Shopify is valid (see #app_installed)
    #   https://en.wikipedia.org/wiki/Cryptographic_nonce
    NONCE = uuid.uuid4().hex

    if ACCESS_TOKEN:
        redirect_url = helpers.generate_dash_redirect_url(shop=shop, nonce=NONCE)
        if ENGINE_PATH is not None: # => let's store the order data
            shopify_client = ShopifyStoreClient(shop=shop, access_token=ACCESS_TOKEN)
            order_df = helpers.get_all_orders(shopify_client)
            logging.info(f'order_df.head: \n{order_df.head()}')
            order_df.to_sql(name=f'orders_{shop.replace(".", "_")}', con=conn, if_exists='replace')
        return redirect(redirect_url, code=200)

    redirect_url = helpers.generate_install_redirect_url(shop=shop, scopes=SCOPES, nonce=NONCE, access_mode=ACCESS_MODE)
    return redirect(redirect_url, code=302)


@app.route('/app_installed', methods=['GET'])
@helpers.verify_web_call
def app_installed():
    state = request.args.get('state')
    global NONCE, ACCESS_TOKEN

    # Shopify passes our NONCE, created in #app_launched, as the `state` parameter, we need to ensure it matches!
    if state != NONCE:
        return "Invalid `state` received", 400
    NONCE = None

    # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
    # Using the `code` received from Shopify we can now generate an access token that is specific to the specified `shop` with the
    #   ACCESS_MODE and SCOPES we asked for in #app_installed
    shop = request.args.get('shop')
    code = request.args.get('code')
    ACCESS_TOKEN = ShopifyStoreClient.authenticate(shop=shop, code=code)

    # We have an access token! Now let's register a webhook so Shopify will notify us if/when the app gets uninstalled
    # NOTE This webhook will call the #app_uninstalled function defined below
    shopify_client = ShopifyStoreClient(shop=shop, access_token=ACCESS_TOKEN)
    shopify_client.create_webook(address=WEBHOOK_APP_UNINSTALL_URL, topic="app/uninstalled")

    redirect_url = helpers.generate_post_install_redirect_url(shop=shop)
    return redirect(redirect_url, code=302)


@app.route('/app_uninstalled', methods=['POST'])
@helpers.verify_webhook_call
def app_uninstalled():
    # https://shopify.dev/docs/admin-api/rest/reference/events/webhook?api[version]=2020-04
    # Someone uninstalled your app, clean up anything you need to
    # NOTE the shop ACCESS_TOKEN is now void!
    global ACCESS_TOKEN
    ACCESS_TOKEN = None

    webhook_topic = request.headers.get('X-Shopify-Topic')
    webhook_payload = request.get_json()
    logging.error(f"webhook call received {webhook_topic}:\n{json.dumps(webhook_payload, indent=4)}")

    return "OK"


@app.route('/data_removal_request', methods=['POST'])
@helpers.verify_webhook_call
def data_removal_request():
    # https://shopify.dev/tutorials/add-gdpr-webhooks-to-your-app
    # Clear all personal information you may have stored about the specified shop
    return "OK"


@app.route('/dash_auth', methods=['GET'])
def dash_auth():
    state = request.args.get('state')
    global NONCE, ACCESS_TOKEN

    # The Dash passes our NONCE, created in #app_launched, as the `state` parameter, we need to ensure it matches!
    if state != NONCE:
        logging.error('state and nonce not equal')
        logging.error(f'state: {state}')
        logging.error(f'nonce: {NONCE}')
        return "Invalid `state` received", 400

    if ACCESS_TOKEN:
        return "Success", 200 # success
    # Ok, NONCE matches, we can get rid of it now (a nonce, by definition, should only be used once)
    NONCE = None


if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5001.
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)
