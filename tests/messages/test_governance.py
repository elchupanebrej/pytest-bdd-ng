from pytest_bdd.script.message_capability_governance import main

def test_governance_report_generation(tmp_path):
    messages_file = tmp_path / "messages.ndjson"
    messages_file.write_text(
        '{"testCaseStarted": {"attempt": 0, "id": "123", "testCaseId": "456", "timestamp": {"seconds": 0, "nanos": 0}}}\n'
    )

    output_file = tmp_path / "governance.json"

    main(["report", "--messages-file", str(messages_file), "--output", str(output_file)])
