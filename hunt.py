#!/usr/bin/python2
from time import sleep
from re import match
import pydot
import ldif

SESSIONS = "sessions.txt"
TARGETS = "targets.txt"
ADMINS = "admins.txt"
LOCAL_ADMINS = "local_admins.txt"
LDAP = "ldap.ldif"
OWNED = "owneds.txt"
DOMAIN = "CORP"

targets = []
admins = []
owneds = []
hosts = []
users = []
graph = pydot.Dot(graph_type='digraph')

class User:
	def __init__(self, name):
		self.name = name
		self.ip = None
		self.access = []

class Host:
	def __init__(self, ip):
		self.ip = ip
		self.admins = []

def is_user_exists(users, user):
	for u in users:
		if u.name == user.name:
			return True
	return False

def get_user_by_name(username):
	for user in users:
		if user.name == username:
			return user

def create_user(username):
	user = get_user_by_name(username)
	if not user:
		user = User(username)
		users.append(user)
	return user

def get_host_by_ip(ip):
	for host in hosts:
		if host.ip == ip:
			return host

def create_host(ip):
	host = get_host_by_ip(ip)
	if not host:
		host = Host(ip)
		hosts.append(host)
	return host

def get_users_by_group(groupname):
	users = []
	if groupname in ldif.groups:
		for user_dn in ldif.groups[groupname].get("member"):
			for dn in ldif.users.keys():
				if user_dn == dn:
					users.append(ldif.users[user_dn].get('sAMAccountName'))
					break
	else:
		users.append(groupname)
	return users

def parse_session(line):
	ip = None
	user = None
	try:
		if line.find("ANONYMOUS LOGON") != -1:
			pass
		elif line.find("logged off from host") != -1:
			#192.168.0.1: user USERNAME logged off from host 192.168.10.10
			source,_,user,_,_,_,_,ip = line.split(' ')
		elif line.find("logged from host") != -1:
			#192.168.0.1: user USERNAME logged from host 192.168.10.10 - active: 5, idle: 5
			source,_,user,_,_,_,ip,_,_,_,_,_ = line.split(' ')
	except:
		print "[!] " + line
	return (ip,user)

known_edges = []
def process(user):
	for admin in admins:
		if user.name.lower() == admin.name.lower():
			#import pdb;pdb.set_trace()

			host = create_host(user.ip)
			host.name = "%s (%s)" % (user.ip, user.name)
			targets.append(host)
			for new_user in [user] + host.admins:
				if not is_user_exists(admins, new_user):
					admins.append(new_user)
			if host.ip in owneds:
				graph.add_node(pydot.Node(host.ip, label=host.name, style="filled", fillcolor="red"))
			else:
				graph.add_node(pydot.Node(host.ip, label=host.name))
			print "[+] {ip} {user}".format(ip=user.ip, user=user.name)
			for target in admin.access:
				if target in targets:
					if (target.ip, host.ip) in known_edges or target.ip == host.ip:
						continue
					known_edges.append((target.ip, host.ip))
					if host.ip in owneds:
						graph.add_edge(pydot.Edge(host.ip, target.ip, color='blue'))
						owneds.append(target.ip)
					else:
						graph.add_edge(pydot.Edge(host.ip, target.ip))
					#graph.write_png('out.png')

ldif.parse(LDAP)

with open(TARGETS) as f:
	for line in f.read().split('\n'):
		ip = line.strip()
		if ip:
			host = create_host(ip)
			targets.append(host)
			graph.add_node(pydot.Node(host.ip))

with open(ADMINS) as f:
	for line in f.read().split('\n'):
		admin = line.strip()
		if admin:
			admin = create_user(admin)
			admin.access = targets[:]
			admins.append(admin)

with open(OWNED) as f:
	for line in f.read().split('\n'):
		ip = line.strip()
		if ip:
			owneds.append(ip)

with open(LOCAL_ADMINS) as f:
	host = None
	for line in f.read().split('\n'):
		if match("[0-9]+.[0-9]+.[0-9]+.[0-9]+", line):
			host = create_host(ip=line)
		else:
			if host and line:
				domain,username = line.split('\\')
				if domain.lower() == DOMAIN.lower():
					for user in get_users_by_group(groupname=username):
						user = create_user(username)
						user.access.append(host)
						host.admins.append(user)
				else:
					user = create_user(username)
					user.access.append(host)
					host.admins.append(user)

with open(SESSIONS) as f:
	is_end = False
	while True:
		line = f.readline().strip()
		if not line:
			if is_end:
				#sleep(1)
				break
			is_end = True
		else:
			is_end = False
			ip,username = parse_session(line)
			if ip and username:
				user = create_user(username)
				user.ip = ip
				process(user)

graph.write_dot('out.dot')
# eog out.png
# xdot out.dot