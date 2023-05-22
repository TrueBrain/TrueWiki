#!/usr/bin/env python

"""
The first argument contains the question we should ask the user.
If it starts with "Username", we return "github".
If it starts with "Password", we return, with help of theGitHub App, an access token.
"""

import base64
import github3
import os
import sys


def main():
    if len(sys.argv) != 2:
        print("Meant to be called via GIT_ASKPASS. Not directly.")
        sys.exit(1)

    question = sys.argv[1]
    type = question.split(" ")[0]

    if type == "Username":
        # The username can be anything.
        print("github")
        return
    elif type != "Password":
        # We only support Username / Password.
        sys.exit(1)

    # Login to the GitHub App and fetch an access token.

    github_app_id = os.getenv("TRUEWIKI_GITHUB_ASKPASS_APP_ID")
    github_app_key = os.getenv("TRUEWIKI_GITHUB_ASKPASS_APP_KEY")
    github_url = os.getenv("TRUEWIKI_GITHUB_ASKPASS_URL")

    user, repo = github_url.split("/")[3:5]
    # Make sure the GitHub URL didn't end with ".git".
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Login as the GitHub App.
    gh = github3.GitHub()
    gh.session.base_url = os.getenv("TRUEWIKI_GITHUB_ASKPASS_API_URL")
    gh.login_as_app(base64.b64decode(github_app_key), github_app_id)

    # Find the installation ID and login on behalf of that installation.
    installation = gh.app_installation_for_repository(user, repo)
    gh.login_as_app_installation(base64.b64decode(github_app_key), github_app_id, installation.id)

    print(gh.session.auth.token)


if __name__ == "__main__":
    main()
