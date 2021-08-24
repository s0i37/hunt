#!/usr/bin/python2
import sys
import base64


class Object:
	def __init__(self):
		self.is_user = False
		self.is_contact = False
		self.is_computer = False
		self.is_group = False
		self.is_container = False

	def save(self,attr,val):
		#print "%s:%s" % ( attr, val )
		if attr in self.__dict__:
			try:
				self.__dict__[attr].append(val)
			except:
				self.__dict__[attr] = [val]
		else:
			self.__dict__[attr] = val

	def get(self, attr):
		return self.__dict__.get(attr) or ''

def get_attr(line):
	if line.split()[0].find('::') != -1:
		return ( True, line.split('::')[0].strip(), line.split('::')[1].strip() )
	elif line.split()[0].find(':') != -1:
		return ( False, line.split(':')[0].strip(), line.split(':')[1].strip() )
	else:
		return ( False, '', line.strip() )

users = {}
contacts = {}
computers = {}
groups = {}
containers = {}

def parse(ldif):
	global users, contacts, computers, groups, containers
	obj = prev_attr = prev_val = prev_is_base64 = None
	with open(ldif, 'r') as f:
		for line in f.readlines():
			line = line.split('\n')[0]
			#print line
			if line.startswith('#'):
				continue
			elif line == '':
				if prev_attr and prev_val:
					if prev_is_base64:
						obj.save( prev_attr, base64.decodestring(prev_val) )
					else:
						obj.save( prev_attr, prev_val )
					prev_attr = ''
					prev_val = ''
				if obj:
					if obj.is_user:
						users[obj.sAMAccountName] = obj
					elif obj.is_contact:
						contacts[obj.cn] = obj
					elif obj.is_computer:
						computers[obj.cn] = obj
					elif obj.is_group:
						groups[obj.cn] = obj
					elif obj.is_container:
						containers[obj.dn] = obj
				obj = Object()
				prev_attr = prev_val = prev_is_base64 = None
			else:
				is_base64, attr, val = get_attr(line)

				if attr and prev_val:# and attr != prev_attr:
					if prev_is_base64:
						obj.save( prev_attr, base64.decodestring(prev_val) )
					else:
						obj.save( prev_attr, prev_val )

				if attr:
					prev_is_base64 = is_base64
					prev_attr = attr
					prev_val = val
				elif prev_val:
					prev_val += val

				if attr == 'objectClass':
					if val == 'user' and not 'computer' in obj.get('objectClass'):
						obj.is_user = True
					elif val == 'contact':
						obj.is_contact = True
					elif val == 'computer':
						obj.is_user = False
						obj.is_computer = True
					elif val == 'group':
						obj.is_group = True
					elif val == 'organizationalUnit':
						obj.is_container = True

if __name__ == '__main__':
	parse(sys.argv[1])
	import ipdb;ipdb.set_trace()
