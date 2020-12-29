import base64
from Crypto import Random
from Crypto.Cipher import AES

BS = 16
pad = lambda s: s + (BS - len(s.encode('utf-8')) % BS) * chr(BS - len(s.encode('utf-8')) % BS)
unpad = lambda s : s[:-ord(s[len(s)-1:])]

class AESCipher:
    def __init__( self, key):
        self.key = key

    def encrypt(self, raw):
        raw = pad(raw)
        iv = Random.new().read( AES.block_size )
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt( raw.encode('utf-8')))

    def decrypt( self, enc ):
        enc = base64.b64decode(enc)
        iv = enc[:16]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt( enc[16:]))


if __name__ == "__main__":
    key = input("Type your security_key: ")

    if len(key) < 32:
        key += " " * (32 - len(key))
    key = key.encode('utf-8')
    data = "original_message"
    e_data = AESCipher(bytes(key)).encrypt(data)

    print("Encrypted: ", e_data)
    d_data = AESCipher(bytes(key)).decrypt(e_data)
    print("Decrypted: ", d_data.decode('utf-8'))

    data = input('contents: ')
    while data:
        print("Encrypted: ", AESCipher(bytes(key)).encrypt(data))
        data = input('contents: ')