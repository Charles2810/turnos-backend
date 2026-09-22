import os
from app import create_app

env_name = os.getenv("FLASK_ENV", "development")
app = create_app(env_name)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    print(f" Iniciando Servidor API REST en http://127.0.0.1:{port}")
    print(f" Documentación interactiva Swagger disponible en: http://127.0.0.1:{port}/api/docs")
    app.run(host="0.0.0.0", port=port, debug=debug)
