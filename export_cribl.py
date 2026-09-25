#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import requests
import urllib3

from cribl_config import load_servers, verify_ssl


# ==============================================================================
# CONFIGURATION
# ==============================================================================

SERVERS = load_servers()

VERIFY_SSL = verify_ssl()

BASE_OUTPUT_DIR = Path("cribl-config")


# ==============================================================================
# HELPERS
# ==============================================================================

def safe_filename(name):

    return (
        name
        .replace("/", "_")
        .replace("\\", "_")
    )


def write_json(filename, data):

    filename.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with filename.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            sort_keys=True,
        )

        file.write("\n")


def show_usage():

    print()
    print("Usage:")
    print()
    print("  python3 export_cribl.py <target>")
    print()
    print("Available targets:")

    for name in SERVERS:
        print(f"  {name}")

    print("  all")
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

        self.output_dir = (
            BASE_OUTPUT_DIR
            / name
        )

        self.session = requests.Session()

        self.session.verify = VERIFY_SSL

        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        })


    # ==========================================================================
    # GET
    # ==========================================================================

    def get(self, endpoint):

        url = (
            f"{self.url}"
            f"/api/v1"
            f"{endpoint}"
        )

        print(
            f"GET {url}"
        )

        response = self.session.get(
            url,
            timeout=60,
        )

        if not response.ok:

            print()
            print("=" * 70)
            print("CRIBL API ERROR")
            print("=" * 70)
            print(f"Server      : {self.name}")
            print(f"HTTP status : {response.status_code}")
            print(f"URL         : {url}")
            print()
            print("Response:")
            print(response.text)
            print("=" * 70)
            print()

            response.raise_for_status()

        return response.json()


    # ==========================================================================
    # EXPORT COLLECTION
    # ==========================================================================

    def export_collection(
        self,
        endpoint,
        directory,
    ):

        data = self.get(
            endpoint
        )

        items = data.get(
            "items",
            [],
        )

        print(
            f"Found {len(items)} object(s)."
        )

        for item in items:

            object_id = item.get(
                "id"
            )

            if not object_id:

                print(
                    "WARNING: Object without "
                    "id skipped."
                )

                continue


            filename = (
                self.output_dir
                / directory
                / f"{safe_filename(object_id)}.json"
            )


            write_json(
                filename,
                item,
            )


            print(
                f"  -> {filename}"
            )


    # ==========================================================================
    # EXPORT ROUTES
    # ==========================================================================

    def export_routes(self):

        data = self.get(
            "/routes/default"
        )


        if isinstance(
            data.get("items"),
            list,
        ):

            if data["items"]:

                data = (
                    data["items"][0]
                )


        filename = (
            self.output_dir
            / "routes"
            / "default.json"
        )


        write_json(
            filename,
            data,
        )


        print(
            f"  -> {filename}"
        )


    # ==========================================================================
    # EXPORT
    # ==========================================================================

    def export(self):

        print()
        print("=" * 70)

        print(
            f"Exporting Cribl server: "
            f"{self.name}"
        )

        print("=" * 70)

        print(
            f"URL    : {self.url}"
        )

        print(
            f"Output : {self.output_dir}"
        )


        self.output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )


        # ----------------------------------------------------------------------
        # Sources
        # ----------------------------------------------------------------------

        print()
        print("Sources")
        print("-" * 70)

        self.export_collection(
            "/system/inputs",
            "sources",
        )


        # ----------------------------------------------------------------------
        # Destinations
        # ----------------------------------------------------------------------

        print()
        print("Destinations")
        print("-" * 70)

        self.export_collection(
            "/system/outputs",
            "destinations",
        )


        # ----------------------------------------------------------------------
        # Pipelines
        # ----------------------------------------------------------------------

        print()
        print("Pipelines")
        print("-" * 70)

        self.export_collection(
            "/pipelines",
            "pipelines",
        )


        # ----------------------------------------------------------------------
        # Routes
        # ----------------------------------------------------------------------

        print()
        print("Routes")
        print("-" * 70)

        self.export_routes()


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


    # --------------------------------------------------------------------------
    # Select targets
    # --------------------------------------------------------------------------

    if target == "all":

        targets = list(
            SERVERS.keys()
        )

    else:

        if target not in SERVERS:

            print()
            print(
                f"ERROR: Unknown target "
                f"'{target}'."
            )

            show_usage()

            sys.exit(1)

        targets = [
            target
        ]


    # --------------------------------------------------------------------------
    # Export
    # --------------------------------------------------------------------------

    failed = []


    for name in targets:

        config = SERVERS[
            name
        ]


        try:

            server = CriblServer(
                name=name,
                url=config["url"],
                token=config["token"],
            )

            server.export()


        except Exception as error:

            print()
            print(
                f"ERROR exporting "
                f"{name}: {error}"
            )

            failed.append(
                name
            )


    # --------------------------------------------------------------------------
    # Summary
    # --------------------------------------------------------------------------

    print()
    print("=" * 70)
    print("EXPORT SUMMARY")
    print("=" * 70)

    print(
        f"Targets    : "
        f"{len(targets)}"
    )

    print(
        f"Successful : "
        f"{len(targets) - len(failed)}"
    )

    print(
        f"Failed     : "
        f"{len(failed)}"
    )


    if failed:

        print()
        print("Failed targets:")

        for name in failed:

            print(
                f"  - {name}"
            )

        sys.exit(1)


    print()
    print(
        "Export completed successfully."
    )


if __name__ == "__main__":
    main()
