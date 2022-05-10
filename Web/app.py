from flask import Flask, render_template

from generator import GameState

app = Flask(__name__)
app.config['SECRET_KEY'] = "lkajdghdadkglajkgah1"

game_state = GameState()


@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")


def gen_html(puzzles):
    links = []

    for i, puzzle in enumerate(puzzles):
        link = puzzle.replace(" ", "_")
        link = f"<a href='https://lichess.org/analysis/{link}' target='_blank'>Puzzle {i + 1}</a>"
        links.append(f"<li>{link}</li>")

    html_link = "<ul>" + "".join(links) + "</ul>"
    return html_link


@app.route("/get-fens-<fen_pos>", methods=["GET", "POST"])
def get_fens(fen_pos):
    fen_pos = fen_pos.replace("^", "/")
    print(fen_pos)
    game_state.update_initial(fen_pos)
    puzzles = game_state.get_puzzles()
    print(puzzles)
    return gen_html(puzzles)


if __name__ == '__main__':
    app.run(debug=True)
