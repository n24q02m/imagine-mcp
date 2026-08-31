from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "cf_full_flow.py"
_spec = importlib.util.spec_from_file_location("cf_full_flow", _SCRIPT)
assert _spec is not None and _spec.loader is not None
cf_full_flow = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cf_full_flow)


def test_base64_validation_emits_only_structural_summary(capsys) -> None:
    encoded = "cHJpdmF0ZS1pbWFnZS1ieXRlcw=="

    summary = cf_full_flow._assert_base64_no_path(
        json.dumps(
            {
                "image_base64": encoded,
                "model": "private-model",
                "provider": "private-provider",
            }
        )
    )

    assert summary == {
        "status": "VERIFIED",
        "image_base64": True,
        "image_path": False,
        "decoded_bytes": 19,
    }
    output = capsys.readouterr().out
    assert encoded not in output
    assert "private-model" not in output
    assert "private-provider" not in output


@pytest.mark.parametrize(
    "payload, expected",
    [
        ("not-json-private-payload", "generate result is not valid JSON"),
        (json.dumps(["private-payload"]), "generate result must be an object"),
        (json.dumps({"image_base64": ""}), "image_base64 must be non-empty"),
        (json.dumps({"image_base64": "not valid base64"}), "image_base64 is invalid"),
        (
            json.dumps(
                {"image_base64": "cHJpdmF0ZQ==", "image_path": "private/path.png"}
            ),
            "image_path must be absent",
        ),
    ],
)
def test_base64_validation_fails_closed_without_payload_echo(
    payload: str, expected: str
) -> None:
    with pytest.raises(AssertionError, match=expected) as error:
        cf_full_flow._assert_base64_no_path(payload)

    assert payload not in str(error.value)
    assert "private" not in str(error.value)


@pytest.mark.asyncio
async def test_call_logs_metadata_without_result_or_error_payload(capsys) -> None:
    class SuccessfulSession:
        async def call_tool(self, tool, args):
            return SimpleNamespace(
                content=[SimpleNamespace(text='{"secret":"private-result"}')]
            )

    result = await cf_full_flow._call(
        SuccessfulSession(), "GENERATE_IMAGE", "generate", {"prompt": "private prompt"}
    )
    assert result == '{"secret":"private-result"}'
    output = capsys.readouterr().out
    record = json.loads(output)
    assert record == {
        "content_blocks": 1,
        "operation": "GENERATE_IMAGE",
        "status": "OK",
        "text_chars": len(result),
    }
    assert "private-result" not in output
    assert "private prompt" not in output

    class FailingSession:
        async def call_tool(self, tool, args):
            raise RuntimeError("private-provider-error")

    assert (
        await cf_full_flow._call(
            FailingSession(), "GENERATE_IMAGE", "generate", {"prompt": "private prompt"}
        )
        is None
    )
    output = capsys.readouterr().out
    assert json.loads(output) == {
        "error_type": "RuntimeError",
        "operation": "GENERATE_IMAGE",
        "status": "ERROR",
    }
    assert "private-provider-error" not in output


@pytest.mark.asyncio
async def test_call_retry_and_give_up_logs_are_metadata_only(
    capsys, monkeypatch
) -> None:
    class AwaitingSession:
        async def call_tool(self, tool, args):
            return SimpleNamespace(
                content=[
                    SimpleNamespace(
                        text='{"status":"awaiting_setup","provider_error":"private-error"}'
                    )
                ]
            )

    async def no_sleep(delay: float) -> None:
        del delay

    monkeypatch.setattr(cf_full_flow.asyncio, "sleep", no_sleep)
    assert (
        await cf_full_flow._call(
            AwaitingSession(),
            "CONFIG_STATUS",
            "config",
            {"action": "status", "prompt": "private prompt"},
            retries=1,
            delay=0,
        )
        is None
    )

    output = capsys.readouterr().out
    records = [json.loads(line) for line in output.splitlines()]
    assert [record["status"] for record in records] == ["RETRY", "GAVE_UP"]
    assert records[0] == {
        "attempt": 1,
        "operation": "CONFIG_STATUS",
        "status": "RETRY",
        "total_attempts": 1,
    }
    assert records[1] == {
        "attempts": 1,
        "operation": "CONFIG_STATUS",
        "status": "GAVE_UP",
    }
    assert "private-error" not in output
