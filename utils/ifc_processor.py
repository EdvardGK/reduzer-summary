# -*- coding: utf-8 -*-
"""
IFC file processing and quality control

This module provides functions to:
- Load and parse IFC files
- Extract elements with properties
- Detect duplicate GUIDs
- Check for overlapping geometry (especially ARK vs RIB)
- Verify materials and load-bearing properties
- Extract MMI codes from property sets
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any, Tuple
from pathlib import Path
import re

try:
    import ifcopenshell
    import ifcopenshell.geom
    IFC_AVAILABLE = True
except ImportError:
    IFC_AVAILABLE = False
    print("Warning: ifcopenshell not installed. IFC processing disabled.")

try:
    from shapely.geometry import box, Polygon
    from shapely.ops import unary_union
    SHAPELY_AVAILABLE = True
except ImportError:
    SHAPELY_AVAILABLE = False
    print("Warning: shapely not installed. Precise overlap detection disabled.")


def load_ifc_file(file_buffer) -> Optional['ifcopenshell.file']:
    """
    Load and parse IFC file from upload buffer.

    Args:
        file_buffer: File-like object or path to IFC file

    Returns:
        IFC file object if successful, None otherwise

    Raises:
        Exception if file cannot be parsed
    """
    if not IFC_AVAILABLE:
        raise ImportError("ifcopenshell is not installed. Run: pip install ifcopenshell")

    try:
        # Handle different input types
        if isinstance(file_buffer, (str, Path)):
            ifc_file = ifcopenshell.open(str(file_buffer))
        else:
            # Streamlit UploadedFile or BytesIO
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.ifc') as tmp:
                tmp.write(file_buffer.read())
                tmp_path = tmp.name

            ifc_file = ifcopenshell.open(tmp_path)

            # Clean up temp file
            Path(tmp_path).unlink(missing_ok=True)

        return ifc_file

    except Exception as e:
        print(f"Error loading IFC file: {e}")
        raise


def extract_mmi_from_properties(element) -> Optional[str]:
    """
    Extract MMI code from element properties.

    Searches for properties matching pattern: *.*MMI* (case insensitive)

    Args:
        element: IFC element

    Returns:
        MMI code as string (e.g., "300", "700") or None if not found
    """
    if not hasattr(element, 'IsDefinedBy'):
        return None

    # Check all property sets
    for definition in element.IsDefinedBy:
        if definition.is_a('IfcRelDefinesByProperties'):
            property_set = definition.RelatingPropertyDefinition

            if property_set.is_a('IfcPropertySet'):
                # Check each property
                for prop in property_set.HasProperties:
                    # Check property name for MMI pattern
                    if prop.is_a('IfcPropertySingleValue'):
                        prop_name = prop.Name.lower() if prop.Name else ''

                        if 'mmi' in prop_name:
                            # Extract value
                            if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                value_str = str(prop.NominalValue.wrappedValue)

                                # Try to extract 3-digit code
                                match = re.search(r'\b(\d{3})\b', value_str)
                                if match:
                                    return match.group(1)

                                # Return as-is if numeric
                                if value_str.isdigit():
                                    return value_str

    # Check classification references
    if hasattr(element, 'HasAssociations'):
        for association in element.HasAssociations:
            if association.is_a('IfcRelAssociatesClassification'):
                ref = association.RelatingClassification

                if hasattr(ref, 'Name'):
                    name = ref.Name.lower() if ref.Name else ''
                    if 'mmi' in name:
                        # Try to extract code
                        match = re.search(r'\b(\d{3})\b', ref.Name)
                        if match:
                            return match.group(1)

                if hasattr(ref, 'Identification'):
                    ident = ref.Identification or ''
                    match = re.search(r'\b(\d{3})\b', str(ident))
                    if match:
                        return match.group(1)

    return None


def detect_discipline(element) -> Optional[str]:
    """
    Detect discipline (ARK, RIV, RIE, RIB, RIBp) from element.

    Logic:
    1. Check property sets for explicit discipline
    2. Check classification
    3. Fallback to element type mapping

    Args:
        element: IFC element

    Returns:
        Discipline code or None
    """
    # Map of IFC types to disciplines (fallback)
    TYPE_TO_DISCIPLINE = {
        # ARK - Architectural
        'IfcWall': 'ARK',
        'IfcWallStandardCase': 'ARK',
        'IfcDoor': 'ARK',
        'IfcWindow': 'ARK',
        'IfcCurtainWall': 'ARK',
        'IfcRoof': 'ARK',
        'IfcStair': 'ARK',
        'IfcRailing': 'ARK',

        # RIB - Structural
        'IfcColumn': 'RIB',
        'IfcBeam': 'RIB',
        'IfcSlab': 'RIB',
        'IfcFooting': 'RIBp',
        'IfcPile': 'RIBp',
        'IfcMember': 'RIB',
        'IfcPlate': 'RIB',

        # RIV - HVAC
        'IfcDuctSegment': 'RIV',
        'IfcDuctFitting': 'RIV',
        'IfcAirTerminal': 'RIV',
        'IfcPipeSegment': 'RIV',
        'IfcPipeFitting': 'RIV',
        'IfcFlowTerminal': 'RIV',
        'IfcFlowController': 'RIV',

        # RIE - Electrical
        'IfcCableSegment': 'RIE',
        'IfcCableCarrierSegment': 'RIE',
        'IfcLightFixture': 'RIE',
        'IfcOutlet': 'RIE',
        'IfcSwitchingDevice': 'RIE',
    }

    # Check property sets first
    if hasattr(element, 'IsDefinedBy'):
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                property_set = definition.RelatingPropertyDefinition

                if property_set.is_a('IfcPropertySet'):
                    for prop in property_set.HasProperties:
                        if prop.is_a('IfcPropertySingleValue'):
                            prop_name = prop.Name.lower() if prop.Name else ''

                            if 'discipline' in prop_name or 'fag' in prop_name:
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    value = str(prop.NominalValue.wrappedValue).upper()

                                    # Match common patterns
                                    if any(disc in value for disc in ['ARK', 'RIV', 'RIE', 'RIB']):
                                        if 'RIBP' in value or 'RIBp' in value:
                                            return 'RIBp'
                                        elif 'RIB' in value:
                                            return 'RIB'
                                        elif 'ARK' in value:
                                            return 'ARK'
                                        elif 'RIV' in value:
                                            return 'RIV'
                                        elif 'RIE' in value:
                                            return 'RIE'

    # Fallback to type mapping
    element_type = element.is_a()
    return TYPE_TO_DISCIPLINE.get(element_type)


def check_load_bearing(element) -> bool:
    """
    Check if element is load-bearing.

    Checks:
    1. LoadBearing property
    2. IsStructural role
    3. Element type (structural elements)

    Args:
        element: IFC element

    Returns:
        True if load-bearing, False otherwise
    """
    # Check LoadBearing property
    if hasattr(element, 'IsDefinedBy'):
        for definition in element.IsDefinedBy:
            if definition.is_a('IfcRelDefinesByProperties'):
                property_set = definition.RelatingPropertyDefinition

                if property_set.is_a('IfcPropertySet'):
                    for prop in property_set.HasProperties:
                        if prop.is_a('IfcPropertySingleValue'):
                            if prop.Name and 'loadbearing' in prop.Name.lower():
                                if hasattr(prop, 'NominalValue') and prop.NominalValue:
                                    return bool(prop.NominalValue.wrappedValue)

    # Check if it's a structural element type
    structural_types = [
        'IfcColumn', 'IfcBeam', 'IfcMember',
        'IfcFooting', 'IfcPile',
        'IfcStructuralCurveMember', 'IfcStructuralSurfaceMember'
    ]

    if element.is_a() in structural_types:
        return True

    # Check if Slab is structural
    if element.is_a('IfcSlab'):
        if hasattr(element, 'PredefinedType'):
            slab_type = element.PredefinedType
            if slab_type in ['FLOOR', 'BASESLAB', 'ROOF']:
                return True

    # Check if Wall is structural
    if element.is_a() in ['IfcWall', 'IfcWallStandardCase']:
        # Assume walls could be load-bearing, check property
        return True  # Conservative assumption

    return False


def extract_material(element) -> Dict[str, Any]:
    """
    Extract material information from element.

    Returns:
        Dictionary with material info: {name, type, category}
    """
    result = {
        'name': None,
        'type': None,
        'category': None
    }

    if not hasattr(element, 'HasAssociations'):
        return result

    for association in element.HasAssociations:
        if association.is_a('IfcRelAssociatesMaterial'):
            material_select = association.RelatingMaterial

            # Single material
            if material_select.is_a('IfcMaterial'):
                result['name'] = material_select.Name
                result['category'] = categorize_material(material_select.Name)

            # Material layer set
            elif material_select.is_a('IfcMaterialLayerSet'):
                layers = []
                for layer in material_select.MaterialLayers:
                    if layer.Material:
                        layers.append(layer.Material.Name)

                result['name'] = ' + '.join(layers) if layers else None
                if layers:
                    result['category'] = categorize_material(layers[0])

            # Material list
            elif material_select.is_a('IfcMaterialList'):
                materials = []
                for mat in material_select.Materials:
                    materials.append(mat.Name)

                result['name'] = ' + '.join(materials) if materials else None
                if materials:
                    result['category'] = categorize_material(materials[0])

            break

    return result


def categorize_material(material_name: str) -> Optional[str]:
    """
    Categorize material into: concrete, steel, wood, etc.

    Args:
        material_name: Material name string

    Returns:
        Material category
    """
    if not material_name:
        return None

    name_lower = material_name.lower()

    if any(word in name_lower for word in ['concrete', 'betong', 'concret']):
        return 'concrete'
    elif any(word in name_lower for word in ['steel', 'stål', 'staal']):
        return 'steel'
    elif any(word in name_lower for word in ['rebar', 'armering', 'reinforcement']):
        return 'rebar'
    elif any(word in name_lower for word in ['wood', 'tre', 'timber', 'lumber']):
        return 'wood'
    elif any(word in name_lower for word in ['glass', 'glas']):
        return 'glass'
    elif any(word in name_lower for word in ['gypsum', 'gips']):
        return 'gypsum'
    else:
        return 'other'


def extract_elements(ifc_file) -> pd.DataFrame:
    """
    Extract all relevant IFC elements to DataFrame.

    Args:
        ifc_file: Parsed IFC file object

    Returns:
        DataFrame with element data
    """
    if not IFC_AVAILABLE:
        raise ImportError("ifcopenshell not installed")

    elements_data = []

    # Element types to extract
    element_types = [
        'IfcWall', 'IfcWallStandardCase', 'IfcColumn', 'IfcBeam', 'IfcSlab',
        'IfcDoor', 'IfcWindow', 'IfcStair', 'IfcRailing', 'IfcRoof',
        'IfcFooting', 'IfcPile', 'IfcMember', 'IfcPlate',
        'IfcDuctSegment', 'IfcPipeSegment', 'IfcCableSegment'
    ]

    for elem_type in element_types:
        elements = ifc_file.by_type(elem_type)

        for element in elements:
            try:
                # Basic info
                guid = element.GlobalId
                name = element.Name or ''
                elem_type_str = element.is_a()

                # Extract properties
                discipline = detect_discipline(element)
                mmi_code = extract_mmi_from_properties(element)
                is_load_bearing = check_load_bearing(element)
                material_info = extract_material(element)

                # Geometry (simplified - just bounding box)
                # TODO: Extract full geometry for overlap detection
                location = None
                volume = None

                elements_data.append({
                    'guid': guid,
                    'element_type': elem_type_str,
                    'name': name,
                    'discipline': discipline,
                    'mmi_code': mmi_code,
                    'load_bearing': is_load_bearing,
                    'material_name': material_info['name'],
                    'material_category': material_info['category'],
                    'volume_m3': volume,
                    'location': location
                })

            except Exception as e:
                print(f"Warning: Could not process element {element.GlobalId}: {e}")
                continue

    df = pd.DataFrame(elements_data)
    return df


def detect_duplicates(elements_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect duplicate GUIDs and near-duplicate geometry.

    Args:
        elements_df: DataFrame with element data

    Returns:
        DataFrame with duplicate issues
    """
    duplicates = []

    # Check 1: Duplicate GUIDs (CRITICAL ERROR!)
    guid_counts = elements_df['guid'].value_counts()
    duplicate_guids = guid_counts[guid_counts > 1]

    for guid, count in duplicate_guids.items():
        rows = elements_df[elements_df['guid'] == guid]
        duplicates.append({
            'guid': guid,
            'element_type': rows.iloc[0]['element_type'],
            'discipline': rows.iloc[0]['discipline'],
            'count': count
        })

    # Check 2: Near-duplicate geometry (WARNING)
    # TODO: Implement geometry-based duplicate detection

    return pd.DataFrame(duplicates)


def detect_ark_rib_overlaps(elements_df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect overlapping geometry between ARK and RIB elements.

    Focus on load-bearing ARK elements vs all RIB elements.

    Args:
        elements_df: DataFrame with element data

    Returns:
        DataFrame with overlap issues
    """
    overlaps = []

    # Get ARK load-bearing elements
    ark_bearing = elements_df[
        (elements_df['discipline'] == 'ARK') &
        (elements_df['load_bearing'] == True)
    ]

    # Get all RIB elements
    rib_all = elements_df[elements_df['discipline'] == 'RIB']

    # TODO: Implement bounding box and geometric overlap detection
    # This requires geometry extraction from IFC which is complex

    # Placeholder for now
    print(f"Found {len(ark_bearing)} ARK load-bearing elements")
    print(f"Found {len(rib_all)} RIB elements")
    print("Geometric overlap detection not yet implemented")

    # Return empty DataFrame with correct structure
    return pd.DataFrame(overlaps, columns=['guid', 'element_type', 'disciplines', 'overlap_type'])


def verify_materials(elements_df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify material assignments are appropriate.

    Checks:
    - Load-bearing elements have materials
    - Structural elements have structural materials

    Args:
        elements_df: DataFrame with element data

    Returns:
        DataFrame with material issues
    """
    issues = []

    # Check 1: Load-bearing without material
    bearing_no_material = elements_df[
        (elements_df['load_bearing'] == True) &
        (elements_df['material_name'].isna())
    ]

    for _, elem in bearing_no_material.iterrows():
        issues.append({
            'guid': elem['guid'],
            'element_type': elem['element_type'],
            'discipline': elem['discipline'],
            'issue': 'Load-bearing element without material definition'
        })

    # Check 2: Structural elements with inappropriate materials
    structural_types = ['IfcColumn', 'IfcBeam', 'IfcSlab']
    structural_materials = ['concrete', 'steel', 'rebar']

    wrong_material = elements_df[
        (elements_df['element_type'].isin(structural_types)) &
        (elements_df['load_bearing'] == True) &
        (~elements_df['material_category'].isin(structural_materials))
    ]

    for _, elem in wrong_material.iterrows():
        issues.append({
            'guid': elem['guid'],
            'element_type': elem['element_type'],
            'discipline': elem['discipline'],
            'issue': f"Structural element has non-structural material: {elem['material_category']}"
        })

    return pd.DataFrame(issues)
