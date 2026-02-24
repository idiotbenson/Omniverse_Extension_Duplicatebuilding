# Omniverse_Extension_Duplicatebuilding

A NVIDIA Omniverse Kit Python UI extension that duplicates selected objects along a chosen axis in the scene.
Overview
Name: benson duplicate building python ui extension
Purpose: Duplicate selected Xform or Mesh prims along the X, Y, or Z axis with a configurable spacing.
Features
1. Duplicate along axis
Supports X, Y, or Z
Configurable count and spacing
Unique names (e.g. baseName_z01, baseName_z02)
2. Duplication modes
Standard copy: Uses CopyPrim to create full copies
Instance mode: Creates an Xform with a reference to the source prim and sets it as instanceable to save memory
3. Transform handling
Uses or adds a Translate op
Computes offset along the chosen axis and distance and applies it to each duplicate
UI
Window title: "benson duplicate building python ui extension"
Control	Description
Count	Number of copies (default: 10)
Distance	Spacing along the axis (default: 300.0)
Axis	Axis (X / Y / Z)
Use instances	Toggle instance mode
Duplicate	Run duplication
Usage
Open or create a USD stage in Omniverse
Select one or more Xform or Mesh prims
Open the extension window
Set Count, Distance, Axis, and Use instances
Click Duplicate
Technical details
Uses omni.usd for stage and selection
Uses omni.kit.commands CopyPrim for duplication
Uses pxr.UsdGeom.Xformable for transforms
Depends on omni.kit.uiapp for UI
