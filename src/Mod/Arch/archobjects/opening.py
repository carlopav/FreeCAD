#***************************************************************************
#*   Copyright (c) 2020 Carlo Pavan                                        *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************
"""Provide the object code for Arch Opening object."""
## @package opening
# \ingroup ARCH
# \brief Provide the object code for Arch Opening object.

import FreeCAD as App

import Part
import DraftVecUtils

from archutils import IFCutils


class Opening(object):
    def __init__(self, obj=None):
        self.Object = obj
        if obj:
            self.attach(obj)

    def __getstate__(self):
        return

    def __setstate__(self,_state):
        return
    
    def execute(self, obj):
        a_shape = self.get_addition_shape(obj)
        f_shape = self.get_filling_shape(obj)
        v_shape = self.get_void_shape(obj)
       
        obj.Shape = f_shape


    def attach(self,obj):
        obj.addExtension('App::GeoFeatureGroupExtensionPython', None)
        self.set_properties(obj)

    def set_properties(self, obj):
        # obj.addProperty('App::PropertyPlacement', 'GlobalPlacement', 
        #                'Base', 
        #                'Object global Placement', 1)

        # Ifc Properties ----------------------------------------------------
        IFCutils.set_ifc_properties(obj, "IfcProduct")
        obj.IfcType = "Opening Element"
        IFCutils.setup_ifc_attributes(obj)
        obj.PredefinedType = "OPENING"

        # COMPONENTS - ADDITIONS (not implemented yet) ----------------------------
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyEnumeration', 'Addition', 
                        'Component - Additions', _tip).Addition = ["Default Sill", "Custom"]

        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLinkListGlobal', 'AdditionElements', 
                        'Component - Additions', _tip)
        obj.setPropertyStatus("AdditionElements", 2)

        # COMPONENTS - FILLING Properties (Windows, doors) ----------------------------
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyEnumeration', 'Filling', 
                        'Component - Filling', _tip).Filling = ["None", "Default Door", "Default Window", "By Sketch", "Custom"]

        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyEnumeration', 'FillingAlignment', 
                        'Component - Filling', _tip).FillingAlignment = ["Left", "Center", "Right", "Offset"]
        
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyDistance', 'FillingDisplacement', 
                        'Component - Filling', _tip).FillingDisplacement = 0.0

        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLinkGlobal', 'FillingElement', 
                        'Component - Filling', _tip)

        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyEnumeration', 'FillingMode', 
                        'Component - Filling', _tip).FillingMode = ["Embed Shape", "Display Child"]

        # COMPONENTS Properties (not implemented yet) ----------------------------
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyEnumeration', 'Void', 
                        'Component - Void', _tip).Void = ["Rectangular", "Arc", "Custom"]

        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLinkGlobal', 'VoidElement', 
                        'Component - Void', _tip)

        # Geometry Properties (not implemented yet) ----------------------------
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLength', 'OpeningWidth', 
                        'Geometry', _tip).OpeningWidth = 800
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLength', 'OpeningHeight', 
                        'Geometry', _tip).OpeningHeight = 1500
        _tip = 'Link the door or the window that you want to insert into the opening'
        obj.addProperty('App::PropertyLength', 'HostThickness', 
                        'Geometry', _tip).HostThickness = 500

    # ADDITIONS ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def get_addition_shape(self, obj):
        pass

    # FILLING ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    
    def get_filling_shape(self, obj):
        f = None
        if 'Filling' in obj.PropertiesList and obj.Filling == "None":
            # return an empty shape
            f = Part.Shape()
        elif 'Filling' in obj.PropertiesList and obj.Filling == "Default Door":
            f = self.get_default_door_shape(obj)
        elif 'Filling' in obj.PropertiesList and obj.Filling == "Default Window":
            f = self.get_default_window_shape(obj)
        elif 'Filling' in obj.PropertiesList and obj.Filling == "By Sketch":
            f = self.get_filling_by_sketch(obj)
        elif 'Filling' in obj.PropertiesList and obj.Filling == "Custom":
            if 'FillingElement' in obj.PropertiesList and obj.FillingElement:
                # TODO: Inherit custom window shape
                f = obj.FillingElement.Shape
        if f: return f

    def get_default_door_shape(self, obj):
        if (not 'OpeningWidth' in obj.PropertiesList or
            not 'OpeningHeight' in obj.PropertiesList):
            return None
        f = Part.makeBox(obj.OpeningWidth,60,obj.OpeningHeight)
        m = App.Matrix()
        m.move(-obj.OpeningWidth/2, 0, 0)
        f = f.transformGeometry(m)
        return f

    def get_default_window_shape(self, obj):
        if (not 'OpeningWidth' in obj.PropertiesList or
            not 'OpeningHeight' in obj.PropertiesList):
            return None
        f = Part.makeBox(obj.OpeningWidth,60,obj.OpeningHeight)
        m = App.Matrix()
        m.move(-obj.OpeningWidth/2, 0, 0)
        f = f.transformGeometry(m)
        return f

    def get_filling_by_sketch(self, obj):
        import Part, DraftGeomUtils,math
        self.sshapes = []
        self.vshapes = []
        shapes = []
        rotdata = None
        for i in range(int(len(obj.WindowParts)/5)):
            wires = []
            hinge = None
            omode = None
            ssymbols = []
            vsymbols = []
            wstr = obj.WindowParts[(i*5)+2].split(',')
            for s in wstr:
                if "Wire" in s:
                    j = int(s[4:])
                    if obj.Base.Shape.Wires:
                        if len(obj.Base.Shape.Wires) >= j:
                            wires.append(obj.Base.Shape.Wires[j])
                elif "Edge" in s:
                    hinge = int(s[4:])-1
                elif "Mode" in s:
                    omode = int(s[-1])
            if wires:
                max_length = 0
                for w in wires:
                    if w.BoundBox.DiagonalLength > max_length:
                        max_length = w.BoundBox.DiagonalLength
                        ext = w
                wires.remove(ext)
                shape = Part.Face(ext)
                norm = shape.normalAt(0,0)
                if hasattr(obj,"Normal"):
                    if obj.Normal:
                        if not DraftVecUtils.isNull(obj.Normal):
                            norm = obj.Normal
                if hinge and omode:
                    opening = None
                    if hasattr(obj,"Opening"):
                        if obj.Opening:
                            opening = obj.Opening/100.0
                    e = obj.Base.Shape.Edges[hinge]
                    ev1 = e.Vertexes[0].Point
                    ev2 = e.Vertexes[-1].Point
                    # choose the one with lowest z to draw the symbol
                    if ev2.z < ev1.z:
                        ev1,ev2 = ev2,ev1
                    # find the point most distant from the hinge
                    p = None
                    d = 0
                    for v in shape.Vertexes:
                        dist = v.Point.distanceToLine(ev1,ev2.sub(ev1))
                        if dist > d:
                            d = dist
                            p = v.Point
                    if p:
                        # bring that point to the level of ev1 if needed
                        chord = p.sub(ev1)
                        enorm = ev2.sub(ev1)
                        proj = DraftVecUtils.project(chord,enorm)
                        v1 = ev1
                        if proj.Length > 0:
                            #chord = p.sub(ev1.add(proj))
                            #p = v1.add(chord)
                            p = p.add(proj.negative())
                        # calculate symbols
                        v4 = p.add(DraftVecUtils.scale(enorm,0.5))
                        if omode == 1: # Arc 90
                            v2 = v1.add(DraftVecUtils.rotate(chord,math.pi/4,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,math.pi/2,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),90*opening]
                        elif omode == 2: # Arc -90
                            v2 = v1.add(DraftVecUtils.rotate(chord,-math.pi/4,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,-math.pi/2,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),-90*opening]
                        elif omode == 3: # Arc 45
                            v2 = v1.add(DraftVecUtils.rotate(chord,math.pi/8,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,math.pi/4,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),45*opening]
                        elif omode == 4: # Arc -45
                            v2 = v1.add(DraftVecUtils.rotate(chord,-math.pi/8,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,-math.pi/4,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),-45*opening]
                        elif omode == 5: # Arc 180
                            v2 = v1.add(DraftVecUtils.rotate(chord,math.pi/2,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,math.pi,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),180*opening]
                        elif omode == 6: # Arc -180
                            v2 = v1.add(DraftVecUtils.rotate(chord,-math.pi/2,enorm))
                            v3 = v1.add(DraftVecUtils.rotate(chord,-math.pi,enorm))
                            ssymbols.append(Part.Arc(p,v2,v3).toShape())
                            ssymbols.append(Part.LineSegment(v3,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [ev1,ev2.sub(ev1),-180*opening]
                        elif omode == 7: # tri
                            v2 = v1.add(DraftVecUtils.rotate(chord,math.pi/2,enorm))
                            ssymbols.append(Part.LineSegment(p,v2).toShape())
                            ssymbols.append(Part.LineSegment(v2,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),90*opening]
                        elif omode == 8: # -tri
                            v2 = v1.add(DraftVecUtils.rotate(chord,-math.pi/2,enorm))
                            ssymbols.append(Part.LineSegment(p,v2).toShape())
                            ssymbols.append(Part.LineSegment(v2,v1).toShape())
                            vsymbols.append(Part.LineSegment(v1,v4).toShape())
                            vsymbols.append(Part.LineSegment(v4,ev2).toShape())
                            if opening:
                                rotdata = [v1,ev2.sub(ev1),-90*opening]
                        elif omode == 9: # sliding
                            pass
                        elif omode == 10: # -sliding
                            pass
                V = 0
                thk = obj.WindowParts[(i*5)+3]
                if "+V" in thk:
                    thk = thk[:-2]
                    V = obj.Frame.Value
                thk = float(thk) + V
                if thk:
                    exv = DraftVecUtils.scaleTo(norm,thk)
                    shape = shape.extrude(exv)
                    for w in wires:
                        f = Part.Face(w)
                        f = f.extrude(exv)
                        shape = shape.cut(f)
                if obj.WindowParts[(i*5)+4]:
                    V = 0
                    zof = obj.WindowParts[(i*5)+4]
                    if "+V" in zof:
                        zof = zof[:-2]
                        V = obj.Offset.Value
                    zof = float(zof) + V
                    if zof:
                        zov = DraftVecUtils.scaleTo(norm,zof)
                        shape.translate(zov)
                        for symb in ssymbols:
                            symb.translate(zov)
                        for symb in vsymbols:
                            symb.translate(zov)
                        if rotdata and hinge and omode:
                            rotdata[0] = rotdata[0].add(zov)
                if obj.WindowParts[(i*5)+1] == "Louvre":
                    if hasattr(obj,"LouvreWidth"):
                        if obj.LouvreWidth and obj.LouvreSpacing:
                            bb = shape.BoundBox
                            bb.enlarge(10)
                            step = obj.LouvreWidth.Value+obj.LouvreSpacing.Value
                            if step < bb.ZLength:
                                box = Part.makeBox(bb.XLength,bb.YLength,obj.LouvreSpacing.Value)
                                boxes = []
                                for i in range(int(bb.ZLength/step)+1):
                                    b = box.copy()
                                    b.translate(App.Vector(bb.XMin,bb.YMin,bb.ZMin+i*step))
                                    boxes.append(b)
                                self.boxes = Part.makeCompound(boxes)
                                #rot = obj.Base.Placement.Rotation
                                #self.boxes.rotate(self.boxes.BoundBox.Center,rot.Axis,math.degrees(rot.Angle))
                                self.boxes.translate(shape.BoundBox.Center.sub(self.boxes.BoundBox.Center))
                                shape = shape.cut(self.boxes)
                if rotdata:
                    shape.rotate(rotdata[0],rotdata[1],rotdata[2])
                shapes.append(shape)
                self.sshapes.extend(ssymbols)
                self.vshapes.extend(vsymbols)
        return Part.makeCompound(shapes)

    # VOID ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

    def get_void_shape(self, obj):
        void = None
        if obj.Void == "Rectangular":
            void = Part.makeBox(obj.OpeningWidth.Value, obj.HostThickness.Value + 50, obj.OpeningHeight.Value)
            void.Placement = obj.Placement
            void.Placement.Base.x -= obj.OpeningWidth.Value/2
            void.Placement.Base.y -= obj.HostThickness.Value/2
        return void



    def onChanged(self, obj, prop):
        if 'Addition' in obj.PropertiesList and prop == 'Addition':
            if obj.Addition != "Custom" and 'AdditionElements' in obj.PropertiesList:
                obj.setPropertyStatus("AdditionElements", 2)
            elif 'AdditionElements' in obj.PropertiesList:
                obj.setPropertyStatus("AdditionElements", -2)

        if 'AdditionElements' in obj.PropertiesList and prop == 'AdditionElements':
            pass

        if 'Filling' in obj.PropertiesList and prop == 'Filling':
            pass

        if 'FillingElement' in obj.PropertiesList and prop == 'FillingElement':
            pass

        if 'Void' in obj.PropertiesList and prop == 'Void':
            pass

        if 'VoidElement' in obj.PropertiesList and prop == 'VoidElement':
            pass


    def onDocumentRestored(self, obj):
        self.Object = obj