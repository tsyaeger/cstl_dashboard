import sys
from flask import Flask, jsonify, request, render_template
from build_graphs import build_graphs 
# testfile = "/Users/main/Desktop/Coding/castle_dash_test/dashboard_challenge/castle_users.json"

app = Flask(__name__)
app.config['PROPAGATE_EXCEPTIONS'] = True

@app.route('/')
def home():
	return render_template("index.html")

if __name__ == '__main__':
	input = sys.argv[1]
	print('input file name is ==>', input)
	build_graphs(input)

	app.run(debug=True, use_reloader=False)
