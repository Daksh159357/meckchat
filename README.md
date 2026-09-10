# MeckChat (Global P2P)

MeckChat is a fully anonymous, peer-to-peer (P2P) chat application for Linux desktops. It allows real-time messaging without any central server, ensuring end-to-end encryption, read receipts, and typing indicators. MeckChat works globally over the internet using a secret passphrase, requiring no port forwarding or VPN.

## Features
- **Global Reach**: Connect from anywhere in the world using a simple passphrase.
- **Fully anonymous user IDs**: Automatic generation of unique key pairs (NaCl).
- **Global Rendezvous**: Powered by an MQTT relay for seamless NAT-traversing connectivity.
- **End-to-End Encryption**: Every message is encrypted with PyNaCl (libsodium) before leaving your machine.
- **Typing Indicators & Read Receipts**: Real-time feedback on your conversation.
- **Modern Linux Desktop UI**: Dark-themed, lightweight design built with PyQt5.

## Requirements
- Python 3.10+
- PyNaCl
- PyQt5
- paho-mqtt

## Setup and Run

### Running from source
1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
2. Start the application:
   ```bash
   python3 main.py
   ```

### Packaging as an Executable
You can package the app as a standalone executable using the included `build.sh` script (requires `pyinstaller`):
```bash
./build.sh
```
The executable will be located at `dist/MeckChat`.

## Using MeckChat
1. Start the application. Enter your display name and generate your identity.
2. Click **Join Secret Room**.
3. Enter a secret passphrase (e.g., `my-super-secret-room-123`).
4. Tell your friend to join the same room with the same passphrase.
5. MeckChat will automatically discover your friend, exchange keys, and establish a secure E2E encrypted channel.
