import sys
import uuid
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QLabel, QListWidget, QListWidgetItem, QInputDialog, QMessageBox, QDialog, QFormLayout, QFrame, QFileDialog, QCheckBox, QScrollArea)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer, QBuffer, QIODevice, QByteArray
from PyQt5.QtGui import QColor, QPixmap, QIcon
import base64

class PhotoViewerDialog(QDialog):
    def __init__(self, pixmap, is_ephemeral, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Photo Viewer")
        self.resize(800, 600)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QPushButton { background-color: #89b4fa; color: #11111b; border-radius: 4px; padding: 8px; font-weight: bold; }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton#deleteBtn { background-color: #f38ba8; }
            QPushButton#deleteBtn:hover { background-color: #eba0ac; }
        """)
        
        layout = QVBoxLayout(self)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("border: none;")
        
        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        
        # Scale if larger than screen while maintaining aspect ratio
        if pixmap.width() > 1200 or pixmap.height() > 800:
            pixmap = pixmap.scaled(1200, 800, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
        self.img_label.setPixmap(pixmap)
        self.scroll_area.setWidget(self.img_label)
        
        layout.addWidget(self.scroll_area)
        
        btn_layout = QHBoxLayout()
        
        if not is_ephemeral:
            self.download_btn = QPushButton("💾 Save Image")
            self.download_btn.clicked.connect(self.save_image)
            btn_layout.addWidget(self.download_btn)
        else:
            warning_label = QLabel("⚠️ 1-Time View: This image cannot be saved and will be deleted when you close this window.")
            warning_label.setStyleSheet("color: #f9e2af; font-weight: bold;")
            btn_layout.addWidget(warning_label)
            
        btn_layout.addStretch()
        
        self.delete_btn = QPushButton("🗑️ Close & Delete")
        self.delete_btn.setObjectName("deleteBtn")
        self.delete_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.delete_btn)
        
        layout.addLayout(btn_layout)
        
        self.pixmap = pixmap
        
    def save_image(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save Image", "", "Images (*.png *.jpg)")
        if path:
            self.pixmap.save(path)
            QMessageBox.information(self, "Saved", "Image saved successfully.")

class WelcomeDialog(QDialog):
    def __init__(self, crypto_manager, net_manager, parent=None):
        super().__init__(parent)
        self.crypto = crypto_manager
        self.net = net_manager
        
        self.setWindowTitle("MeckChat")
        self.setFixedSize(450, 450)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-family: 'Inter', sans-serif; }
            QLineEdit { 
                background-color: #313244; 
                color: #cdd6f4; 
                border: 1px solid #45475a; 
                border-radius: 8px; 
                padding: 12px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #89b4fa;
                color: #11111b;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #b4befe; }
            QPushButton:disabled { background-color: #45475a; color: #a6adc8; }
            QFrame { background-color: #45475a; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(15)
        
        # Title
        title = QLabel("MeckChat")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #89b4fa;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Global • Passphrase • End-to-End Encrypted")
        subtitle.setStyleSheet("font-size: 13px; color: #a6adc8;")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(10)
        
        # Name Input
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter Display Name...")
        self.name_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.name_input)
        
        # Generate Identity Button
        self.gen_btn = QPushButton("Generate Secure Identity")
        self.gen_btn.clicked.connect(self.generate_identity)
        layout.addWidget(self.gen_btn)
        
        layout.addSpacing(10)
        
        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)
        
        layout.addSpacing(10)
        
        # ID Section
        id_label = QLabel("Your Anonymous ID")
        id_label.setStyleSheet("font-weight: bold; font-size: 16px;")
        id_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(id_label)
        
        self.id_display = QLabel("Not Generated")
        self.id_display.setAlignment(Qt.AlignCenter)
        self.id_display.setStyleSheet("font-family: monospace; color: #f9e2af; font-size: 14px;")
        layout.addWidget(self.id_display)
        
        layout.addStretch()
        
        self.tor_cb = QCheckBox("🧅 Route through Tor Network (Requires local Tor)")
        self.tor_cb.setStyleSheet("color: #a6e3a1; font-weight: bold; font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(self.tor_cb)
        
        # Enter Chat Button
        self.enter_btn = QPushButton("Enter Chat")
        self.enter_btn.setStyleSheet("background-color: #a6e3a1; color: #11111b; font-size: 16px; padding: 14px;")
        self.enter_btn.clicked.connect(self.accept)
        self.enter_btn.setEnabled(False)
        layout.addWidget(self.enter_btn)

    def generate_identity(self):
        if not self.name_input.text().strip():
            QMessageBox.warning(self, "Name Required", "Please enter a display name first.")
            return
        self.crypto.generate_keys()
        my_id = self.crypto.get_my_id()
        self.id_display.setText(f"{my_id[:24]}...")
        
        self.gen_btn.setText("Identity Generated ✅")
        self.gen_btn.setEnabled(False)
        self.name_input.setEnabled(False)
        
        self.enter_btn.setEnabled(True)

    def get_info(self):
        return self.name_input.text().strip() or "Anonymous", self.tor_cb.isChecked()


class RoomDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Join Secret Room")
        self.setFixedSize(350, 200)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e2e; }
            QLabel { color: #cdd6f4; font-size: 14px; }
            QLineEdit { 
                background-color: #313244; 
                color: #cdd6f4; 
                border: 1px solid #45475a; 
                border-radius: 8px; 
                padding: 10px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #f9e2af;
                color: #11111b;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #f2cdcd; }
        """)
        
        layout = QVBoxLayout(self)
        
        label = QLabel("Enter Secret Passphrase:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("e.g. correct-horse-battery-staple")
        self.pass_input.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.pass_input)
        
        layout.addSpacing(10)
        
        connect_btn = QPushButton("Connect Globally")
        connect_btn.clicked.connect(self.accept)
        layout.addWidget(connect_btn)

    def get_passphrase(self):
        return self.pass_input.text().strip()


class ChatUI(QMainWindow):
    message_received_signal = pyqtSignal(str, dict)
    peer_discovered_signal = pyqtSignal(str)
    
    def __init__(self, crypto_manager, network_manager):
        super().__init__()
        self.crypto = crypto_manager
        self.net = network_manager
        
        self.my_name = "Anonymous"
        
        self.peers = {} # id -> name
        self.room_name = ""
        
        self.messages = {} # msg_id -> list item
        self.image_data_store = {} # msg_id -> {'b64': str, 'ephemeral': bool, 'name': str, 'file_type': str}
        self.file_buffers = {} # msg_id -> dict
        
        self.init_ui()
        self.message_received_signal.connect(self.handle_incoming_payload)
        self.peer_discovered_signal.connect(self.handle_peer_discovery)
        
        self.typing_timer = QTimer()
        self.typing_timer.setSingleShot(True)
        self.typing_timer.timeout.connect(self.typing_label.hide)
        
        self.input_timer = QTimer()
        self.input_timer.setSingleShot(True)
        self.input_timer.timeout.connect(self.send_typing_indicator)

    def ask_for_profile(self):
        dialog = WelcomeDialog(self.crypto, self.net, self)
        if dialog.exec_():
            self.my_name, self.use_tor = dialog.get_info()
            self.update_my_info_label()
            self.net.start(use_tor=self.use_tor)
        else:
            sys.exit(0)

    def update_my_info_label(self):
        self.my_info_label.setText(f"Name: {self.my_name}")

    def init_ui(self):
        self.setWindowTitle("MeckChat Global")
        self.resize(1100, 800)
        self.setStyleSheet("""
            QMainWindow { background-color: #111b21; }
            QLabel { color: #e9edef; font-family: 'Inter', sans-serif; font-size: 14px; }
            QLineEdit, QTextEdit { 
                background-color: #2a3942; 
                color: #e9edef; 
                border: 1px solid #2a3942; 
                border-radius: 8px; 
                padding: 12px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #00a884;
                color: #111b21;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #00c298; }
            QPushButton#joinBtn { background-color: #005c4b; color: white; }
            QPushButton#joinBtn:hover { background-color: #008069; }
            QListWidget {
                background-color: #0b141a;
                border: none;
                color: #e9edef;
                font-size: 14px;
            }
            QListWidget::item { padding: 12px; margin: 4px; border-radius: 8px; background-color: #202c33; }
        """)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Left Panel (Sidebar) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(320)
        left_panel.setStyleSheet("QFrame { background-color: #111b21; border-right: 1px solid #202c33; }")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(15, 15, 15, 15)

        self.my_info_label = QLabel("Name: Anonymous")
        self.my_info_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
        left_layout.addWidget(self.my_info_label)

        join_btn = QPushButton("🔑 Join Secret Room")
        join_btn.setObjectName("joinBtn")
        join_btn.clicked.connect(self.open_room_dialog)
        left_layout.addWidget(join_btn)

        left_layout.addSpacing(15)
        
        contacts_lbl = QLabel("Contacts Online")
        contacts_lbl.setStyleSheet("color: #8696a0; font-weight: bold;")
        left_layout.addWidget(contacts_lbl)

        self.contact_list = QListWidget()
        self.contact_list.setStyleSheet("QListWidget { background-color: #111b21; } QListWidget::item { background-color: transparent; border-bottom: 1px solid #202c33; border-radius: 0; }")
        left_layout.addWidget(self.contact_list)

        left_layout.addStretch()

        self.route_btn = QPushButton("🌍 Show Routing Info")
        self.route_btn.setStyleSheet("background-color: #202c33; color: #00a884;")
        self.route_btn.clicked.connect(self.show_routing_info)
        left_layout.addWidget(self.route_btn)

        self.route_label = QLabel("")
        self.route_label.setWordWrap(True)
        self.route_label.setStyleSheet("color: #8696a0; font-size: 12px; margin-top: 10px;")
        self.route_label.hide()
        left_layout.addWidget(self.route_label)

        main_layout.addWidget(left_panel)

        # --- Right Panel (Chat Window) ---
        right_panel = QWidget()
        right_panel.setStyleSheet("QWidget { background-color: #0b141a; }")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)

        # Top Bar
        top_bar = QWidget()
        top_bar.setStyleSheet("background-color: #202c33; border-radius: 8px;")
        top_bar_layout = QHBoxLayout(top_bar)
        
        self.peer_label = QLabel("Not connected")
        self.peer_label.setStyleSheet("color: #8696a0; font-weight: bold; font-size: 16px;")
        top_bar_layout.addWidget(self.peer_label)
        
        right_layout.addWidget(top_bar)

        self.chat_list = QListWidget()
        self.chat_list.itemClicked.connect(self.on_chat_item_clicked)
        right_layout.addWidget(self.chat_list)

        self.typing_label = QLabel("Peer is typing...")
        self.typing_label.setStyleSheet("color: #00a884; font-style: italic;")
        self.typing_label.hide()
        right_layout.addWidget(self.typing_label)

        # Input Area
        input_widget = QWidget()
        input_widget.setStyleSheet("background-color: #202c33; border-radius: 8px; padding: 5px;")
        input_layout = QHBoxLayout(input_widget)
        
        self.ephemeral_cb = QCheckBox("🔥 1-Time")
        self.ephemeral_cb.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 12px;")
        input_layout.addWidget(self.ephemeral_cb)
        
        self.attach_btn = QPushButton("📎")
        self.attach_btn.setStyleSheet("background-color: transparent; color: #8696a0; font-size: 20px; padding: 0;")
        self.attach_btn.setFixedWidth(40)
        self.attach_btn.clicked.connect(self.send_media)
        input_layout.addWidget(self.attach_btn)
        
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type a message")
        self.msg_input.returnPressed.connect(self.send_message)
        self.msg_input.textChanged.connect(self.on_text_changed)
        input_layout.addWidget(self.msg_input)
        
        self.send_btn = QPushButton("▶")
        self.send_btn.setStyleSheet("background-color: #00a884; border-radius: 20px; font-size: 18px; padding: 0;")
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_btn)
        
        right_layout.addWidget(input_widget)
        main_layout.addWidget(right_panel)

    def open_room_dialog(self):
        dialog = RoomDialog(self)
        if dialog.exec_():
            passphrase = dialog.get_passphrase()
            if not passphrase:
                return
            
            if self.room_name and self.room_name != passphrase:
                self.chat_list.clear()
                self.messages.clear()
                self.image_data_store.clear()
                self.file_buffers.clear()
                self.peers.clear()
                self.update_contact_list()
                self.route_label.hide()
                
            self.room_name = passphrase
            self.peer_label.setText(f"Joined room '{passphrase}'. Waiting for peers...")
            self.peer_label.setStyleSheet("color: #00a884; font-weight: bold; font-size: 16px;")
            
            self.net.join_room(passphrase)

    def update_contact_list(self):
        self.contact_list.clear()
        for pid, name in self.peers.items():
            item = QListWidgetItem(f"👤 {name}")
            self.contact_list.addItem(item)
            
    def show_routing_info(self):
        self.route_label.setText("Fetching IP routing info...")
        self.route_label.show()
        
        def fetch_ip():
            try:
                import urllib.request
                import json
                
                if hasattr(self, 'use_tor') and self.use_tor:
                    import socks
                    import socket
                    socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
                    socket.socket = socks.socksocket
                    
                req = urllib.request.Request("http://ip-api.com/json/")
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode())
                    ip = data.get('query', 'Unknown')
                    country = data.get('country', 'Unknown')
                    isp = data.get('isp', 'Unknown')
                    
                if hasattr(self, 'use_tor') and self.use_tor:
                    import socket
                    import _socket
                    socket.socket = _socket.socket
                    
                result = f"Exit Node IP: {ip}\nLocation: {country}\nISP: {isp}"
                if hasattr(self, 'use_tor') and self.use_tor:
                    result = "🧅 Tor Route:\n" + result + "\n(3 Tor layers applied securely)"
            except Exception as e:
                result = f"Failed to fetch route: {e}"
                
            from PyQt5.QtCore import QMetaObject, Qt, Q_ARG
            QMetaObject.invokeMethod(self.route_label, "setText", Qt.QueuedConnection, Q_ARG(str, result))

        threading.Thread(target=fetch_ip).start()

    def handle_peer_discovery(self, sender_id):
        if sender_id not in self.peers:
            self.peers[sender_id] = "Unknown Peer"
            # Send a hello via E2E channel to exchange names
            self.send_system_message('hello')

    def on_text_changed(self):
        if not self.peers: return
        self.input_timer.start(500)

    def send_system_message(self, sys_type):
        if not self.peers: return
        payload = {'type': sys_type, 'name': self.my_name}
        for pid in self.peers.keys():
            threading.Thread(target=self.net.send_payload, args=(pid, payload)).start()

    def send_typing_indicator(self):
        self.send_system_message('typing')

    def send_message(self):
        text = self.msg_input.text().strip()
        if not text or not self.peers: return
        
        msg_id = str(uuid.uuid4())
        payload = {
            'type': 'text',
            'msg_id': msg_id,
            'text': text,
            'name': self.my_name
        }
        
        self.msg_input.clear()
        
        item = QListWidgetItem(f"You: {text}\n✓ Sent")
        item.setTextAlignment(Qt.AlignRight)
        item.setBackground(QColor("#005c4b"))
        item.setForeground(QColor("#e9edef"))
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()
        
        self.messages[msg_id] = item
        
        def send_task():
            for pid in self.peers.keys():
                self.net.send_payload(pid, payload)
        threading.Thread(target=send_task).start()

    def send_media(self):
        if not self.peers:
            QMessageBox.warning(self, "Not Connected", "Join a room and wait for a peer first.")
            return

        path, _ = QFileDialog.getOpenFileName(self, "Send Media", "", "Media (*.png *.jpg *.jpeg *.gif *.bmp *.mp4 *.mkv *.avi *.mov)")
        if not path:
            return

        is_ephemeral = self.ephemeral_cb.isChecked()
        is_video = path.lower().endswith(('.mp4', '.mkv', '.avi', '.mov'))
        
        try:
            with open(path, "rb") as f:
                raw_bytes = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read file: {e}")
            return
            
        full_b64 = base64.b64encode(raw_bytes).decode('utf-8')
        msg_id = str(uuid.uuid4())
        
        chunk_size = 64000
        total_chunks = (len(full_b64) // chunk_size) + (1 if len(full_b64) % chunk_size != 0 else 0)
        
        item = QListWidgetItem()
        media_type = "video" if is_video else "photo"
        ephemeral_text = " (1-Time View)" if is_ephemeral else ""
        item.setText(f"You sent a {media_type}{ephemeral_text}\n✓ Sent")
        item.setTextAlignment(Qt.AlignRight)
        item.setBackground(QColor("#005c4b"))
        item.setForeground(QColor("#e9edef"))
        self.chat_list.addItem(item)
        self.chat_list.scrollToBottom()
        
        self.messages[msg_id] = item

        def send_chunks_task():
            for i in range(total_chunks):
                chunk_data = full_b64[i*chunk_size:(i+1)*chunk_size]
                payload = {
                    'type': 'file_chunk',
                    'msg_id': msg_id,
                    'chunk_index': i,
                    'total_chunks': total_chunks,
                    'file_type': media_type,
                    'is_ephemeral': is_ephemeral,
                    'data': chunk_data,
                    'name': self.my_name
                }
                for pid in list(self.peers.keys()):
                    self.net.send_payload(pid, payload)
                import time
                time.sleep(0.1) # Prevent flooding
                
        threading.Thread(target=send_chunks_task).start()

    def handle_incoming_payload(self, sender_id, payload):
        p_type = payload.get('type')
        raw_name = payload.get('name', 'Peer')
        
        if p_type == 'hello':
            unique_name = raw_name
            if raw_name == self.my_name:
                unique_name = f"{raw_name}#{sender_id[:4]}"
            else:
                for pid, existing_name in self.peers.items():
                    if pid != sender_id and (existing_name == raw_name or existing_name.startswith(f"{raw_name}#")):
                        unique_name = f"{raw_name}#{sender_id[:4]}"
                        break
                        
            self.peers[sender_id] = unique_name
            self.peer_label.setText(f"Room: {self.room_name} | {len(self.peers)} Peers Online")
            self.update_contact_list()
            
            if 'hello_reply' not in payload:
                reply_payload = {'type': 'hello', 'name': self.my_name, 'hello_reply': True}
                threading.Thread(target=self.net.send_payload, args=(sender_id, reply_payload)).start()
        
        display_name = self.peers.get(sender_id, raw_name)
            
        if p_type == 'typing':
            self.typing_label.setText(f"{display_name} is typing...")
            self.typing_label.show()
            self.typing_timer.start(3000)
            
        elif p_type == 'text':
            self.typing_label.hide()
            text = payload.get('text')
            msg_id = payload.get('msg_id')
            
            item = QListWidgetItem(f"{display_name}: {text}")
            item.setBackground(QColor("#202c33"))
            item.setForeground(QColor("#e9edef"))
            self.chat_list.addItem(item)
            self.chat_list.scrollToBottom()
            
            receipt_payload = {'type': 'read', 'msg_id': msg_id}
            if sender_id in self.peers:
                threading.Thread(target=self.net.send_payload, args=(sender_id, receipt_payload)).start()
                
        elif p_type == 'file_chunk':
            msg_id = payload.get('msg_id')
            idx = payload.get('chunk_index')
            total = payload.get('total_chunks')
            
            if msg_id not in self.file_buffers:
                self.file_buffers[msg_id] = {
                    'chunks': {},
                    'total': total,
                    'file_type': payload.get('file_type', 'photo'),
                    'ephemeral': payload.get('is_ephemeral', False),
                    'name': display_name
                }
                
            buf = self.file_buffers[msg_id]
            buf['chunks'][idx] = payload.get('data')
            
            if len(buf['chunks']) == total:
                self.typing_label.hide()
                assembled_b64 = "".join(buf['chunks'][i] for i in range(total))
                
                self.image_data_store[msg_id] = {
                    'b64': assembled_b64,
                    'ephemeral': buf['ephemeral'],
                    'name': buf['name'],
                    'file_type': buf['file_type']
                }
                
                item = QListWidgetItem()
                item.setData(Qt.UserRole, msg_id)
                media_icon = "🔥" if buf['ephemeral'] else ("🎥" if buf['file_type'] == "video" else "📷")
                
                if buf['ephemeral']:
                    item.setText(f"🔥 {buf['name']} sent a 1-Time View {buf['file_type']}\n[Click to View]")
                    item.setForeground(QColor("#ef4444"))
                else:
                    item.setText(f"{media_icon} {buf['name']} sent a {buf['file_type']}\n[Click to View/Save]")
                    item.setForeground(QColor("#e9edef"))
                    
                item.setBackground(QColor("#202c33"))
                self.chat_list.addItem(item)
                self.chat_list.scrollToBottom()
                
                del self.file_buffers[msg_id]
                
                receipt_payload = {'type': 'read', 'msg_id': msg_id}
                if sender_id in self.peers:
                    threading.Thread(target=self.net.send_payload, args=(sender_id, receipt_payload)).start()
                
        elif p_type == 'image':
            self.typing_label.hide()
            img_b64 = payload.get('image_data')
            msg_id = payload.get('msg_id')
            is_ephemeral = payload.get('is_ephemeral', False)
            
            self.image_data_store[msg_id] = {
                'b64': img_b64,
                'ephemeral': is_ephemeral,
                'name': display_name
            }
            
            item = QListWidgetItem()
            item.setData(Qt.UserRole, msg_id)
            if is_ephemeral:
                item.setText(f"🔥 {display_name} sent a 1-Time View photo\n[Click to View]")
                item.setForeground(QColor("#fab387"))
            else:
                item.setText(f"📷 {display_name} sent a photo\n[Click to View]")
                
            item.setBackground(QColor("#313244"))
            self.chat_list.addItem(item)
            self.chat_list.scrollToBottom()
            
            receipt_payload = {'type': 'read', 'msg_id': msg_id}
            if sender_id in self.peers:
                threading.Thread(target=self.net.send_payload, args=(sender_id, receipt_payload)).start()
                
        elif p_type == 'read':
            msg_id = payload.get('msg_id')
            if msg_id in self.messages:
                item = self.messages[msg_id]
                current_text = item.text()
                if "✓ Sent" in current_text:
                    item.setText(current_text.replace("✓ Sent", "✓✓ Read"))
                    item.setForeground(QColor("#a6e3a1"))

    def on_chat_item_clicked(self, item):
        msg_id = item.data(Qt.UserRole)
        if not msg_id or msg_id not in self.image_data_store:
            return
            
        data = self.image_data_store[msg_id]
        raw_data = base64.b64decode(data['b64'])
        file_type = data.get('file_type', 'photo')
        
        if file_type == 'video':
            path, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "Videos (*.mp4 *.mkv *.avi *.mov)")
            if path:
                with open(path, "wb") as f:
                    f.write(raw_data)
                QMessageBox.information(self, "Saved", "Video saved successfully. You can now play it.")
                
            if data['ephemeral']:
                del self.image_data_store[msg_id]
                item.setText(f"🔥 {data['name']}'s video has been deleted.")
                item.setForeground(QColor("#a6adc8"))
                item.setData(Qt.UserRole, None)
            return

        pixmap = QPixmap()
        pixmap.loadFromData(raw_data)
        
        dialog = PhotoViewerDialog(pixmap, data['ephemeral'], self)
        dialog.exec_()
        
        # Post-view actions for ephemeral images
        if data['ephemeral']:
            del self.image_data_store[msg_id]
            # Wipe variable to encourage GC
            raw_data = None
            pixmap = None
            item.setText(f"🔥 {data['name']}'s photo has been deleted.")
            item.setForeground(QColor("#a6adc8"))
            item.setData(Qt.UserRole, None) # Remove clickability

