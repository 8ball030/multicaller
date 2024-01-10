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

"""This package contains the implementation of ."""
import json
import threading
import time
from asyncio import Future
from typing import Any, Callable, Dict, Optional, Tuple, cast

from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue
from aea.skills.behaviours import SimpleBehaviour

from packages.valory.connections.ipfs.connection import IpfsDialogues
from packages.valory.connections.ipfs.connection import PUBLIC_ID as IPFS_CONNECTION_ID
from packages.valory.protocols.ipfs import IpfsMessage
from packages.valory.protocols.ipfs.dialogues import IpfsDialogue
from packages.valory.skills.ipfs_package_downloader.models import Params
from packages.valory.skills.ipfs_package_downloader.utils.ipfs import (
    ComponentPackageLoader,
)


class IpfsPackageDownloader(SimpleBehaviour):
    """A class to execute tasks."""

    def __init__(self, **kwargs: Any):
        """Initialise the agent."""
        super().__init__(**kwargs)
        # we only want to execute one task at a time, for the time being
        self._tools_to_file_hash: Dict[str, str] = {}
        self._all_tools: Dict[str, Tuple[str, str]] = {}
        self._inflight_tool_req: Optional[str] = None
        self._done_task: Optional[Dict[str, Any]] = None
        self._last_polling: Optional[float] = None
        self._invalid_request = False
        self._async_result: Optional[Future] = None

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("Setting up IpfsPackageDownloader")
        self._tools_to_file_hash = {
            value: key
            for key, values in self.params.file_hash_to_tools.items()
            for value in values
        }

    def act(self) -> None:
        """Implement the act."""
        self._download_tools()
        self._execute_task()
        self._check_for_new_reqs()

    @property
    def done_tasks_lock(self) -> threading.Lock:
        """Get done_tasks_lock."""
        return self.context.shared_state[DONE_TASKS_LOCK]

    @property
    def params(self) -> Params:
        """Get the parameters."""
        return cast(Params, self.context.params)

    @property
    def request_id_to_num_timeouts(self) -> Dict[int, int]:
        """Maps the request id to the number of times it has timed out."""
        return self.params.request_id_to_num_timeouts

    def count_timeout(self, request_id: int) -> None:
        """Increase the timeout for a request."""
        self.request_id_to_num_timeouts[request_id] += 1

    def timeout_limit_reached(self, request_id: int) -> bool:
        """Check if the timeout limit has been reached."""
        return self.params.timeout_limit <= self.request_id_to_num_timeouts[request_id]

    # @property
    # def pending_tasks(self) -> List[Dict[str, Any]]:
    #     """Get pending_tasks."""
    #     return self.context.shared_state[PENDING_TASKS]

    # @property
    # def done_tasks(self) -> List[Dict[str, Any]]:
    #     """Get done_tasks."""
    #     return self.context.shared_state[DONE_TASKS]

    def _has_executing_task_timed_out(self) -> bool:
        """Check if the executing task timed out."""
        if self._executing_task is None:
            return False
        timeout_deadline = self._executing_task.get("timeout_deadline", None)
        if timeout_deadline is None:
            return False
        return timeout_deadline <= time.time()

    def _download_tools(self) -> None:
        """Download tools."""
        if self._inflight_tool_req is not None:
            # there already is a req in flight
            return
        if len(self._tools_to_file_hash) == len(self._all_tools):
            # we already have all the tools
            return
        for tool, file_hash in self._tools_to_file_hash.items():
            if tool in self._all_tools:
                continue
            # read one at a time
            ipfs_msg, message = self._build_ipfs_get_file_req(file_hash)
            self._inflight_tool_req = tool
            self.send_message(ipfs_msg, message, self._handle_get_tool)
            return

    def _handle_get_tool(self, message: IpfsMessage, dialogue: Dialogue) -> None:
        """Handle get tool response"""
        _component_yaml, tool_py, callable_method = ComponentPackageLoader.load(
            message.files
        )
        tool_req = cast(str, self._inflight_tool_req)
        self._all_tools[tool_req] = tool_py, callable_method
        self._inflight_tool_req = None

    def send_message(
        self, msg: Message, dialogue: Dialogue, callback: Callable
    ) -> None:
        """Send message."""
        self.context.outbox.put_message(message=msg)
        nonce = dialogue.dialogue_label.dialogue_reference[0]
        self.params.req_to_callback[nonce] = callback
        self.params.in_flight_req = True

    def _build_ipfs_message(
        self,
        performative: IpfsMessage.Performative,
        timeout: Optional[float] = None,
        **kwargs: Any,
    ) -> Tuple[IpfsMessage, IpfsDialogue]:
        """Builds an IPFS message."""
        ipfs_dialogues = cast(IpfsDialogues, self.context.ipfs_dialogues)
        message, dialogue = ipfs_dialogues.create(
            counterparty=str(IPFS_CONNECTION_ID),
            performative=performative,
            timeout=timeout,
            **kwargs,
        )
        return message, dialogue

    def _build_ipfs_get_file_req(
        self,
        ipfs_hash: str,
        timeout: Optional[float] = None,
    ) -> Tuple[IpfsMessage, IpfsDialogue]:
        """
        Builds a GET_FILES IPFS request.

        :param ipfs_hash: the ipfs hash of the file/dir to download.
        :param timeout: timeout for the request.
        :returns: the ipfs message, and its corresponding dialogue.
        """
        message, dialogue = self._build_ipfs_message(
            performative=IpfsMessage.Performative.GET_FILES,  # type: ignore
            ipfs_hash=ipfs_hash,
            timeout=timeout,
        )
        return message, dialogue
