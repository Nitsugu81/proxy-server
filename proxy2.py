import socket
import threading
import select

# Définition de la version SOCKS utilisée
SOCKS_VERSION = 5

class Proxy:
    def __init__(self):
        self.username = "Augustin"  # Nom d'utilisateur pour l'authentification
        self.password = "1208"       # Mot de passe pour l'authentification
        self.blocked_urls = []
        self.lock = threading.Lock()  # Verrou pour la modification sécurisée de la liste d'adresses bloquées

    # Méthode pour gérer chaque client connecté
    def handle_client(self, connection):
        # En-tête de salutation
        version, nmethods = connection.recv(2)

        # Obtenir les méthodes disponibles [0, 1, 2]
        methods = self.get_available_methods(nmethods, connection)

        # Accepter uniquement l'authentification USERNAME/PASSWORD
        if 2 not in set(methods):
            connection.close()
            return
        
        

        # Envoyer un message de bienvenue
        connection.sendall(bytes([SOCKS_VERSION, 2]))

        # Vérifier les informations d'identification
        if not self.verify_credentials(connection):
            return

        # Traitement de la demande (version=5)
        version, cmd, _, address_type = connection.recv(4)

        if address_type == 1:  # IPv4
            address = socket.inet_ntoa(connection.recv(4))
        elif address_type == 3:  # Nom de domaine
            domain_length = connection.recv(1)[0]
            address = connection.recv(domain_length)
            address = socket.gethostbyname(address)
        

        port = int.from_bytes(connection.recv(2), 'big', signed=False)

        try:
            if cmd == 1:  # CONNECT
                remote = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                remote.connect((address, port))
                bind_address = remote.getsockname()
                print("* Connecté à {} {}".format(address, port))
            else:
                connection.close()

            addr = int.from_bytes(socket.inet_aton(bind_address[0]), 'big', signed=False)
            port = bind_address[1]

            reply = b''.join([
                SOCKS_VERSION.to_bytes(1, 'big'),
                int(0).to_bytes(1, 'big'),
                int(0).to_bytes(1, 'big'),
                int(1).to_bytes(1, 'big'),
                addr.to_bytes(4, 'big'),
                port.to_bytes(2, 'big')
            ])
        except Exception as e:
            # Retourner une erreur de connexion refusée
            reply = self.generate_failed_reply(address_type, 5)

        connection.sendall(reply)

        # Établir l'échange de données
        if reply[1] == 0 and cmd == 1:
            self.exchange_loop(connection, remote)

        connection.close()

    # Boucle d'échange de données entre le client et le serveur distant
    def exchange_loop(self, client, remote):
        while True:
            r, w, e = select.select([client, remote], [], [])

            if client in r:
                data = client.recv(4096)
                if remote.send(data) <= 0:
                    break

            if remote in r:
                data = remote.recv(4096)
                if client.send(data) <= 0:
                    break

    # Générer une réponse de connexion échouée
    def generate_failed_reply(self, address_type, error_number):
        return b''.join([
            SOCKS_VERSION.to_bytes(1, 'big'),
            error_number.to_bytes(1, 'big'),
            int(0).to_bytes(1, 'big'),
            address_type.to_bytes(1, 'big'),
            int(0).to_bytes(4, 'big'),
            int(0).to_bytes(4, 'big')
        ])

    # Vérifier les informations d'identification de l'utilisateur
    def verify_credentials(self, connection):
        version = ord(connection.recv(1)) # Devrait être 1

        # Réception et décodage du mdp et de l'username
        username_len = ord(connection.recv(1))
        username = connection.recv(username_len).decode('utf-8')

        password_len = ord(connection.recv(1))
        password = connection.recv(password_len).decode('utf-8')

        if username == self.username and password == self.password:
            response = bytes([version, 0])  # Succès, status = 0
            connection.sendall(response)
            return True

        response = bytes([version, 0xFF])  # Échec, status != 0
        connection.sendall(response)
        connection.close()
        return False

    # Obtenir les méthodes disponibles
    def get_available_methods(self, nmethods, connection):
        methods = []
        for i in range(nmethods):
            methods.append(ord(connection.recv(1)))
        return methods
    
    # Vérifier si l'URL est bloquée
    def is_blocked(self, url):
        for blocked_url in self.blocked_urls:
            if blocked_url in url:
                return True
        return False

    # Méthode pour exécuter le proxy
    def run(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((host, port))
        s.listen()

        print("* Serveur proxy SOCKS5 en cours d'exécution sur {}:{}".format(host, port))
        print("*Liste des commandes")
        print("* -q = pour fermer le terminal")
        print("* -b 'IPadresse' = bloque une adresse IP")
        print("* -u 'IPadresse' = débloque une adresse IP")
        # Thread pour gérer les entrées utilisateur
        threading.Thread(target=self.user_input_thread).start()

        while True:
            conn, addr = s.accept()
            print("* Nouvelle connexion de {}".format(addr))
            if self.is_blocked(addr):
                print("* Votre adresse est fait partie des adresses bloquées")
                conn.close()
                continue
            else :
                t = threading.Thread(target=self.handle_client, args=(conn,))
                t.start()


    def user_input_thread(self):
        while True:
            user_input = input()
            if user_input.lower() == '-q':
                return
            elif '-b' in user_input:
                with self.lock:
                    user_input_split = user_input.split(" ")
                    self.blocked_urls.append(user_input_split[1])
                    print("* Adresse ajoutée à la liste des adresses bloquées.")
            elif '-u' in user_input:
                with self.lock:
                    user_input_split = user_input.split(" ")
                    if user_input_split[1] in self.blocked_urls:
                        self.blocked_urls.remove(user_input_split[1])
                        print("* Adresse retirée de la liste des adresses bloquées.")
                    else:
                        print("* L'adresse spécifiée n'est pas dans la liste des adresses bloquées.")
            else:
                print("* Commande inconnue")



    
    
# Exécution du proxy
if __name__ == "__main__":
    proxy = Proxy()
    proxy.run("127.0.0.1", 3000)
