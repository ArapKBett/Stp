import os
from OCC.Core.STEPControl import STEPControl_Reader, STEPControl_Writer
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Face
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCC.Core.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Dir, gp_Ax3
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Core.XSControl import XSControl_WorkSession
from OCC.Core.STEPCAFControl import STEPCAFControl_Writer
from OCC.Core.TDF import TDF_Label
from OCC.Core.TDataStd import TDataStd_Name
from OCC.Core.XCAFDoc import XCAFDoc_ColorTool, XCAFDoc_DocumentTool
from OCC.Core.TDocStd import TDocStd_Document
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.Interface import Interface_Static

import numpy as np

class STEPProcessor:
    def __init__(self):
        self.shape = None
        self.faces = []
        
    def load_step_file(self, file_path):
        """Load a STEP file and return the shape"""
        reader = STEPControl_Reader()
        status = reader.ReadFile(file_path)
        
        if status == IFSelect_RetDone:
            reader.TransferRoots()
            self.shape = reader.OneShape()
            self._extract_faces()
            return True, "File loaded successfully"
        else:
            return False, "Error: Could not load file"
    
    def _extract_faces(self):
        """Extract all faces from the shape"""
        self.faces = []
        explorer = TopExp_Explorer(self.shape, TopAbs_FACE)
        while explorer.More():
            face = TopoDS_Face(explorer.Current())
            self.faces.append(face)
            explorer.Next()
    
    def orient_shape(self, criteria="largest_face_down"):
        """Orient the shape based on given criteria"""
        if criteria == "largest_face_down":
            self._orient_by_largest_face()
        elif criteria == "z_axis_up":
            self._orient_z_up()
        # Add more orientation criteria as needed
    
    def _orient_by_largest_face(self):
        """Orient the shape so the largest face is facing down"""
        if not self.faces:
            return
            
        # Find the largest face
        largest_face = None
        max_area = 0
        
        for face in self.faces:
            props = BRep_Tool.Surface(face).Properties()
            area = props.Area()
            if area > max_area:
                max_area = area
                largest_face = face
        
        if largest_face:
            # Get the normal of the largest face
            surf = BRep_Tool.Surface(largest_face)
            umin, umax, vmin, vmax = surf.Bounds()
            u_center = (umin + umax) / 2
            v_center = (vmin + vmax) / 2
            pnt = surf.Value(u_center, v_center)
            normal = surf.Normal(u_center, v_center)
            
            # Create transformation to align normal with Z-down
            current_dir = gp_Dir(normal.X(), normal.Y(), normal.Z())
            target_dir = gp_Dir(0, 0, -1)  # Z-down
            
            # Calculate rotation
            rot = gp_Trsf()
            rot.SetRotation(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), 
                           gp_Ax3(gp_Pnt(0, 0, 0), current_dir, target_dir))
            
            # Apply transformation
            transformer = BRepBuilderAPI_Transform(self.shape, rot, True)
            self.shape = transformer.Shape()
            self._extract_faces()
    
    def _orient_z_up(self):
        """Simple orientation to ensure Z-axis is up"""
        # This is a simple example - you might need more complex logic
        rot = gp_Trsf()
        rot.SetRotation(gp_Ax3(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), np.pi/2)
        transformer = BRepBuilderAPI_Transform(self.shape, rot, True)
        self.shape = transformer.Shape()
        self._extract_faces()
    
    def color_faces_by_orientation(self, angle_tolerance=15):
        """Color faces based on their orientation"""
        colors = {}
        
        for face in self.faces:
            # Get face normal
            surf = BRep_Tool.Surface(face)
            umin, umax, vmin, vmax = surf.Bounds()
            u_center = (umin + umax) / 2
            v_center = (vmin + vmax) / 2
            normal = surf.Normal(u_center, v_center)
            normal_dir = gp_Dir(normal.X(), normal.Y(), normal.Z())
            
            # Determine orientation category
            angle_to_z = normal_dir.Angle(gp_Dir(0, 0, 1))
            angle_deg = np.degrees(angle_to_z)
            
            if angle_deg < angle_tolerance:
                color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)  # Red for top faces
            elif abs(angle_deg - 180) < angle_tolerance:
                color = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB)  # Green for bottom faces
            elif abs(angle_deg - 90) < angle_tolerance:
                # Check if it's facing primarily in X or Y direction
                angle_to_x = normal_dir.Angle(gp_Dir(1, 0, 0))
                if angle_to_x < np.radians(45) or angle_to_x > np.radians(135):
                    color = Quantity_Color(0.0, 0.0, 1.0, Quantity_TOC_RGB)  # Blue for X-facing
                else:
                    color = Quantity_Color(1.0, 1.0, 0.0, Quantity_TOC_RGB)  # Yellow for Y-facing
            else:
                color = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)  # Gray for other faces
            
            colors[face] = color
        
        return colors
    
    def save_colored_step(self, input_path, output_path, face_colors):
        """Save the shape with colored faces to a new STEP file"""
        # Create a document
        doc = TDocStd_Document(TCollection_ExtendedString("XmlXCAF"))
        
        # Get the color tool
        tool = XCAFDoc_DocumentTool.ColorTool(doc.Main()).GetObject()
        
        # Add the shape to the document
        label = TDF_Label()
        tool.AddShape(self.shape, False, label)
        
        # Apply colors to faces
        for face, color in face_colors.items():
            face_label = tool.AddSubShape(label, face)
            if not face_label.IsNull():
                tool.SetColor(face_label, color, XCAFDoc_ColorTool_Gen)
        
        # Write the STEP file
        writer = STEPCAFControl_Writer()
        writer.Transfer(doc, STEPControl_AsIs)
        
        # Set STEP version
        Interface_Static.SetCVal("write.step.schema", "AP214")
        
        status = writer.Write(output_path)
        return status
