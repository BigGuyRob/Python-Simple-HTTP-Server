import socket
import signal
import sys
import random

from requests import get

# Read a command line argument for the port where the server
# must run.
port = 8080
host_name = socket.gethostname()
if len(sys.argv) > 1:
    port = int(sys.argv[1])
else:
    print("Using default port 8080")

# Start a listening server socket on the port
sock = socket.socket()
sock.bind(('', port))
sock.listen(2)

### Contents of pages we will serve.
# Login form
login_form = f"""
   <form action = "http://{host_name}:{port}" method = "post">
   Name: <input type = "text" name = "username">  <br/>
   Password: <input type = "text" name = "password" /> <br/>
   <input type = "submit" value = "Submit" />
   </form>
"""
# Default: Login page.
login_page = "<h1>Please login</h1>" + login_form
# Error page for bad credentials
bad_creds_page = "<h1>Bad user/pass! Try again</h1>" + login_form
# Successful logout
logout_page = "<h1>Logged out successfully</h1>" + login_form
# A part of the page that will be displayed after successful
# login or the presentation of a valid cookie
success_page = f"""
   <h1>Welcome!</h1>
   <form action="http://{host_name}:{port}" method = "post">
   <input type = "hidden" name = "action" value = "logout" />
   <input type = "submit" value = "Click here to logout" />
   </form>
   <br/><br/>
   <h1>Your secret data is here:</h1>
"""
#makes a new cookie header, returns two values
#you can call it like this:
# number, header = make_new_cookie_header()
def make_new_cookie_header():
    rand_val = random.getrandbits(64)
    return rand_val, 'Set-Cookie: token=' + str(rand_val) + '\r\n'
#retrieves the cookie value from a request
#you can give it the entire header and it should return the cookie
#if there is no cookie it will return None
def get_cookie_from_request(request):
    for line in request.split('\n'):
        # print(line.lower())
        # print("cookie" in line.lower())
        if "cookie" in line.lower():
            split = line.split('=')
            try:
                return int(split[-1])
            except ValueError:
                return None

#### Helper functions
# Printing.
def print_value(tag, value):
    print( "Here is the", tag)
    print( "\"\"\"")
    print( value)
    print( "\"\"\"")
    print()

# Signal handler for graceful exit
def sigint_handler(sig, frame):
    print('Finishing up by closing listening socket...')
    sock.close()
    sys.exit(0)
# Register the signal handler
signal.signal(signal.SIGINT, sigint_handler)

passwords = {}
secrets = {}
#initialize the cookies database, we will fill it later
cookies = {}

for line in open("passwords.txt", "r"):
    split_line = line.split()
    passwords[split_line[0]] = split_line[1]
for line in open("secrets.txt", "r"):
    split_line = line.split()
    secrets[split_line[0]] = split_line[1]
print(passwords, secrets)
### Loop to accept incoming HTTP connections and respond.
while True:
    client, addr = sock.accept()
    req = client.recv(1024).decode()

    # Let's pick the headers and entity body apart
    header_body = req.split('\r\n\r\n')
    headers = header_body[0]
    body = '' if len(header_body) == 1 else header_body[1]
    print_value('headers', headers)
    print_value('entity body', body)
    username = ''
    password = ''
    authenticationFlag = False
    usernameNotFoundFlag = False
    passwordNotFoundFlag = False
    makeCookieFlag = True 
    headers_to_send = ''
    #Recover username and password from body field=val&field2=val no matter if we actually have data for this form
    if(body == "action=logout"):
        print("connection closed")
    else:
        if(body):
            a = body.split("&")
            usernameA = a[0]
            passwordA = a[1]
            username = usernameA.split("=")[1]
            password = passwordA.split("=")[1]
            
            try:
                if(passwords[username] == password):
                    #If we look at the passwords and the password is correct then auth flag is good
                    authenticationFlag = True
                else:
                    #If we look at the passwords and the password is incorrect auth flag stays false but password has not been found
                    passwordNotFoundFlag = True
            except KeyError:
                #The username was not in the passwords file if we get a keyerror we were unable to find the username
                usernameNotFoundFlag = True
            if(get_cookie_from_request(headers) and not authenticationFlag):
                token = get_cookie_from_request(headers)
                #If we get a cookie check it against the cookies we got
                print("got cookie " + str(token))
                try:
                    credentials = cookies[token]
                    username = credentials[0]
                    password = credentials[1]
                    makeCookieFlag = False
                    authenticationFlag = True
                except KeyError:
                    #If the cookie isnt good we just stay with whatever was input
                    pass
    html_content_to_send = ''
    
    if(authenticationFlag):
        if(makeCookieFlag):
            rand_val, headers_to_send = make_new_cookie_header()
            cookies[rand_val] = [username,password]
        html_content_to_send = success_page + secrets[username]
    else:
        if(username.strip() == '' and password.strip() == ''):
            #User did not input any credentials, redirect to log in page regardless of any flags
            html_content_to_send = login_page
        elif(usernameNotFoundFlag or passwordNotFoundFlag):
            #If one of the fields is filled in, but was wrong in that username or password was not found
            html_content_to_send = bad_creds_page
        else:
            html_content_to_send = login_page
    # But other possibilities exist, including
    # html_content_to_send = success_page + <secret>
    # html_content_to_send = bad_creds_page
    # html_content_to_send = logout_page
    # Construct and send the final response
    response  = 'HTTP/1.1 200 OK\r\n'
    response += headers_to_send
    response += 'Content-Type: text/html\r\n\r\n'
    response += html_content_to_send
    print_value('response', response)
    client.send(response.encode())
    client.close()

    print("Served one request/connection!")
    print()

# We will never actually get here.
# Close the listening socket
sock.close()
