"""
Logic-Based Student Access and Data Management System
BISU Final Project
"""

from flask import Flask, render_template, jsonify, request
import math
import json
import random 

app = Flask(__name__)

class AccessManagementSystem:
    def __init__(self):
        self.students = {"S001", "S002", "S003", "S004", "S005"}
        self.faculty = {"F001", "F002", "F003", "F004", "F005"}
        self.staff = {"ST001", "ST002", "ST003", "ST004", "ST005"}
        self.visitors = {"V001", "V002"}

        self.all_users = self.students | self.faculty | self.staff | self.visitors
        self.authorized_users = {"S001", "S002", "F001", "F002", "ST001", "ST002"}
        self.restricted_users = {"S003", "V001", "V002"}

        self.rooms = {"R101", "R102", "R103", "R201", "R202"}
        self.lab_rooms = {"R101", "R102"}
        self.lecture_rooms = {"R103", "R201", "R202"}

        self.access_permissions = {
            "S001": {"R101", "R102", "R103"},
            "S002": {"R101", "R102"},
            "S003": {"R201"},
            "S004": set(),
            "S005": {"R103"},
            "F001": {"R101", "R102", "R103", "R201", "R202"},
            "F002": {"R101", "R102", "R201"},
            "ST001": {"R101", "R102", "R103", "R201", "R202"},
            "ST002": {"R103", "R202"},
            "V001": {"R201"},
            "V002": set()
        }

        self.user_list = sorted(self.all_users)
        self.room_list = sorted(self.rooms)
        self.access_matrix = self._build_access_matrix()
        self.user_access_levels = self._calculate_access_levels()

        self.current_state = "Idle"
        self.secure_credentials = {
            "S001": self._encrypt("pass123"), 
            "F001": self._encrypt("admin456"),
            "ST001": self._encrypt("staff789")
        }

        self.campus_graph = {
            'Main Gate': {'Admin Bldg': 50, 'Library': 100},
            'Admin Bldg': {'Main Gate': 50, 'Science Hall': 80, 'Library': 60},
            'Library': {'Main Gate': 100, 'Admin Bldg': 60, 'Science Hall': 40},
            'Science Hall': {'Admin Bldg': 80, 'Library': 40, 'Engineering Bldg': 70},
            'Engineering Bldg': {'Science Hall': 70}
        }

        self.campus_directory = {
            "BISU Campus": {
                "College of Science": {"Science Hall": ["R101", "R102", "R103"]},
                "College of Engineering": {"Engineering Bldg": ["R201", "R202"]}
            }
        }

    # --- EXISTING METHODS ---
    def evaluate_predicate_logic(self, user, room):
        return (user in self.all_users) and (user in self.authorized_users) and (user not in self.restricted_users) and (room in self.access_permissions.get(user, set()))

    def _build_access_matrix(self):
        return [[1 if room in self.access_permissions.get(user, set()) else 0 for room in self.room_list] for user in self.user_list]

    def _calculate_access_levels(self):
        levels = {}
        for user in self.user_list:
            permission_bits = sum((1 << i) for i, room in enumerate(self.room_list) if room in self.access_permissions.get(user, set()))
            levels[user] = math.gcd(permission_bits, 31) if permission_bits > 0 else 0
        return levels

    def get_matrix_for_html(self):
        return {
            'headers': self.room_list,
            'rows': [{'user': u, 'permissions': self.access_matrix[i], 'level': self.user_access_levels.get(u, 0)} for i, u in enumerate(self.user_list)]
        }

    # --- NEW METHODS ---
    def _encrypt(self, text, shift=3):
        return "".join(chr((ord(c) + shift - 97) % 26 + 97) if c.isalpha() else c for c in text)

    def verify_login(self, user_id, password_attempt):
        return self.secure_credentials.get(user_id) == self._encrypt(password_attempt)

    def find_shortest_path(self, start, end):
        if start not in self.campus_graph or end not in self.campus_graph: return None, float('inf')
        dist = {n: float('inf') for n in self.campus_graph}; dist[start] = 0
        prev = {n: None for n in self.campus_graph}; unvisited = set(self.campus_graph)
        while unvisited:
            curr = min(unvisited, key=lambda n: dist[n]); unvisited.remove(curr)
            if dist[curr] == float('inf') or curr == end: break
            for nxt, w in self.campus_graph[curr].items():
                if dist[curr] + w < dist[nxt]: dist[nxt] = dist[curr] + w; prev[nxt] = curr
        path, curr = [], end
        while curr: path.insert(0, curr); curr = prev[curr]
        return path, dist[end]

    def traverse_directory(self, node, level=0):
        out = []
        if isinstance(node, dict):
            for k, v in node.items(): out.append("  "*level + f"📁 {k}"); out.extend(self.traverse_directory(v, level+1))
        elif isinstance(node, list):
            for i in node: out.append("  "*level + f"📄 {i}")
        return out

    def search_tree(self, node, target):
        if isinstance(node, dict): return any(target.lower() in k.lower() or self.search_tree(v, target) for k, v in node.items())
        if isinstance(node, list): return any(target.lower() in i.lower() for i in node)
        return False

    def binary_search_user(self, user_id):
        users = sorted(self.user_list); low, high = 0, len(users)-1
        while low <= high:
            mid = (low + high) // 2
            if users[mid] == user_id: return True
            elif users[mid] < user_id: low = mid + 1
            else: high = mid - 1
        return False

    def get_live_monitoring_data(self):
        data = []
        for room in self.room_list:
            p, cap = random.randint(0, 50), 40
            status = "FULL" if p >= cap else ("NEARLY FULL" if (p/cap)*100 > 75 else "AVAILABLE")
            data.append({'room': room, 'people': p, 'capacity': cap, 'status': status, 'wait_time': random.randint(10,30) if status=="FULL" else 0})
        return data

    def simulate_wait_time(self): return random.randint(1, 15)

    def generate_access_code(self, user_id, room):
        if not self.evaluate_predicate_logic(user_id, room): return "DENIED"
        seed = (self.user_access_levels.get(user_id, 1) * int(room[1:])) % 99 
        return f"CODE: {self._encrypt(f'{user_id}-{room}-{seed}').upper()[-6:]}"

system = AccessManagementSystem()

# ==========================================
# ROUTES PARA SA TAGSATAGSA NGA HTML
# ==========================================

@app.route('/')
def login_page():
    # Kini ang una nga makita (Login)
    return render_template('login.html')

@app.route('/dashboard')
def dashboard_page():
    # Kini ang makita human maka-login
    matrix_data = system.get_matrix_for_html()
    return render_template('dashboard.html', data=json.dumps(matrix_data))

# --- API ROUTES (Parehas ra sa una) ---
@app.route('/api/navigate', methods=['POST'])
def navigate():
    data = request.json
    system.current_state = "Login"
    if not system.binary_search_user(data.get('user_id')): return jsonify({"state": "Access Denied", "error": "User not found"})
    
    if system.verify_login(data.get('user_id'), data.get('password')):
        system.current_state = "Access Granted"
        if not system.search_tree(system.campus_directory, data.get('destination')):
            return jsonify({"error": "Destination not found"})
        
        path, distance = system.find_shortest_path(data.get('start'), data.get('destination'))
        if not path: return jsonify({"error": "No path found"})

        return jsonify({
            "state": "Navigating", "message": "Access Granted",
            "path": " -> ".join(path), "distance": f"{distance} meters",
            "access_code": system.generate_access_code(data.get('user_id'), "R101"),
            "simulated_wait_time": f"{system.simulate_wait_time()} mins",
            "directory_preview": system.traverse_directory(system.campus_directory)[:6]
        })
    return jsonify({"state": "Access Denied", "error": "Invalid credentials"})

@app.route('/api/monitoring')
def monitoring_api():
    return jsonify({'state': "Monitoring", 'data': system.get_live_monitoring_data()})

@app.route('/api/add_user', methods=['POST'])
def add_user():
    data = request.json
    uid, utype = data.get('user_id').upper(), data.get('user_type')
    if uid in system.all_users: return jsonify({"error": "User exists"}), 400
    
    getattr(system, f"{utype}s").add(uid) if hasattr(system, f"{utype}s") else system.visitors.add(uid)
    system.all_users.add(uid); system.user_list = sorted(system.all_users)
    system.access_permissions[uid] = set()
    system.access_matrix = system._build_access_matrix(); system.user_access_levels = system._calculate_access_levels()
    return jsonify({"message": f"Added {uid}"})

if __name__ == '__main__':
    app.run(debug=True)