import bpy
import math
import numpy as np
from mathutils import Color
import matplotlib.cm as cm
import sys

####################################################
# clear the scene
####################################################
def clear_scene():
	
	# clear mesh and object
	for item in bpy.context.scene.objects:
		if item.type == 'MESH':
			bpy.context.scene.objects.unlink(item)
	for item in bpy.data.objects:
		if item.type == 'MESH':
			bpy.data.objects.remove(item)
	for item in bpy.data.meshes:
		bpy.data.meshes.remove(item)
	for item in bpy.data.materials:
		bpy.data.materials.remove(item)

####################################################
# init the scene
####################################################
def init_scene(nFrame):
	bpy.context.scene.frame_start = 0
	bpy.context.scene.frame_end = nFrame


####################################################
# create the vertices
####################################################
def create_verts(X,Y,Z):

	""" Create the vertices, faces and colors of the grid points
		X and Y are 1D array of size nx and ny 
		Z must be a 1D array of size nx*ny if provided """

	# declare the verts arrays
	verts = []

	# define the verts and colors
	k=0
	for ix,x in enumerate(X):
		for iy,y in enumerate(Y):   
				verts.append((x,y,Z[k]))
				k+=1
	return verts

####################################################
# create the faces
####################################################
def create_faces(numX,numY):
	""" create the faces of the verts 
	This only works for a perfect rectangular mesh """

	# fill faces array
	count,faces = 0,[]

	# loop through all the indexes
	for i in range (0, numY *(numX-1)):
		if count < numY-1:
			face = (i, i+1, (i+numY)+1, (i+numY))
			faces.append(face)
			count = count + 1
		else:
			count = 0
	return faces 

####################################################
# color the vertex of the mesh
####################################################
def color_vertex(obj,color):

	"""Paints all the vertex of the object
	 color is a tuple with the RGB values of all the vertexes."""

	mesh = obj.data 
	scn = bpy.context.scene

	#check if our mesh already has Vertex Colors, and if not add some... 
	#(first we need to make sure it's the active object)
	scn.objects.active = obj
	obj.select = True
	if mesh.vertex_colors:
		vcol_layer = mesh.vertex_colors.active
	else:
		vcol_layer = mesh.vertex_colors.new()

	for poly in mesh.polygons:
		for loop_index in poly.loop_indices:
			loop_vert_index = mesh.loops[loop_index].vertex_index
			vcol_layer.data[loop_index].color = color[loop_vert_index]


####################################################
# Create the object and mesh of the data
####################################################
def create_object(X,Y,Z,name='grid',matname='gridMat',location=None,cmap=None,makeactive=True):

	# create mesh and object
	mesh = bpy.data.meshes.new(name)
	obj = bpy.data.objects.new(name,mesh)

	# move the object if specified
	if location != None:
		obj.location = location
	bpy.context.scene.objects.link(obj)

	# create the vects, faces and colors
	verts = create_verts(X,Y,Z)
	faces = create_faces(len(X),len(Y))
	
	# link the grid to the mesh
	mesh.from_pydata(verts,[],faces)
	mesh.update(calc_edges=True)

	# new material
	mat = bpy.data.materials.new(name=matname)
	obj.data.materials.append(mat)

	# apply the cmap if specified
	if cmap != None:

		# colormap
		colors = cmap(Z)[:,:3]

		# colors of the verts
		for iv in range(len(verts)):
			color_vertex(obj,colors)
		mat.use_vertex_color_paint = True

	# make this object active
	if makeactive:
		bpy.context.scene.objects.active=bpy.data.objects[name]

	return obj

####################################################
# modify the mesh 
####################################################
def modify_mesh(Z):

	# get the mesh information
	obj = bpy.data.objects['grid']
	me = obj.data
	colors = _cmap_(Z)[:,:3]
	color_vertex(obj,colors)	
	
	# modify the meshes
	for iv,v in enumerate(me.vertices):
		v.co[2] = Z[iv]
		
	# recalculate the normals for smooth shading
	me.calc_normals()

####################################################
# fram handler to create the animaation
# every frame change, this function is called.
####################################################
def frame_handler(scene):
    frame = scene.frame_current
    modify_mesh(_Zdata_[frame].flatten())
    

#################################################
# Generate data for demonstration
#################################################
def generate_demo_data(nx=25,ny=25,nFrame=101):

	def gaussian2D(X,Y,x0=0,y0=0,sx=0.25,sy=0.25):
		gx = np.exp(-(X-x0)**2/sx**2)
		gy = np.exp(-(Y-y0)**2/sy**2)
		return (gx*gy[:,np.newaxis]).flatten()

	X = np.linspace(-1,1,nx)
	Y = np.linspace(-1,1,ny)

	x0 = np.linspace(0,0.5,nFrame)
	y0 = np.zeros(nFrame)

	Z = []
	for iF in range(nFrame):
		Z.append(gaussian2D(X,Y,x0[iF],y0[iF]))
	return X,Y,Z

#################################################
# load the data from a data file
#################################################
def load_data(filename):
	data = np.load(filename)
	X = data['xaxis']
	Y = data['yaxis']
	Zdata = data['zdata']
	return X,Y,Zdata

##################################################
# create the blender animation
##################################################
def create_blender_animation(filename=None,cmap=cm.Blues):

	# generate the data if we did not specify a data filename
	# the _Zdata_ and cmap needs to be global as it is used by the handler
	global _Zdata_
	global _cmap_ 

	if filename==None:
		X,Y,_Zdata_ = generate_demo_data()
	else:
		# load the data
		X,Y,_Zdata_ = load_data(filename)

	# init the colormap
	_cmap_ = cmap

	# start/end frame
	if _Zdata_.ndim != 3:
		print('Dimension error with the Zdata')
	init_scene(len(_Zdata_)-1)
	
		
	# create the object, mesh and verts
	obj = create_object(X,Y,_Zdata_[0].flatten(),cmap=_cmap_)

	# clear the handlers
	bpy.app.handlers.frame_change_pre.clear()

	# append the handler
	bpy.app.handlers.frame_change_pre.append(frame_handler)



PATH = ''
clear_scene()

# load a fixed object
objname = PATH + '/pot_data.npz'
xpot,ypot,zpot = load_data(objname)
create_object(xpot,ypot,zpot.flatten(),name='pot',matname='potMat',cmap=cm.bone,makeactive=False)

# load the data of the moving surface
filename = PATH+'/schrodinger_data.npz'
create_blender_animation(filename,cmap=cm.BuGn)









