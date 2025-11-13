from flask import Flask
from flask import render_template, redirect, request
from flask import flash
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'COPACK'

@app.route("/")
def nome ():
    return render_template("login.html")
@app.route(".login", methods=['POST'])
def login():
        
    nome = request.form.get('nome')
    senha = request.form.get('senha')

    with open('usuarios.json') as tempuser:
        users = json.load(tempuser)

        cont = 0
        for user in users:
            cont += 1

            if user['nome'] == nome and user['senha'] == senha:
                return render_template('usuarios.html')
            
            if cont >= len(users):
                flash('Usuario Invalido')
                return redirect('/')
            
if __name__ == "__main__":
    app.run(debug=True)