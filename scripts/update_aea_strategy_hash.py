# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023-2024 Valory AG
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""
Simple script to update the hash of the strategy in the AEA config file.

Usage:

python scripts/update_aea_strategy_hash.py <path_to_aea_config_file|aea_config.yaml> <strategy_hash>
Example:
"""


import re

import click


def update_aea_strategy_hash(aea_config_path: str, strategy_hash: str) -> None:
    """Update the strategy hash in the AEA config file."""

    replace_with = (
        "file_hash_to_id: ${list:[["
        + f"\"{strategy_hash.strip()}\""
        + ',["sma_strategy"]]]}'
    )

    with open(aea_config_path, "r", encoding="utf8") as file:
        filedata = file.read()

    # We search uintil ",

    regex = r"file_hash_to_id: \$\{list:\[\[\"[a-zA-Z0-9]*\",\[\"sma_strategy\"\]\]\]\}"

    newdata = re.sub(regex, replace_with, filedata)

    with open(aea_config_path, "w", encoding="utf8") as file:
        file.write(newdata)


@click.command()
@click.argument("aea_config_path", type=click.Path(exists=True))
@click.argument("strategy_hash", type=str)
def main(aea_config_path: str, strategy_hash: str) -> None:
    """Update the strategy hash in the AEA config file."""
    update_aea_strategy_hash(aea_config_path, strategy_hash)
    print("Strategy hash updated successfully.")


if __name__ == "__main__":
    main()  # pylint: disable=no-value-for-parameter
