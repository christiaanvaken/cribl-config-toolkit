# Cribl Configuration Export / Import

Small Python utility for exporting and importing configuration from
multiple Cribl Stream instances using the Cribl REST API.

The scripts use Bearer token authentication, support multiple explicitly
configured Cribl servers, and share server configuration through
`cribl_config.py`.

## Project structure

``` text
cribl-config-toolkit/
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── cribl_config.py
├── export_cribl.py
├── import_cribl.py
└── cribl-config/
    ├── cribl01/
    │   ├── sources/
    │   ├── destinations/
    │   ├── pipelines/
    │   └── routes/
    └── cribl02/
        ├── sources/
        ├── destinations/
        ├── pipelines/
        └── routes/
```

## Requirements

Python 3 is required.

The scripts use these Python modules:

-   `requests`
-   `python-dotenv`

Install them with:

``` bash
python3 -m pip install -r requirements.txt
```

Using a virtual environment is recommended:

``` bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Configure `.env`

Create a `.env` file in the project directory. A convenient approach is
to copy `.env.example`:

``` bash
cp .env.example .env
```

Example configuration:

``` dotenv
CRIBL_SERVERS=cribl01,cribl02

CRIBL_CRIBL01_URL=https://cribl01.example.local:9000
CRIBL_CRIBL01_TOKEN=replace-with-bearer-token

CRIBL_CRIBL02_URL=https://cribl02.example.local:9000
CRIBL_CRIBL02_TOKEN=replace-with-bearer-token

CRIBL_VERIFY_SSL=true
```

`CRIBL_SERVERS` contains a comma-separated list of available targets.

For each target, configure:

``` text
CRIBL_<TARGET>_URL
CRIBL_<TARGET>_TOKEN
```

For example, target `cribl01` uses:

``` dotenv
CRIBL_CRIBL01_URL=https://cribl01.example.local:9000
CRIBL_CRIBL01_TOKEN=replace-with-bearer-token
```

Target names are converted to uppercase by `cribl_config.py` when the
corresponding environment variables are read.

## TLS verification

TLS certificate verification is enabled by default:

``` dotenv
CRIBL_VERIFY_SSL=true
```

For testing with an untrusted or self-signed certificate, verification
can be disabled:

``` dotenv
CRIBL_VERIFY_SSL=false
```

Using a trusted CA certificate is recommended instead of disabling TLS
verification.

## Export configuration

Export a single Cribl server:

``` bash
python3 export_cribl.py cribl01
```

The configuration is written to:

``` text
cribl-config/cribl01/
```

Export another target:

``` bash
python3 export_cribl.py cribl02
```

Export all configured targets:

``` bash
python3 export_cribl.py all
```

The export currently includes:

-   Sources
-   Destinations
-   Pipelines
-   Default routing table

Where applicable, each Cribl object is stored in a separate JSON file.

## Import configuration

Import requires one explicit target:

``` bash
python3 import_cribl.py cribl01
```

The importer reads configuration from:

``` text
cribl-config/cribl01/
```

and connects only to the `cribl01` server configured in `.env`.

Importing all servers at once is intentionally not supported:

``` bash
python3 import_cribl.py all
```

This reduces the chance of accidentally modifying multiple Cribl
instances.

## Dry run

The importer is configured with:

``` python
DRY_RUN = True
```

With dry-run enabled, the script determines whether resources would be
created or updated but does not make configuration changes.

Always test an import first with:

``` python
DRY_RUN = True
```

Then run:

``` bash
python3 import_cribl.py cribl01
```

Review the proposed operations. When ready to apply the changes, set:

``` python
DRY_RUN = False
```

and run the import again.

Existing resources are updated using `PATCH`, while new resources are
created using `POST`.

The importer does not delete resources that exist in Cribl but are
absent from `cribl-config/`.

## Security

The `.env` file contains Cribl Bearer tokens and must not be committed
to Git.

At minimum, `.gitignore` should contain:

``` gitignore
.env
.venv/
__pycache__/
*.pyc
```

The `.env.example` file can be committed as long as it contains only
placeholders and no real credentials.

Also review exported JSON files before committing `cribl-config/`.
Depending on the Cribl configuration, exported Sources or Destinations
may contain sensitive configuration.

## Typical workflow

1.  Export the current configuration:

    ``` bash
    python3 export_cribl.py cribl01
    ```

2.  Review or modify files under:

    ``` text
    cribl-config/cribl01/
    ```

3.  Keep `DRY_RUN = True` and test the import:

    ``` bash
    python3 import_cribl.py cribl01
    ```

4.  Review the proposed `CREATE` and `UPDATE` operations.

5.  When ready, set:

    ``` python
    DRY_RUN = False
    ```

6.  Apply the configuration:

    ``` bash
    python3 import_cribl.py cribl01
    ```

