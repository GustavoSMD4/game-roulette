import logging
from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from server.blackjack.controller.blackjackController import BlackjackController
from server.front.controller.frontController import FrontController
from server.roulette.controller.rouletteController import RouletteController
from server.usuario.controller.usuarioController import UsuarioController

app = Flask(__name__)
CORS(app)

logger = logging.getLogger('flask_app')
fileHandler = logging.FileHandler('app.log')
fileHandler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)
logger.setLevel(logging.DEBUG)

limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=[],
            headers_enabled=True,
            storage_uri="memory://"
        )


@app.errorhandler(429)
def limiteExcedido(erro):
    return jsonify({"error": "Muitas requisições em pouco tempo. Aguarde um instante e tente novamente."}), 429


UsuarioController.newController(app, limiter, logger)
RouletteController.newController(app, limiter, logger)
BlackjackController.blackjackController(app)
FrontController.newController(app, limiter, logger)
    
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
        
        
    