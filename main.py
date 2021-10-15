# coding: utf-8
import os
import gzip
import typing
import shutil
import argparse
import binascii
import xml.etree.ElementTree as ET


# Arguments parser
parser = argparse.ArgumentParser(description="Script to import Guitar Pro markers as locators in Ableton")
parser.add_argument(
    "als_file", type=str,
    help="Relative or absolute path to Ableton project '.als' file. It's been tested only with Ableton 10.1.41."
)
parser.add_argument(
    "gp_xml_file", type=str,
    help="XML file exported from Guitar Pro. It's been tested only witg Guitar Pro 7.5.5."
)
args = parser.parse_args()


def add_als_extension_if_it_is_not_set(als_file: str) -> str:
    """
    Add the extension ".als" to the selected file in case it does not have it
    :param als_file: file to check
    :return: the file with the correct extension
    """
    return als_file if als_file.endswith(".als") else f"{als_file}.als"


def extract_xml_from_ableton_project(als_file: str) -> ET.ElementTree:
    """
    Extract the XML inner file from a Ableton project
    :param als_file: relative or absolute path to Ableton project ".als" file
    :return: if everything went right, it returns the project config as a XML tree
    """
    als_file = add_als_extension_if_it_is_not_set(als_file)
    if os.path.isfile(als_file):
        with open(als_file, 'rb') as project_compressed:
            if not binascii.hexlify(project_compressed.read(2)) == b'1f8b':
                raise Exception("Nothing to do here")
        with gzip.open(als_file, 'rb') as project_uncompressed:
            project_xml_string = project_uncompressed.read().decode("utf-8")
            return ET.ElementTree(ET.fromstring(project_xml_string))
    else:
        raise FileNotFoundError(f"The Ableton project {als_file} does not exist")


def extract_marker_from_gp_xml(gp_xml_file: str) -> list[dict[str, str]]:
    """
    Extract the markers a Guitar Pro project contains. It needs the Guitar Pro project extracted as XML. Only
    XML created with GP7.5 have been tested
    :param gp_xml_file: XML file to read
    :return: a list of dictionaries whose first key is "bar", representing the bar where the marker belongs, and the
    second is "marker", where the marker name is
    """
    if os.path.isfile(gp_xml_file):
        marker_list = []
        tree = ET.parse(gp_xml_file)
        # Get all the bars of the tab
        measures = tree.find("part").findall("measure")
        # Find all the measures with marker
        for measure in [measure for measure in measures if measure.find("direction")]:
            for rehearsal in [
                direction.find("direction-type").find("rehearsal") for direction
                in measure.findall("direction") if direction.find("direction-type").findall("rehearsal")
            ]:
                # Extract the marker
                marker_list.append({"bar": measure.get("number"), "marker": rehearsal.text})
        return marker_list
    else:
        raise FileNotFoundError(f"The GuitarPro XML file {gp_xml_file} does not exist")


def add_markers_to_ableton_project(
        ableton_project_tree: ET.ElementTree, gp_markers_dict: list[dict[str, str]]
) -> typing.NoReturn:
    """
    Modify the Ableton project XML and add the markers selected
    :param ableton_project_tree: ElementTree extracted from the Ableton project XML
    :param gp_markers_dict: a list of dictionaries whose first key is "bar", representing the bar where the marker belongs,
    and the second is "marker", where the marker name is
    :return: nothing, but ableton_project_tree is modified
    """
    if not gp_markers_dict:
        raise Exception("There is no Guitar Pro market to import!")
    else:
        live_set = ableton_project_tree.find("LiveSet")
        if live_set.find("Locators"):
            # Removing "Locators" element in case it exists and create a new one from scratch
            live_set.remove(live_set.find("Locators"))
        # Add the "Locators" element right after "ViewStateSessionMixerHeight"
        position_for_locators_element_1 = [
            position for position in range(len(live_set)) if live_set[position].tag == "ViewStateSessionMixerHeight"
        ][0] + 1
        live_set.insert(position_for_locators_element_1, ET.Element("Locators"))
        locators_element_2 = ET.SubElement(live_set.find("Locators"), "Locators")
        # Add each locator to the XML
        locator_id = 0
        for marker in gp_markers_dict:
            locator_id += 1
            locator = ET.SubElement(locators_element_2, "Locator", Id=f"{locator_id}")
            ET.SubElement(locator, "LomId", Value="0")
            ET.SubElement(locator, "Time", Value="{}".format((int(marker["bar"]) - 1) * 4))
            ET.SubElement(locator, "Name", Value="{}".format(marker["marker"]))
            ET.SubElement(locator, "Annotation", Value="")
            ET.SubElement(locator, "IsSongStart", Value="false")


def replace_ableton_project(als_file: str, ableton_project_tree: ET.ElementTree) -> typing.NoReturn:
    """
    Replace a Ableton project ".als" for a new one with the selected markers added to it
    :param als_file: relative or absolute path to Ableton project ".als" file
    :param ableton_project_tree: XML ElementTree of the Ableton project
    :return:
    """
    als_project = add_als_extension_if_it_is_not_set(als_file)
    als_xml = als_project.replace(".als", "")
    # Move the old Ableton project to a new file
    shutil.move(als_project, f"{als_xml}_old.als")
    print(f"'{als_project}' is now in '{als_xml}_old.als'")
    # Write the new Ableton tree to a XML file
    ET.indent(ableton_project_tree)
    with open(als_xml, "wb+") as new_file:
        ableton_project_tree.write(new_file, encoding="UTF-8", xml_declaration=True)
    # Compress the file
    with open(als_xml, "rb") as f_in:
        with open(als_project, "wb") as f_out1:
            with gzip.GzipFile(als_xml, "wb", fileobj=f_out1) as f_out2:
                shutil.copyfileobj(f_in, f_out2)
    print(f"New Ableton project created in '{als_project}'")
    os.remove(als_xml)


if __name__ == "__main__":
    ableton_xml = extract_xml_from_ableton_project(args["als_file"])
    add_markers_to_ableton_project(ableton_xml, extract_marker_from_gp_xml(args["gp_xml_file"]))
    replace_ableton_project(args["als_file"], ableton_xml)
