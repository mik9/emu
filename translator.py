from commands import *
import sys
import os

if len(sys.argv) != 3:
	print 'Usage: %s folder_with_files filesystem_image' % (sys.argv[0])
	quit()

def translate(filename):
	f = open(filename)

	labels = {}
	command_count = 0
	code = ''
	for_replace = list()
	for line in f:
		line = line.split('#')[0].strip()
		if not line:
			continue
		args = []
		tmp = line.strip().split(' ')
		if len(tmp) > 1:
			my_command, args = tmp[0], tmp[1:]
		else:
			my_command = tmp[0]
		if my_command == 'label':
			labels[args[0].strip()] = command_count
			continue
		elif my_command.startswith('jmp') or my_command in ['==', '!=', 'call', 'catch_irq', '<', '<=', '>', '>=']:
			for_replace.append(args[-1])
			args[-1] = '%s'
		elif my_command == 'store_data':
			args = [' '.join(args)]
		cc = False
		for command in command_list:
			if my_command == command['name']:
				cc = True
				code += str(commands_str[command['name']])
				code += chr(30)
				if len(args) != command['args']:
					print args
					raise Exception, 'Syntax error at:\n%s\nNeed %d arguments, got %d:' % (line, command['args'], len(args))
				for arg in args:
					code += str(arg)
					code += str(chr(30))
		if not cc:
			raise Exception, 'Unknown command %s' % (my_command)
			continue
		command_count += 1 + len(args)
	for_replace2 = tuple(labels[i] for i in for_replace)
	code = code % (for_replace2)
	return code

files = []
root = sys.argv[1]
for dirpath, dirnames, filenames in os.walk(root):
	print dirpath, dirnames, filenames
	for file in filenames:
		#dirpath = dirpath.replace(root + '\\','')
		files.append(os.path.join(dirpath, file))

fs = ''
for f in files:
	fs += ':' + f.replace('\\', '/').replace(root + '/', '')
	fs += ' ' + translate(f) + ' '
	fs += '@end '
with open(sys.argv[2], 'w') as image:
	image.write(fs)