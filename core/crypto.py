

import nacl.utils
from nacl.public import PrivateKey, Box, PublicKey
from nacl.secret import SecretBox
from nacl.encoding import Base64Encoder

class CryptoManager:
    def __init__(self):
        # Keys will be generated explicitly
        self.private_key = None
        self.public_key = None

    def generate_keys(self):
        self.private_key = PrivateKey.generate()
        self.public_key = self.private_key.public_key

    def get_public_key_bytes(self) -> bytes:
        if self.public_key is None:
            return None
        return self.public_key.encode(encoder=Base64Encoder)

    def get_my_id(self) -> str:
        pk_bytes = self.get_public_key_bytes()
        if pk_bytes is None:
            return "Not Generated"
        return pk_bytes.decode('utf-8')

    def encrypt_message(self, message: bytes, recipient_public_key_bytes: bytes) -> bytes:
        recipient_key = PublicKey(recipient_public_key_bytes, encoder=Base64Encoder)
        box = Box(self.private_key, recipient_key)
        return box.encrypt(message)

    def decrypt_message(self, encrypted_message: bytes, sender_public_key_bytes: bytes) -> bytes:
        sender_key = PublicKey(sender_public_key_bytes, encoder=Base64Encoder)
        box = Box(self.private_key, sender_key)
        return box.decrypt(encrypted_message)

    @staticmethod
    def generate_group_key() -> bytes:
        return nacl.utils.random(nacl.secret.SecretBox.KEY_SIZE)

    @staticmethod
    def encrypt_group_message(message: bytes, group_key: bytes) -> bytes:
        box = SecretBox(group_key)
        return box.encrypt(message)

    @staticmethod
    def decrypt_group_message(encrypted_message: bytes, group_key: bytes) -> bytes:
        box = SecretBox(group_key)
        return box.decrypt(encrypted_message)
