"""This modules sets up and manages the IFC-related properties, types
and attributes of Arch/BIM objects.

IFC, or Industry Foundation Classes are a standardised way to digitally
describe the built environment.  The ultimate goal of IFC is to provide
better interoperability between software that deals with the built
environment. You can learn more here:
https://technical.buildingsmart.org/standards/ifc/

You can learn more about the technical details of the IFC schema here:
https://standards.buildingsmart.org/IFC/RELEASE/IFC4/FINAL/HTML/

This bunch of functions is copied from ArchIFC module, in a genaralization
attempt of Arch IFC Properties in May 2020 By carlo pavan.
"""

import FreeCAD as App
import json

if App.GuiUp:
    from PySide.QtCore import QT_TRANSLATE_NOOP
else:
    def QT_TRANSLATE_NOOP(ctx, txt):
        return txt

import ArchIFCSchema

IfcTypes = [''.join(map(lambda x: x if x.islower() else " "+x, t[3:]))[1:] for t in ArchIFCSchema.IfcProducts.keys()]

# Functions to set IFC properties on most used objects
def set_ifc_type_as_wall(obj):
    """Not implemented yet"""
    pass

def set_ifc_type_as_window(obj):
    """Not implemented yet"""
    pass

def set_ifc_type_as_building_level(obj):
    """Not implemented yet"""
    pass

# Functions to set IFC properties (IfcType, IfcData, IfcProperties)

def set_ifc_properties(obj, ifc_type="IfcProduct"):
    """Add the object properties for storing IFC data.

    Also migrate old versions of IFC properties to the new property names
    using the .migrateDeprecatedAttributes() method.

    Parameters
    ----------
    ifc_type: string
        The IFC Type that have to be initialized.
        "IfcProduct" : The Schema used by almost every Arch Object
        "IfcContext" : Currently, only the Project object has Context schema.
        "IfcType" : not supported yet
    """

    if not "IfcData" in obj.PropertiesList:
        obj.addProperty("App::PropertyMap", "IfcData",
                        "IFC", QT_TRANSLATE_NOOP("App::Property","IFC data"))

    if not "IfcType" in obj.PropertiesList:
        # IfcType is set read only to be controlled only by a proper setter function
        obj.addProperty("App::PropertyEnumeration", "IfcType",
                        "IFC", QT_TRANSLATE_NOOP("App::Property","The IFC type of this object"))#, 1)

    if not "IfcSchema" in obj.PropertiesList:
        obj.addProperty("App::PropertyString", "IfcSchema",
                        "IFC", QT_TRANSLATE_NOOP("App::Property","The IFC schema of this object"), 4)
        obj.IfcSchema = ifc_type

    if not "IfcProperties" in obj.PropertiesList:
        obj.addProperty("App::PropertyMap", "IfcProperties",
                        "IFC", QT_TRANSLATE_NOOP("App::Property","IFC properties of this object"))

    if "IfcType" in obj.PropertiesList:
        if obj.IfcSchema == "IfcProduct":
            ifc_schema = ArchIFCSchema.IfcProducts
        elif obj.IfcSchema == "IfcContext":
            # TODO: IfcContext not supported yet
            ifc_schema = ArchIFCSchema.IfcProducts
        elif obj.IfcSchema == "IfcType":
            # TODO: IfcType not supported yet
            ifc_schema = ArchIFCSchema.IfcProducts
        else:
            return
        obj.IfcType = canonicalize_ifc_types(ifc_schema)

    migrate_deprecated_attributes(obj)


def canonicalize_ifc_types(IFC_schema):
    """Get the names of IFC types, converted to the form used in Arch.

    Change the names of all IFC types to a more human readable form which
    is used instead throughout Arch instead of the raw type names. The
    names have the "Ifc" stripped from the start of their name, and spaces
    inserted between the words.

    Returns
    -------
    list of str
        The list of every IFC type name in their form used in Arch. List
        will have names in the same order as they appear in the schema's
        JSON, as per the .keys() method of dicts.

    """
    return [''.join(map(lambda x: x if x.islower() else " "+x, t[3:]))[1:] for t in IFC_schema.keys()]


def migrate_deprecated_attributes(obj):
    """Update the object to use the newer property names for IFC related properties.
    """

    if "Role" in obj.PropertiesList:
        r = obj.Role
        obj.removeProperty("Role")
        if r in IfcTypes:
            obj.IfcType = r
            App.Console.PrintMessage("Upgrading "+obj.Label+" Role property to IfcType\n")

    if "IfcRole" in obj.PropertiesList:
        r = obj.IfcRole
        obj.removeProperty("IfcRole")
        if r in IfcTypes:
            obj.IfcType = r
            App.Console.PrintMessage("Upgrading "+obj.Label+" IfcRole property to IfcType\n")
    
    if "IfcAttributes"in obj.PropertiesList:
        obj.IfcData = obj.IfcAttributes
        obj.removeProperty("IfcAttributes")


# Functions to set IFC attributes according to the given IfcType

def setup_ifc_attributes(obj):
    """Set up the IFC attributes in the object's properties.

    Add the attributes specified in the object's IFC type schema, to the
    object's properties. Do not re-add them if they're already present.
    Also remove old IFC attribute properties that no longer appear in the
    schema for backwards compatibility.

    Do so using the .add_ifc_attributes() and
    .purgeUnusedIfcAttributesFromPropertiesList() methods.

    Learn more about IFC attributes here:
    https://standards.buildingsmart.org/IFC/RELEASE/IFC4/FINAL/HTML/schema/chapter-3.htm#attribute
    """

    ifcTypeSchema = get_ifc_type_schema(obj)
    if ifcTypeSchema is None:
        return
    purgeUnusedIfcAttributesFromPropertiesList(ifcTypeSchema, obj)
    add_ifc_attributes(ifcTypeSchema, obj)


def get_ifc_type_schema(obj):
    """Get the schema of the IFC type provided.

    If the IFC type is undefined, return the schema of the
    IfcBuildingElementProxy.

    Parameter
    ---------
    IfcType: str
        The IFC type whose schema you want.

    Returns
    -------
    dict
        Returns the schema of the type as a dict.
    None
        Returns None if the IFC type does not exist.
    """
    IfcType = obj.IfcType
    name = "Ifc" + IfcType.replace(" ", "")
    if IfcType == "Undefined":
        name = "IfcBuildingElementProxy"
    if name in get_ifc_schema(obj):
        return get_ifc_schema(obj)[name]
    return None


def get_ifc_schema(obj):
    """Get the IFC schema of all types relevant to this class.

    Intended to be overwritten by the classes that inherit this class.

    Returns
    -------
    dict
        The schema of all the types relevant to this class.
    """
    if obj.IfcSchema == "IfcProduct":
        return ArchIFCSchema.IfcProducts
    elif obj.IfcSchema == "IfcContext":
        return ArchIFCSchema.IfcContexts
    elif obj.IfcSchema == "IfcType":
        # TODO: IfcType not supported yet
        return ArchIFCSchema.IfcProducts


def add_ifc_attributes(ifcTypeSchema, obj):
    """Add the attributes of the IFC type's schema to the object's properties.

    Add the attributes as properties of the object. Also add the
    attribute's schema within the object's IfcData property. Do so using
    the .add_ifc_attribute() method.

    Also add expressions to copy data from the object's editable
    properties.  This means the IFC properties will remain accurate with
    the actual values of the object. Do not do so for all IFC properties.
    Do so using the .add_ifc_attribute_value_expressions() method.

    Learn more about expressions here:
    https://wiki.freecadweb.org/Expressions

    Do not add the attribute if the object has a property with the
    attribute's name. Also do not add the attribute if its name is
    RefLatitude, RefLongitude, or Name.

    Parameters
    ----------
    ifcTypeSchema: dict
        The schema of the IFC type.
    """

    for attribute in ifcTypeSchema["attributes"]:
        if attribute["name"] in obj.PropertiesList \
            or attribute["name"] == "RefLatitude" \
            or attribute["name"] == "RefLongitude" \
            or attribute["name"] == "Name":
            continue
        add_ifc_attribute(obj, attribute)
        add_ifc_attribute_value_expressions(obj, attribute)


def add_ifc_attribute(obj, attribute):
    """Add an IFC type's attribute to the object, within its properties.

    Add the attribute's schema to the object's IfcData property, as an
    item under its "attributes" array.

    Also add the attribute as a property of the object.

    Parameters
    ----------
    attribute: dict
        The attribute to add. Should have the structure of an attribute
        found within the IFC schemas.
    """
    if not hasattr(obj, "IfcData"):
        return
    IfcData = obj.IfcData

    if "attributes" not in IfcData:
        IfcData["attributes"] = "{}"
    IfcAttributes = json.loads(IfcData["attributes"])
    IfcAttributes[attribute["name"]] = attribute
    IfcData["attributes"] = json.dumps(IfcAttributes)

    obj.IfcData = IfcData
    if attribute["is_enum"]:
        obj.addProperty("App::PropertyEnumeration", 
                        attribute["name"], 
                        "IFC Attributes", 
                        QT_TRANSLATE_NOOP("App::Property", "Description of IFC attributes are not yet implemented"))
        setattr(obj, attribute["name"], attribute["enum_values"])
    else:
        propertyType = "App::" + ArchIFCSchema.IfcTypes[attribute["type"]]["property"]
        obj.addProperty(propertyType, 
                        attribute["name"], 
                        "IFC Attributes", 
                        QT_TRANSLATE_NOOP("App::Property", "Description of IFC attributes are not yet implemented"))


def add_ifc_attribute_value_expressions(obj, attribute):
    """Add expressions for IFC attributes, so they stay accurate with the object.

    Add expressions to the object that copy data from the editable
    properties of the object. This ensures that the IFC attributes will
    remain accurate with the actual values of the object.

    Currently, add expressions for the following IFC attributes:

    - OverallWidth
    - OverallHeight
    - ElevationWithFlooring
    - Elevation
    - NominalDiameter
    - BarLength
    - RefElevation
    - LongName

    Learn more about expressions here:
    https://wiki.freecadweb.org/Expressions

    Parameters
    ----------
    attribute: dict
        The schema of the attribute to add the expression for.
    """

    if obj.getGroupOfProperty(attribute["name"]) != "IFC Attributes" \
        or attribute["name"] not in obj.PropertiesList:
        return
    if attribute["name"] == "OverallWidth":
        if "Length" in obj.PropertiesList:
            obj.setExpression("OverallWidth", "Length.Value")
        elif "Width" in obj.PropertiesList:
            obj.setExpression("OverallWidth", "Width.Value")
        elif hasattr(obj, "Shape") and obj.Shape and (obj.Shape.BoundBox.XLength > obj.Shape.BoundBox.YLength):
            obj.setExpression("OverallWidth", "Shape.BoundBox.XLength")
        elif hasattr(obj, "Shape") and obj.Shape:
            obj.setExpression("OverallWidth", "Shape.BoundBox.YLength")
    elif attribute["name"] == "OverallHeight":
        if "Height" in obj.PropertiesList:
            obj.setExpression("OverallHeight", "Height.Value")
        elif hasattr(obj, "Shape"):
            obj.setExpression("OverallHeight", "Shape.BoundBox.ZLength")
    elif attribute["name"] == "ElevationWithFlooring" and "Shape" in obj.PropertiesList:
        obj.setExpression("ElevationWithFlooring", "Shape.BoundBox.ZMin")
    elif attribute["name"] == "Elevation" and "Placement" in obj.PropertiesList:
        obj.setExpression("Elevation", "Placement.Base.z")
    elif attribute["name"] == "NominalDiameter" and "Diameter" in obj.PropertiesList:
        obj.setExpression("NominalDiameter", "Diameter.Value")
    elif attribute["name"] == "BarLength" and "Length" in obj.PropertiesList:
        obj.setExpression("BarLength", "Length.Value")
    elif attribute["name"] == "RefElevation" and "Elevation" in obj.PropertiesList:
        obj.setExpression("RefElevation", "Elevation.Value")
    elif attribute["name"] == "LongName":
        obj.LongName = obj.Label


def set_obj_ifc_attribute_value(obj, attributeName, value):
    """Change the value of an IFC attribute within the IfcData property's json.

    Parameters
    ----------
    attributeName: str
        The name of the attribute to change.
    value:
        The new value to set.
    """
    IfcData = obj.IfcData
    if "attributes" not in IfcData:
        IfcData["attributes"] = "{}"
    IfcAttributes = json.loads(IfcData["attributes"])
    if isinstance(value, App.Units.Quantity):
        value = float(value)
    if not attributeName in IfcAttributes:
        IfcAttributes[attributeName] = {}
    IfcAttributes[attributeName]["value"] = value
    IfcData["attributes"] = json.dumps(IfcAttributes)
    obj.IfcData = IfcData


def setObjIfcComplexAttributeValue(obj, attributeName, value):
    """Changes the value of the complex attribute in the IfcData property JSON.

    Parameters
    ----------
    attributeName: str
        The name of the attribute to change.
    value:
        The new value to set.
    """

    IfcData = obj.IfcData
    IfcAttributes = json.loads(IfcData["complex_attributes"])
    IfcAttributes[attributeName] = value
    IfcData["complex_attributes"] = json.dumps(IfcAttributes)
    obj.IfcData = IfcData


def getObjIfcComplexAttribute(obj, attributeName):
    """Get the value of the complex attribute, as stored in the IfcData JSON.

    Parameters
    ----------
    attributeName: str
        The name of the complex attribute to access.

    Returns
    -------
    The value of the complex attribute.
    """

    return json.loads(obj.IfcData["complex_attributes"])[attributeName]


def purgeUnusedIfcAttributesFromPropertiesList(ifcTypeSchema, obj):
    """Remove properties representing IFC attributes if they no longer appear.

    Remove the property representing an IFC attribute, if it does not
    appear in the schema of the IFC type provided. Also, remove the
    property if its attribute is an enum type, presumably for backwards
    compatibility.

    Learn more about IFC enums here:
    https://standards.buildingsmart.org/IFC/RELEASE/IFC4/FINAL/HTML/schema/chapter-3.htm#enumeration
    """

    for property in obj.PropertiesList:
        if obj.getGroupOfProperty(property) != "IFC Attributes":
            continue
        ifcAttribute = getIfcAttributeSchema(ifcTypeSchema, property)
        if ifcAttribute is None or ifcAttribute["is_enum"] is True:
            obj.removeProperty(property)


def getIfcAttributeSchema(ifcTypeSchema, name):
    """Get the schema of an IFC attribute with the given name.
    
    Convert the IFC attribute's name from the human readable version Arch
    uses, and convert it to the less readable name it has in the IFC
    schema.

    Parameters
    ----------
    ifcTypeSchema: dict
        The schema of the IFC type to access the attribute of.
    name: str
        The name the attribute has in Arch.

    Returns
    -------
    dict
        Returns the schema of the attribute.
    None
        Returns None if the IFC type does not have the attribute requested.

    """

    for attribute in ifcTypeSchema["attributes"]:
        if attribute["name"].replace(' ', '') == name:
            return attribute
    return None


def migrateDeprecatedAttributes(obj):
    """Update the object to use the newer property names for IFC related properties.
    """

    if "Role" in obj.PropertiesList:
        r = obj.Role
        obj.removeProperty("Role")
        if r in IfcTypes:
            obj.IfcType = r
            App.Console.PrintMessage("Upgrading "+obj.Label+" Role property to IfcType\n")

    if "IfcRole" in obj.PropertiesList:
        r = obj.IfcRole
        obj.removeProperty("IfcRole")
        if r in IfcTypes:
            obj.IfcType = r
            App.Console.PrintMessage("Upgrading "+obj.Label+" IfcRole property to IfcType\n")
    
    if "IfcAttributes"in obj.PropertiesList:
        obj.IfcData = obj.IfcAttributes
        obj.removeProperty("IfcAttributes")