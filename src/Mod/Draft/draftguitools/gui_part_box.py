#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2018 Yorik van Havre <yorik@uncreated.net>              *
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
"""Provides the Draft Gui tool to graphically create a Part Box."""
## @package gui_part_box
# \ingroup DRAFT
# \brief This module provides the Draft Gui tool to create a Part Box.

from __future__ import print_function

import FreeCAD as App
import FreeCADGui as Gui
import draftguitools.gui_base as gui_base
import draftutils.gui_utils as gui_utils
import draftutils.todo as todo
import DraftTrackers, DraftVecUtils
from PySide import QtCore, QtGui

def QT_TRANSLATE_NOOP(ctx,txt): return txt # dummy function for QT translator


class GuiCommand_Part_Box(gui_base.GuiCommandBase):
    """
    This Class provides the Draft command to create a Part::Box graphically
    """

    def GetResources(self):
        """Set icon, menu and tooltip."""
        _menu = "Part Box"
        _tip = ("Creates a Part Box.\n"
                "Create a Part Workbench Box primitive graphically by\n  "
                "entering 4 points or the box dimensions.")
        d = {'Pixmap': 'Draft_PartBox',
             'MenuText': QT_TRANSLATE_NOOP("Draft_SetWorkingPlaneProxy",
                                           _menu),
             'ToolTip': QT_TRANSLATE_NOOP("Draft_SetWorkingPlaneProxy",
                                          _tip)}
        return d

    def IsActive(self):
        """Return True when this command should be available."""
        if App.ActiveDocument:
            return True
        else:
            return False

    def Activated(self):

        # here we will store our points
        self.points = []
        # we build a special cube tracker which is a list of 4 rectangle trackers
        self.cubetracker = []
        self.LengthValue = 0
        self.WidthValue = 0
        self.HeightValue = 0
        self.currentpoint = None
        for i in range(4):
            self.cubetracker.append(DraftTrackers.rectangleTracker())
        if hasattr(Gui,"Snapper"):
            Gui.Snapper.getPoint(callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())

    def MoveCallback(self,point,snapinfo):

        self.currentpoint = point

        if len(self.points) == 1:
            # we have the base point already
            l = self.points[-1].sub(point).Length
            self.Length.setText(App.Units.Quantity(str(l)+"mm").UserString)
            self.Length.selectAll()
            self.Length.setFocus()

        elif len(self.points) == 2:
            # now we already have our base line, we update the 1st rectangle
            p = point
            v1 = point.sub(self.points[1])
            v4 = v1.cross(self.points[1].sub(self.points[0]))
            if v4 and v4.Length:
                n = (self.points[1].sub(self.points[0])).cross(v4)
                if n and n.Length:
                    n = DraftVecUtils.project(v1,n)
                    p = self.points[1].add(n)
            self.cubetracker[0].p3(p)
            w = self.cubetracker[0].getSize()[1]
            self.Width.setText(App.Units.Quantity(str(w)+"mm").UserString)
            self.Width.selectAll()
            self.Width.setFocus()
        elif len(self.points) == 3:
            # we must first find our height point by projecting on the normal
            w = DraftVecUtils.project(point.sub(self.cubetracker[0].p3()),
                                      self.normal)
            # then we update all rectangles
            self.cubetracker[1].p3((self.cubetracker[0].p2()).add(w))
            self.cubetracker[2].p3((self.cubetracker[0].p4()).add(w))
            self.cubetracker[3].p1((self.cubetracker[0].p1()).add(w))
            self.cubetracker[3].p3((self.cubetracker[0].p3()).add(w))
            h = w.Length
            self.Height.setText(App.Units.Quantity(str(h)+"mm").UserString)
            self.Height.selectAll()
            self.Height.setFocus()

    def PointCallback(self,point,snapinfo):

        if not point:
            # cancelled
            if hasattr(App,"DraftWorkingPlane"):
                App.DraftWorkingPlane.restore()
            Gui.Snapper.setGrid()
            for c in self.cubetracker:
                c.off()
            return

        if len(self.points) == 0:
            # this is our first clicked point, nothing to do just yet
            Gui.Snapper.getPoint(last = point,
                                 callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())

        elif len(self.points) == 1:
            # this is our second point
            # we turn on only one of the rectangles
            baseline = point.sub(self.points[0])
            self.cubetracker[0].setPlane(baseline)
            self.cubetracker[0].p1(self.points[0])
            self.cubetracker[0].on()
            Gui.Snapper.getPoint(last = point,
                                 callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())

        elif len(self.points) == 2:
            # this is our third point
            # we can get the cubes Z axis from our first rectangle
            self.normal = self.cubetracker[0].getNormal()
            # we can therefore define the (u,v) planes of all rectangles
            u = self.cubetracker[0].u
            v = self.cubetracker[0].v
            self.cubetracker[1].setPlane(u,self.normal)
            self.cubetracker[2].setPlane(u,self.normal)
            self.cubetracker[3].setPlane(u,v)
            # and the origin points of the vertical rectangles
            self.cubetracker[1].p1(self.cubetracker[0].p1())
            self.cubetracker[2].p1(self.cubetracker[0].p3())
            # finally we turn all rectangles on
            for r in self.cubetracker:
                r.on()
            if hasattr(App,"DraftWorkingPlane"):
                App.DraftWorkingPlane.save()
                App.DraftWorkingPlane.position = self.cubetracker[0].p3()
                u = (self.cubetracker[0].p4().sub(self.cubetracker[0].p3()))
                App.DraftWorkingPlane.u = u.normalize()
                v = App.Vector(self.normal)
                App.DraftWorkingPlane.v = v.normalize()
                axis = (self.cubetracker[0].p2().sub(self.cubetracker[0].p3()))
                App.DraftWorkingPlane.axis = axis.normalize()
                Gui.Snapper.setGrid()
            Gui.Snapper.getPoint(last = self.cubetracker[0].p3(),
                                 callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())
        
        elif len(self.points) == 3:
            # finally we have all our points. Let's create the actual cube
            App.ActiveDocument.openTransaction("Draft_PartBox")
            cube = App.ActiveDocument.addObject("Part::Box","Cube")
            cube.Length = self.LengthValue
            cube.Width = self.WidthValue
            cube.Height = self.HeightValue
            # we get 3 points that define our cube orientation
            p1 = self.cubetracker[0].p1()
            p2 = self.cubetracker[0].p2()
            p3 = self.cubetracker[0].p4()
            import WorkingPlane
            cube.Placement = WorkingPlane.getPlacementFromPoints([p1,p2,p3])
            if hasattr(App,"DraftWorkingPlane"):
                App.DraftWorkingPlane.restore()
            Gui.Snapper.setGrid()
            for c in self.cubetracker:
                c.off()
            gui_utils.autogroup(cube)
            App.ActiveDocument.recompute()
            App.ActiveDocument.commitTransaction()

        self.points.append(point)


    def setLength(self,d):

        self.LengthValue = d


    def setWidth(self,d):

        self.WidthValue = d


    def setHeight(self,d):

        self.HeightValue = d


    def taskbox(self):
        """Command Gui.
        sets up a TaskPanel widget for the Box command"""

        wid = QtGui.QWidget()
        ui = Gui.UiLoader()
        wid.setWindowTitle(QT_TRANSLATE_NOOP("BIM","Box dimensions"))
        grid = QtGui.QGridLayout(wid)

        label1 = QtGui.QLabel(QT_TRANSLATE_NOOP("BIM","Length"))
        self.Length = ui.createWidget("Gui::InputField")
        self.Length.setText(str(self.LengthValue)+"mm")
        grid.addWidget(label1,0,0,1,1)
        grid.addWidget(self.Length,0,1,1,1)
        if self.LengthValue:
            self.Length.setEnabled(False)

        label2 = QtGui.QLabel(QT_TRANSLATE_NOOP("BIM","Width"))
        self.Width = ui.createWidget("Gui::InputField")
        self.Width.setText(str(self.WidthValue)+"mm")
        grid.addWidget(label2,1,0,1,1)
        grid.addWidget(self.Width,1,1,1,1)
        if self.WidthValue or (not self.LengthValue):
            self.Width.setEnabled(False)

        label3 = QtGui.QLabel(QT_TRANSLATE_NOOP("BIM","Height"))
        self.Height = ui.createWidget("Gui::InputField")
        self.Height.setText(str(self.HeightValue)+"mm")
        grid.addWidget(label3,2,0,1,1)
        grid.addWidget(self.Height,2,1,1,1)
        if not self.WidthValue:
            self.Height.setEnabled(False)

        QtCore.QObject.connect(self.Length,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.setLength)

        QtCore.QObject.connect(self.Width,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.setWidth)

        QtCore.QObject.connect(self.Height,
                               QtCore.SIGNAL("valueChanged(double)"),
                               self.setHeight)

        QtCore.QObject.connect(self.Length,
                               QtCore.SIGNAL("returnPressed()"),
                               self.setLengthUI)

        QtCore.QObject.connect(self.Width,
                               QtCore.SIGNAL("returnPressed()"),
                               self.setWidthUI)

        QtCore.QObject.connect(self.Height,
                               QtCore.SIGNAL("returnPressed()"),
                               self.setHeightUI)

        return wid


    def setLengthUI(self):
        """Command Gui.
        """
        if (len(self.points) == 1) and self.currentpoint and self.LengthValue:
            baseline = self.currentpoint.sub(self.points[0])
            baseline.normalize()
            baseline.multiply(self.LengthValue)
            p2 = self.points[0].add(baseline)
            self.points.append(p2)
            self.cubetracker[0].setPlane(baseline)
            self.cubetracker[0].p1(self.points[0])
            self.cubetracker[0].on()
            Gui.Snapper.getPoint(last = p2,
                                 callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())


    def setWidthUI(self):
        """Command Gui.
        """
        if (len(self.points) == 2) and self.currentpoint and self.WidthValue:
            self.normal = self.cubetracker[0].getNormal()
            if self.normal:
                n = (self.points[1].sub(self.points[0])).cross(self.normal)
                if n and n.Length:
                    n.normalize()
                    n.multiply(self.WidthValue)
                    p2 = self.points[1].add(n) 
            self.cubetracker[0].p3(p2)
            self.points.append(p2)
            u = self.cubetracker[0].u
            v = self.cubetracker[0].v
            self.cubetracker[1].setPlane(u,self.normal)
            self.cubetracker[2].setPlane(u,self.normal)
            self.cubetracker[3].setPlane(u,v)
            self.cubetracker[1].p1(self.cubetracker[0].p1())
            self.cubetracker[2].p1(self.cubetracker[0].p3())
            for r in self.cubetracker:
                r.on()
            if hasattr(App,"DraftWorkingPlane"):
                App.DraftWorkingPlane.save()
                App.DraftWorkingPlane.position = self.cubetracker[0].p3()
                u = (self.cubetracker[0].p4().sub(self.cubetracker[0].p3()))
                App.DraftWorkingPlane.u = u.normalize()
                v = self.normal
                App.DraftWorkingPlane.v = v
                axis = (self.cubetracker[0].p2().sub(self.cubetracker[0].p3()))
                App.DraftWorkingPlane.axis = axis.normalize()
                Gui.Snapper.setGrid()
            Gui.Snapper.getPoint(last = p2,
                                 callback = self.PointCallback,
                                 movecallback = self.MoveCallback,
                                 extradlg = self.taskbox())


    def setHeightUI(self):
        """Command Gui.
        """
        if (len(self.points) == 3) and self.HeightValue:
            cube = App.ActiveDocument.addObject("Part::Box","Cube")
            cube.Length = self.LengthValue
            cube.Width = self.WidthValue
            cube.Height = self.HeightValue
            # we get 3 points that define our cube orientation
            p1 = self.cubetracker[0].p1()
            p2 = self.cubetracker[0].p2()
            p3 = self.cubetracker[0].p4()
            Gui.Snapper.off()
            import WorkingPlane
            cube.Placement = WorkingPlane.getPlacementFromPoints([p1,p2,p3])
            if hasattr(App,"DraftWorkingPlane"):
                App.DraftWorkingPlane.restore()
            Gui.Snapper.setGrid()
            for c in self.cubetracker:
                c.off()
            Gui.Snapper.getPoint()
            Gui.Snapper.off()
            if hasattr(Gui,"draftToolBar"):
                Gui.draftToolBar.offUi()
            App.ActiveDocument.recompute()
            


Gui.addCommand('Draft_PartBox', GuiCommand_Part_Box())
