from pycognito import Cognito
from utils import readConfig


def get_u_p(input_email):
# get "nickname" from Cognito
    config = readConfig()
    cognito_session_config = config['cognito']

    client = Cognito(cognito_session_config['USER_POOL_ID'],
                     cognito_session_config['CLIENT_ID'])

    users = client.get_users(attr_map={"email": "email", 
                              "nickname":"nickname"})
    for user in users:
        if user.email==input_email:
            return (user.email, user.nickname)
