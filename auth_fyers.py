"""Generate a FYERS access token locally and save it to .env.
Never paste the token into chat. The .env file is ignored by git and excluded from the submission ZIP.
"""
from __future__ import annotations
import os,re
from pathlib import Path
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
ROOT=Path(__file__).resolve().parent; ENV_FILE=ROOT/'.env'; load_dotenv(ENV_FILE)
APP_ID=os.getenv('FYERS_APP_ID','');SECRET=os.getenv('FYERS_SECRET','');REDIRECT=os.getenv('FYERS_REDIRECT_URI','https://trade.fyers.in/api-login/redirect-uri/index.html')

def save_token(token:str):
    text=ENV_FILE.read_text(encoding='utf-8') if ENV_FILE.exists() else ''
    if 'FYERS_ACCESS_TOKEN=' in text:text=re.sub(r'^FYERS_ACCESS_TOKEN=.*$',f'FYERS_ACCESS_TOKEN={token}',text,flags=re.M)
    else:text += f'\nFYERS_ACCESS_TOKEN={token}\n'
    ENV_FILE.write_text(text,encoding='utf-8')
if __name__=='__main__':
    if not APP_ID or not SECRET: raise SystemExit('Set FYERS_APP_ID and FYERS_SECRET in .env first.')
    session=fyersModel.SessionModel(client_id=APP_ID,secret_key=SECRET,redirect_uri=REDIRECT,response_type='code',grant_type='authorization_code')
    print('\n1) Open this URL in your browser:\n');print(session.generate_authcode())
    print('\n2) After FYERS redirects you, copy ONLY the auth code from the URL and paste it below.')
    auth_code=input('Auth code: ').strip()
    session.set_token(auth_code); response=session.generate_token()
    if not isinstance(response,dict) or not response.get('access_token'):
        print('Token generation response did not contain access_token. Check the FYERS app redirect URI and auth code.');print(response);raise SystemExit(1)
    save_token(response['access_token']);print('\nSUCCESS: access token saved to local .env. Do not send the token to anyone.')
