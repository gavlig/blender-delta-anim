import bpy, math

bl_info = {
	"name": "Delta Animation Calculator (from NLA editor)",
	"author": "Vladyslav \"gavlig\" Gapchych",
	"version": (2015, 7, 16),
	"blender": (2, 7, 4),
	"location": "Space > Apply Delta Animation",
	"description": "Apply \"Delta\" animation made of one frame containing offset that needed to be applyed to all frames in target animation",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Animation"}

class apply_delta(bpy.types.Operator):
	bl_idname					= "animation.apply_delta"
	bl_label					= "Apply Delta Animation"

	#
	#
	###
	def main(self):
		print					("\n\nCALCULATING DELTAS BITCHES!")
		armature				= bpy.context.selected_objects[0]

		if len(bpy.context.selected_objects) > 1 or "ARMATURE" != armature.type:
			self.report			({'ERROR'}, "Select an armature with nla tracks")
			return

		print					("selected %s : %s" % (armature.type, armature.name))

		delta_track				= 0
		delta_action			= 0
		target_track			= 0
		target_action			= 0

		for track in armature.animation_data.nla_tracks:
			strip				= track.strips[0];
			action				= strip.action;

			if "delta" == strip.name or "delta" == action.name:
				delta_action	= action
				delta_track		= track
			else:
				target_action	= action
				target_track	= track

		print					("target_action: %s" % (target_action.name))
		print					("delta_action: %s" % (delta_action.name))

		# "group" is a bone
		delta_bones				= delta_action.groups
		target_bones			= target_action.groups

		delta_bone_names		= []
		for b in delta_bones:
			delta_bone_names.append	(b.name)

		# getting reference frame number (it is assumed that anim is 1 frame long)
		ch						= delta_bones[0].channels[0]
		reference_frame_id		= ch.keyframe_points[0].co[0]
		if len(ch.keyframe_points) > 1:
			self.report			({'ERROR'}, "Delta animation should be 1 frame long")
			return

		sce						= bpy.context.scene
		ob						= bpy.context.object

		baked_bones				= list( filter(lambda x: x.name in delta_bone_names, ob.pose.bones) )
		for bb in baked_bones:
			target_bone			= next( filter(lambda x: x.name == bb.name, target_bones) )
			self.apply_deltas	(bb, reference_frame_id, target_bone, delta_track, target_track, sce)


		print					("yay!")

	#
	#
	###
	def apply_deltas(self, bb, reference_frame_id, target_bone, delta_track, target_track, sce):
		delta_track.is_solo		= True
		sce.frame_set			(reference_frame_id)
		offset_mat				= bb.matrix_basis.copy()
		ioffset_mat				= offset_mat.copy()
		ioffset_mat.invert		()
		#print					("offset_mat:\n{0}".format(offset_mat))

		target_track.is_solo	= True
		sce.frame_set			(reference_frame_id)
		delta					= bb.matrix_basis * ioffset_mat
		delta.invert			()

		keyframes				= set()

		for ch in target_bone.channels:
			for k in ch.keyframe_points:
				keyframes.add	(int(k.co[0]))

		#print					("keyframes:\n{0}".format(keyframes))

		new_mats				= dict()
		for k in keyframes:
			sce.frame_set		(k)
			new_mats[k]			= bb.matrix_basis * delta

			#print				("frame: {0}".format(k))
			#print				("old_mat:\n{0}".format(bb.matrix_basis))
			#print				("delta:\n{0}".format(delta))
			#print				("new_mat:\n{0}".format(new_mats[k]))

		for ch in target_bone.channels:
			op_word				= ch.data_path.rsplit(".", 1)[1]
			#print				("applying {0} channel {1}".format(ch.data_path, ch.array_index))

			for k in ch.keyframe_points:
				# co[0] -- frame number
				# co[1] -- value
				frame			= int(k.co[0])
				#print			("frame: {0}".format(frame))
				sce.frame_set	(frame)

				new_mat			= new_mats[ frame ]

				T				= new_mat.to_translation()
				Q				= new_mat.to_quaternion()
				S				= new_mat.to_scale()

				if "location" == op_word:
					k.co[1]		= T[ch.array_index]
				if "rotation_quaternion" == op_word:
					k.co[1]		= Q[ch.array_index]
				if "scale" == op_word:
					k.co[1]		= S[ch.array_index]

			# curves get messed up
			ch.update			()

	#
	#
	###
	def execute(self, context):
		self.main				()

		return					{'FINISHED'}


########################################
# class "apply_delta" definition ended #
########################################


class NLA_panel(bpy.types.Panel):
	bl_label = "Delta Animation"
	bl_space_type = "NLA_EDITOR"
	bl_region_type = "UI"

	def draw(self, context):
		self.layout.operator("animation.apply_delta", text='Apply')

def register():
	bpy.utils.register_module	(__name__)

def unregister():
	bpy.utils.unregister_module	(__name__)

if __name__ == "__main__":
	register					()

#
#
#
