import time

import requests

from config import FIREBASE_API_KEY, FIREBASE_PROJECT_ID

REQUEST_TIMEOUT = 15


class FirebaseError(Exception):
    def __init__(self, message, sign_in_again=False):
        super().__init__(message)
        self.sign_in_again = sign_in_again


def validate_config():
    if not FIREBASE_PROJECT_ID.strip() or not FIREBASE_API_KEY.strip():
        raise FirebaseError("Copy .env.example to .env, fill in Project ID and Web API Key, then restart the app.")
    if any(c in FIREBASE_PROJECT_ID for c in "/ ?#"):
        raise FirebaseError("Project ID should be the ID from Firebase Console, not a URL or project name.")


def _request(method, url, **kwargs):
    try:
        response = requests.request(method, url, timeout=REQUEST_TIMEOUT, **kwargs)
    except requests.RequestException:
        raise FirebaseError("Cannot reach Firebase. Check your connection and try again.") from None

    try:
        data = response.json()
    except ValueError:
        raise FirebaseError("Firebase returned an unexpected response. Try again later.") from None
    if not isinstance(data, dict):
        raise FirebaseError("Firebase returned an unexpected response. Try again later.")
    if response.ok:
        return data

    error = data.get("error", {})
    code = str(error.get("message", "")) if isinstance(error, dict) else ""
    if any(item in code for item in ("TOKEN_EXPIRED", "INVALID_ID_TOKEN", "USER_DISABLED")) or response.status_code == 401:
        raise FirebaseError("Your session is no longer valid. Please sign in again.", True)
    if "EMAIL_EXISTS" in code:
        raise FirebaseError("That email is already registered. Choose Sign in instead.")
    if "OPERATION_NOT_ALLOWED" in code:
        raise FirebaseError("Enable Email/Password in Firebase Console > Authentication > Sign-in method.")
    if "WEAK_PASSWORD" in code or "PASSWORD_DOES_NOT_MEET_REQUIREMENTS" in code:
        raise FirebaseError("Choose a password that meets this Firebase project's password policy.")
    if "INVALID_EMAIL" in code:
        raise FirebaseError("Enter a valid email address.")
    if any(item in code for item in ("INVALID_LOGIN_CREDENTIALS", "INVALID_PASSWORD", "EMAIL_NOT_FOUND")):
        raise FirebaseError("Sign-in failed. Check your app email and password.")
    if "TOO_MANY_ATTEMPTS" in code or response.status_code == 429:
        raise FirebaseError("Too many requests. Wait a little before trying again.")
    if response.status_code == 403:
        raise FirebaseError("Access denied. Check the project and API settings in Firebase Console.")
    if "API_KEY" in code or "PROJECT_NOT_FOUND" in code or response.status_code == 404:
        raise FirebaseError("Check Project ID and Web API Key.")
    raise FirebaseError("Firebase could not complete the request. Check the setup in README.md.")


def _authenticate(action, email, password):
    validate_config()
    email = email.strip()
    if not email or not password:
        raise FirebaseError("Enter both email and password.")
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:{action}"
    return _request(
        "POST", url, params={"key": FIREBASE_API_KEY.strip()},
        json={"email": email, "password": password, "returnSecureToken": True},
    )


def create_account(email, password):
    _authenticate("signUp", email, password)


def sign_in(email, password):
    data = _authenticate("signInWithPassword", email, password)
    return _session_from_response(data)


def _session_from_response(data):
    try:
        user = {
            "uid": data["localId"],
            "email": data["email"],
            "id_token": data["idToken"],
            "expires_at": time.time() + int(data["expiresIn"]),
        }
        if not all(isinstance(user[k], str) and user[k] for k in ("uid", "email", "id_token")):
            raise ValueError
    except (KeyError, TypeError, ValueError):
        raise FirebaseError("Sign-in returned incomplete data. Please try again.") from None
    return user
