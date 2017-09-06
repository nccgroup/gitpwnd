import hmac
import hashlib

from gitpwnd import app

class CryptoHelper:

    @staticmethod
    def verify_signature(payload, secret):
        key = app.config["HOOK_SECRET"].encode('utf-8')
        h = hmac.new(key, digestmod=hashlib.sha1)
        h.update(payload.encode('utf-8'))
        signature = "sha1=" + h.hexdigest()

        return hmac.compare_digest(signature, secret)
