import wsgiref.simple_server
import urllib.parse
import sqlite3
import http.cookies
import random
import os
import io


def getcookies(environ):
    cookiesDict = {}
    theCookie = environ['HTTP_COOKIE']

    if 'HTTP_COOKIE' in environ:
        cookies = environ['HTTP_COOKIE']
        cookies = cookies.split('; ')
        for cookie in cookies:
            cookie = cookie.split('=')
            cookiesDict[cookie[0]] = cookie[1]
    return cookiesDict


connection = sqlite3.connect('users.db')
stmt = "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
cursor = connection.cursor()
result = cursor.execute(stmt)
r = result.fetchall()
page = ''
if (r == []):
    exp = 'CREATE TABLE users (username,password)'
    connection.execute(exp)


def application(environ, start_response):
    headers = [('Content-Type', 'text/html; charset=utf-8')]
    path = environ['PATH_INFO']
    params = urllib.parse.parse_qs(environ['QUERY_STRING'])
    un = params['username'][0] if 'username' in params else None
    pw = params['password'][0] if 'password' in params else None
    if path == '/register' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ?', [un]).fetchall()
        if user:
            start_response('200 OK', headers)
            return ['Sorry, username {} is taken'.format(un).encode()]
        else:
            connection.execute('INSERT INTO users VALUES (?,?)', [un, pw])
            connection.commit()
            headers.append(('Set-Cookie', 'session={}:{}'.format(un, pw)))
            start_response('200 OK', headers)
            return ['Username {} is successfully registered!'.format(un).encode()]
    elif path == '/login' and un and pw:
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()
        if user:
            headers.append(('Set-Cookie', 'session={}:{}'.format(un, pw)))
            start_response('200 OK', headers)
            return ['User {} successfully logged in. <a href="/account">Account</a>'.format(un).encode()]
        else:
            start_response('200 OK', headers)
            return ['Incorrect username or password'.encode()]
    elif path == '/logout':
        headers.append(('Set-Cookie', 'session=0; expires=Thu, 01 Jan 1970 00:00:00 GMT'))
        start_response('200 OK', headers)
        return ['Logged out. <a href="/">Login</a>'.encode()]
    elif path == '/account':

        if 'HTTP_COOKIE' not in environ:
            return ['Not logged in <a href="/">Login</a>'.encode()]
        cookies = http.cookies.SimpleCookie()
        cookies.load(environ['HTTP_COOKIE'])
        if 'session' not in cookies:
            return ['Not logged in <a href="/">Login</a>'.encode()]
        [un, pw] = cookies['session'].value.split(':')
        user = cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', [un, pw]).fetchall()
        hyperlink = ''
        if user:
            correct = 0
            wrong = 0
            cookies = getcookies(environ)
            if 'HTTP_COOKIE' in environ:
                print(environ['HTTP_COOKIE'])
                start_response('200 OK', headers)
                if 'score' in cookies:
                    correct = int(cookies['score'].split(':')[0])
                    wrong = int(cookies['score'].split(':')[1])
            page = '<!DOCTYPE html><html><head><title>Multiply with Score</title></head><body>'
            f1 = random.randrange(10) + 1
            f2 = random.randrange(10) + 1
            theAnswer = f1 * f2
            NOTTHEANSWER1 = random.randrange(f1 * f2)
            NOTTHEANSWER2 = random.randrange(f1 * f2)
            NOTTHEANSWER3 = random.randrange(f1 * f2)
            ansList = [theAnswer, NOTTHEANSWER1, NOTTHEANSWER2, NOTTHEANSWER3]
            random.shuffle(ansList)
            if 'factor1' in params and 'factor2' in params and 'answer' in params:
                random.shuffle(ansList)
                ff1 = int(params['factor1'][0])
                ff2 = int(params['factor2'][0])
                ansUser = int(params['answer'][0])
                ansGood = ff1 * ff2
                if ansUser == ansGood:
                    page += '<p style="background-color:lightgreen">Correct! {} x {} = {}</p>'.format(ff1, ff2, ansGood)
                    correct = int(cookies['score'].split(':')[0]) + 1
                else:
                    page += '<p style="background-color:red">Wrong!</p>'
                    wrong = int(cookies['score'].split(':')[1]) + 1
            elif 'reset' in params:
                correct = 0
                wrong = 0
            page = page + '<h1>What is {} x {}</h1>'.format(f1, f2)
            page += "\n"
            page += "<a href=\"/account?" + "factor1={}".format(f1) + "&" + "factor2={}".format(
                f2) + "&" + "answer={}\"".format(ansList[0]) + ">" + "{}".format(ansList[0]) + "</a><br>"
            page += "<a href=\"/account?" + "factor1={}".format(f1) + "&" + "factor2={}".format(
                f2) + "&" + "answer={}\"".format(ansList[1]) + ">" + "{}".format(ansList[1]) + "</a><br>"
            page += "<a href=\"/account?" + "factor1={}".format(f1) + "&" + "factor2={}".format(
                f2) + "&" + "answer={}\"".format(ansList[2]) + ">" + "{}".format(ansList[2]) + "</a><br>"
            page += "<a href=\"/account?" + "factor1={}".format(f1) + "&" + "factor2={}".format(
                f2) + "&" + "answer={}\"".format(ansList[3]) + ">" + "{}".format(ansList[3]) + "</a><br>"
            page += '''<h2>Score</h2>
                        Correct: {}<br>
                        Wrong: {}<br>
                        <a href="/account?reset=true">Reset</a>
                        </body></html>'''.format(correct, wrong)
            headers.append(('Set-Cookie', 'score={}:{};expires=Sun, 01 Jan 2023 00:00:00 GMT'.format(correct, wrong)))
        else:
            return ['Not logged in. <a href="/">Login</a>'.encode()]
    elif path == "/":
        page = '''<form action = "/login" style="background-color:gold">
                            <h2>Login</h2>
                            Username <input type="text" name="username"><br>
                            Password <input type="password" name="password"><br>
                            <input type = "submit" value="Log me in!"><br>
                        </form>     
                        <form action = "/register" style="background-color:gold">
                            <h2>Register</h2>
                            Username <input type="text" name="username"><br>
                            Password <input type="password" name="password"><br>
                            <input type = "submit" value="Register">
                        </form>
                        '''
        correct = 0
        wrong = 0
        start_response('200 OK', headers)
        return [page.encode()]
    else:
        start_response('404 Not Found', headers)
        return ['Status 404: Resource not found'.encode()]
    return [page.encode()]


httpd = wsgiref.simple_server.make_server('', 8000, application)
httpd.serve_forever()


