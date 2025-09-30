#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
Test file for cplinfo module demonstrating usage and providing example tests.
This script uses an existing CPL.xml file in the same directory.
"""

import unittest
import json
from pathlib import Path

# Import the cplinfo module
import cplInfo


class CPLInfoUsageExamples:
    """
    Examples of how to use the cplinfo module
    """

    @staticmethod
    def example_parse_from_file():
        """Example: Parse CPL from a file"""
        # Parse the CPL file
        cpl_info = cplInfo.parse_cpl_file("CPL.xml")

        # Print basic information
        print(f"Content Title: {cpl_info.content_title}")
        print(f"Edit Rate: {cpl_info.edit_rate}")
        print(f"Number of Virtual Tracks: {len(cpl_info.virtual_tracks)}")

        return cpl_info

    @staticmethod
    def example_get_json():
        """Example: Get JSON representation of CPL"""
        # Parse the CPL file
        cpl_info = cplInfo.parse_cpl_file("CPL.xml")

        # Get JSON representation
        json_output = cplInfo.get_cpl_info_json(cpl_info, indent="    ")
        print("CPL as JSON (first 500 characters):")
        print(json_output[:500] + "...")

        # Save JSON to file
        with open("cpl_info.json", "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Full JSON saved to cpl_info.json")

        return cpl_info

    @staticmethod
    def example_extract_tracks():
        """Example: Extract specific track types"""
        # Parse the CPL
        cpl_info = cplInfo.parse_cpl_file("CPL.xml")

        # Get image tracks
        image_tracks = cplInfo.get_main_image_tracks(cpl_info)
        print(f"Found {len(image_tracks)} image track(s)")
        for i, track in enumerate(image_tracks):
            print(f"  Image Track {i + 1}:")
            print(f"    - Resolution: {track.stored_width}x{track.stored_height}")
            print(f"    - Sample Rate: {track.sample_rate}")

        # Get audio tracks
        audio_tracks = cplInfo.get_main_audio_tracks(cpl_info)
        print(f"Found {len(audio_tracks)} audio track(s)")
        for i, track in enumerate(audio_tracks):
            print(f"  Audio Track {i + 1}:")
            print(f"    - Sample Rate: {track.sample_rate}")
            if hasattr(track, 'spoken_language') and track.spoken_language:
                print(f"    - Language: {track.spoken_language}")
            if hasattr(track, 'channels') and track.channels:
                print(f"    - Channels: {', '.join(track.channels)}")

        # Get subtitle tracks
        subtitle_tracks = cplInfo.get_subtitle_tracks(cpl_info)
        print(f"Found {len(subtitle_tracks)} subtitle track(s)")
        for i, track in enumerate(subtitle_tracks):
            print(f"  Subtitle Track {i + 1}:")
            if hasattr(track, 'subtitle_language') and track.subtitle_language:
                print(f"    - Language: {track.subtitle_language}")

        return cpl_info

    @staticmethod
    def example_get_summary():
        """Example: Get a summary of the CPL"""
        # Parse the CPL
        cpl_info = cplInfo.parse_cpl_file("CPL.xml")

        # Get summary
        summary = cplInfo.get_cpl_summary(cpl_info)
        print("CPL Summary:")
        print(json.dumps(summary, indent=2))

        return cpl_info

    @staticmethod
    def example_process_to_json():
        """Example: Process CPL file directly to JSON"""
        # Process the CPL file to JSON and save to output file
        cplInfo.process_cpl_file_to_json("CPL.xml", "cpl_output.json", indent="  ")
        print(f"Processed CPL.xml and saved JSON to cpl_output.json")

        # Process the CPL file to JSON and return as string
        json_str = cplInfo.process_cpl_file_to_json("CPL.xml")
        print(f"Processed CPL.xml to JSON string (first 500 characters):")
        print(json_str[:500] + "...")

    @staticmethod
    def run_all_examples():
        """Run all examples"""
        if not Path("CPL.xml").exists():
            print("Error: CPL.xml file not found in the current directory.")
            print("Please ensure the CPL.xml file is in the same directory as this script.")
            return

        print("\n=== Example: Parse from file ===")
        CPLInfoUsageExamples.example_parse_from_file()

        print("\n=== Example: Get JSON representation ===")
        CPLInfoUsageExamples.example_get_json()

        print("\n=== Example: Extract tracks ===")
        CPLInfoUsageExamples.example_extract_tracks()

        print("\n=== Example: Get summary ===")
        CPLInfoUsageExamples.example_get_summary()

        print("\n=== Example: Process to JSON ===")
        CPLInfoUsageExamples.example_process_to_json()


class TestCPLInfo(unittest.TestCase):
    """
    Unit tests for the cplinfo module using the existing CPL.xml file
    """

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures that are used for all tests"""
        if not Path("CPL.xml").exists():
            raise FileNotFoundError("CPL.xml file not found in the current directory")

        cls.cpl_info = cplInfo.parse_cpl_file("CPL.xml")

    def test_cpl_has_content_title(self):
        """Test that content title is present"""
        self.assertIsNotNone(self.cpl_info.content_title)
        self.assertTrue(len(self.cpl_info.content_title) > 0)
        print(f"Content Title: {self.cpl_info.content_title}")

    def test_cpl_has_edit_rate(self):
        """Test that edit rate is present and valid"""
        self.assertIsNotNone(self.cpl_info.edit_rate)
        self.assertIsInstance(self.cpl_info.edit_rate, cplInfo.Fraction)
        print(f"Edit Rate: {self.cpl_info.edit_rate}")

    def test_cpl_has_virtual_tracks(self):
        """Test that virtual tracks are present"""
        self.assertTrue(len(self.cpl_info.virtual_tracks) > 0)
        print(f"Number of Virtual Tracks: {len(self.cpl_info.virtual_tracks)}")

    def test_track_extraction(self):
        """Test that tracks can be extracted by type"""
        image_tracks = cplInfo.get_main_image_tracks(self.cpl_info)
        audio_tracks = cplInfo.get_main_audio_tracks(self.cpl_info)
        subtitle_tracks = cplInfo.get_subtitle_tracks(self.cpl_info)

        print(f"Image Tracks: {len(image_tracks)}")
        print(f"Audio Tracks: {len(audio_tracks)}")
        print(f"Subtitle Tracks: {len(subtitle_tracks)}")

        # The total should match the number of virtual tracks
        self.assertEqual(
            len(image_tracks) + len(audio_tracks) + len(subtitle_tracks),
            len(self.cpl_info.virtual_tracks)
        )

    def test_to_dict_conversion(self):
        """Test conversion to dictionary"""
        cpl_dict = self.cpl_info.to_dict()

        # Check that the dictionary has the expected keys
        self.assertIn("namespace", cpl_dict)
        self.assertIn("content_title", cpl_dict)
        self.assertIn("virtual_tracks", cpl_dict)

        # Check that virtual_tracks is a list
        self.assertIsInstance(cpl_dict["virtual_tracks"], list)

        # Check that each virtual track has the expected format
        if cpl_dict["virtual_tracks"]:
            track = cpl_dict["virtual_tracks"][0]
            self.assertIn("kind", track)
            self.assertIn("fingerprint", track)
            self.assertIn("virtual_track_id", track)
            self.assertIn("essence_info", track)

    def test_json_serialization(self):
        """Test JSON serialization"""
        json_str = cplInfo.get_cpl_info_json(self.cpl_info)

        # Check that the result is a valid JSON string
        try:
            json_obj = json.loads(json_str)
            self.assertIsInstance(json_obj, dict)
        except json.JSONDecodeError:
            self.fail("get_cpl_info_json did not produce valid JSON")

    def test_summary_generation(self):
        """Test summary generation"""
        summary = cplInfo.get_cpl_summary(self.cpl_info)

        # Check that the summary has the expected keys
        self.assertIn("content_title", summary)
        self.assertIn("namespace", summary)
        self.assertIn("edit_rate", summary)
        self.assertIn("duration", summary)
        self.assertIn("track_count", summary)

        # Check that track_count has the expected structure
        self.assertIn("image", summary["track_count"])
        self.assertIn("audio", summary["track_count"])
        self.assertIn("subtitle", summary["track_count"])
        self.assertIn("total", summary["track_count"])


if __name__ == "__main__":
    print("=== CPLInfo Module Usage Examples ===")
    CPLInfoUsageExamples.run_all_examples()

    print("\n=== Running Unit Tests ===")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)