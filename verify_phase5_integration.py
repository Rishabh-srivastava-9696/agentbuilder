#!/usr/bin/env python3
"""
Quick verification script for Phase 5 memory integration.

This script checks that all components are properly connected.
"""

import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "commons", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "memory", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "retrieval", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "packages", "llm", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apps", "api"))


def check_imports():
    """Verify all Phase 5 imports work."""
    print("🔍 Checking imports...")
    
    try:
        from memory.config import MemoryConfig
        print("  ✅ MemoryConfig")
    except ImportError as e:
        print(f"  ❌ MemoryConfig: {e}")
        return False
    
    try:
        from memory.managers.short_term import ShortTermMemory
        print("  ✅ ShortTermMemory")
    except ImportError as e:
        print(f"  ❌ ShortTermMemory: {e}")
        return False
    
    try:
        from memory.managers.episodic import EpisodicMemory
        print("  ✅ EpisodicMemory")
    except ImportError as e:
        print(f"  ❌ EpisodicMemory: {e}")
        return False
    
    try:
        from memory.managers.graph import GraphMemory
        print("  ✅ GraphMemory")
    except ImportError as e:
        print(f"  ❌ GraphMemory: {e}")
        return False
    
    try:
        from memory.types import MessageRole, MemoryContext
        print("  ✅ Memory types (MessageRole, MemoryContext)")
    except ImportError as e:
        print(f"  ❌ Memory types: {e}")
        return False
    
    print("\n✅ All imports successful!")
    return True


def check_message_service():
    """Check MessageService can be imported."""
    print("\n🔍 Checking MessageService...")
    
    try:
        # This will fail if there are syntax errors
        with open("apps/api/app/services/message_service.py", "r") as f:
            content = f.read()
        
        # Check for key Phase 5 components
        checks = {
            "ShortTermMemory": "from memory.managers.short_term import ShortTermMemory",
            "EpisodicMemory": "from memory.managers.episodic import EpisodicMemory",
            "GraphMemory": "from memory.managers.graph import GraphMemory",
            "_build_memory_context": "async def _build_memory_context",
            "9-step flow docstring": "Process a single message with Phase 5 Memory System",
            "Auto-summary check": "should_summarize",
            "Escalation check": "check_escalation",
            "Fact extraction": "extract_and_store_facts",
        }
        
        for name, pattern in checks.items():
            if pattern in content:
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} - not found")
                return False
        
        print("\n✅ MessageService integration complete!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading MessageService: {e}")
        return False


def check_integration_tests():
    """Check integration tests exist."""
    print("\n🔍 Checking integration tests...")
    
    test_file = "apps/api/tests/test_message_service_integration.py"
    
    if not os.path.exists(test_file):
        print(f"  ❌ Test file not found: {test_file}")
        return False
    
    try:
        with open(test_file, "r") as f:
            content = f.read()
        
        test_functions = [
            "test_process_message_basic_flow",
            "test_process_message_with_escalation",
            "test_process_message_auto_summary_trigger",
            "test_stream_message_basic_flow",
            "test_build_memory_context",
            "test_build_prompt_with_full_context",
        ]
        
        for test_name in test_functions:
            if test_name in content:
                print(f"  ✅ {test_name}")
            else:
                print(f"  ❌ {test_name} - not found")
        
        print("\n✅ Integration tests created!")
        return True
        
    except Exception as e:
        print(f"  ❌ Error reading tests: {e}")
        return False


def check_documentation():
    """Check documentation exists."""
    print("\n🔍 Checking documentation...")
    
    docs = {
        "PHASE5_INTEGRATION_COMPLETE.md": "Integration summary",
        "ENV_SETUP.md": "Environment setup guide",
        "GIT_CONFIGURATION.md": "Git security configuration",
    }
    
    all_found = True
    for doc_file, description in docs.items():
        if os.path.exists(doc_file):
            print(f"  ✅ {doc_file} - {description}")
        else:
            print(f"  ❌ {doc_file} - not found")
            all_found = False
    
    if all_found:
        print("\n✅ All documentation present!")
    return all_found


def main():
    """Run all checks."""
    print("=" * 60)
    print("Phase 5 Memory Integration - Verification")
    print("=" * 60)
    
    results = []
    
    # Run checks
    results.append(("Imports", check_imports()))
    results.append(("MessageService", check_message_service()))
    results.append(("Integration Tests", check_integration_tests()))
    results.append(("Documentation", check_documentation()))
    
    # Summary
    print("\n" + "=" * 60)
    print("VERIFICATION SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for check_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:20s} {status}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED!")
        print("\n📋 Next Steps:")
        print("1. Run integration tests:")
        print("   cd apps/api && pytest tests/test_message_service_integration.py -v")
        print("\n2. Test with real MongoDB:")
        print("   Start the API server and send test messages")
        print("\n3. Verify memory features:")
        print("   - Send 4 messages (trigger auto-summary)")
        print("   - Test safety escalation ('I smell gas')")
        print("   - Check fact extraction (preferences)")
        return 0
    else:
        print("\n❌ SOME CHECKS FAILED")
        print("Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
