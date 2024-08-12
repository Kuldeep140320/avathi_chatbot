import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

workers = 1
bind = "unix:/var/www/html/chatbot/chatbot.sock"
forwarded_allow_ips = '*'
secure_scheme_headers = {'X-Forwarded-Proto': 'http'}
