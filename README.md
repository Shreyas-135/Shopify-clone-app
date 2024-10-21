# Shopify-clone-app
A Simple Streamlit/Flask Shopify App

This repo is forked from garettB/shopify-flask-example and adds a streamlit dashboard onto that flask Shopify App.

## What does this repo do?
This repo will create the server-side component for your Shopify app + the ability to pass a user to a streamlit dashboard for their shop and provide you some basic tools which you can build on to create a robust commercial application.

## Setup
Step 1: Get the App Running Locally
(this section is the same as garettB/shopify-flask-example)

## Install dependencies
1. Clone the repo
    sh 
      gh repo clone Shreyas-135/Shopify-clone-app
    
2. Install Python packages
    sh
      pip install -r requirements.txt
    
3. Run the application
    sh
      python3 flask/server.py
   
Leave this running. If new changes fail to appear, restart the server.

Set up ngrok by installing it and running it locally.
sh
  ngrok http 5001

Throughout the development process, ngrok should be running in the background. You will not need to restart this, as you will generate a new URL.

Set up your Shopify app, following these steps.

Create a local .env file by copying over the template
sh
  cp ./flask/.env.template ./flask/.env

Fill out your .env file using your Shopify API key and Shopify secret key. 
Replace your_server.hostname with your ngrok base URL.
Do not put quotations around the values.

Install the app onto a Shopify test store by following these steps. If you do not have one, create one.

You should be redirected to the admin dashboard of your test store. The url should be formatted as follows
sh
  https://{{store_name}}.myshopify.com/admin/apps/{{app_name}}/app_launched

Step 2: Get the App Running On Heroku
sh
  Install the heroku command line: https://devcenter.heroku.com/categories/command-line
sh
  # Create a remote heroku repo
  heroku git:remote -a shopify-streamlit
  # Launch a free tier dyno
  heroku ps:scale web=1
  # Push your local main branch up to heroku
  git push heroku main
  # Or push a specific branch
  git push heroku new/connecting_w_streamlit_dyno:main
  # Add all your .env variables as environmental variables in heroku:
  heroku config:set SHOPIFY_API_KEY=<your_api_key>
  # repeating for the rest of the .env variables
  Step 3: Get your Streamlit Dashboard Running on Heroku
  https://github.com/Shreyas-135/Shopify-clone-app
sh

Once it's up and running be sure to add the url to that dashboard into your environmental variables for this app

# example:
heroku config:set DASHBOARD_REDIRECT_URL=https://shoplit-dash.herokuapp.com
Step 4: Get your DB setup and start retrieving order data
Add a free postgres database onto this application through the heroku add-ons options.

Warning: to actually productionize this data storage we recommend using a more robust approach (ex: a cron job that runs once a day) and you'll need to setup the ability to delete the data once you've retrieved it (see the data_removal_request function in server.py).

Set your db parameters as environmental variables in heroku

heroku config:set DB_HOST=db_host
heroku config:set DB=db_name
heroku config:set DB_USER=db_user_name
heroku config:set DB_PWD=db_password

# port is assumed to be 5432
Once setting your db parameters, you'll start downloading the store's order data.

Understanding Each Component
For more details on each component see here: https://github.com/garettB/shopify-flask-example#serverpy

The only changes we make to these components are:

Rather than showing the index page for shops that have successfully installed the app, we redirect them to the streamlit dashboard.
We add a dash_auth function which uses Cryptographic nonce to authenticate the user on the streamlit dashboard.
Warning: it's recommended to consult a security expert on the security risks around this redirect approach using nonce before deploying this into a production environment.
