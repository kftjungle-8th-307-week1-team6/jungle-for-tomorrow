from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'a089wah09fga2f0ag2n34'  # flash()의 플래시 메시지를 사용하기 위한 시크릿 키

# 데모용 사용자 데이터 (실제 운영에서는 MongoDB 사용 필요)
users = {
    "admin": "admin123"
}

@app.route('/j2-test')
def j2_test():
    # The render_template function will look for 'index.html' in the 'templates' folder.
    return render_template('test.j2', title='Home Page')

@app.route('/landing')
def dashboard():
    return "랜딩 페이지 (로그인 성공 후 접근 가능)"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # 간단한 로그인 검증 로직
        if username in users and users[username] == password:
            flash('로그인 성공!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('아이디 또는 비밀번호가 틀렸습니다.', 'danger')
    return render_template('login.html')


@app.route('/')
def home():
    # The render_template function will look for 'index.html' in the 'templates' folder.
    return render_template('index.html', title='Home Page')

if __name__ == '__main__':
    # debug=True enables auto-reloading and provides debug information.
    app.run(host='0.0.0.0', debug=True)
