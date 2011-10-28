command_list = (
	dict(name='reset', args=0),

	# arg - register number
	dict(name='input', args=1),

	# arg - intruction number
	dict(name='jmp', args=1),

	# arg1 - register
	# arg2 - instruction
	# if object in register arg1 is not 0 jmp to arg2
	dict(name='jmp_if', args=2),
	# Same as above, but jumps if 0
	dict(name='jmp_if_not', args=2),
	# Jumps only if exception flag is true and sets it to false
	dict(name='jmp_if_exception', args=1),
	# If [object in] register[arg1] equal to [object in] register[arg2] jump to intruction arg3
	dict(name='==', args=3),
	# Same as above but "if not equal"
	dict(name='!=', args=3),
	#
	dict(name='<', args=3),
	dict(name='<=', args=3),
	dict(name='>', args=3),
	dict(name='>=', args=3),

	dict(name='sign', args=1),
	# Jumps to arg1 but saves return address into stack
	dict(name='call', args=1),

	# Store data in RAM, id_ of the data will be in register #2
	dict(name='store_data', args=1),

	# Copy data from register[arg2] to register[arg1]
	dict(name='copy', args=2),

	# Free object from RAM, id_ should be in register #2
	dict(name='free_data', args=0),

	# Add value of register[arg2] to register[arg1]
	dict(name='add', args=2),

	# Increments value in register[arg1]
	dict(name='inc', args=1),
	# Decrements value in register[arg1]
	dict(name='dec', args=1),

	# Write arg2 to register[arg1]
	dict(name='write', args=2),

	# Print value of register #arg
	dict(name='print', args=1),
	# Same as above but adds \n at the end
	dict(name='print_line', args=1),

	# Sleep for register #1 miliseconds
	dict(name='msleep', args=1),

	# Working with arrays
	# Creates emty array, writer id_ to register[arg]
	dict(name='create_array', args=1),
	# Get element at index arg1 of array arg2
	dict(name='get_element', args=2),
	# Append element arg1 to array arg2
	dict(name='append_element', args=2),
	# Set element arg1 to index arg of array arg2
	dict(name='set_element', args=3),
	# Delete element at index arg1 of array arg2
	dict(name='del_element', args=2),
	# Write length  of array arg1 to register arg2
	dict(name='len', args=2),

	# Stack
	# Saves state of register intp stack
	dict(name='push', args=0),
	# Reads and sets state of register from stack
	dict(name='pop', args=0),

	# Loads file data into CPU and begins execution
	dict(name='execute', args=1),

	# Switch between text and graphics display
	dict(name='switch_display', args=1),

	# Jumps back to the previous address in stack
	dict(name='ret', args=0),

	# Graphics
	# Creates rectangle with specified coordinates (name, x, y, wid_th, height)
	dict(name='create_rect', args=5),
	# Creates an ellipse with specified coordinates (name, x, y, wid_th, height)
	dict(name='create_ellipse', args=5),
	# Moves item arg1 to (register[arg2], register[arg3])
	dict(name='move_item', args=3),
	# Check collisions for object arg1 and store name of collid_ing object to register[5]
	# At this time it supports only one object
	dict(name='check_for_object_collisions', args=1),

	# Sets an address to jump on arg1 IRQ
	dict(name='catch_irq', args=2),

	# Clears jump adress of arg1 IRQ
	dict(name='abandon_irq', args=1),

	# Loads file list of MetaFile(arg1) and save address in register[arg2]
	dict(name='load_file_list', args=2),
	# Deletes file
	dict(name='delete_file', args=1),
	# Loads data from file arg1 into register arg2
	dict(name='load_file_data', args=2),
	dict(name='load_or_create_file', args=2),
	# Saves data from register[arg1] to file at register[arg2] 
	dict(name='save_file_data', args=2),

	# Disables new lines
	dict(name='switch_console_mode', args=1),
	# Set connection between object in register[arg1] and text buffer
	dict(name='connect_with_buffer', args=1),
)

commands_str = {}
for id_, i in enumerate(command_list):
	commands_str[i['name']] = id_

commands_id = {}
for id_, i in enumerate(command_list):
	commands_id[id_] = i['name']

commands_str_args = {}
for id_, i in enumerate(command_list):
	commands_str_args[i['name']] = i['args']

commands_id_args = {}
for id_, i in enumerate(command_list):
	commands_id_args[id_] = i['args']