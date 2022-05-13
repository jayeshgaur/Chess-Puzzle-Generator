$("#submit-btn").click(function (){
    const res = $("#results");
    const fen_input = $("#fen").val();

    const fen = fen_input.replaceAll("/", "^");

    if (fen === "") {
        res.html("Invalid FEN");
        return;
    }
    res.html("Retrieving puzzles, please wait. This may take up to 15 seconds");

    $.ajax({
        url: "/get-fens-" + fen,
        type: "GET",
        contentType: 'application/json',
        success: function (data) {
            res.html(data);
        }
    });
})
