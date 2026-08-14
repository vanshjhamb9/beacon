from communication_gateway.email.gmail import GmailProvider
from communication_gateway.models.types import ChannelType, ProviderName


def test_gmail_fetch_inbound_replies_maps_inbox_messages(monkeypatch) -> None:
    provider = GmailProvider(access_token="token", daily_quota=10)

    def fake_request(method: str, path: str, **kwargs):
        if path == "/users/me/history":
            return {
                "historyId": "200",
                "history": [{"messagesAdded": [{"message": {"id": "m1"}}, {"message": {"id": "m2"}}]}],
            }
        if path.endswith("/m1"):
            return {
                "id": "m1",
                "threadId": "t1",
                "labelIds": ["INBOX"],
                "snippet": "Thanks",
                "payload": {
                    "headers": [
                        {"name": "From", "value": "prospect@example.com"},
                        {"name": "Subject", "value": "Re: Hello"},
                    ],
                    "body": {},
                    "parts": [],
                },
            }
        if path.endswith("/m2"):
            return {"id": "m2", "threadId": "t1", "labelIds": ["SENT"], "snippet": "out", "payload": {"headers": []}}
        return {}

    monkeypatch.setattr(provider, "_request", fake_request)
    events, next_id = provider.fetch_inbound_replies(start_history_id="100")
    assert next_id == "200"
    assert len(events) == 1
    assert events[0].provider == ProviderName.GMAIL
    assert events[0].channel == ChannelType.EMAIL
    assert events[0].event_type == "reply"
    assert events[0].from_address == "prospect@example.com"
