# Class for hitting the GitHub releases API
import os
import json
import logging
from contextlib import closing

import requests
from requests.auth import HTTPBasicAuth

from ksp_deploy.config import ENABLE_SSL


class GitHubReleasesAPI(object):

    base_url = "https://api.github.com"
    login_url = "api/login"
    create_release_url = "repos/{owner}/{repo}/releases"
    latest_release_url = "repos/{owner}/{repo}/releases/latest"
    list_release_assets_url = "repos/{owner}/{repo}/releases/{release_id}/assets"
    release_base_url = "https://uploads.github.com/repos/{owner}/{repo}/releases/{release_id}/assets"

    def __init__(self, username, token, repo_slug, session=None):
        """
        Initializes the API session

        Inputs:
            username (str): Github user name
            token (str): Oauth token
            repo_slug (str): Github repo slug of the form org/repo
        """
        self.credentials = {"username":username, "token":token}
        self.logger = logging.getLogger('deploy.github')
        self.owner, self.repo = repo_slug.split('/')

        if isinstance(session, requests.Session):
            self.session = session
        else:
            self.session =requests.Session()

    def get_latest_release(self):
        """
        Gets the latest release for the repo

        Returns:
            reponse (dict): json describing the latest release
        """
        url = f'{self.base_url}/{self.latest_release_url}'.format(
            owner=self.owner, repo=self.repo)
        self.logger.info(f"GET {url}")
        try:
            resp = self.session.get(url, verify=ENABLE_SSL)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"HTTP ERROR: {err}")
            self.logger.error(f"{resp.url} returned {resp.text}")
            return resp.text

    def get_release_assets(self, id):
        """
        Lists a release assets

        Inputs:
            id (int): the github release's ID
            changelog (str): a Markdown-formatted changelog
        Returns:
            reponse (list): list of assets in a release
        """
        url = f'{self.base_url}/{self.list_release_assets_url}'.format(
            owner=self.owner, repo=self.repo, release_id=id)
        self.logger.info(f"GET {url}")
        try:
            resp = self.session.get(
                url,
                verify=ENABLE_SSL)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"HTTP ERROR: {err}")
            self.logger.error(f"{resp.url} returned {resp.text}")
            return resp.text

    def create_release(self, version, changelog):
        """
        Creates a github release

        Inputs:
            version (str): the string mod version to use
            changelog (str): a Markdown-formatted changelog
        Return:
            response (dict): json response from server
        """
        url = f'{self.base_url}/{self.create_release_url}'.format(
            owner=self.owner, repo=self.repo)
        payload = {
            "tag_name": version,
            "body": changelog,
            "name": f"{repo} {version}",
            "target_commitish": "master",
            "draft": False,
            "prerelease": False
        }
        self.logger.info(f"Posting {payload} to {url}")
        try:
            resp = self.session.post(
                url,
                data=json.dumps(payload),
                verify=ENABLE_SSL,
                auth=HTTPBasicAuth(
                    self.credentials["username"],
                    self.credentials["token"])
                )

            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"HTTP ERROR: {err}")
            self.logger.error(f"{resp.url} returned {resp.text}")
            return resp.text

    def upload_release_file(self, release_id, zip):
        """
        Upload a file to a release

        Inputs:
            release_id (int): the github release ID
            zip (str): path to the zip to upload
        """
        slug = os.environ["TRAVIS_REPO_SLUG"]
        owner, repo = slug.split('/')
        file_name = os.path.basename(zip)

        release_url = self.release_base_url.format(
            owner=owner, repo=repo, release_id=release_id) + f"?name={file_name}"
        self.logger.info(f"> Posting {zip} to {release_url}")
        headers={
            'Content-Type': 'application/zip'
        }
        try:
            resp = self.session.post(release_url,
                verify=ENABLE_SSL,
                headers=headers,
                files={'zip': open(zip, 'rb')},
                auth=HTTPBasicAuth(
                    self.credentials["username"],
                    self.credentials["token"])
                )
            resp.raise_for_status()
            self.logger.info(f"{resp.url} returned {resp.text}")
            return resp.json()
        except requests.exceptions.HTTPError as err:
            self.logger.error(f"HTTP ERROR: {err}")
            self.logger.error(f"{resp.url} returned {resp.text}")
            return resp.text

    def login(self):
        pass

    def logout(self):
        pass

    def close(self):
        self.session.close()

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, *args):
        self.logout()
        self.close()