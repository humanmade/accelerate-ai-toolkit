from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
SPEC = importlib.util.spec_from_file_location("check_contract", SCRIPTS / "check-contract.py")
assert SPEC and SPEC.loader
check_contract = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(check_contract)


ABILITY = """<?php
wp_register_ability( 'accelerate/example', [
  'input_schema' => [
    'properties' => [
      'rules' => [
        'items' => [
          'required' => [ 'value' ],
        ],
      ],
      'post_id' => [ 'type' => 'integer' ],
      'limit' => [ 'type' => 'integer' ],
    ],
    'required' => [ 'post_id' ],
  ],
  'output_schema' => [
    'properties' => [
      'items' => [
        'type' => 'array',
        'items' => [
          'properties' => [
            'revision' => [ 'type' => 'string' ],
          ],
        ],
      ],
    ],
  ],
  'permission_callback' => 'Altis\\Accelerate\\Abilities\\can_view_analytics',
] );
"""


class ContractCheckerTests(unittest.TestCase):
    def test_extracts_required_inputs_and_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            producer = Path(temporary_directory)
            abilities = producer / "inc" / "abilities"
            abilities.mkdir(parents=True)
            (abilities / "example.php").write_text(ABILITY, encoding="utf-8")
            extracted = check_contract.extract_producer(producer)

        self.assertEqual(extracted["abilities"]["accelerate/example"]["required_inputs"], ["post_id"])
        self.assertEqual(extracted["abilities"]["accelerate/example"]["input_fields"], ["rules", "post_id", "limit"])
        self.assertEqual(extracted["abilities"]["accelerate/example"]["output_fields"], ["items", "items[].revision"])

    def test_reports_required_input_change(self) -> None:
        expected = {"abilities": {"accelerate/example": {"required_inputs": ["post_id"], "input_fields": ["post_id"], "output_fields": ["items"], "permission_callback": "view"}}}
        actual = {"abilities": {"accelerate/example": {"required_inputs": ["id"], "input_fields": ["id"], "output_fields": ["items"], "permission_callback": "view"}}}
        messages = check_contract.differences(expected, actual)

        self.assertTrue(any("required_inputs changed" in message for message in messages))


if __name__ == "__main__":
    unittest.main()
