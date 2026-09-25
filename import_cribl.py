#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from urllib.parse import quote

import requests
import urllib3

from cribl_config import load_servers, verify_ssl


# ==============================================================================
# CONFIGURATION
# ==============================================================================

SERVERS = load_servers()

VERIFY_SSL = verify_ssl()

BASE_CONFIG_DIR = Path(
    "cribl-config"
)

# IMPORTANT:
#
# True  = don't change Cribl
# False = actually make changes
#
DRY_RUN = True


# ==============================================================================
# HELPERS
# ==============================================================================

def load_json(filename):

    with filename.open(
        "r",
        encoding="utf-8",
    ) as handle:

        return json.load(
            handle
        )


def fail(message):

    print()
    print(
        f"ERROR: {message}",
        file=sys.stderr,
    )

    sys.exit(1)


def show_usage():

    print()
    print("Usage:")
    print()
    print(
        "  python3 import_cribl.py "
        "<target>"
    )
    print()
    print("Available targets:")

    for name in SERVERS:

        print(
            f"  {name}"
        )

    print()


# ==============================================================================
# CRIBL SERVER
# ==============================================================================

class CriblServer:

    def __init__(
        self,
        name,
        url,
        token,
    ):

        self.name = name

        self.url = url.rstrip("/")

        self.config_dir = (
            BASE_CONFIG_DIR
            / name
        )

        self.session = (
            requests.Session()
        )

        self.session.verify = (
            VERIFY_SSL
        )

        self.session.headers.update({
            "Authorization":
                f"Bearer {token}",

            "Accept":
                "application/json",

            "Content-Type":
                "application/json",
        })


    # ==========================================================================
    # API URL
    # ==========================================================================

    def api_url(
        self,
        endpoint,
    ):

        return (
            f"{self.url}"
            f"/api/v1"
            f"{endpoint}"
        )


    # ==========================================================================
    # REQUEST
    # ==========================================================================

    def request(
        self,
        method,
        url,
        **kwargs,
    ):

        print(
            f"       {method} {url}"
        )

        response = (
            self.session.request(
                method,
                url,
                timeout=60,
                **kwargs,
            )
        )


        if not response.ok:

            print()
            print("=" * 70)
            print("CRIBL API ERROR")
            print("=" * 70)

            print(
                f"Server      : "
                f"{self.name}"
            )

            print(
                f"HTTP status : "
                f"{response.status_code}"
            )

            print(
                f"Method      : "
                f"{method}"
            )

            print(
                f"URL         : "
                f"{url}"
            )

            print()
            print("Response:")

            print(
                response.text
            )

            print("=" * 70)
            print()

            response.raise_for_status()


        if response.text.strip():

            try:

                return (
                    response.json()
                )

            except ValueError:

                return (
                    response.text
                )

        return None


    # ==========================================================================
    # RESOURCE EXISTS
    # ==========================================================================

    def resource_exists(
        self,
        endpoint,
        resource_id,
    ):

        encoded_id = quote(
            resource_id,
            safe="",
        )


        url = self.api_url(
            f"{endpoint}/"
            f"{encoded_id}"
        )


        response = (
            self.session.get(
                url,
                timeout=30,
            )
        )


        if response.status_code == 404:

            return False


        if not response.ok:

            print()
            print(
                f"Unable to check "
                f"resource '{resource_id}'."
            )

            print(
                f"HTTP "
                f"{response.status_code}"
            )

            print(
                f"URL: {url}"
            )

            print(
                response.text
            )

            response.raise_for_status()


        try:

            data = (
                response.json()
            )

        except ValueError:

            return True


        if (
            isinstance(
                data,
                dict,
            )
            and isinstance(
                data.get("items"),
                list,
            )
        ):

            return (
                len(
                    data["items"]
                )
                > 0
            )


        return True


    # ==========================================================================
    # IMPORT COLLECTION
    # ==========================================================================

    def import_collection(
        self,
        title,
        directory,
        endpoint,
    ):

        path = (
            self.config_dir
            / directory
        )


        print()
        print("=" * 70)
        print(title)
        print("=" * 70)


        if not path.exists():

            print(
                f"Directory '{path}' "
                f"does not exist. "
                f"Skipping."
            )

            return


        files = sorted(
            path.glob(
                "*.json"
            )
        )


        if not files:

            print(
                "No JSON files found."
            )

            return


        for filename in files:

            data = load_json(
                filename
            )


            resource_id = (
                data.get("id")
            )


            if not resource_id:

                fail(
                    f"{filename} does not "
                    f"contain an 'id'."
                )


            exists = (
                self.resource_exists(
                    endpoint,
                    resource_id,
                )
            )


            if exists:

                action = "UPDATE"

                method = "PATCH"

                encoded_id = quote(
                    resource_id,
                    safe="",
                )

                url = self.api_url(
                    f"{endpoint}/"
                    f"{encoded_id}"
                )

            else:

                action = "CREATE"

                method = "POST"

                url = self.api_url(
                    endpoint
                )


            print()

            print(
                f"{action:6} "
                f"{resource_id}"
            )


            if DRY_RUN:

                print(
                    "       DRY RUN - "
                    "no changes made"
                )

                continue


            self.request(
                method,
                url,
                json=data,
            )


    # ==========================================================================
    # ROUTES
    # ==========================================================================

    def import_routes(self):

        filename = (
            self.config_dir
            / "routes"
            / "default.json"
        )


        print()
        print("=" * 70)
        print("Routes")
        print("=" * 70)


        if not filename.exists():

            print(
                f"{filename} does not "
                f"exist. Skipping."
            )

            return


        data = load_json(
            filename
        )


        print()
        print(
            "UPDATE default"
        )


        if DRY_RUN:

            print(
                "       DRY RUN - "
                "no changes made"
            )

            return


        self.request(
            "PATCH",

            self.api_url(
                "/routes/default"
            ),

            json=data,
        )


    # ==========================================================================
    # VALIDATE
    # ==========================================================================

    def validate(self):

        print()
        print("=" * 70)
        print(
            "Validating configuration"
        )
        print("=" * 70)


        if not self.config_dir.exists():

            fail(
                f"Configuration directory "
                f"does not exist: "
                f"{self.config_dir}"
            )


        json_files = list(
            self.config_dir.rglob(
                "*.json"
            )
        )


        if not json_files:

            fail(
                f"No JSON files found in "
                f"{self.config_dir}"
            )


        errors = 0


        for filename in sorted(
            json_files
        ):

            try:

                load_json(
                    filename
                )

                print(
                    f"OK  {filename}"
                )


            except json.JSONDecodeError as error:

                print(
                    f"ERROR {filename}: "
                    f"{error}"
                )

                errors += 1


        if errors:

            fail(
                f"{errors} invalid "
                f"JSON file(s)."
            )


        print()

        print(
            f"{len(json_files)} "
            f"JSON file(s) valid."
        )


    # ==========================================================================
    # IMPORT
    # ==========================================================================

    def import_config(self):

        print()
        print("=" * 70)

        print(
            f"Cribl configuration import: "
            f"{self.name}"
        )

        print("=" * 70)

        print(
            f"Target : {self.name}"
        )

        print(
            f"URL    : {self.url}"
        )

        print(
            f"Config : {self.config_dir}"
        )

        print(
            f"Dry run: {DRY_RUN}"
        )


        if DRY_RUN:

            print()
            print(
                "DRY RUN ENABLED - "
                "Cribl will NOT be changed."
            )

        else:

            print()
            print(
                "WARNING: changes WILL "
                "be written to Cribl."
            )


        self.validate()


        self.import_collection(
            "Sources",
            "sources",
            "/system/inputs",
        )


        self.import_collection(
            "Destinations",
            "destinations",
            "/system/outputs",
        )


        self.import_collection(
            "Pipelines",
            "pipelines",
            "/pipelines",
        )


        self.import_routes()


        print()
        print("=" * 70)

        if DRY_RUN:

            print(
                "DRY RUN completed."
            )

            print(
                "No changes were made "
                "to Cribl."
            )

        else:

            print(
                "Import completed."
            )

        print("=" * 70)


# ==============================================================================
# MAIN
# ==============================================================================

def main():

    if not VERIFY_SSL:

        urllib3.disable_warnings(
            urllib3.exceptions.InsecureRequestWarning
        )


    if len(sys.argv) != 2:

        show_usage()

        sys.exit(1)


    target = sys.argv[1]


    # Do not allow mass imports.
    if target == "all":

        fail(
            "'all' is not supported for imports. "
            "Specify one target."
        )


    if target not in SERVERS:

        print()

        print(
            f"ERROR: Unknown target "
            f"'{target}'."
        )

        show_usage()

        sys.exit(1)


    config = SERVERS[
        target
    ]


    server = CriblServer(
        name=target,
        url=config["url"],
        token=config["token"],
    )


    server.import_config()


if __name__ == "__main__":
    main()
