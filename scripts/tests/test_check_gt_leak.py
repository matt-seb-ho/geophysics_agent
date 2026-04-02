import os
import tempfile
import json
import shutil
from pathlib import Path
from check_gt_leak import check_leaks

def run_tests():
    print("Running check_gt_leak tests...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        run_dir = tmp_path / "run"
        gt_dir = tmp_path / "gt"
        run_dir.mkdir()
        gt_dir.mkdir()
        
        # Test 1: No leak
        setup_task(run_dir, gt_dir, "task_no_leak", "mock_gt.xml", "<secret>data with lots of padding so it passes length</secret>", [
            create_tool_call_json("content", "<normal>data with lots of padding so it passes length</normal>")
        ])
        
        # Test 2: Partial substring (should NOT be detected as leak)
        setup_task(run_dir, gt_dir, "task_partial", "mock_gt.xml", "<secret>super secret data with lots of padding</secret>", [
            create_tool_call_json("content", "I found <secret>super secret data with lots of... wait no.")
        ])
        
        # Test 3: Exact match in Read File config (content) - LEAK
        setup_task(run_dir, gt_dir, "task_leak_read", "mock_truth.xml", "<xml>exact secret that is very long indeed wow</xml>", [
            create_tool_call_json("content", "Here is the file:\n<xml>exact secret that is very long indeed wow</xml>\nBye.")
        ])
        
        # Test 4: Exact match in Terminal (stdout) - LEAK
        setup_task(run_dir, gt_dir, "task_leak_term", "mock_truth2.xml", "<xml>another secret that is very very long yup</xml>", [
            create_tool_call_json("stdout", "cat mock_truth2.xml\n<xml>another secret that is very very long yup</xml>")
        ])
        
        # Test 5: Exact match in Agent Message (NOT tool output) - Should NOT trigger according to current logic (only tool outputs are checked)
        agent_msg = json.dumps({
            "params": {
                "update": {
                    "sessionUpdate": "agent_message_chunk",
                    "content": {"text": "<xml>agent secret over thirty characters long</xml>"}
                }
            }
        })
        setup_task(run_dir, gt_dir, "task_agent_msg_no_leak", "mock_truth3.xml", "<xml>agent secret over thirty characters long</xml>", [
            agent_msg
        ])
        
        # Run checker on each task to isolate tests
        for test_name, expected in [
            ("task_no_leak", False),
            ("task_partial", False),
            ("task_leak_read", True),
            ("task_leak_term", True),
            ("task_agent_msg_no_leak", False)
        ]:
            print(f"\n--- Checking test isolation for: {test_name} (Expected: {expected}) ---")
            # Create isolated parent dirs
            iso_run = tmp_path / f"iso_run_{test_name}"
            iso_gt = tmp_path / f"iso_gt_{test_name}"
            iso_run.mkdir()
            iso_gt.mkdir()
            # Move the specific task into this isolated structure temporarily
            shutil.copytree(run_dir / test_name, iso_run / test_name)
            shutil.copytree(gt_dir / test_name, iso_gt / test_name)
            res = check_leaks(iso_run, iso_gt)
            assert res == expected, f"Test failed for {test_name}. Expected {expected}, got {res}"
            
    print("\nAll individual checks ready, running full suite:")

def test_full_suite():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        run_dir = tmp_path / "run"
        gt_dir = tmp_path / "gt"
        run_dir.mkdir()
        gt_dir.mkdir()
        
        # Setup all tasks
        setup_task(run_dir, gt_dir, "task1_no_leak", "mock.xml", "A" * 50, [
            create_tool_call_json("content", "B" * 50)
        ])
        setup_task(run_dir, gt_dir, "task2_leak", "mock2.xml", "SECRET" * 10, [
            create_tool_call_json("content", "SECRET" * 10)
        ])
        
        leaks_found = check_leaks(run_dir, gt_dir)
        assert leaks_found == True, "Full suite should return True for leaks found"
        print("Integration test passed!")

def setup_task(base_run, base_gt, task_name, gt_filename, gt_content, acpx_lines):
    task_run = base_run / task_name
    task_run.mkdir(parents=True, exist_ok=True)
    
    task_gt = base_gt / task_name
    task_gt.mkdir(parents=True, exist_ok=True)
    
    # Write GT file
    with open(task_gt / gt_filename, "w") as f:
        f.write(gt_content)
        
    # Write eval_metadata
    with open(task_run / "eval_metadata.json", "w") as f:
        json.dump({"blocked_gt_xml_filenames": [gt_filename]}, f)
        
    # Write acpx_output.json
    with open(task_run / "acpx_output.json", "w") as f:
        for line in acpx_lines:
            f.write(line + "\n")

def create_tool_call_json(key, value):
    return json.dumps({
        "params": {
            "update": {
                "sessionUpdate": "tool_call_update",
                "status": "completed",
                "rawOutput": {
                    key: value
                }
            }
        }
    })

if __name__ == "__main__":
    run_tests()
    test_full_suite()
    print("All tests successfully completed.")
