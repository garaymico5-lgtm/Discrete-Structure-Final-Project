"""
Logic-Based Student Access and Data Management System
BISU Final Project (corrected version)

Discrete Structures topics used:
  Sets ............. user groups, rooms, authorization (union / difference)
  Predicate logic .. evaluate_predicate_logic
  Relations ........ access matrix (user x room)
  Number theory .... Caesar cipher (modular arithmetic), GCD-based access code
  Graphs ........... Dijkstra shortest path on the campus map
  Trees ............ campus_directory traversal / search (recursion)
  Searching ........ binary search
  FSM .............. explicit transition table
"""

from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from functools import wraps
import math
import json
import random

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # needed for sessions

# ------------------------------------------------------------------
# FINITE STATE MACHINE: (state, event) -> next state
# ------------------------------------------------------------------
FSM_TRANSITIONS = {
    ("Idle", "submit"): "Login",
    ("Login", "valid"): "Access Granted",
    ("Login", "invalid"): "Access Denied",
    ("Access Denied", "submit"): "Login",
    ("Access Granted", "navigate"): "Navigating",
    ("Navigating", "navigate"): "Navigating",
    ("Access Granted", "logout"): "Idle",
    ("Navigating", "logout"): "Idle",
    ("Access Denied", "logout"): "Idle",
}


def fsm_step(state, event):
    """Return the next state; stay in the same state if the move is not allowed."""
    return FSM_TRANSITIONS.get((state, event), state)


class AccessManagementSystem:
    USER_GROUPS = {"student": "students", "faculty": "faculty",
                   "staff": "staff", "visitor": "visitors"}

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
            "V002": set(),
        }

        self.user_list = sorted(self.all_users)
        self.room_list = sorted(self.rooms)
        self.refresh_matrix()

        # Caesar-cipher "encrypted" passwords (demo only, NOT real security)
        self.secure_credentials = {
            "S001": self._encrypt("pass123"),
            "F001": self._encrypt("admin456"),
            "ST001": self._encrypt("staff789"),
        }

        self.campus_graph = {
            'Main Gate': {'Admin Bldg': 50, 'Library': 100},
            'Admin Bldg': {'Main Gate': 50, 'Science Hall': 80, 'Library': 60},
            'Library': {'Main Gate': 100, 'Admin Bldg': 60, 'Science Hall': 40},
            'Science Hall': {'Admin Bldg': 80, 'Library': 40, 'Engineering Bldg': 70},
            'Engineering Bldg': {'Science Hall': 70},
        }

        self.campus_directory = {
            "BISU Campus": {
                "College of Science": {"Science Hall": ["R101", "R102", "R103"]},
                "College of Engineering": {"Engineering Bldg": ["R201", "R202"]},
            }
        }

    # --------------------------------------------------------------
    # PREDICATE LOGIC / RELATIONS
    # --------------------------------------------------------------
    def evaluate_predicate_logic(self, user, room):
        """Access(u, r) = Exists(u) AND Authorized(u) AND NOT Restricted(u) AND HasPermission(u, r)"""
        return (user in self.all_users
                and user in self.authorized_users
                and user not in self.restricted_users
                and room in self.access_permissions.get(user, set()))

    def _build_access_matrix(self):
        # Uses the predicate, so the matrix always agrees with the logic.
        return [[1 if self.evaluate_predicate_logic(u, r) else 0 for r in self.room_list]
                for u in self.user_list]

    def _calculate_access_levels(self):
        """Level = number of rooms the user can effectively enter (popcount of the bit mask)."""
        levels = {}
        for i, user in enumerate(self.user_list):
            mask = sum(bit << j for j, bit in enumerate(self.access_matrix[i]))
            levels[user] = bin(mask).count("1")
        return levels

    def refresh_matrix(self):
        self.user_list = sorted(self.all_users)
        self.access_matrix = self._build_access_matrix()
        self.user_access_levels = self._calculate_access_levels()

    def get_matrix_for_html(self):
        return {
            'headers': self.room_list,
            'rows': [{'user': u,
                      'permissions': self.access_matrix[i],
                      'level': self.user_access_levels.get(u, 0)}
                     for i, u in enumerate(self.user_list)],
        }

    # --------------------------------------------------------------
    # NUMBER THEORY: Caesar cipher (case preserving)
    # --------------------------------------------------------------
    def _encrypt(self, text, shift=3):
        out = []
        for c in text:
            if c.isalpha():
                base = 65 if c.isupper() else 97
                out.append(chr((ord(c) - base + shift) % 26 + base))
            else:
                out.append(c)
        return "".join(out)

    def verify_login(self, user_id, password_attempt):
        stored = self.secure_credentials.get(user_id)
        return stored is not None and stored == self._encrypt(password_attempt)

    # --------------------------------------------------------------
    # GRAPHS: Dijkstra
    # --------------------------------------------------------------
    def find_shortest_path(self, start, end):
        if start not in self.campus_graph or end not in self.campus_graph:
            return None, float('inf')
        dist = {n: float('inf') for n in self.campus_graph}
        dist[start] = 0
        prev = {n: None for n in self.campus_graph}
        unvisited = set(self.campus_graph)

        while unvisited:
            curr = min(unvisited, key=lambda n: dist[n])
            unvisited.remove(curr)
            if dist[curr] == float('inf') or curr == end:
                break
            for nxt, w in self.campus_graph[curr].items():
                if dist[curr] + w < dist[nxt]:
                    dist[nxt] = dist[curr] + w
                    prev[nxt] = curr

        if dist[end] == float('inf'):      # unreachable
            return None, dist[end]

        path, curr = [], end
        while curr:
            path.insert(0, curr)
            curr = prev[curr]
        return path, dist[end]

    # --------------------------------------------------------------
    # TREES: recursive traversal and search
    # --------------------------------------------------------------
    def traverse_directory(self, node, level=0):
        out = []
        if isinstance(node, dict):
            for k, v in node.items():
                out.append("  " * level + f"📁 {k}")
                out.extend(self.traverse_directory(v, level + 1))
        elif isinstance(node, list):
            for i in node:
                out.append("  " * level + f"📄 {i}")
        return out

    def search_tree(self, node, target):
        target = target.lower()
        if isinstance(node, dict):
            return any(target in k.lower() or self.search_tree(v, target) for k, v in node.items())
        if isinstance(node, list):
            return any(target in i.lower() for i in node)
        return False

    def rooms_in_building(self, building, node=None):
        """Recursively find the room list of a building in the directory tree."""
        node = self.campus_directory if node is None else node
        if isinstance(node, dict):
            for k, v in node.items():
                if k == building and isinstance(v, list):
                    return v
                found = self.rooms_in_building(building, v)
                if found:
                    return found
        return []

    # --------------------------------------------------------------
    # SEARCHING
    # --------------------------------------------------------------
    def binary_search_user(self, user_id):
        users = sorted(self.user_list)
        low, high = 0, len(users) - 1
        while low <= high:
            mid = (low + high) // 2
            if users[mid] == user_id:
                return True
            elif users[mid] < user_id:
                low = mid + 1
            else:
                high = mid - 1
        return False

    # --------------------------------------------------------------
    # SIMULATION
    # --------------------------------------------------------------
    def get_live_monitoring_data(self):
        data = []
        for room in self.room_list:
            cap = 40
            p = random.randint(0, 50)
            status = "FULL" if p >= cap else ("NEARLY FULL" if (p / cap) * 100 > 75 else "AVAILABLE")
            data.append({'room': room, 'people': p, 'capacity': cap, 'status': status,
                         'wait_time': random.randint(10, 30) if status == "FULL" else 0})
        return data

    def simulate_wait_time(self):
        return random.randint(1, 15)

    def generate_access_code(self, user_id, room):
        if not self.evaluate_predicate_logic(user_id, room):
            return "DENIED"
        seed = (self.user_access_levels.get(user_id, 1) * int(room[1:])) % 99
        return f"CODE: {self._encrypt(f'{user_id}-{room}-{seed}').upper()[-6:]}"

    def add_user(self, user_id, user_type):
        group = getattr(self, self.USER_GROUPS[user_type])
        group.add(user_id)
        self.all_users.add(user_id)
        self.access_permissions[user_id] = set()
        self.refresh_matrix()


system = AccessManagementSystem()


# ==================================================================
# AUTH HELPERS
# ==================================================================
def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if "user" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Not logged in"}), 401
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)
    return wrapper


# ==================================================================
# PAGE ROUTES
# ==================================================================
@app.route('/')
def login_page():
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html',
                           data=json.dumps(system.get_matrix_for_html()),
                           user=session["user"])


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ==================================================================
# API ROUTES
# ==================================================================
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    user_id = str(data.get("user_id", "")).strip().upper()
    password = str(data.get("password", ""))

    session.clear()
    state = fsm_step("Idle", "submit")                       # Idle -> Login

    if not user_id or not system.binary_search_user(user_id):
        state = fsm_step(state, "invalid")
        session["state"] = state
        return jsonify({"state": state, "error": "User not found"}), 401

    if system.verify_login(user_id, password):
        state = fsm_step(state, "valid")                     # Login -> Access Granted
        session["user"] = user_id
        session["state"] = state
        return jsonify({"state": state, "message": "Access Granted"})

    state = fsm_step(state, "invalid")                       # Login -> Access Denied
    session["state"] = state
    return jsonify({"state": state, "error": "Invalid credentials"}), 401


@app.route('/api/navigate', methods=['POST'])
@login_required
def navigate():
    data = request.get_json(silent=True) or {}
    user_id = session["user"]
    start = str(data.get("start", "")).strip()
    dest = str(data.get("destination", "")).strip()

    if start not in system.campus_graph:
        return jsonify({"error": "Start location not found"})
    if dest not in system.campus_graph:
        return jsonify({"error": "Destination not found"})

    path, distance = system.find_shortest_path(start, dest)
    if not path:
        return jsonify({"error": "No path found"})

    session["state"] = fsm_step(session.get("state", "Idle"), "navigate")

    # Access code: first room in the destination building the user may enter
    rooms = system.rooms_in_building(dest)
    code = next((system.generate_access_code(user_id, r) for r in rooms
                 if system.evaluate_predicate_logic(user_id, r)), None)
    if rooms and code is None:
        code = "DENIED"
    elif not rooms:
        code = "N/A (no rooms in this building)"

    return jsonify({
        "state": session["state"],
        "message": "Access Granted",
        "path": " -> ".join(path),
        "distance": f"{distance} meters",
        "access_code": code,
        "simulated_wait_time": f"{system.simulate_wait_time()} mins",
        "directory_preview": system.traverse_directory(system.campus_directory)[:6],
    })


@app.route('/api/monitoring')
@login_required
def monitoring_api():
    return jsonify({'state': "Monitoring", 'data': system.get_live_monitoring_data()})


@app.route('/api/add_user', methods=['POST'])
@login_required
def add_user():
    data = request.get_json(silent=True) or {}
    uid = str(data.get('user_id', '')).strip().upper()
    utype = str(data.get('user_type', '')).strip().lower()

    if not uid or not uid.isalnum():
        return jsonify({"error": "User ID is required (letters and numbers only)"}), 400
    if utype not in system.USER_GROUPS:
        return jsonify({"error": "Invalid user type"}), 400
    if uid in system.all_users:
        return jsonify({"error": "User exists"}), 400

    system.add_user(uid, utype)
    return jsonify({"message": f"Added {uid}"})


if __name__ == '__main__':
    app.run(debug=False)