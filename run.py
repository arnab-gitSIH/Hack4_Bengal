from app import create_app, mysql

app = create_app()
mysql.init_app(app)

if __name__ == '__main__':
    app.run(debug=True)

