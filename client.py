import socket

def send_http_request():
    # Adresse et port du serveur proxy
    proxy_ip = '127.0.0.1'
    proxy_port = 8080

    # Créer une socket TCP/IP
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Se connecter au serveur proxy
    client_socket.connect((proxy_ip, proxy_port))

    # Construire une requête HTTP GET
    request = b"GET / HTTP/1.1\r\nHost: www.example.com\r\n\r\n"

    # Envoyer la requête au serveur proxy
    client_socket.send(request)

    # Recevoir la réponse du serveur proxy
    response = client_socket.recv(4096)

    print("[*] Received response:")
    print(response.decode())

    # Fermer la connexion
    client_socket.close()

if __name__ == "__main__":
    send_http_request()
