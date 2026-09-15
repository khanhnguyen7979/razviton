"""Read-only release checks; fixtures never reach real accounts."""
import asyncio
import json
import os
import secrets
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ['RAZVITON_DATA_DIR'] = tempfile.mkdtemp(prefix='razviton-release-test-')
from app import main
from app.routes.auth import register, auth_config
from app.schemas.auth import RegisterRequest
from fastapi import HTTPException
from sqlalchemy.exc import OperationalError

ROOT = Path(__file__).resolve().parents[1]

class ReleaseTests(unittest.TestCase):
    def test_render_defaults_closed(self):
        with patch.dict(os.environ, {'RENDER':'true'}, clear=True):
            self.assertFalse(auth_config()['registration_enabled'])

    def test_paused_register_before_database(self):
        payload=RegisterRequest(username='fixture',email='fixture@example.invalid',password=secrets.token_urlsafe(24))
        with patch.dict(os.environ, {'RAZVITON_REGISTRATION_ENABLED':'0'}):
            with self.assertRaises(HTTPException) as err:
                register(payload,None,None,None)
            self.assertEqual(err.exception.status_code,503)
            self.assertEqual(err.exception.detail,'REGISTRATION_PAUSED')

    def test_local_explicit_enabled(self):
        with patch.dict(os.environ, {'RAZVITON_REGISTRATION_ENABLED':'1'}):
            self.assertTrue(auth_config()['registration_enabled'])

    def test_db_failure_safe(self):
        exc=OperationalError('private test query',{},Exception('private sentinel'))
        with patch.object(main.engine,'connect',side_effect=exc):
            self.assertEqual(main.health().status_code,503)
        response=asyncio.run(main.database_error(None,exc))
        self.assertNotIn(b'private sentinel',response.body)

    def test_public_claims_withheld(self):
        home=(ROOT/'public/index.html').read_text(encoding='utf-8-sig')
        proof=(ROOT/'public/proof.html').read_text(encoding='utf-8-sig')
        self.assertNotIn('<b>ONLINE</b>',home)
        for count in ['16,186','890','144','35/35']:
            self.assertNotIn(count,proof)
        self.assertIn('UNVERIFIED',proof)
        metadata=json.loads((ROOT/'public/token/metadata.json').read_text())
        self.assertEqual(metadata['verification_status'],'UNVERIFIED')

    def test_metadata_and_mirrors(self):
        for page in (ROOT/'public').glob('*.html'):
            text=page.read_text(encoding='utf-8-sig')
            self.assertEqual(text.count('name="description"'),1,page.name)
            self.assertEqual(text.count('rel="canonical"'),1,page.name)
            self.assertIn('property="og:title"',text,page.name)
            self.assertIn('rel="icon"',text,page.name)
            self.assertEqual(page.read_bytes(),(ROOT/page.name).read_bytes(),page.name)

if __name__=='__main__':
    unittest.main()
