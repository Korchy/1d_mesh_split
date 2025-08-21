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
    def split_by_density(cls, context, split_parts=5, split_mode='VERTS'):
        # split mesh by density
        #   mode 'VERTS' | 'FACES' - different counting modes
        if context.active_object and split_parts > 1:
            # execution time
            start_time = time()
            # current mode
            mode = context.active_object.mode
            # if context.active_object.mode == 'EDIT':
            #     bpy.ops.object.mode_set(mode='OBJECT')
            # deselect all
            cls._deselect_all(obj=context.active_object)
            print('after deselect all ', round(time() - start_time, 5))
            # count number of vertices in one part
            vertices_in_a_part = round(cls.vertices_in_part(
                context=context,
                parts=split_parts
            ))
            print('after vertices in a part', round(time() - start_time, 5))
            # split by split_parts
            if split_mode == 'VERTS':
                print('VERTS mode')
                # counting by vertices
                for _i in range(split_parts - 1):   #  (-2 because ex: 5 parts = 3 cuts + 1 cut / 2)
                    vertices_sorted = sorted(context.active_object.data.vertices, key=lambda _vert: _vert.co.x)
                    print('after vertices_sorted', round(time() - start_time, 5))
                    vertices_to_split = vertices_sorted[:vertices_in_a_part]
                    # we need to select faces by vertices_to_split
                    vertices_to_split_ids = set(_v.index for _v in vertices_to_split)
                    for face in context.active_object.data.polygons:
                        if set(face.vertices).issubset(vertices_to_split_ids):
                            face.select = True
                    print('after face', round(time() - start_time, 5))
                    context.active_object.data.validate()
                    context.active_object.data.update()
                    # context.active_object.update_from_editmode()

                    # if selected faces exists - split
                    selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                    print('selected_faces_n', selected_faces_n)
                    if selected_faces_n:
                        # bpy.ops.object.mode_set(mode='EDIT')
                        print('after edit', round(time() - start_time, 5))
                        bpy.ops.mesh.separate(type='SELECTED')
                        print('after split', round(time() - start_time, 5))
                        # bpy.ops.object.mode_set(mode='OBJECT')
                        print('after object', round(time() - start_time, 5))
                    print('_i', _i)
                # if in the last part vertices amount > vertices_in_a_part - split it into 2 parts by Y
                remaining_vertices_n = len(context.active_object.data.vertices)
                if remaining_vertices_n >= vertices_in_a_part:
                    vertices_sorted = sorted(context.active_object.data.vertices, key=lambda _vert: _vert.co.y)
                    vertices_to_split = vertices_sorted[:vertices_in_a_part]
                    # we need to select faces by vertices_to_split
                    vertices_to_split_ids = set(_v.index for _v in vertices_to_split)
                    for face in context.active_object.data.polygons:
                        if set(face.vertices).issubset(vertices_to_split_ids):
                            face.select = True
                    # if selected faces exists - split
                    selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                    if selected_faces_n:
                        bpy.ops.object.mode_set(mode='EDIT')
                        bpy.ops.mesh.separate(type='SELECTED')
                        bpy.ops.object.mode_set(mode='OBJECT')
            elif split_mode == 'FACES':
                print('FACES mode')
                # counting by faces centroids
                for _i in range(split_parts - 1):   #  (-2 because ex: 5 parts = 3 cuts + 1 cut / 2)
                    # get faces sorted by centroids by local X coordinate
                    faces_sorted = cls._faces_sorted_by_centroid(
                        obj=context.active_object,
                        axis='X'
                    )
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
                            # if selected faces exists - split
                            selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                            if selected_faces_n:
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.separate(type='SELECTED')
                                bpy.ops.object.mode_set(mode='OBJECT')
                                # after splitting we need to start from beginning because mesh was rebuilt
                                break
                # if in the last part vertices amount > vertices_in_a_part - split it into 2 parts by Y
                remaining_vertices_n = len(context.active_object.data.vertices)
                if remaining_vertices_n >= vertices_in_a_part:
                    # get faces sorted by centroids by local X coordinate
                    faces_sorted = cls._faces_sorted_by_centroid(
                        obj=context.active_object,
                        axis='Y'
                    )
                    faces_vertices = set()  # vertices counter
                    # walk from left by sorted faces
                    for _face in faces_sorted:
                        # increase counter by faces vertices amount
                        faces_vertices.update(_face[1])
                        # if counter less vertices_in_a_part - select face and continue#
                        # else - split selected faces
                        if len(faces_vertices) < round(remaining_vertices_n / 2):
                            _face[0].select = True
                        else:
                            # if selected faces exists - split
                            selected_faces_n = len([_face for _face in context.active_object.data.polygons if _face.select])
                            if selected_faces_n:
                                bpy.ops.object.mode_set(mode='EDIT')
                                bpy.ops.mesh.separate(type='SELECTED')
                                bpy.ops.object.mode_set(mode='OBJECT')
                                # after splitting we need to start from beginning because mesh was rebuilt
                                break
            # return mode back
            bpy.ops.object.mode_set(mode=mode)
            # execution time
            print('Executed in %s seconds' % (round(time() - start_time, 2)))

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
        layout.prop(
            data=context.window_manager,
            property='mesh_split_1d_prop_split_parts'
        )
        layout.prop(
            data=context.window_manager,
            property='mesh_split_1d_prop_split_mode',
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
        ],
        default='VERTS'
    )

    def execute(self, context):
        MeshSplit.split_by_density(
            context=context,
            split_parts=self.split_parts,
            split_mode=self.split_mode
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
        ],
        default='VERTS'
    )

    register_class(MeshSplit_OT_split_by_density)
    if ui:
        register_class(MeshSplit_PT_panel)


def unregister(ui=True):
    if ui:
        unregister_class(MeshSplit_PT_panel)
    # butch clean
    unregister_class(MeshSplit_OT_split_by_density)
    del WindowManager.mesh_split_1d_prop_split_parts


if __name__ == "__main__":
    register()
