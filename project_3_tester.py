import requests
from bs4 import BeautifulSoup
from sys import argv
host_name = 'localhost'
VERBOSE=False
if len(argv) > 1:
	PORT = argv[1]
	if len(argv) > 2:
		VERBOSE = 'v' in argv[2] or 'V' in argv[2]
else:
	PORT = 8080
READ_DEST = True
# print(dest_url)
# response = s.post(url, data={'username':'bezos', 'password':'amazon'})
# print(response.text)
# print(response.cookies)
# s.close()
# s2 = requests.Session()
# req = s2.get(url, cookies={})
# print(req.text)
def get_current_page(verbose=VERBOSE):
	with requests.Session() as s:
		url = f'http://{host_name}:{PORT}/'
		req = s.get(url)
	if verbose:
		print(req.text)
	return req
def post_with_username_pass(username, password, verbose=VERBOSE, clear_cookies=True, get_cookies=False, cookies={}, logout=False):
	global READ_DEST
	with requests.Session() as s:
		url = f'http://{host_name}:{PORT}/'
		req = s.get(url)
		if READ_DEST:
			soup = BeautifulSoup(req.text, 'html.parser')
			url2 = soup.find('form')['action']
		else:
			url2 = url
		if clear_cookies:
			# print(s.cookies)
			s.cookies.clear()
		if logout:
			data = {'action':'logout'}
		else:
			data={'username':username, 'password':password}
		try:
			response = s.post(url2, data=data, cookies=cookies)
		except requests.exceptions.ConnectionError:
			if READ_DEST:
				print('FAILED TO CONNECT, changing url and retrying')
				READ_DEST = False
				response = s.post(url, data=data, cookies=cookies)
			else:
				print('FAILED TO CONNECT')
				return
		if verbose:
			print(response)
			print(response.request.headers)
			print(response.request.body)
			print(response.text)
		if get_cookies:
			if verbose:
				print(f'cookies {s.cookies}')
			return response, dict(s.cookies)
		return response
def extract_secret(http, verbose=VERBOSE):
	if http == None:
		return False
	soup = BeautifulSoup(http.text, 'html.parser')
	secret = soup.get_text('\n').strip().split('\n')[-1]
	if verbose:
		print(secret)
	return secret
def extract_message(http, verbose=VERBOSE):
	soup = BeautifulSoup(http.text, 'html.parser')
	message = soup.get_text('\n').strip().split('\n')[0]
	if verbose:
		print(f'message is {message}')
	return message
def evaluate_test(condition, passes, failures):
	if condition:
		print('PASSED')
		passes += 1
	else:
		print('FAILED')
		failures += 1
	return passes, failures

failures = 0
passes = 0


#test 1
#here we test that with a blank username and password, and no cookies, we get the login page
print('TEST 1')
page = post_with_username_pass('', '')
message = extract_message(page)
passes, failures = evaluate_test(message.strip() == 'Please login', passes, failures)

#test 2
#here we test that with a correct user and password, we get the secret data
print('TEST 2')
page = post_with_username_pass('naiveuser', 'password123')
secret = extract_secret(page)
passes, failures = evaluate_test(secret.strip() == 'mymostsecretpassword', passes, failures)

#test 3a
#here we make sure that cookies are only sent to users who log in correctly
print('TEST 3a (additional test) (tests whether cookies is sent automatically to all users)')
page = post_with_username_pass('naiveuser', 'wrong_password', clear_cookies=False)
secret = extract_secret(page)
passes, failures = evaluate_test(secret.strip() != 'mymostsecretpassword', passes, failures)

#test 3
#Here we check that the wrong username leads to the bad user/pass page
print('TEST 3')
page = post_with_username_pass('not_a_user', 'password')
message = extract_message(page)
passes, failures = evaluate_test(message.strip() == "Bad user/pass! Try again", passes, failures)

#test 4
#here we check that right username wrong password also leads to the wrong page
print('TEST 4')
page = post_with_username_pass('naiveuser', 'bad_password')
message = extract_message(page)
passes, failures = evaluate_test(message.strip() == "Bad user/pass! Try again", passes, failures)

#test 5
#here we check that blank username and non-blank password leads to bad pass page
print('TEST 5')
page = post_with_username_pass('', 'bad_password')
message = extract_message(page)
pass_only = message.strip() == "Bad user/pass! Try again"
page = post_with_username_pass('bad_user', '')
message = extract_message(page)
passes, failures = evaluate_test(message.strip() == "Bad user/pass! Try again" and pass_only, passes, failures)

#test 6
#here we check 2 things, 1 that we successfully se cookies, two that we read the cookie sent, not just the last user
print('TEST 6')
page,cookies = post_with_username_pass('bezos', 'amazon', get_cookies=True)
page = post_with_username_pass('naiveuser', 'password123')
page = post_with_username_pass('', '',cookies=cookies)
secret = extract_secret(page)
passes, failures = evaluate_test(secret.strip() == 'kaching', passes, failures)

#test 7
#here we check that as long as we have a good cookie, even if the entered data is wrong, we get the secret
print('TEST 7')
page,cookies = post_with_username_pass('bezos', 'amazon', get_cookies=True)
page = post_with_username_pass('naiveuser', 'password123')
page = post_with_username_pass('naiveuser', 'wrong_password',cookies=cookies)
message = extract_message(page)
passes, failures = evaluate_test(secret.strip() == 'kaching', passes, failures)

print(f'failures: {failures} passes: {passes}')
