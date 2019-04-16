# Class for accessing the CurseForge API
import requests
import logging
from contextlib import closing
import json

class CurseForgeAPI(object):

    base_url = "https://kerbal.curseforge.com"
    versions_url = "api/game/versions"
    upload_file_url = "api/projects/{mod_id}/upload-file"

    def __init__(self, token, session=None):
        """
        Initializes the API session

        Inputs:
            token (str): Curse authentication token
        """
        self.auth_token = token
        self.logger = logging.getLogger('deploy.curseforge')

        if isinstance(session, requests.Session):
            self.session = session
        else:
            self.session = requests.Session()

    def query_version(self):
        """
        Queries the API and returns a list of available game versions
        """
        url = f'{self.base_url}/{self.versions_url}'
        headers = {'X-Api-Token': self.auth_token}
        with closing(self.session.get(url, headers=headers)) as resp:
            try:
                return resp.json()
            except requests.exceptions.HTTPError as err:
                self.logger.error(err)
                self.logger.error(f"{resp.url} returned {resp.text}")
                return resp.text

    def get_curse_game_version_id(self, game_version):
        """
        Gets the curse version id by querying the API and comparing to the provided
        ID

        Inputs:
            game_version (str): the string game version to match
        Returns:
            curse_version (int): the integer curse version
        """
        versions = self.query_version()
        curse_version = None
        for version in versions:
            if version["name"] == game_version:
                curse_version = version["id"]
                self.logger.info(f"Found curse version {curse_version} from string version {game_version}")

        if curse_version is None:
            curse_version = versions[-1]["id"]
            print(f"Couldn't determine curse version from game version {game_version}, using latest version {curse_version}")

        return curse_version

    def update_mod(self, mod_id, changelog, game_version, releaseType, zip):
        """
        Updates a mod by hitting the project upload files API

        Inputs:
            mod_id (str): the curseforge project ID
            changelog (str): a Markdown-formatted changelog
            game_version (str): the string game version to use
            releaseType (str): One of alpha, beta, release
            zip (str): the path of the zip to upload
        """
        curse_version = int(self.get_curse_game_version_id(game_version))
        url = f'{self.base_url}/{self.upload_file_url}'.format(mod_id=mod_id)
        metadata = {
            "changelog": changelog,
            "changelogType": "markdown",
            "gameVersions": [curse_version],
            "releaseType": releaseType
        }
        self.logger.info(f"File metadata {metadata}, zip {zip}")
        headers = {'X-Api-Token': self.auth_token}
        self.logger.info(f"Posting {metadata} to {url}")
        try:
            resp = self.session.post(url,
                files={'file': open(zip, 'rb')},
                data={'metadata': json.dumps(metadata)},
                headers=headers)
            resp.raise_for_status()
            self.logger.info(f"{resp.url} returned {resp.text}")
            return resp.text
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"HTTP ERROR: {err}")
            self.logger.error(f"{resp.url} returned {resp.text}")
            return resp.text

    def login(self):
        """Unneeded"""
        pass

    def logout(self):
        """Unneeded"""
        pass

    def close(self):
        self.session.close()

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()
        self.close()
