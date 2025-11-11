from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from server.blackjack.controller.blackjackController import BlackjackController
from server.service.playRouletteService import PlayService
from server.usuario.controller.usuarioController import UsuarioController

app = Flask(__name__)
CORS(app)

# @app.route("/")
# def home():
#     return render_template("main.html")

# @app.route("/criarconta")
# def criarConta():
#     return render_template("criarConta.html")

# @app.route("/depositar")
# def depositar():
#     return render_template("depositar.html")
    
@app.route("/roulette/play", methods=["POST"])
def playRouletteUrlParams():
    try:
        return PlayService.playService().play(request.json)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
UsuarioController.newController(app)
BlackjackController.blackjackController(app)
    
if __name__ == "__main__":
    app.run(debug=True)
        
        
    