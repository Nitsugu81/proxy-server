import requests

# Configuration du proxy SOCKS5
proxy_host = '127.0.0.1'
proxy_port = 3000
proxy_username = 'Augustin'
proxy_password = '1208'

# URL cible pour la requête
target_urls = ['http://httpbin.org/get', 'http://httpbin.org/get']

# Configuration du proxy dans la requête
proxies = {
    'http': f'socks5h://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}',
    'https': f'socks5h://{proxy_username}:{proxy_password}@{proxy_host}:{proxy_port}'
}


i = 1
# Effectuer la requête via le proxy SOCKS5
for target_url in target_urls :
    print("* answer for request ", i," :")
    response = requests.get(target_url, proxies=proxies)
    # Afficher la réponse
    print(response.text)
    i+=1
