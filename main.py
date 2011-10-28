from commands import *
from PySide.QtCore import *
from PySide.QtGui import *
import sys
import re

re_flags = re.I | re.M

class MetaFile(object):
	'''
	This object contain data and sub-metafiles
	'''
	parent = None
	name = None
	data = None

	def __init__(self, name):
		self.name = name
		self.list = []

	def fullPath(self):
		'''
		Generates full path to the file based on a parent objects
		'''
		p = self.parent
		path = self.name
		while p.parent:
			if p.name:
				path = p.name + '/' + path
			p = p.parent
		return '/' + path

	def get(self, name):
		'''
		Returns sub-metafile with choosed name
		In case metafile not found raises Exception 
		'''
		f = filter(lambda x: x.name == name, self.list)
		if f:
			return f[0]
		else:
			raise Exception, 'MetaFile not found ' + name

	def create(self, name, data=''):
		'''
		Creates children metafile with choosed name and data
		'''
		child = MetaFile(name)
		child.parent = self
		child.data = data
		self.list.append(child)
		return child

	def get_or_create(self, name):
		'''
		It tries to get choose metafile
		In case file not found it creates new one
		'''
		try:
			return self.get(name)
		except:
			return self.create(name)
	
	def delete(self):
		'''
		Deletes current metafile from filesystem
		'''
		self.parent.list.remove(self)
		del self

	def __unicode__(self):
		return self.name

	def __str__(self):
		return self.name or '/'

class Filesystem(object):
	'''
	Generates filesystem structure from choosed file
	'''
	def __init__(self, filename):
		self.filename = filename
		with open(filename) as f:
			data = f.read()
		regex = r':(?P<filename>[\w/\.]+) (?P<code>.*?) @end'
		files = re.findall(regex, data, re_flags)
		#print files
		files = {x[0]:x[1] for x in files}
		self.root = MetaFile(None)
		for f in files:
			filepath = f.split('/')
			c = self.root
			for mf in filepath:
				c = c.get_or_create(mf)
			c.data = files[f]
		self.fs = ''

	def getFile(self, name):
		'''
		Returns MetaFile object
		'''
		if name == '/':
			return self.root
		else:
			name = name[1:]
		filepath = name.split('/')
		c = self.root
		for mf in filepath:
			c = c.get(mf)
		return c

	def read(self, name):
		'''
		Returns data of choosed MetaFile
		'''
		return self.getFile(name).data

	def save(self):
		'''
		Generates new filesyste image and saves it
		'''
		self.save_(self.root)
		with open(self.filename, 'w') as f:
			f.write(self.fs)
		self.fs = ''

	def save_(self, mf):
		for l in mf.list:
			self.save_(l)
		if mf.name:
			self.fs += ':' + mf.name + ' ' + mf.data + ' ' + '@end '

class GraphicsDisplay(QGraphicsView):
	'''
	Describes simple graphic display with 2 primitives
	'''
	keyPress = Signal(int)
	keyRelease = Signal(int)
	items = {}

	def __init__(self):
		QGraphicsView.__init__(self)
		self.s = QGraphicsScene()
		self.s.setSceneRect(0, 0, self.width(), self.height())
		self.setScene(self.s)

	def createRect(self, name, x, y, w, h):
		'''
		Creates a rectangle with a name and coordinates
		'''
		item = QGraphicsRectItem(x, y, w, h)
		item.setBrush(QBrush(QColor(0,0,0)))
		item.setData(0, name)
		self.s.addItem(item)
		self.items[name] = item

	def createEllipse(self, name, x, y, w, h):
		'''
		Creates an ellipse with a name and coordinates
		'''
		item = QGraphicsEllipseItem(x, y, w, h)
		item.setBrush(QBrush(QColor(0,0,0)))
		item.setData(0, name)
		self.s.addItem(item)
		self.items[name] = item

	def moveItem(self, name, dx, dy):
		'''
		Move item with the <name> do x+dx, y+dy
		'''
		i = self.items[name]
		i.translate(dx, dy)

	def checkCollisionsFor(self, name):
		'''
		Finds items which collides with choosed one
		'''
		i = self.items[name]
		a = self.s.collidingItems(i)
		if a:
			a = a[0]
			return a.data(0)
		else:
			return None

	def clear(self):
		'''
		Removes all items from scene
		'''
		for i in self.items:
			self.s.removeItem(self.items[i])
		self.items = {}

	def event(self, e):
		if e.type() == QEvent.Close:
			quit()
		if e.type() == QEvent.KeyPress:
			# We will emit signal here and catch it in CPU
			if not e.isAutoRepeat():
				self.keyPress.emit(e.key())
			return True
		elif e.type() == QEvent.KeyRelease:
			if not e.isAutoRepeat():
				self.keyRelease.emit(e.key())
			return True
		return QGraphicsView.event(self, e)

class Buffer(object):
	'''
	Simple class to make possible to use same object as
	text buffer and as a variable in RAM
	'''
	def __init__(self):
		self.text = ''

	def __str__(self):
		return self.text

	def setText(self, text):
		self.text = text
	
	def append(self, text):
		self.text += text

class TextDisplay(QGraphicsView):
	'''
	Text console
	Optimized for simple rendering text commands
	'''
	next_line_pos = 0
	buffer = None
	fixed_pos = 0
	history = []
	buffer2 = Buffer()
	command_accepted = Signal(str)
	command_accepted2 = Signal()
	keyPress = Signal(int)
	keyRelease = Signal(int)

	def __init__(self):
		QGraphicsView.__init__(self)
		self.s = QGraphicsScene()
		self.s.setSceneRect(0, 0, self.width(), self.height())
		self.setScene(self.s)
		self.buffer = QGraphicsSimpleTextItem()
		self.buffer.setFont(QFont('Consolas'))
		self.s.addItem(self.buffer)
		self.console_mode = True

	def printLine(self, text):
		'''
		Print singleline text with a newline ending
		'''
		if '\n' in text:
			raise Exception, 'You are trying to print multiline text with printLine'
		self.printAny(text)

	def printAny(self, text):
		'''
		Prints any text with a newline ending
		'''
		self.printLazy(text)
		self.printLazy('\n')

	def printLazy(self, text):
		'''
		Print any text
		'''
		if not text.startswith('\n'):
			self.addNewLine()
		self.buffer.setText(self.buffer.text() + text)
		if self.console_mode:
			self.buffer2.setText('')
		else:
			self.buffer2.setText(text)
		self.updateFixedPosition()

	def setBuffer(self, text):
		'''
		Sets buffers to <text>
		'''
		self.buffer2.setText(text)
		self.buffer.setText(text)
		self.updateFixedPosition()

	def setDisplay(self, text):
		'''
		Set display to <text>
		Clears buffers
		'''
		self.buffer.setText(text)
		self.buffer2.setText('')
		self.updateFixedPosition()

	def addNewLine(self):
		'''
		Calculate last line length and adds new line
		'''
		curr = self.buffer.text()
		if len(curr) - curr.rfind('\n') > 71:
			curr += '\n'
		self.checkForEnd()

	def checkForEnd(self):
		'''
		Make buffer save only one display of text
		'''
		curr = self.buffer.text()
		if curr.count('\n') > 24:
			curr = '\n'.join(curr.split('\n')[1:])
		self.buffer.setText(curr)

	def updateFixedPosition(self):
		'''
		Sets fixed_pos to last position
		'''
		if self.console_mode:
			self.fixed_pos = len(self.buffer.text()) + 1

	def event(self, e):
		if e.type() == QEvent.Close:
			quit()
		if e.type() == QEvent.KeyPress:
			# We will emit signal here and catch it in CPU
			if not e.isAutoRepeat():
				self.keyPress.emit(e.key())
		elif e.type() == QEvent.KeyRelease:
			if not e.isAutoRepeat():
				self.keyRelease.emit(e.key())
		if e.type() == QEvent.KeyPress:
			#print self.buffer2
			text = e.text()
			if text == '\r':
				text = '\n'
				self.updateFixedPosition()
				#self.history.append(str(self.buffer2))
				self.command_accepted.emit(str(self.buffer2))
				self.command_accepted2.emit()
				self.buffer2.setText('')
			if text == '\x08':
				if len(self.buffer.text().strip()) >= self.fixed_pos:
					self.buffer.setText(self.buffer.text()[:-1])
					self.buffer2.setText(str(self.buffer2)[:-1])
			elif text:
				if not text == '\n':
					self.addNewLine()
					self.buffer2.append(text)
				else:
					self.checkForEnd()
				self.buffer.setText(self.buffer.text() + text)
			return True
		return QGraphicsView.event(self, e)

class RAM(object):
	'''
	Simple model of RAM
	'''
	memory_objects = {}
	last_addr = 0
	free_addrs = []

	def storeObject(self, o):
		'''
		Saves object and returns address
		'''
		if self.free_addrs:
			a = self.free_addrs.pop()
		else:
			a = self.last_addr
			self.last_addr += 1
		self.memory_objects[a] = o
		return '!' + str(a)

	def removeObjectAt(self, a):
		'''
		Removes object at address <a>
		'''
		# FIXME: I shouldn't delete this, only remove from array
		del self.memory_objects[a]
		self.free_addrs.append(a)

	def removeObject(self, o):
		'''
		Remove the object from RAM
		'''
		addr = self.getAddr(o)
		self.removeObjectAt(addr)

	def getAddr(self, o):
		'''
		Finds and object's address
		'''
		for i in self.memory_objects:
			if self.memory_objects[i] == o:
				return i
		raise Exception, 'Bad object'

	def getObject(self, addr):
		'''
		Returns object located at <addr>
		'''
		if addr in self.memory_objects:
			return self.memory_objects[addr]
		else:
			raise Exception, 'Bad address: %s' % (addr)

class CPU(object):
	'''
	Simple CPU model
	'''
	registers = {
		'0':'',
		'1':'',
		'2':'',
		'3':'',
		'4':'',
		'5':'',
		'6':'',
		'7':'',
		'8':'',
		'9':'',
	}
	IRQs = {
		'key_press': None,
		'key_release': None,
	}
	flags = {
		'reset':False,
		'waiting_for_input':False,
		'exception':False,
	}
	stack = []
	addr_stack = []
	def __init__(self, ram, text_display, graphics_display, filesystem):
		self.ram = ram
		self.text_display = text_display
		self.graphics_display = graphics_display
		# We don't need this
		# self.text_display.graphics_display = graphics_display
		# self.graphics_display.text_display = text_display
		self.filesystem = filesystem

		self.graphics_display.keyPress.connect(self.keyPressEvent)
		self.graphics_display.keyRelease.connect(self.keyReleaseEvent)
		self.text_display.keyPress.connect(self.keyPressEvent)
		self.text_display.keyRelease.connect(self.keyReleaseEvent)

	def keyPressEvent(self, key):
		'''
		Receives key_press events
		Initiate key_press IRQ
		'''
		if not self.IRQs['key_press']:
			return
		self.registers['8'] = str(key)
		self.jumpWithStack(self.IRQs['key_press'])
	
	def keyReleaseEvent(self, key):
		'''
		Receives key_release events
		Initiate key_release IRQ
		'''
		if not self.IRQs['key_release']:
			return
		self.registers['8'] = str(key)
		self.jumpWithStack(self.IRQs['key_release'])

	def jumpTo(self, i):
		'''
		Changes current position to <i>-1 to make <i> command next
		'''
		self.position = int(i) - 1

	def jumpWithStack(self, i):
		'''
		Changes current position to <i>-1 to make <i> command next
		Saves return address into stack
		'''
		self.addr_stack.append(self.position)
		self.position = int(i) - 1

	def init_reset(self):
		'''
		Initiates reset process
		'''
		self.text_display.printLazy('\n\nCPU: Going to reset')
		self.flags['reset'] = True
		#self.position = len(self.data) + 1
		QTimer.singleShot(2000, self.reset)

	def reset(self):
		'''
		Clears hardware and restarts CPU
		'''
		self.ram = RAM()
		self.flags['reset'] = False
		self.text_display.setDisplay('')
		self.graphics_display.clear()
		self.start()

	def readRegister(self, r):
		'''
		Reads register data and in case it's an address returns the object
		located at this address
		'''
		data = str(self.registers[str(r)])
		if not data:
			return ''
		elif data[0] == '!':
			try:
				o = self.ram.getObject(int(data[1:]))
			except:
				self.flags['exception'] = True
			return o
		return str(data)

	def processCommand(self, command, args):
		'''
		Process choosed command with arguments
		'''
		if self.flags['reset']:
			return
		if not command:
			return
		command = int(command)
		if command == commands_str['reset']:
			self.init_reset()
		elif command == commands_str['input']:
			reg = str(args[0])
			l = QEventLoop()
			def gotString(s):
				if not self.flags['waiting_for_input']:
					return
				self.registers[reg] = self.ram.storeObject(s)
				self.flags['waiting_for_input'] = False
				self.text_display.command_accepted.disconnect(gotString)
			self.flags['waiting_for_input'] = True
			self.text_display.command_accepted2.connect(l.exit)
			self.text_display.command_accepted.connect(gotString)
			l.exec_()
			self.text_display.command_accepted2.disconnect(l.exit)
		elif command == commands_str['jmp']:
			pos = int(args[0])
			self.jumpTo(pos)
		elif command == commands_str['jmp_if']:
			pos, reg = args
			if self.registers[str(reg)]:
				self.jumpTo(pos)
		elif command == commands_str['jmp_if_exception']:
			pos = args[0]
			if self.flags['exception']:
				self.jumpTo(pos)
		elif command == commands_str['jmp_if_not']:
			pos, reg = args
			if not self.registers[str(reg)]:
				self.jumpTo(pos)
		elif command == commands_str['store_data']:
			o = args[0]
			a = self.ram.storeObject(o)
			self.registers['2'] = a
		elif command == commands_str['copy']:
			r1, r2 = args
			self.registers[str(r1)] = self.registers[str(r2)]
		elif command == commands_str['free_data']:
			self.ram.removeObjectAt(int(self.registers['2'][1:]))
		elif command == commands_str['add']:
			r1, r2 = args
			d1 = int(self.readRegister(r1))
			d2 = int(self.readRegister(r2))
			self.registers[str(r1)] = d1 + d2
		elif command == commands_str['write']:
			r, data = args
			self.registers[str(r)] = data
		elif command == commands_str['print']:
			r = args[0]
			data = self.readRegister(r)
			self.text_display.printLazy(str(data))
		elif command == commands_str['==']:
			r1, r2, j = args
			if self.readRegister(r1) == self.readRegister(r2):
				self.jumpTo(j)
		elif command == commands_str['!=']:
			r1, r2, j = args
			if self.readRegister(r1) != self.readRegister(r2):
				self.jumpTo(j)
		elif command == commands_str['<']:
			r1, r2, j = args
			if int(self.readRegister(r1)) < int(self.readRegister(r2)):
				self.jumpTo(j)
		elif command == commands_str['<=']:
			r1, r2, j = args
			if int(self.readRegister(r1)) <= int(self.readRegister(r2)):
				self.jumpTo(j)
		elif command == commands_str['>']:
			r1, r2, j = args
			if int(self.readRegister(r1)) > int(self.readRegister(r2)):
				self.jumpTo(j)
		elif command == commands_str['>=']:
			r1, r2, j = args
			if int(self.readRegister(r1)) >= int(self.readRegister(r2)):
				self.jumpTo(j)
		elif command == commands_str['sign']:
			r1 = str(args[0])
			self.registers[str(r1)] = -int(self.registers[str(r1)])
		elif command == commands_str['msleep']:
			msecs = int(args[0])
			l = QEventLoop()
			QTimer.singleShot(msecs, l.exit)
			l.exec_()
			del l
		elif command == commands_str['create_array']:
			reg = str(args[0])
			self.registers[str(reg)] = self.ram.storeObject([])
		elif command == commands_str['get_element']:
			r1, r2 = args
			index = int(self.readRegister(r1))
			arr = self.readRegister(r2)
			self.registers['4'] = self.ram.storeObject(arr[index])
		elif command == commands_str['append_element']:
			r1, r2 = args
			data = self.readRegister(r1)
			arr = self.readRegister(r2)
			arr.append(data)
		elif command == commands_str['set_element']:
			r1, r2, r3 = args
			e = self.readRegister(r1)
			i = self.readRegister(r2)
			self.readRegister(r3)[i] = e
		elif command == commands_str['del_element']:
			r1, r2 = args
			self.readRegister(r2).pop(int(self.readRegister(r1)))
		elif command == commands_str['len']:
			r1, r2 = args
			arr = self.readRegister(r1)
			self.registers[str(r2)] = len(arr)
		elif command == commands_str['push']:
			self.stack.append(self.registers.copy())
		elif command == commands_str['pop']:
			self.registers = self.stack.pop()
		elif command == commands_str['print_line']:
			r = args[0]
			data = self.readRegister(r)
			self.text_display.printLine(str(data))
		elif command == commands_str['execute']:
			r = args[0]
			filename = self.readRegister(r)
			try:
				data = self.filesystem.getFile(filename).data
			except:
				self.text_display.printLine('MetaFile not found')
				self.init_reset()
				return
			self.stack = []
			self.addr_stack = []
			for i in self.IRQs:
				self.IRQs[i] = None
			self.data = data.split(chr(30))
			self.position = -1
		elif command == commands_str['switch_display']:
			d = args[0]
			if d == '0':
				self.graphics_display.hide()
				self.text_display.show()
				self.graphics_display.clear()
			elif d=='1':
				self.text_display.hide()
				self.graphics_display.show()
		elif command == commands_str['ret']:
			self.position = self.addr_stack.pop()
		elif command == commands_str['create_rect']:
			name, x, y, w, h = args
			self.graphics_display.createRect(name, int(x), int(y), int(w), int(h))
		elif command == commands_str['create_ellipse']:
			name, x, y, w, h = args
			self.graphics_display.createEllipse(name, int(x), int(y), int(w), int(h))
		elif command == commands_str['move_item']:
			name, r1, r2 = args
			dx = self.readRegister(r1)
			dy = self.readRegister(r2)
			self.graphics_display.moveItem(name, int(dx), int(dy))
		elif command == commands_str['call']:
			addr = args[0]
			self.jumpWithStack(addr)
		elif command == commands_str['check_for_object_collisions']:
			name = args[0]
			c = self.graphics_display.checkCollisionsFor(name)
			if c:
				self.registers['5'] = self.ram.storeObject(c)
		elif command == commands_str['catch_irq']:
			irq, addr = args
			self.IRQs[irq] = int(addr)
		elif command == commands_str['abandon_irq']:
			irq = args[0]
			self.IRQs[irq] = None
		elif command == commands_str['inc']:
			reg = args[0]
			i = int(self.readRegister(reg))
			self.registers[reg] = str(i + 1)
		elif command == commands_str['dec']:
			reg = args[0]
			i = int(self.readRegister(reg))
			self.registers[reg] = str(i - 1)
		elif command == commands_str['load_file_list']:
			r1, r2 = args
			name = self.readRegister(r2)
			arr = []
			for i in self.filesystem.getFile(name).list:
				arr.append(i.fullPath())
			self.registers[str(r1)] = self.ram.storeObject(arr)
		elif command == commands_str['delete_file']:
			reg = args[0]
			name = self.readRegister(reg)
			f = self.filesystem.getFile(name)
			f.delete()
		elif command == commands_str['load_file_data']:
			r1, r2 = args
			name = self.readRegister(r1)
			f = self.filesystem.read(name)
			self.registers[str(r2)] = self.ram.storeObject(f)
		elif command == commands_str['save_file_data']:
			r1, r2 = args
			data = str(self.readRegister(r1))
			name = str(self.readRegister(r2))
			f = self.filesystem.getFile(name)
			f.data = data
		elif command == commands_str['switch_console_mode']:
			reg = args[0]
			val = bool(int(reg))
			if val:
				self.text_display.console_mode = True
			else:
				self.text_display.console_mode = False
		elif command == commands_str['connect_with_buffer']:
			reg = args[0]
			text = str(self.readRegister(reg))
			self.text_display.buffer2.setText(text)
			self.registers[reg] = self.ram.storeObject(self.text_display.buffer2)
		else:
			print 'Invalid command:', command

	def execute(self):
		'''
		Main loop
		Prepares command and arguments for processCommand
		'''
		while self.position < len(self.data):
			command = self.data[self.position]
			if not command:
				self.position += 1
				continue
			args = []
			if commands_id_args[int(self.data[self.position])] > 0:
				args = self.getAdditionalArgs(commands_id_args[int(self.data[self.position])])
			if commands_id_args[int(self.data[self.position])] == 1:
				args = list(args)
			self.processCommand(command, args)
			self.position += 1

	def start(self):
		'''
		Prepares /boot file for loading and exceutes it
		'''
		data = self.filesystem.read('/boot')
		self.data = data.split(chr(30))
		self.position = 0
		self.execute()

	def getAdditionalArgs(self, n):
		'''
		Returns <n> next valuen in a self.data
		'''
		for i in xrange(n):
			self.position += 1
			yield self.data[self.position]

if len(sys.argv) != 2:
	print 'Usage: %s filesystem_image' % (sys.argv[0])
	quit()
filesystem_image = sys.argv[1]

app = QApplication(sys.argv)

d = TextDisplay()
d.show()
g = GraphicsDisplay()

filesystem = Filesystem(filesystem_image)
cpu = CPU(RAM(), d, g, filesystem)
QTimer.singleShot(100, cpu.start)
sys.exit(app.exec_())