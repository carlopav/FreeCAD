# ***************************************************************************
# *   Copyright (c) 2009, 2010 Yorik van Havre <yorik@uncreated.net>        *
# *   Copyright (c) 2009, 2010 Ken Cline <cline@frii.com>                   *
# *                                                                         *
# *   This program is free software; you can redistribute it and/or modify  *
# *   it under the terms of the GNU Lesser General Public License (LGPL)    *
# *   as published by the Free Software Foundation; either version 2 of     *
# *   the License, or (at your option) any later version.                   *
# *   for detail see the LICENCE text file.                                 *
# *                                                                         *
# *   This program is distributed in the hope that it will be useful,       *
# *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
# *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
# *   GNU Library General Public License for more details.                  *
# *                                                                         *
# *   You should have received a copy of the GNU Library General Public     *
# *   License along with this program; if not, write to the Free Software   *
# *   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
# *   USA                                                                   *
# *                                                                         *
# ***************************************************************************
"""This module provides the object code for Draft make_polyline function.
"""
## @package make_polyline
# \ingroup DRAFT
# \brief This module provides the code for Draft make_polyline function.

import FreeCAD as App

import DraftGeomUtils

from draftutils.gui_utils import format_object
from draftutils.gui_utils import select

from draftutils.utils import get_param
from draftutils.utils import type_check
from draftutils.utils import get_type
from draftutils.todo import ToDo

from draftobjects.clone import Clone
from draftviewproviders.view_clone import ViewProviderClone


def make_clone(obj, delta=None, forcedraft=False):
    """clone(obj,[delta,forcedraft])
    
    Makes a clone of the given object(s). 
    The clone is an exact, linked copy of the given object. If the original
    object changes, the final object changes too. 
    
    Parameters
    ----------
    obj : 

    delta : Base.Vector
        Delta Vector to move the clone from the original position. 

    forcedraft : bool
        If forcedraft is True, the resulting object is a Draft clone
        even if the input object is an Arch object.
    
    """

    prefix = get_param("ClonePrefix","")

    cl = None

    if prefix:
        prefix = prefix.strip() + " "

    if not isinstance(obj,list):
        obj = [obj]

    if (len(obj) == 1) and obj[0].isDerivedFrom("Part::Part2DObject"):
        cl = App.ActiveDocument.addObject("Part::Part2DObjectPython","Clone2D")
        cl.Label = prefix + obj[0].Label + " (2D)"

    elif (len(obj) == 1) and (hasattr(obj[0],"CloneOf") or (get_type(obj[0]) == "BuildingPart")) and (not forcedraft):
        # arch objects can be clones
        import Arch
        if get_type(obj[0]) == "BuildingPart":
            cl = Arch.makeComponent()
        else:
            try:
                clonefunc = getattr(Arch,"make"+obj[0].Proxy.Type)
            except:
                pass # not a standard Arch object... Fall back to Draft mode
            else:
                cl = clonefunc()
        if cl:
            base = getCloneBase(obj[0])
            cl.Label = prefix + base.Label
            cl.CloneOf = base
            if hasattr(cl,"Material") and hasattr(obj[0],"Material"):
                cl.Material = obj[0].Material
            if get_type(obj[0]) != "BuildingPart":
                cl.Placement = obj[0].Placement
            try:
                cl.Role = base.Role
                cl.Description = base.Description
                cl.Tag = base.Tag
            except:
                pass
            if App.GuiUp:
                format_object(cl,base)
                cl.ViewObject.DiffuseColor = base.ViewObject.DiffuseColor
                if get_type(obj[0]) in ["Window","BuildingPart"]:
                    ToDo.delay(Arch.recolorize,cl)
            select(cl)
            return cl
    # fall back to Draft clone mode
    if not cl:
        cl = App.ActiveDocument.addObject("Part::FeaturePython","Clone")
        cl.addExtension("Part::AttachExtensionPython", None)
        cl.Label = prefix + obj[0].Label
    Clone(cl)
    if App.GuiUp:
        ViewProviderClone(cl.ViewObject)
    cl.Objects = obj
    if delta:
        cl.Placement.move(delta)
    elif (len(obj) == 1) and hasattr(obj[0],"Placement"):
        cl.Placement = obj[0].Placement
    format_object(cl,obj[0])
    if hasattr(cl,"LongName") and hasattr(obj[0],"LongName"):
        cl.LongName = obj[0].LongName
    if App.GuiUp and (len(obj) > 1):
        cl.ViewObject.Proxy.resetColors(cl.ViewObject)
    select(cl)
    return cl


def getCloneBase(obj, strict=False):
    """getCloneBase(obj, [strict])
    
    Returns the object cloned by this object, if any, or this object if 
    it is no clone. 

    Parameters
    ----------
    obj : 
        TODO: describe

    strict : bool (default = False)
        If strict is True, if this object is not a clone, 
        this function returns False
    """
    if hasattr(obj,"CloneOf"):
        if obj.CloneOf:
            return getCloneBase(obj.CloneOf)
    if get_type(obj) == "Clone":
        return obj.Objects[0]
    if strict:
        return False
    return obj