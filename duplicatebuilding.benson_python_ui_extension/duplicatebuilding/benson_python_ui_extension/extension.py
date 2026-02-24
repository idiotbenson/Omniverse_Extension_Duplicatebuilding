# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

import omni.ext
import omni.ui as ui
import omni.usd
import omni.kit.commands
from pxr import Usd, UsdGeom, Sdf, Gf


# Functions and vars are available to other extensions as usual in python:
# `duplicatebuilding.benson_python_ui_extension.some_public_function(x)`
def some_public_function(x: int):
    """This is a public function that can be called from other extensions."""
    print(f"[duplicatebuilding.benson_python_ui_extension] some_public_function was called with {x}")
    return x ** x


# Any class derived from `omni.ext.IExt` in the top level module (defined in
# `python.modules` of `extension.toml`) will be instantiated when the extension
# gets enabled, and `on_startup(ext_id)` will be called. Later when the
# extension gets disabled on_shutdown() is called.
class MyExtension(omni.ext.IExt):
    """This extension manages a simple counter UI."""
    # ext_id is the current extension id. It can be used with the extension
    # manager to query additional information, like where this extension is
    # located on the filesystem.
    def on_startup(self, _ext_id):
        """This is called every time the extension is activated."""
        print("[duplicatebuilding.benson_python_ui_extension] Extension startup")

        self._count = 0
        self._window = ui.Window(
            "benson duplicate building python ui extension", width=360, height=200
        )
        with self._window.frame:
            with ui.VStack():
                ui.Label("Duplicate Along Axis (Xform or Mesh)")

                # Inputs in one row
                with ui.HStack(spacing=8):
                    ui.Label("Count:", width=60)
                    self._dup_count_model = ui.SimpleIntModel(10)
                    ui.IntField(model=self._dup_count_model, width=80, height=24)
                    ui.Spacer(width=12)
                    ui.Label("Distance:", width=60)
                    self._dup_distance_model = ui.SimpleFloatModel(300.0)
                    ui.FloatField(model=self._dup_distance_model, width=100, height=24)
                    ui.Spacer(width=12)
                    ui.Label("Axis:", width=60)
                    self._axis_combo = ui.ComboBox(2, "X", "Y", "Z")

                # Instance option
                with ui.HStack(spacing=8):
                    ui.Label("Use instances:", width=120)
                    self._use_instances_model = ui.SimpleBoolModel(False)
                    ui.CheckBox(model=self._use_instances_model)

                ui.Spacer(height=6)

                with ui.HStack():
                    ui.Button("Duplicate", clicked_fn=self._on_duplicate_along_z_clicked, height=28)
                    self._status_label = ui.Label("", style={"color": 0xFFAAAAAA})

    def _on_duplicate_along_z_clicked(self):
        try:
            count = max(0, int(self._dup_count_model.get_value_as_int()))
            distance = float(self._dup_distance_model.get_value_as_float())
        except Exception:
            self._status_label.text = "Invalid input"
            return

        if count <= 0:
            self._status_label.text = "Count must be > 0"
            return

        usd_ctx = omni.usd.get_context()
        stage = usd_ctx.get_stage()
        if not stage:
            self._status_label.text = "No USD stage is open"
            return

        selection = usd_ctx.get_selection().get_selected_prim_paths()
        if not selection:
            self._status_label.text = "Please select an Xform or Mesh"
            return

        total_created = 0
        axis_index = 2
        try:
            axis_index = int(self._axis_combo.model.get_item_value_model().get_value_as_int())
        except Exception:
            axis_index = 2
        axis_letter = "x" if axis_index == 0 else ("y" if axis_index == 1 else "z")
        use_instances = False
        try:
            use_instances = bool(self._use_instances_model.get_value_as_bool())
        except Exception:
            use_instances = False
        for sel_path in selection:
            prim = stage.GetPrimAtPath(sel_path)
            if not prim or not prim.IsValid():
                continue

            parent_path = prim.GetPath().GetParentPath()
            base_name = prim.GetName()

            for i in range(1, count + 1):
                # Generate a unique target path
                candidate_name = f"{base_name}_{axis_letter}{i:02d}"
                target_path = Sdf.Path(str(parent_path) + "/" + candidate_name)
                suffix = 1
                while stage.GetPrimAtPath(target_path).IsValid():
                    candidate_name = f"{base_name}_{axis_letter}{i:02d}_{suffix}"
                    target_path = Sdf.Path(str(parent_path) + "/" + candidate_name)
                    suffix += 1

                # Duplicate prim
                try:
                    if use_instances:
                        # Create Xform and add internal reference to source prim; mark as instanceable
                        dup_prim = stage.DefinePrim(target_path, "Xform")
                        refs = dup_prim.GetReferences()
                        refs.AddReference("", prim.GetPath())
                        dup_prim.SetInstanceable(True)
                    else:
                        omni.kit.commands.execute(
                            "CopyPrim", path_from=str(prim.GetPath()), path_to=str(target_path)
                        )
                        dup_prim = stage.GetPrimAtPath(str(target_path))
                except Exception:
                    continue

                # Offset along chosen axis by i * distance
                if not dup_prim or not dup_prim.IsValid():
                    continue

                try:
                    xformable = UsdGeom.Xformable(dup_prim)
                    ops = xformable.GetOrderedXformOps()
                    translate_op = None
                    for op in ops:
                        if op.GetOpType() == UsdGeom.XformOp.TypeTranslate:
                            translate_op = op
                            break
                    if translate_op is None:
                        translate_op = xformable.AddTranslateOp()

                    current = translate_op.Get()
                    if current is None:
                        current = Gf.Vec3d(0.0, 0.0, 0.0)
                    if axis_index == 0:
                        offset = Gf.Vec3d(current[0] + (i * distance), current[1], current[2])
                    elif axis_index == 1:
                        offset = Gf.Vec3d(current[0], current[1] + (i * distance), current[2])
                    else:
                        offset = Gf.Vec3d(current[0], current[1], current[2] + (i * distance))
                    translate_op.Set(offset)
                    total_created += 1
                except Exception:
                    # If transform application failed, still count the copy
                    total_created += 1

        self._status_label.text = f"Done: Duplicated {total_created}"

    def on_shutdown(self):
        """This is called every time the extension is deactivated. It is used
        to clean up the extension state."""
        print("[duplicatebuilding.benson_python_ui_extension] Extension shutdown")
