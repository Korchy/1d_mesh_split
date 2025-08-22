# Nikita Akimov
# interplanety@interplanety.org
#
# GitHub
#    https://github.com/Korchy/1d_mesh_split

import bmesh
import bpy
from bpy.props import EnumProperty, IntProperty
from bpy.types import Operator, Panel, WindowManager
from bpy.utils import register_class, unregister_class
from mathutils import Vector
from time import time

bl_info = {
    "name": "1D Mesh Split",
    "description": "Split Mesh by Density",
    "author": "Nikita Akimov, Paul Kotelevets",
    "version": (1, 0, 0),
    "blender": (2, 79, 0),
    "location": "View3D > Tool panel > 1D > Mesh Split",
    "doc_url": "https://github.com/Korchy/1d_mesh_split",
    "tracker_url": "https://github.com/Korchy/1d_mesh_split",
    "category": "All"
}


# MAIN CLASS

class MeshSplit:

    @classmethod
    def split_by_density(cls, context, split_parts=5, split_mode='VERTS', split_direction='X'):
        # split mesh by density
        #   mode 'VERTS' | 'FACES' - different counting modes
        if context.active_object and split_parts > 1:
            # execution time
            first_time = time()
            start_time = time()
            # current mode
            mode = context.active_object.mode
            if context.active_object.mode == 'EDIT':
                bpy.ops.object.mode_set(mode='OBJECT')
            # deselect all
            cls._deselect_all(obj=context.active_object)
            print('after deselect all ', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
            start_time = time()
            # count number of vertices in one part
            vertices_in_a_part = round(cls.vertices_in_part(
                context=context,
                parts=split_parts
            ))
            print('after vertices in a part', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
            start_time = time()
            # split by split_parts
            if split_mode == 'VERTS':
                print('VERTS mode')
                # counting by vertices
                for _i in range(split_parts - 1):   #  (-1 because ex: 5 parts = 4 cuts)
                    if split_direction == 'X':
                        vertices_sorted = sorted(context.active_object.data.vertices, key=lambda _vert: _vert.co.x)
                    elif split_direction == 'Y':
                        vertices_sorted = sorted(context.active_object.data.vertices, key=lambda _vert: _vert.co.y)
                    else:   # 'Z'
                        vertices_sorted = sorted(context.active_object.data.vertices, key=lambda _vert: _vert.co.z)
                    print('after vertices_sorted', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    vertices_to_split = vertices_sorted[:vertices_in_a_part]
                    # we need to select faces by vertices_to_split
                    vertices_to_split_ids = set(_v.index for _v in vertices_to_split)
                    for face in context.active_object.data.polygons:
                        if set(face.vertices).issubset(vertices_to_split_ids):
                            face.select = True
                    print('after face', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    # context.active_object.data.validate()
                    # context.active_object.data.update()
                    # # context.active_object.update_from_editmode()
                    # if selected faces exists - split
                    selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                    if selected_faces_n:
                        bpy.ops.object.mode_set(mode='EDIT')
                        print('after switch to edit mode', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                        start_time = time()
                        bpy.ops.mesh.separate(type='SELECTED')
                        print('after split', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                        start_time = time()
                        bpy.ops.object.mode_set(mode='OBJECT')
                        print('after switch to object mode', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                        start_time = time()
                    print('end of iteration', _i)
            elif split_mode == 'FACES':
                print('FACES mode')
                # counting by faces centroids
                for _i in range(split_parts - 1):   #  (-1 because ex: 5 parts = 4 cuts)
                    # get faces sorted by centroids by local X coordinate
                    faces_sorted = cls._faces_sorted_by_centroid(
                        obj=context.active_object,
                        axis=split_direction,
                    )
                    print('after faces_sorted', round(time() - first_time, 5), '(+', round(time() - start_time, 5),')')
                    start_time = time()
                    # we need to get faces from faces_sorted with summar number of vertices near number of vertices_in_a_part
                    #   and split it from current object
                    faces_vertices = set()  # vertices counter
                    # walk from left by sorted faces
                    for _face in faces_sorted:
                        # increase counter by faces vertices amount
                        faces_vertices.update(_face[1])
                        # if counter less vertices_in_a_part - select face and continue#
                        # else - split selected faces
                        if len(faces_vertices) < vertices_in_a_part:
                            _face[0].select = True
                        else:
                            print('after faces selected', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                            start_time = time()
                            # if selected faces exists - split
                            selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                            if selected_faces_n:
                                bpy.ops.object.mode_set(mode='EDIT')
                                print('after switch to edit mode', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                                start_time = time()
                                bpy.ops.mesh.separate(type='SELECTED')
                                print('after split', round(time() - first_time, 5), '(+', round(time() - start_time, 5),')')
                                start_time = time()
                                bpy.ops.object.mode_set(mode='OBJECT')
                                print('after switch to object mode', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                                start_time = time()
                                # after splitting we need to start from beginning because mesh was rebuilt
                                break
                    print('end of iteration', _i)
            elif split_mode == 'BM':
                print('BM mode')
                # use bmesh
                bm = bmesh.new()
                bm.from_mesh(context.active_object.data)
                bm.verts.ensure_lookup_table()
                bm.faces.ensure_lookup_table()
                # splitting to number of parts
                for _i in range(split_parts - 1):  # (-1 because ex: 5 parts = 4 cuts + 1 cut / 2)
                    if split_direction == 'X':
                        vertices_sorted = sorted(bm.verts, key=lambda _vert: _vert.co.x)
                    elif split_direction == 'Y':
                        vertices_sorted = sorted(bm.verts, key=lambda _vert: _vert.co.y)
                    else:   # 'Z'
                        vertices_sorted = sorted(bm.verts, key=lambda _vert: _vert.co.z)
                    print('after vertices_sorted', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    vertices_to_split = set(vertices_sorted[:vertices_in_a_part])
                    # we need to select faces by vertices_to_split
                    for face in bm.faces:
                        if set(face.verts).issubset(vertices_to_split):
                            face.select = True
                    print('after face selected', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    # from selected faces we need to create data for from_pydata function (faces and vertices_co lists)
                    selected_faces = [face for face in bm.faces if face.select]
                    vertices = list(set(v for f in selected_faces for v in f.verts))
                    coordinates = [v.co for v in vertices]
                    vmap = dict()
                    for i, vert in enumerate(vertices):
                        vmap[vert.index] = i
                    faces = []
                    for face in selected_faces:
                        faces.append([vmap[v.index] for v in face.verts])
                    print('after preparing pydata', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    # remove selected faces not to use them on the next step
                    bmesh.ops.delete(bm, geom=selected_faces, context=5)
                    print('after remove', round(time() - first_time, 5), '(+', round(time() - start_time, 5), ')')
                    start_time = time()
                    # create new mesh from collected data
                    me = bpy.data.meshes.new(name=context.active_object.name)
                    me.from_pydata(coordinates, [], faces)
                    scene = context.scene
                    obj = bpy.data.objects.new(context.active_object.name, me)
                    scene.objects.link(obj)
                    obj.matrix_world = context.active_object.matrix_world.copy()
                    print('end of iteration', _i)
                # save changed data to mesh
                bm.to_mesh(context.active_object.data)
                bm.free()
            # return mode back
            bpy.ops.object.mode_set(mode=mode)
            # execution time
            print('Executed in %s seconds' % (round(time() - first_time, 2)))

    @staticmethod
    def vertices_in_part(context, parts):
        # count number of vertices in one part of splitting mesh
        if context.active_object and parts != 0:
            if context.active_object.mode == 'OBJECT':
                vertices_in_part = len(context.active_object.data.vertices) / parts
            else:   # EDIT
                bm = bmesh.from_edit_mesh(context.active_object.data)
                vertices_in_part = len(bm.verts) / parts
                # bm.free()     # if not commented - crushed with AttributeError: 'bytes' object has no attribute 'verts'
            return vertices_in_part
        else:
            return 0

    @staticmethod
    def _deselect_all(obj):
        # deselect all vertices/edges/faced on mesh data
        for face in obj.data.polygons:
            face.select = False
        for edge in obj.data.edges:
            edge.select = False
        for vertex in obj.data.vertices:
            vertex.select = False

    @staticmethod
    def centroid(vertices):
        x_list = [vertex[0] for vertex in vertices]
        y_list = [vertex[1] for vertex in vertices]
        z_list = [vertex[2] for vertex in vertices]
        length = len(vertices)
        x = sum(x_list) / length
        y = sum(y_list) / length
        z = sum(z_list) / length
        return Vector((x, y, z))

    @classmethod
    def _faces_sorted_by_centroid(cls, obj, axis='X'):
        # get list of faces (with additional data) sorted by face centroid X local coordinate
        #   [(face, [face vertices ids], face_centroid_co), ...] => [(face_ptr, [1, 3, 4], Vector(x,y,z)), ...]
        faces = [(_face, _face.vertices, cls.centroid([obj.data.vertices[v_id].co for v_id in _face.vertices])) \
                 for _face in obj.data.polygons]
        # return faces sorted by local X centroid coordinates
        if axis == 'X':
            return sorted(faces, key=lambda _face: _face[2].x)
        elif axis == 'Y':
            return sorted(faces, key=lambda _face: _face[2].y)
        else:
            return sorted(faces, key=lambda _face: _face[2].z)

    @classmethod
    def ui(cls, layout, context):
        # ui panels
        op = layout.operator(
            operator='split_mesh.split_by_density',
            icon='SPLITSCREEN'
        )
        op.split_parts = context.window_manager.mesh_split_1d_prop_split_parts
        op.split_mode = context.window_manager.mesh_split_1d_prop_split_mode
        op.split_direction = context.window_manager.mesh_split_1d_prop_split_direction
        layout.prop(
            data=context.window_manager,
            property='mesh_split_1d_prop_split_parts'
        )
        layout.prop(
            data=context.window_manager,
            property='mesh_split_1d_prop_split_mode',
            expand=True
        )
        layout.prop(
            data=context.window_manager,
            property='mesh_split_1d_prop_split_direction',
            expand=True
        )
        layout.label(
            text='Vertices in a part: ' + str(round(cls.vertices_in_part(
                context=context,
                parts=context.window_manager.mesh_split_1d_prop_split_parts
            ))))


# OPERATORS

class MeshSplit_OT_split_by_density(Operator):
    bl_idname = 'split_mesh.split_by_density'
    bl_label = 'Split Mesh by Density'
    bl_options = {'REGISTER', 'UNDO'}

    split_parts = IntProperty(
        name='Split Parts',
        default=5,
        min=1
    )
    split_mode = EnumProperty(
        name='Split Mode',
        items=[
            ('VERTS', 'VERTS', 'VERTS', '', 0),
            ('FACES', 'FACES', 'FACES', '', 1),
            ('BM', 'BM', 'BM', '', 2)
        ],
        default='VERTS'
    )
    split_direction = EnumProperty(
        name='Split Direction',
        items=[
            ('X', 'X', 'X', '', 0),
            ('Y', 'Y', 'Y', '', 1),
            ('Z', 'Z', 'Z', '', 2)
        ],
        default='X'
    )

    def execute(self, context):
        MeshSplit.split_by_density(
            context=context,
            split_parts=self.split_parts,
            split_mode=self.split_mode,
            split_direction=self.split_direction
        )
        return {'FINISHED'}


# PANELS

class MeshSplit_PT_panel(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'
    bl_label = 'Mesh Split'
    bl_category = '1D'

    def draw(self, context):
        MeshSplit.ui(
            layout=self.layout,
            context=context
        )


# REGISTER

def register(ui=True):
    WindowManager.mesh_split_1d_prop_split_parts = IntProperty(
        name='Split Parts',
        default=5,
        min=1
    )
    WindowManager.mesh_split_1d_prop_split_mode = EnumProperty(
        name='Split Mode',
        items=[
            ('VERTS', 'VERTS', 'VERTS', '', 0),
            ('FACES', 'FACES', 'FACES', '', 1),
            ('BM', 'BM', 'BM', '', 2)
        ],
        default='VERTS'
    )
    WindowManager.mesh_split_1d_prop_split_direction = EnumProperty(
        name='Split Direction',
        items=[
            ('X', 'X', 'X', '', 0),
            ('Y', 'Y', 'Y', '', 1),
            ('Z', 'Z', 'Z', '', 2)
        ],
        default='X'
    )

    register_class(MeshSplit_OT_split_by_density)
    if ui:
        register_class(MeshSplit_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(MeshSplit_PT_panel)
    # butch clean
    unregister_class(MeshSplit_OT_split_by_density)
    del WindowManager.mesh_split_1d_prop_split_direction
    del WindowManager.mesh_split_1d_prop_split_mode
    del WindowManager.mesh_split_1d_prop_split_parts


if __name__ == "__main__":
    register()
