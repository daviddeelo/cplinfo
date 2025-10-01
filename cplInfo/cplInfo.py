import xml.etree.ElementTree as et
import re
import logging
import json
import typing
from fractions import Fraction
import hashlib
import datetime
import io

from .labels import lookup_name

LOGGER = logging.getLogger(__name__)


def split_qname(qname: str):
    m = re.match(r'\{(.*)\}(.*)', qname)
    return (m.group(1) if m else None, m.group(2) if m else None)


def cpl_rational_to_fraction(r: str) -> Fraction:
    return Fraction(*map(int, r.split()))


REGXML_NS = {
    "r0": "http://www.smpte-ra.org/reg/395/2014/13/1/aaf",
    "r1": "http://www.smpte-ra.org/reg/335/2012",
    "r2": "http://www.smpte-ra.org/reg/2003/2012"
}

COMPATIBLE_CPL_NS = set((
    "http://www.smpte-ra.org/schemas/2067-3/2016",
    "http://www.smpte-ra.org/schemas/2067-3/2013"
))

COMPATIBLE_CORE_NS = set((
    "http://www.smpte-ra.org/schemas/2067-2/2013",
    "http://www.smpte-ra.org/schemas/2067-2/2016",
    "http://www.smpte-ra.org/ns/2067-2/2020"
))


class MainImageVirtualTrack:
    """Image information"""

    sample_rate: Fraction
    stored_width: int
    stored_height: int
    fingerprint: str

    def __init__(self, descriptor_element: et.Element, fingerprint: str, track_id: str, duration: Fraction,
                 resource_count: int) -> None:
        self.sample_rate = Fraction(descriptor_element.findtext(".//r1:SampleRate", namespaces=REGXML_NS))
        self.stored_width = int(descriptor_element.findtext(".//r1:StoredWidth", namespaces=REGXML_NS))
        self.stored_height = int(descriptor_element.findtext(".//r1:StoredHeight", namespaces=REGXML_NS))
        self.picture_compression = str(descriptor_element.findtext(".//r1:PictureCompression", namespaces=REGXML_NS))
        self.container_format = str(descriptor_element.findtext(".//r1:ContainerFormat", namespaces=REGXML_NS))
        self.transfer_characteristic = str(
            descriptor_element.findtext(".//r1:TransferCharacteristic", namespaces=REGXML_NS))
        self.coding_equations = str(descriptor_element.findtext(".//r1:CodingEquations", namespaces=REGXML_NS))
        self.color_primaries = str(descriptor_element.findtext(".//r1:ColorPrimaries", namespaces=REGXML_NS))
        self.fingerprint = fingerprint
        self.track_id = track_id
        self.duration = duration
        self.resource_count = resource_count

    def to_dict(self) -> dict:
        return {
            "kind": "main_image",
            "fingerprint": self.fingerprint,
            "virtual_track_id": self.track_id,
            "resource_count": self.resource_count,
            "duration": str(datetime.timedelta(milliseconds=int(self.duration * 1000)))[:-3],
            "essence_info": {
                "sample_rate": str(self.sample_rate),
                "stored_width": self.stored_width,
                "stored_height": self.stored_height,
                "picture_compression": lookup_name(self.picture_compression),
                "container_format": lookup_name(self.container_format),
                "transfer_characteristic": lookup_name(self.transfer_characteristic),
                "coding_equations": lookup_name(self.coding_equations),
                "color_encoding": lookup_name(self.color_primaries)
            }
        }


class MainAudioVirtualTrack:
    """Sound information"""

    @property
    def kind(self) -> str:
        return "main_audio"

    sample_rate: Fraction
    channels: typing.List[str]
    soundfield: str
    fingerprint: str

    def __init__(self, descriptor_element: et.Element, fingerprint: str, track_id: str, duration: Fraction,
                 resource_count: int) -> None:
        self.sample_rate = Fraction(descriptor_element.findtext(".//r1:SampleRate", namespaces=REGXML_NS))
        self.spoken_language = descriptor_element.findtext(".//r1:RFC5646SpokenLanguage", namespaces=REGXML_NS)
        self.fingerprint = fingerprint
        self.track_id = track_id
        self.duration = duration
        self.resource_count = resource_count
        self.channels = [x.text for x in
                         descriptor_element.findall(".//r0:AudioChannelLabelSubDescriptor/r1:MCATagSymbol",
                                                    namespaces=REGXML_NS)]
        self.soundfield = descriptor_element.findtext(".//r0:SoundfieldGroupLabelSubDescriptor/r1:MCATagSymbol",
                                                      namespaces=REGXML_NS)
        self.container_format = str(descriptor_element.findtext(".//r1:ContainerFormat", namespaces=REGXML_NS))
        self.channel_assignment = str(descriptor_element.findtext(".//r1:ChannelAssignment", namespaces=REGXML_NS))

    def to_dict(self) -> dict:
        return {
            "kind": "main_audio",
            "fingerprint": self.fingerprint,
            "virtual_track_id": self.track_id,
            "resource_count": self.resource_count,
            "duration": str(datetime.timedelta(milliseconds=int(self.duration * 1000)))[:-3],
            "essence_info": {
                "sample_rate": str(self.sample_rate),
                "spoken_language": str(self.spoken_language),
                "soundfield": self.soundfield,
                "container_format": lookup_name(self.container_format),
                "channel_assignment": lookup_name(self.channel_assignment),
                "channels": self.channels
            }
        }


class SubtitlesVirtualTrack:
    """Subtitle information"""

    @property
    def kind(self) -> str:
        return "main_subtitle"

    sample_rate: Fraction
    channels: typing.List[str]
    soundfield: str
    fingerprint: str

    def __init__(self, descriptor_element: et.Element, fingerprint: str, track_id: str, duration: Fraction,
                 resource_count: int) -> None:
        self.sample_rate = Fraction(descriptor_element.findtext(".//r1:SampleRate", namespaces=REGXML_NS))
        self.subtitle_language = descriptor_element.findtext(".//r2:RFC5646LanguageTagList", namespaces=REGXML_NS)
        self.fingerprint = fingerprint
        self.track_id = track_id
        self.duration = duration
        self.resource_count = resource_count
        self.container_format = str(descriptor_element.findtext(".//r1:ContainerFormat", namespaces=REGXML_NS))

    def to_dict(self) -> dict:
        return {
            "kind": "main_subtitle",
            "fingerprint": self.fingerprint,
            "virtual_track_id": self.track_id,
            "resource_count": self.resource_count,
            "duration": str(datetime.timedelta(milliseconds=int(self.duration * 1000)))[:-3],
            "essence_info": {
                "sample_rate": str(self.sample_rate),
                "subtitle_language": str(self.subtitle_language),
                "container_format": lookup_name(self.container_format)
            }
        }


class CPLInfo:
    """CPL information"""
    namespace: str
    content_title: str
    edit_rate: Fraction
    virtual_tracks: typing.List[typing.Any]

    def __init__(self, cpl_element: et.Element) -> None:
        self.namespace, local_name = split_qname(cpl_element.tag)

        if self.namespace not in COMPATIBLE_CPL_NS:
            LOGGER.error("Unknown CompositionPlaylist namespace: %s", self.namespace)

        if local_name != "CompositionPlaylist":
            LOGGER.error("Unknown CompositionPlaylist element name: %s", local_name)

        ns_dict = {"cpl": self.namespace}

        self.content_title = cpl_element.findtext(".//cpl:ContentTitle", namespaces=ns_dict)

        self.edit_rate = cpl_rational_to_fraction(cpl_element.findtext(".//cpl:EditRate", namespaces=ns_dict))

        self.virtual_tracks = []

        sequence_list = cpl_element.find("./cpl:SegmentList/cpl:Segment/cpl:SequenceList", namespaces=ns_dict)

        for sequence in sequence_list:
            track_id = sequence.findtext("cpl:TrackId", namespaces=ns_dict)

            if track_id is None:
                LOGGER.error("Sequence is missing TrackId")
                continue

            sequence_ns, sequence_name = split_qname(sequence.tag)

            if sequence_ns not in COMPATIBLE_CORE_NS:
                LOGGER.warning("Unknown virtual track namespace %s", sequence_ns)
                continue

            if sequence_name == "MainImageSequence":
                vt_class = MainImageVirtualTrack
            elif sequence_name == "MainAudioSequence":
                vt_class = MainAudioVirtualTrack
            elif sequence_name == "SubtitlesSequence":
                vt_class = SubtitlesVirtualTrack
            else:
                LOGGER.warning("Unknown Sequence kind: %s", sequence_name)
                continue

            source_encoding = sequence.findtext(".//cpl:SourceEncoding", namespaces=ns_dict)

            if source_encoding is None:
                LOGGER.error("Cannot find source encoding descriptor")
                continue

            essence_descriptor = cpl_element.find(f".//cpl:EssenceDescriptor[cpl:Id='{source_encoding}']",
                                                  namespaces=ns_dict)

            if essence_descriptor is None:
                LOGGER.error("Cannot find essence descriptor")
                continue

            resources = cpl_element.findall(
                f"./cpl:SegmentList/cpl:Segment/cpl:SequenceList/*[cpl:TrackId='{track_id}']/cpl:ResourceList/cpl:Resource",
                namespaces=ns_dict)

            fingerprint = hashlib.sha1()

            total_duration = 0

            for resource in resources:
                edit_rate = cpl_rational_to_fraction(
                    resource.findtext(".//cpl:EditRate", namespaces=ns_dict)) or self.edit_rate

                entry_point = edit_rate * int(resource.findtext(".//cpl:EntryPoint", namespaces=ns_dict) or 0)

                resource_duration = int(
                    resource.findtext(".//cpl:SourceDuration", namespaces=ns_dict) or resource.findtext(
                        ".//cpl:IntrinsicDuration", namespaces=ns_dict)) / edit_rate

                if resource_duration == 0:
                    continue
                total_duration += resource_duration

                repeat_count = int(resource.findtext(".//cpl:RepeatCount", namespaces=ns_dict) or 1)

                trackfile_id = resource.findtext(".//cpl:TrackFileId", namespaces=ns_dict)

                fingerprint.update(bytes(str(entry_point), 'ascii'))
                fingerprint.update(bytes(str(resource_duration), 'ascii'))
                fingerprint.update(bytes(str(repeat_count), 'ascii'))
                fingerprint.update(bytes(str(trackfile_id), 'ascii'))

            self.virtual_tracks.append(
                vt_class(essence_descriptor, fingerprint.hexdigest(), track_id, total_duration, len(resources)))

    def to_dict(self) -> dict:
        return {
            "namespace": self.namespace,
            "content_title": self.content_title,
            "virtual_tracks": [vt.to_dict() for vt in self.virtual_tracks]
        }


# New module functions

def parse_cpl_file(file_path: str) -> CPLInfo:
    """
    Parse a CPL file from a file path and return CPLInfo object

    Args:
        file_path: Path to the CPL file

    Returns:
        CPLInfo object containing the parsed CPL information
    """
    with open(file_path, 'r', encoding="UTF-8") as cpl_file:
        cpl_doc = et.parse(cpl_file)
        return CPLInfo(cpl_doc.getroot())


def parse_cpl_string(cpl_content: str) -> CPLInfo:
    """
    Parse a CPL from a string and return CPLInfo object

    Args:
        cpl_content: String containing CPL XML content

    Returns:
        CPLInfo object containing the parsed CPL information
    """
    cpl_doc = et.parse(io.StringIO(cpl_content))
    return CPLInfo(cpl_doc.getroot())


def parse_cpl_element(cpl_element: et.Element) -> CPLInfo:
    """
    Parse a CPL from an ElementTree Element and return CPLInfo object

    Args:
        cpl_element: ElementTree Element containing the CPL root

    Returns:
        CPLInfo object containing the parsed CPL information
    """
    return CPLInfo(cpl_element)


def get_cpl_info_json(cpl_info: CPLInfo, indent: str = "  ") -> str:
    """
    Convert CPLInfo object to a JSON string

    Args:
        cpl_info: CPLInfo object
        indent: Indentation to use for JSON formatting (default: two spaces)

    Returns:
        JSON string representation of the CPL information
    """
    return json.dumps(cpl_info.to_dict(), indent=indent)


def extract_virtual_tracks(cpl_info: CPLInfo) -> typing.List[typing.Dict]:
    """
    Extract virtual tracks information from a CPLInfo object

    Args:
        cpl_info: CPLInfo object

    Returns:
        List of dictionaries containing virtual track information
    """
    return [vt.to_dict() for vt in cpl_info.virtual_tracks]


def get_main_image_tracks(cpl_info: CPLInfo) -> typing.List[MainImageVirtualTrack]:
    """
    Extract only the main image tracks from a CPLInfo object

    Args:
        cpl_info: CPLInfo object

    Returns:
        List of MainImageVirtualTrack objects
    """
    return [vt for vt in cpl_info.virtual_tracks if isinstance(vt, MainImageVirtualTrack)]


def get_main_audio_tracks(cpl_info: CPLInfo) -> typing.List[MainAudioVirtualTrack]:
    """
    Extract only the main audio tracks from a CPLInfo object

    Args:
        cpl_info: CPLInfo object

    Returns:
        List of MainAudioVirtualTrack objects
    """
    return [vt for vt in cpl_info.virtual_tracks if isinstance(vt, MainAudioVirtualTrack)]


def get_subtitle_tracks(cpl_info: CPLInfo) -> typing.List[SubtitlesVirtualTrack]:
    """
    Extract only the subtitle tracks from a CPLInfo object

    Args:
        cpl_info: CPLInfo object

    Returns:
        List of SubtitlesVirtualTrack objects
    """
    return [vt for vt in cpl_info.virtual_tracks if isinstance(vt, SubtitlesVirtualTrack)]


def process_cpl_file_to_json(file_path: str, output_file: str = None, indent: str = "  ") -> str:
    """
    Process a CPL file and convert it to JSON

    Args:
        file_path: Path to the CPL file
        output_file: Optional path to write the JSON output (if None, returns the JSON string)
        indent: Indentation to use for JSON formatting (default: two spaces)

    Returns:
        JSON string representation of the CPL information (if output_file is None)
    """
    cpl_info = parse_cpl_file(file_path)
    json_output = get_cpl_info_json(cpl_info, indent)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_output)
    else:
        return json_output


def get_cpl_summary(cpl_info: CPLInfo) -> dict:
    """
    Generate a summary of the CPL information

    Args:
        cpl_info: CPLInfo object

    Returns:
        Dictionary containing summary information about the CPL
    """
    image_tracks = get_main_image_tracks(cpl_info)
    audio_tracks = get_main_audio_tracks(cpl_info)
    subtitle_tracks = get_subtitle_tracks(cpl_info)

    # Find the longest duration among all tracks
    all_durations = [vt.duration for vt in cpl_info.virtual_tracks]
    max_duration = max(all_durations) if all_durations else 0

    return {
        "content_title": cpl_info.content_title,
        "namespace": cpl_info.namespace,
        "edit_rate": str(cpl_info.edit_rate),
        "duration": str(datetime.timedelta(milliseconds=int(max_duration * 1000)))[:-3],
        "track_count": {
            "image": len(image_tracks),
            "audio": len(audio_tracks),
            "subtitle": len(subtitle_tracks),
            "total": len(cpl_info.virtual_tracks)
        }
    }
