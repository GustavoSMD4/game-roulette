from flask import Flask, jsonify, request
from flask_cors import CORS

from games.roulette import Roulette

app = Flask(__name__)
CORS(app)

@app.route("/")
def home():
    return "Temos roleta"

@app.route("/roulette", methods=["POST"])
def playRoulette():
    try:
        req: dict = request.json
        bet = req.get("bet")
        betAmount = req.get("betAmount")
        type = req.get("type")
        
        if type != "number" and type != "color":
            raise Exception("Types only color or number")

        if type == "number":
            return jsonify(Roulette.newRoulette().playNumber(bet, betAmount)), 200

        if type == "color":
            return jsonify(Roulette.newRoulette().playColor(bet, betAmount))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
@app.route("/roulette")
def playRouletteUrlParams():
    try:
        type = request.args.get("type", type=str)
        bet = request.args.get("bet")
        betAmount = request.args.get("betAmount")
        
        if type not in ["number", "color"]:
            raise Exception("Types only color or number")

        if type == "number":
            return jsonify(Roulette.newRoulette().playNumber(bet, betAmount)), 200

        if type == "color":
            return jsonify(Roulette.newRoulette().playColor(bet, betAmount))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
if __name__ == "__main__":
    app.run(debug=True)
        
        
    