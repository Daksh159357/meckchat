import json
import base64
import uuid
import paho.mqtt.client as mqtt
import hashlib
import socks

class NetworkManager:
    def __init__(self, crypto_manager, message_callback, discovery_callback):
        self.crypto_manager = crypto_manager
        self.message_callback = message_callback
        self.discovery_callback = discovery_callback
        
        # Using a public free MQTT broker for global rendezvous
        self.broker = "broker.hivemq.com"
        self.port = 1883
        
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=f"dc_{uuid.uuid4().hex[:8]}")
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        self.topic = ""
        self.connected = False

    def start(self, use_tor=False):
        try:
            if use_tor:
                print("Configuring MQTT to route via Tor (127.0.0.1:9050)...")
                self.client.proxy_set(proxy_type=socks.SOCKS5, proxy_addr="127.0.0.1", proxy_port=9050)
                
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_start()
        except Exception as e:
            print(f"MQTT Connect error: {e}")

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if reason_code == 0:
            self.connected = True
            print("Connected to Global Relay.")
        else:
            print(f"Failed to connect, return code {reason_code}")

    def join_room(self, passphrase):
        if self.topic:
            self.client.unsubscribe(self.topic)
            
        # Hash passphrase to prevent accidental collisions with other apps using same broker
        room_hash = hashlib.sha256(passphrase.encode('utf-8')).hexdigest()[:16]
        self.topic = f"decentrachat/room/{room_hash}"
        self.client.subscribe(self.topic)
        print(f"Joined room: {self.topic}")
        
        # Broadcast discovery so peer knows our pubkey
        discovery_pkt = {
            'type': 'discovery',
            'sender_id': self.crypto_manager.get_my_id()
        }
        self.client.publish(self.topic, json.dumps(discovery_pkt))

    def _on_message(self, client, userdata, msg):
        try:
            packet = json.loads(msg.payload.decode('utf-8'))
            p_type = packet.get('type')
            sender_id = packet.get('sender_id')
            
            # Ignore our own messages
            if sender_id == self.crypto_manager.get_my_id():
                return
                
            if p_type == 'discovery':
                # Peer is announcing themselves.
                self.discovery_callback(sender_id)
                # Reply to them
                reply_pkt = {
                    'type': 'discovery_reply',
                    'sender_id': self.crypto_manager.get_my_id()
                }
                self.client.publish(self.topic, json.dumps(reply_pkt))
                return
                
            elif p_type == 'discovery_reply':
                # Peer replied to our announcement
                self.discovery_callback(sender_id)
                return
                
            # Otherwise it's an encrypted message
            encrypted_data_b64 = packet.get('encrypted_data')
            if not encrypted_data_b64:
                return

            encrypted_data = base64.b64decode(encrypted_data_b64)
            sender_pub_key_bytes = sender_id.encode('utf-8')
            
            decrypted_bytes = self.crypto_manager.decrypt_message(encrypted_data, sender_pub_key_bytes)
            payload = json.loads(decrypted_bytes.decode('utf-8'))
            
            self.message_callback(sender_id, payload)
        except Exception as e:
            pass

    def send_payload(self, recipient_id, payload_dict):
        if not self.topic:
            return False
            
        try:
            decrypted_bytes = json.dumps(payload_dict).encode('utf-8')
            recipient_pub_key_bytes = recipient_id.encode('utf-8')
            
            encrypted_data = self.crypto_manager.encrypt_message(decrypted_bytes, recipient_pub_key_bytes)
            
            packet = {
                'sender_id': self.crypto_manager.get_my_id(),
                'encrypted_data': base64.b64encode(encrypted_data).decode('utf-8')
            }
            
            self.client.publish(self.topic, json.dumps(packet))
            return True
        except Exception as e:
            print(f"Error sending payload: {e}")
            return False

    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()
