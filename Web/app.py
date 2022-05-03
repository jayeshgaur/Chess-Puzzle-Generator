from flask import Flask, render_template

from generator import GameState

app = Flask(__name__)
app.config['SECRET_KEY'] = "lkajdghdadkglajkgah1"

game_state = GameState()

@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


@app.route("/get-fens-<fen_pos>", methods=["GET", "POSt"])
def get_fens(fen_pos):
    game_state.update_initial(fen_pos)
    game_state.get_puzzles()


if __name__ == '__main__':
    app.run(debug=True)
