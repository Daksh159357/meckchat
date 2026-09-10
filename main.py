import sys
from PyQt5.QtWidgets import QApplication
from core.crypto import CryptoManager
from core.network import NetworkManager
from ui.ui import ChatUI

def main():
    # Initialize PyNaCl Crypto Manager
    crypto = CryptoManager()
    
    # Initialize PyQt5 App
    app = QApplication(sys.argv)
    
    # Create UI
    ui = ChatUI(crypto, None)
    
    # Networking Callbacks
    def on_message(sender_id, payload):
        ui.message_received_signal.emit(sender_id, payload)
        
    def on_discovery(sender_id):
        ui.peer_discovered_signal.emit(sender_id)
        
    # Initialize Network Manager
    net = NetworkManager(crypto, on_message, on_discovery)
    ui.net = net
    print(f"MeckChat Global initialized.")
    
    # Show UI
    ui.ask_for_profile()
    ui.show()
    
    # Run App
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
