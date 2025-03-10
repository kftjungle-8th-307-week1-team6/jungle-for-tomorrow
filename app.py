from flask import Flask, render_template

app = Flask(__name__)

@app.route('/j2-test')
def j2_test():
    # The render_template function will look for 'index.html' in the 'templates' folder.
    return render_template('test.j2', title='Home Page')

@app.route('/')
def home():
    # The render_template function will look for 'index.html' in the 'templates' folder.
    return render_template('index.html', title='Home Page')

if __name__ == '__main__':
    # debug=True enables auto-reloading and provides debug information.
    app.run(debug=True)
