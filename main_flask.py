from flask import Flask, jsonify, request
from flask_cors import CORS

from server.games.roulette import Roulette
from server.service.playService import PlayService
from server.usuario.controller.usuarioController import UsuarioController

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Temos roleta"

@app.route("/roulette", methods=["POST"])
def playRoulette():
    try:
        req: dict = request.json
        usuario = req.get("usuario")
        bet = req.get("bet")
        betAmount = req.get("betAmount")
        type = req.get("type")
        
        return PlayService.playService().play(usuario, bet, betAmount, type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route("/roulette")
def playRouletteUrlParams():
    try:
        usuario = request.args.get("usuario")
        type = request.args.get("type", type=str)
        bet = request.args.get("bet")
        betAmount = request.args.get("betAmount")
        
        return PlayService.playService().play(usuario, bet, betAmount, type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
UsuarioController(app).routes()
    
if __name__ == "__main__":
    app.run(debug=True)
        
        
    