from flask import Flask, jsonify, request, render_template
from flask_cors import CORS

from server.blackjack.controller.blackjackController import BlackjackController
from server.service.playRouletteService import PlayService
from server.usuario.controller.usuarioController import UsuarioController

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return render_template("main.html")

@app.route("/criarconta")
def criarConta():
    return render_template("criarConta.html")

@app.route("/depositar")
def depositar():
    return render_template("depositar.html")

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
        betAmount = request.args.get("betAmount", type=int)
        
        return PlayService.playService().play(usuario, bet, betAmount, type)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
UsuarioController(app).routes()
BlackjackController.blackjackController(app)
    
if __name__ == "__main__":
    app.run(debug=True)
        
        
    