from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Contraseña que quieras
password = "admin123"

# Generar hash
hash_generado = pwd_context.hash(password)

print("Hash:", hash_generado)
