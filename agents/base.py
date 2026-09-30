"""
base.py
Agent base class, the process-side serve loop, and the client-side handle
used to talk to an agent running in another process.

An agent is any object with:
    setup()             -- acquire resources (hardware, files); called once
    handle(request)     -- dict in, dict out; dispatches to on_<kind>()
    teardown()          -- release resources; called once on exit

handle() is pure message-in / message-out, so the same agent can be driven
by the multiprocessing transport below, by a test, or later by an LLM
supervisor that exposes each on_<kind>() as a tool.
"""

import queue
import sys
import traceback

from . import protocol


class AgentError(RuntimeError):
    """Raised on the client side when an agent reports a failure or dies."""


class Agent:
    name = "agent"

    def setup(self):
        pass

    def teardown(self):
        pass

    def handle(self, request: dict) -> dict:
        method = getattr(self, "on_" + request["kind"], None)
        if method is None:
            raise ValueError(f"{self.name} agent cannot handle '{request['kind']}'")
        return method(**request["payload"]) or {}


# ---------------------------------------------------------------------------
# Process side
# ---------------------------------------------------------------------------

def serve(agent_cls, agent_kwargs: dict, inbox, outbox):
    """
    Entry point of an agent process: build the agent, run setup(), then
    answer requests from inbox on outbox until a shutdown request arrives.
    """
    # Keep child output in step with the parent's in the shared terminal.
    sys.stdout.reconfigure(line_buffering=True)

    agent = None
    try:
        agent = agent_cls(**agent_kwargs)
        agent.setup()
    except BaseException:
        outbox.put(protocol.make_reply(None, agent_cls.name, ok=False,
                                       error=traceback.format_exc()))
        return
    outbox.put(protocol.make_reply(None, agent.name, ok=True,
                                   payload={"status": protocol.READY}))

    try:
        while True:
            request = inbox.get()
            if request["kind"] == protocol.SHUTDOWN:
                break
            try:
                payload = agent.handle(request)
                reply   = protocol.make_reply(request, agent.name, ok=True,
                                              payload=payload)
            except Exception:
                reply = protocol.make_reply(request, agent.name, ok=False,
                                            error=traceback.format_exc())
            outbox.put(reply)
    except KeyboardInterrupt:
        pass
    finally:
        agent.teardown()


# ---------------------------------------------------------------------------
# Client side
# ---------------------------------------------------------------------------

class AgentHandle:
    """Start an agent in its own process and exchange messages with it."""

    def __init__(self, ctx, agent_cls, agent_kwargs: dict,
                 log: protocol.MessageLog, sender: str = "optimizer"):
        self.name    = agent_cls.name
        self.sender  = sender
        self.log     = log
        self.inbox   = ctx.Queue()
        self.outbox  = ctx.Queue()
        self.process = ctx.Process(
            target=serve,
            args=(agent_cls, agent_kwargs, self.inbox, self.outbox),
            name=f"{self.name}-agent",
        )
        self.process.start()

    def _receive(self) -> dict:
        while True:
            try:
                return self.outbox.get(timeout=1.0)
            except queue.Empty:
                if not self.process.is_alive():
                    raise AgentError(
                        f"{self.name} agent exited unexpectedly "
                        f"(exit code {self.process.exitcode})."
                    )

    def _check(self, reply: dict) -> dict:
        self.log.write("recv", self.name, reply)
        if not reply["ok"]:
            raise AgentError(f"{self.name} agent failed:\n{reply['error']}")
        return reply["payload"]

    def wait_ready(self):
        """Block until setup() in the agent process has finished."""
        self._check(self._receive())

    def request(self, kind: str, **payload) -> dict:
        """Send one request and block until its reply arrives."""
        msg = protocol.make_request(kind, self.sender, payload)
        self.log.write("send", self.name, msg)
        self.inbox.put(msg)
        return self._check(self._receive())

    def shutdown(self, timeout: float = 10.0):
        if self.process.is_alive():
            self.inbox.put(protocol.make_request(protocol.SHUTDOWN, self.sender))
            self.process.join(timeout)
        if self.process.is_alive():
            self.process.terminate()
            self.process.join()
